#!/usr/bin/env python3
# server — FastAPI app: static site serving, admin panel, XML-RPC, sync/regen triggers
# Author: Pito Salas and Claude Code
# Version: 3
# Created: 2026-09-08
# Updated: 2026-09-09
# Open Source Under MIT license
"""
FastAPI server for Salasblog2 - serves static files + API endpoints.
Includes Blogger API (XML-RPC) support for blog editors.
"""

import os
import random
import time
import yaml
import xmlrpc.client as xmlrpc_client
import logging
import subprocess
import asyncio
import json
import shutil
import re
import frontmatter
import mimetypes
from pathlib import Path
from datetime import datetime, date
from typing import List
from dataclasses import dataclass
from fastapi import (
    FastAPI,
    HTTPException,
    Request,
    Form,
    UploadFile,
    File,
    BackgroundTasks,
)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from jinja2 import Environment, FileSystemLoader
from salasblog2.generator import SiteGenerator
from salasblog2.raindrop import RaindropDownloader
from salasblog2.blogger_api import BloggerAPI
from salasblog2.scheduler import get_scheduler
from salasblog2.utils import process_markdown_to_html, top_tags_by_frequency, BLOG_TAGS
from salasblog2.stats import get_counter
from salasblog2.visitor_type import classify_visitor
from salasblog2.propose import get_proposed_posts, get_proposed_drops, DropFilter
from salasblog2.draft_generator import generate_draft_from_drop, save_draft

# Global status tracking
sync_status = {"running": False, "message": "Ready"}
regen_status = {"running": False, "message": "Ready"}

# Process activity tracking
_server_start_time = datetime.now()
_generation_count = 0
_last_generation_time = None


def _load_yaml_config() -> dict:
    """Load config.yaml from project root, returning defaults if missing."""
    for candidate in [
        Path(__file__).parent.parent.parent / "config.yaml",
        Path("config.yaml"),
    ]:
        if candidate.exists():
            with open(candidate) as f:
                return yaml.safe_load(f) or {}
    return {}


yaml_config = _load_yaml_config()


def _cfg(*keys, default=None):
    """Read a nested value from yaml_config."""
    node = yaml_config
    for k in keys:
        if not isinstance(node, dict):
            return default
        node = node.get(k, default)
        if node is default:
            return default
    return node


# Global configuration
config = {
    "root_dir": None,
    "output_dir": None,
    "templates_dir": None,
    "admin_password": None,
    "session_secret": None,
    "jinja_env": None,
}


def validate_environment_and_setup():
    """Validate all environment variables and system assumptions at startup"""
    logger = logging.getLogger(__name__)

    # Set up paths
    config["root_dir"] = Path(__file__).parent.parent.parent
    config["output_dir"] = config["root_dir"] / "output"
    config["templates_dir"] = config["root_dir"] / "templates"

    # Validate critical directories exist
    if not config["templates_dir"].exists():
        # Log detailed path information for debugging
        logger.error(f"Templates directory not found: {config['templates_dir']}")
        logger.error(f"__file__ = {__file__}")
        logger.error(f"Root dir = {config['root_dir']}")
        logger.error(f"Root dir exists: {config['root_dir'].exists()}")
        logger.error(
            f"Contents of root dir: {list(config['root_dir'].iterdir()) if config['root_dir'].exists() else 'N/A'}"
        )
        error_msg = f"Templates directory not found: {config['templates_dir']}"
        raise RuntimeError(error_msg)

    # Set up Jinja2 environment
    config["jinja_env"] = Environment(loader=FileSystemLoader(config["templates_dir"]))

    # Store configuration
    config["admin_password"] = os.getenv("ADMIN_PASSWORD")
    config["session_secret"] = os.getenv("SESSION_SECRET")

    # Create output directory if needed
    config["output_dir"].mkdir(exist_ok=True)

    logger.info("✓ Environment validation complete")
    logger.info(f"✓ Root directory: {config['root_dir']}")
    logger.info(f"✓ Output directory: {config['output_dir']}")
    logger.info(f"✓ Templates directory: {config['templates_dir']}")

    return True


def setup_logging():
    """Configure logging with custom format"""
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level_value = getattr(logging, log_level, logging.INFO)

    log_format = "%(asctime)s [%(levelname)s] %(message)s"
    date_format = "%M:%S"

    logging.basicConfig(
        level=log_level_value, format=log_format, datefmt=date_format, force=True
    )

    # Configure uvicorn loggers
    formatter = logging.Formatter(log_format, datefmt=date_format)
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
        logger_obj = logging.getLogger(logger_name)
        logger_obj.setLevel(log_level_value)
        for handler in logger_obj.handlers:
            handler.setFormatter(formatter)


def _check_single_instance():
    """Check if this is the only instance running and error if not."""
    logger = logging.getLogger(__name__)

    # Only check on Fly.io (has FLY_APP_NAME environment variable)
    if not os.getenv("FLY_APP_NAME"):
        logger.info("Not running on Fly.io, skipping instance check")
        return

    try:
        # Get list of machines for this app
        result = subprocess.run(
            ["fly", "machines", "list", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            machines = json.loads(result.stdout)

            # Count running machines
            running_machines = [m for m in machines if m.get("state") == "started"]

            if len(running_machines) > 1:
                machine_ids = [m.get("id", "unknown") for m in running_machines]
                error_msg = f"CRITICAL: Multiple instances detected! Running machines: {machine_ids}. This app requires exactly 1 machine for data consistency."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                logger.info(
                    f"Single instance check passed: {len(running_machines)} machine(s) running"
                )
        else:
            logger.warning(f"Could not check machine count: {result.stderr}")

    except subprocess.TimeoutExpired:
        logger.warning("Timeout checking machine count")
    except FileNotFoundError:
        logger.warning("fly CLI not available, cannot check machine count")
    except Exception as e:
        logger.warning(f"Error checking machine count: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage FastAPI lifecycle - start/stop background services."""
    logger = logging.getLogger(__name__)

    # Startup
    logger.info("Starting Salasblog2 server")

    # Setup logging first
    setup_logging()

    # Validate environment and setup configuration
    validate_environment_and_setup()

    # Skip mounting static files - using custom endpoints instead
    # mount_static_files()

    # Check if we're the only instance running
    _check_single_instance()

    scheduler = get_scheduler()
    scheduler.start_scheduler()

    # Pre-generate stats cache once and schedule refresh every 60 seconds
    # Write placeholder so the file exists immediately
    output_dir = config.get("output_dir")
    if output_dir:
        (output_dir / "admin-stats.html").write_text(
            _STATS_PLACEHOLDER, encoding="utf-8"
        )
    try:
        generate_stats_cache()
    except Exception as e:
        logger.warning("Initial stats cache generation failed: %s", e)

    try:
        generate_posts_index_cache()
    except Exception as e:
        logger.warning("Initial posts index cache generation failed: %s", e)

    def _stats_cache_job():
        try:
            generate_stats_cache()
        except Exception as ex:
            logging.getLogger(__name__).warning("Stats cache refresh failed: %s", ex)

    def posts_index_cache_job():
        try:
            generate_posts_index_cache()
        except Exception as ex:
            logging.getLogger(__name__).warning(
                "Posts index cache refresh failed: %s", ex
            )

    import schedule as _sched

    _sched.every(_cfg("stats", "cache_refresh_seconds", default=60)).seconds.do(
        _stats_cache_job
    )
    _sched.every(_cfg("posts_index", "cache_refresh_seconds", default=300)).seconds.do(
        posts_index_cache_job
    )

    yield

    # Shutdown
    logger.info("Shutting down Salasblog2 server")
    scheduler.stop_scheduler()


# Create FastAPI app with validated configuration
app = FastAPI(
    title="Salasblog2",
    description="Static site generator with API endpoints",
    lifespan=lifespan,
)

# Add session middleware — read directly from env since middleware registers before lifespan
app.add_middleware(
    SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "fallback-dev-key")
)


# Custom endpoints to fix FastAPI StaticFiles HEAD/GET inconsistency
def _safe_resolve(base_dir: Path, file_path: str) -> Path | None:
    """Resolve file_path within base_dir, blocking traversal, symlink escapes, and hidden files."""
    if any(part.startswith(".") for part in Path(file_path).parts):
        return None
    full_path = (base_dir / file_path).resolve()
    if not full_path.is_relative_to(base_dir.resolve()):
        return None
    return full_path


@app.api_route("/static/{file_path:path}", methods=["GET", "HEAD"])
async def serve_static_files(file_path: str, request: Request):
    """Custom static file serving with consistent GET/HEAD behavior"""
    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="No output directory configured")

    full_path = _safe_resolve(config["output_dir"] / "static", file_path)
    if full_path is None or not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    # Use mimetypes module for automatic MIME type detection
    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        if full_path.suffix == ".css":
            content_type = "text/css"
        elif full_path.suffix == ".js":
            content_type = "application/javascript"
        elif full_path.suffix == ".html":
            content_type = "text/html"
        else:
            content_type = "application/octet-stream"

    try:
        content = full_path.read_bytes() if request.method == "GET" else b""
    except (PermissionError, OSError):
        raise HTTPException(status_code=404, detail="Not found")
    return Response(content=content, media_type=content_type)


@app.api_route("/blog/{file_path:path}", methods=["GET", "HEAD"])
async def serve_blog_files(file_path: str, request: Request):
    """Custom blog file serving with consistent GET/HEAD behavior"""
    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="Not found")

    full_path = config["output_dir"] / "blog" / file_path

    # Handle directory index
    if full_path.is_dir():
        full_path = full_path / "index.html"

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        content_type = "text/html"

    if request.method == "GET" and str(full_path).endswith(".html"):
        vtype = classify_visitor(
            request.headers.get("user-agent", ""),
            request.headers.get("accept-language", ""),
        )
        get_counter().increment(f"/blog/{file_path}", vtype)

    # Return content for GET, empty for HEAD
    content = full_path.read_bytes() if request.method == "GET" else b""
    return Response(content=content, media_type=content_type)


@app.api_route("/tags/{file_path:path}", methods=["GET", "HEAD"])
async def serve_tags_files(file_path: str, request: Request):
    """Serve tag index pages"""
    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="Not found")

    full_path = config["output_dir"] / "tags" / file_path

    if full_path.is_dir():
        full_path = full_path / "index.html"

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        content_type = "text/html"

    content = full_path.read_bytes() if request.method == "GET" else b""
    return Response(content=content, media_type=content_type)


@app.api_route("/pages/{file_path:path}", methods=["GET", "HEAD"])
async def serve_pages_files(file_path: str, request: Request):
    """Custom pages file serving with consistent GET/HEAD behavior"""
    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="Not found")

    full_path = config["output_dir"] / "pages" / file_path

    # Handle directory index
    if full_path.is_dir():
        full_path = full_path / "index.html"

    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")

    if request.method == "GET" and str(full_path).endswith(".html"):
        vtype = classify_visitor(
            request.headers.get("user-agent", ""),
            request.headers.get("accept-language", ""),
        )
        get_counter().increment(f"/pages/{file_path}", vtype)

    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        content_type = "text/html"

    # Return content for GET, empty for HEAD
    content = full_path.read_bytes() if request.method == "GET" else b""
    return Response(content=content, media_type=content_type)


@app.api_route("/raindrops/{file_path:path}", methods=["GET", "HEAD"])
async def serve_raindrops_files(file_path: str, request: Request):
    """Custom raindrops file serving with consistent GET/HEAD behavior"""
    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="Not found")

    base_dir = config["output_dir"] / "raindrops"
    full_path = (
        _safe_resolve(base_dir, file_path) if file_path else base_dir / "index.html"
    )
    if full_path is None:
        raise HTTPException(status_code=404, detail="Not found")

    try:
        # Handle directory index
        if full_path.is_dir():
            full_path = full_path / "index.html"
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="Not found")
    except (PermissionError, OSError):
        raise HTTPException(status_code=404, detail="Not found")

    if request.method == "GET" and str(full_path).endswith(".html"):
        vtype = classify_visitor(
            request.headers.get("user-agent", ""),
            request.headers.get("accept-language", ""),
        )
        get_counter().increment(f"/raindrops/{file_path}", vtype)

    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        content_type = "text/html"

    try:
        content = full_path.read_bytes() if request.method == "GET" else b""
    except (PermissionError, OSError):
        raise HTTPException(status_code=404, detail="Not found")
    return Response(content=content, media_type=content_type)


# Mount static files if output directory exists
def mount_static_files():
    if config["output_dir"] and config["output_dir"].exists():
        logging.getLogger(__name__).info(
            f"mounting static directory at {config['output_dir'] / 'static'}"
        )
        # Mount static assets (CSS, JS, images, etc.) - this handles proper MIME types automatically
        app.mount(
            "/static",
            StaticFiles(directory=config["output_dir"] / "static"),
            name="static",
        )

        logging.getLogger(__name__).info(
            f"mounting blog content at {config['output_dir'] / 'blog'}"
        )
        # Mount blog content directory
        blog_dir = config["output_dir"] / "blog"
        if blog_dir.exists():
            app.mount("/blog", StaticFiles(directory=blog_dir, html=True), name="blog")

        logging.getLogger(__name__).info(
            f"mounting pages content at {config['output_dir'] / 'pages'}"
        )
        # Mount pages content directory
        pages_dir = config["output_dir"] / "pages"
        if pages_dir.exists():
            app.mount(
                "/pages", StaticFiles(directory=pages_dir, html=True), name="pages"
            )
    else:
        logging.getLogger(__name__).error("No Output Directory Found")


# Authentication helpers
def is_admin_authenticated(request: Request) -> bool:
    """Check if admin is authenticated via session"""
    return request.session.get("admin_authenticated", False)


def render_template(template_name: str, context: dict = None) -> str:
    """Render Jinja2 template with context"""
    if context is None:
        context = {}

    template = config["jinja_env"].get_template(template_name)
    return template.render(**context)


# Shared content management helpers
def get_content_directory(content_type: str) -> Path:
    """Get directory for content type using volume-first logic (same as generator)"""
    volume_content_dir = Path("/data/content")
    if volume_content_dir.exists():
        content_dir = volume_content_dir
    else:
        content_dir = config["root_dir"] / "content"

    return content_dir / content_type


def create_filename_for_content(title: str, date: str, content_type: str) -> str:
    """Generate filename based on content type"""
    safe_title = re.sub(r"[^\w\s-]", "", title.lower())
    safe_title = re.sub(r"[-\s]+", "-", safe_title)
    safe_title = safe_title.strip("-")

    if content_type == "blog":
        return f"{date}-{safe_title}.md"  # Date prefix for blog posts
    else:  # pages
        return f"{safe_title}.md"  # No date prefix for pages


def load_content_item(filename: str, content_type: str):
    """Load and parse frontmatter for any content type"""
    content_dir = get_content_directory(content_type)
    content_file = content_dir / filename

    if not content_file.exists():
        raise HTTPException(
            status_code=404, detail=f"{content_type.title()} not found: {filename}"
        )

    try:
        with open(content_file, "r", encoding="utf-8") as f:
            item = frontmatter.load(f)

        return {
            "title": item.metadata.get("title", ""),
            "date": item.metadata.get("date", ""),
            "type": item.metadata.get(
                "type", content_type.rstrip("s")
            ),  # 'blog' or 'page'
            "tags": item.metadata.get("tags", []),
            "category": item.metadata.get("category", ""),
            "image_size": item.metadata.get("image_size", ""),
            "content": item.content,
            "loaded_mtime": content_file.stat().st_mtime,
        }
    except Exception as e:
        logging.getLogger(__name__).error(
            f"Error loading {content_type} {filename}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error loading {content_type}: {str(e)}"
        )


def check_no_concurrent_edit(content_file: Path, loaded_mtime: str):
    """Reject a save if the file changed on disk since the editor loaded it.

    `loaded_mtime` is the mtime the edit form was rendered with (see
    load_content_item), sent back as a hidden field. An empty/missing value
    (e.g. an old cached page, or a client that doesn't send it) skips the
    check rather than blocking the save — this is a best-effort conflict
    warning, not a hard lock.
    """
    if not loaded_mtime:
        return
    try:
        current_mtime = content_file.stat().st_mtime
        if abs(current_mtime - float(loaded_mtime)) > 0.001:
            raise HTTPException(
                status_code=409,
                detail=(
                    "This was changed elsewhere since you opened it. "
                    "Reload the page to see the latest version before saving over it."
                ),
            )
    except (ValueError, OSError) as e:
        logging.getLogger(__name__).warning(
            f"Skipping concurrency check for {content_file} — malformed mtime "
            f"or file briefly unreadable: {e}"
        )
        return


@dataclass
class ContentFields:
    """Frontmatter + body fields for a blog post or page, as submitted by
    the create/edit forms and written to disk by save_content_item()."""

    title: str
    date: str
    item_type: str
    content: str
    tags: list
    image_size: str = ""
    category: str = ""


def save_content_item(filename: str, content_type: str, fields: ContentFields) -> float:
    """Write content item to disk. Regeneration is handled separately as a
    background task. Returns the new file's mtime, for the concurrency check
    on subsequent edits (see save_edited_post/save_edited_page)."""
    logger = logging.getLogger(__name__)

    content_dir = get_content_directory(content_type)
    content_dir.mkdir(parents=True, exist_ok=True)
    content_file = content_dir / filename

    try:
        item = frontmatter.Post(fields.content.strip())
        item.metadata = {
            "title": fields.title.strip(),
            "date": fields.date,
            "type": fields.item_type,
            "tags": fields.tags,
        }
        if fields.image_size:
            item.metadata["image_size"] = fields.image_size
        if fields.category:
            item.metadata["category"] = fields.category.strip()

        with open(content_file, "w", encoding="utf-8") as f:
            f.write(frontmatter.dumps(item))
            f.flush()
            os.fsync(f.fileno())

        logger.info(f"{content_type.title()} saved successfully: {filename}")
        return content_file.stat().st_mtime
    except Exception as e:
        logger.error(f"Error saving {content_type} {filename}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error saving {content_type}: {str(e)}"
        )


def _regenerate_in_background(filename: str, content_type: str):
    """Run incremental site regeneration — intended for use as a background task."""
    global _generation_count, _last_generation_time
    logger = logging.getLogger(__name__)
    logger.info(f"Background regeneration START for {content_type}: {filename}")
    try:
        generator = SiteGenerator()
        generator.incremental_regenerate_post(filename, content_type)
        _generation_count += 1
        _last_generation_time = datetime.now()
        logger.info(f"Background regeneration DONE for {content_type}: {filename}")
    except Exception as e:
        logger.error(
            f"Background regeneration FAILED for {content_type} {filename}: {e}"
        )


def delete_content_item(content_dir: Path, filename: str):
    """Delete a content file from disk. `content_dir` is already volume-aware
    (see get_content_directory), so this is the one and only copy to remove."""
    content_file = content_dir / filename
    if not content_file.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")
    content_file.unlink()
    logging.getLogger(__name__).info(f"Deleted content file: {content_file}")


def regenerate_after_deletion_in_background(filename: str, content_type: str):
    """Run incremental site regeneration after a delete — intended for use as
    a background task."""
    logger = logging.getLogger(__name__)
    logger.info(
        f"Background deletion regeneration START for {content_type}: {filename}"
    )
    try:
        generator = SiteGenerator()
        generator.incremental_regenerate_after_deletion(filename, content_type)
        logger.info(
            f"Background deletion regeneration DONE for {content_type}: {filename}"
        )
    except Exception as e:
        logger.error(
            f"Background deletion regen FAILED for {content_type} {filename}: {e}"
        )


# API Routes
@app.get("/")
async def serve_home(request: Request):
    """Serve the home page"""
    vtype = classify_visitor(
        request.headers.get("user-agent", ""),
        request.headers.get("accept-language", ""),
    )
    get_counter().increment("/", vtype)
    home_file = config["output_dir"] / "index.html"
    if home_file.exists():
        return HTMLResponse(content=home_file.read_text(encoding="utf-8"))
    raise HTTPException(status_code=404, detail="Site not generated yet")


@app.get("/admin")
async def serve_admin_get(request: Request):
    """Serve admin login form or admin page"""
    # If no admin password is set, allow access without authentication
    if not config["admin_password"]:
        logging.getLogger(__name__).warning(
            "No ADMIN_PASSWORD set - allowing unrestricted admin access"
        )
        admin_file = config["templates_dir"] / "admin.html"
        return HTMLResponse(content=admin_file.read_text(encoding="utf-8"))

    # Check if admin is authenticated
    if is_admin_authenticated(request):
        admin_file = config["templates_dir"] / "admin.html"
        return HTMLResponse(content=admin_file.read_text(encoding="utf-8"))

    # Show login form
    return HTMLResponse(content=render_template("admin_login.html"))


@app.post("/admin")
async def serve_admin_post(request: Request, password: str = Form(...)):
    """Handle admin login"""
    logger = logging.getLogger(__name__)

    # If no admin password is set, redirect to admin page
    if not config["admin_password"]:
        return RedirectResponse(url="/admin", status_code=302)

    # Check password
    if password == config["admin_password"]:
        request.session["admin_authenticated"] = True
        logger.info("Admin authentication successful")
        return RedirectResponse(url="/admin", status_code=302)
    else:
        logger.warning("Admin authentication failed - incorrect password")
        return HTMLResponse(
            content=render_template("admin_login.html", {"error": True}),
            status_code=401,
        )


@app.post("/admin/logout")
async def admin_logout(request: Request):
    """Logout admin user"""
    request.session.pop("admin_authenticated", None)
    logging.getLogger(__name__).info("Admin logged out")
    return RedirectResponse(url="/", status_code=302)


# Sync API endpoints with simplified error handling
@app.post("/api/sync-to-volume")
async def sync_to_volume():
    """Sync content from /app/content/ to /data/content/"""
    logger = logging.getLogger(__name__)

    # Ensure data directory exists
    data_dir = Path("/data/content")
    data_dir.mkdir(parents=True, exist_ok=True)

    # Use rsync with checksum comparison
    result = subprocess.run(
        ["rsync", "-av", "--checksum", "/app/content/", "/data/content/"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        logger.error(f"Sync to volume failed: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result.stderr}")

    logger.info("Successfully synced content to volume")
    return JSONResponse(
        content={
            "status": "success",
            "message": "Content synced to volume successfully",
            "output": result.stdout,
        }
    )


@app.post("/api/sync-from-volume")
async def sync_from_volume():
    """Sync content from /data/content/ to /app/content/"""
    logger = logging.getLogger(__name__)

    # Ensure app content directory exists
    app_dir = Path("/app/content")
    app_dir.mkdir(parents=True, exist_ok=True)

    # Use rsync for bidirectional sync
    result = subprocess.run(
        ["rsync", "-av", "--update", "/data/content/", "/app/content/"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        logger.error(f"Sync from volume failed: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result.stderr}")

    logger.info("Successfully synced content from volume")
    return JSONResponse(
        content={
            "status": "success",
            "message": "Content synced from volume successfully",
            "output": result.stdout,
        }
    )


@app.post("/api/bidirectional-sync")
async def bidirectional_sync():
    """Perform bidirectional sync between /app/content/ and /data/content/"""
    logger = logging.getLogger(__name__)

    # Ensure both directories exist
    app_dir = Path("/app/content")
    data_dir = Path("/data/content")
    app_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    # First sync: app to data
    result1 = subprocess.run(
        ["rsync", "-av", "--update", "/app/content/", "/data/content/"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result1.returncode != 0:
        logger.error(f"Bidirectional sync (app->data) failed: {result1.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result1.stderr}")

    # Second sync: data to app
    result2 = subprocess.run(
        ["rsync", "-av", "--update", "/data/content/", "/app/content/"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result2.returncode != 0:
        logger.error(f"Bidirectional sync (data->app) failed: {result2.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result2.stderr}")

    logger.info("Successfully completed bidirectional sync")
    return JSONResponse(
        content={
            "status": "success",
            "message": "Bidirectional sync completed successfully",
            "app_to_data": result1.stdout,
            "data_to_app": result2.stdout,
        }
    )


# Scheduler API endpoints
@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get the current status of the scheduler"""
    scheduler = get_scheduler()
    status = scheduler.get_status()
    return JSONResponse(content=status)


@app.get("/api/process-activity")
async def get_process_activity():
    """Get process activity stats: uptime, generation counts, sync counts"""
    scheduler = get_scheduler()
    sched_status = scheduler.get_status()
    uptime_seconds = int((datetime.now() - _server_start_time).total_seconds())
    hours, remainder = divmod(uptime_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    uptime_str = f"{hours}h {minutes}m {seconds}s"
    return JSONResponse(
        content={
            "server_started": _server_start_time.isoformat(),
            "uptime": uptime_str,
            "generation_count": _generation_count,
            "last_generation": _last_generation_time.isoformat()
            if _last_generation_time
            else None,
            "git_sync_count": sched_status.get("git_sync_count", 0),
            "last_git_sync": sched_status.get("last_git_sync"),
            "raindrop_sync_count": sched_status.get("raindrop_sync_count", 0),
            "last_raindrop_sync": sched_status.get("last_raindrop_sync"),
            "scheduler_running": sched_status.get("running", False),
        }
    )


@app.post("/api/scheduler/sync-now")
async def trigger_git_sync(request: Request):
    """Manually trigger a Git sync to GitHub (admin only)"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    scheduler = get_scheduler()

    success = await scheduler.sync_to_github()
    if success:
        return JSONResponse(
            content={
                "status": "success",
                "message": "Content successfully synced to GitHub",
            }
        )
    else:
        raise HTTPException(
            status_code=500, detail="Git sync failed - check logs for details"
        )


@app.post("/api/scheduler/sync-raindrops-now")
async def trigger_raindrop_sync(request: Request):
    """Manually trigger a Raindrop sync (admin only)"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    logger = logging.getLogger(__name__)
    scheduler = get_scheduler()

    try:
        success = await scheduler.sync_raindrops()
        if success:
            return JSONResponse(
                content={
                    "status": "success",
                    "message": "Raindrops successfully synced and site regenerated",
                }
            )
        else:
            raise HTTPException(
                status_code=500, detail="Raindrop sync failed - check logs for details"
            )
    except Exception as e:
        logger.error(f"Manual Raindrop sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Raindrop sync error: {str(e)}")


@app.post("/api/scheduler/start")
async def start_scheduler(
    request: Request, git_hours: float = None, raindrop_hours: float = None
):
    """Start or restart the scheduler with specified intervals (admin only)"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    if git_hours is not None and (git_hours < 0.1 or git_hours > 24):
        raise HTTPException(
            status_code=400, detail="Git interval must be between 0.1 and 24 hours"
        )
    if raindrop_hours is not None and (raindrop_hours < 0.1 or raindrop_hours > 24):
        raise HTTPException(
            status_code=400, detail="Raindrop interval must be between 0.1 and 24 hours"
        )

    scheduler = get_scheduler()
    scheduler.stop_scheduler()
    scheduler.start_scheduler(
        git_interval_hours=git_hours, raindrop_interval_hours=raindrop_hours
    )

    # Get actual intervals used
    actual_git_hours = (
        git_hours
        if git_hours is not None
        else float(
            os.environ.get(
                "SCHED_GITSYNC_HRS", _cfg("scheduler", "git_sync_hours", default=6.0)
            )
        )
    )
    actual_raindrop_hours = (
        raindrop_hours
        if raindrop_hours is not None
        else float(
            os.environ.get(
                "SCHED_RAINSYNC_HRS",
                _cfg("scheduler", "raindrop_sync_hours", default=2.0),
            )
        )
    )

    return JSONResponse(
        content={
            "status": "success",
            "message": f"Scheduler started - Git sync every {actual_git_hours} hours, Raindrop sync every {actual_raindrop_hours} hours",
        }
    )


@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    scheduler = get_scheduler()
    scheduler.stop_scheduler()

    return JSONResponse(content={"status": "success", "message": "Scheduler stopped"})


@app.post("/api/emergency-restore")
async def emergency_restore_from_github():
    """
    EMERGENCY: Restore /data/content from GitHub repository
    WARNING: This overwrites the persistent volume with repository content!
    """
    logger = logging.getLogger(__name__)
    logger.warning(
        "EMERGENCY RESTORE: Starting restoration from GitHub to /data/content"
    )

    # Ensure we're in the git directory
    git_dir = Path("/app")
    if not (git_dir / ".git").exists():
        raise HTTPException(status_code=500, detail="Git repository not found in /app")

    # Pull latest from GitHub
    logger.info("Pulling latest content from GitHub...")
    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd=git_dir,
        capture_output=True,
        text=True,
        timeout=60,
    )

    if result.returncode != 0:
        logger.error(f"Git pull failed: {result.stderr}")
        raise HTTPException(
            status_code=500, detail=f"Failed to pull from GitHub: {result.stderr}"
        )

    # Check if /app/content exists
    app_content = git_dir / "content"
    if not app_content.exists():
        raise HTTPException(
            status_code=500, detail="/app/content does not exist after git pull"
        )

    # Backup and restore
    data_content = Path("/data/content")
    backup_path = Path("/data/content_backup_" + str(int(time.time())))

    if data_content.exists():
        logger.info(f"Backing up current /data/content to {backup_path}")
        shutil.move(str(data_content), str(backup_path))

    # Create and copy
    data_content.mkdir(parents=True, exist_ok=True)

    logger.info("Copying /app/content to /data/content...")
    result = subprocess.run(
        ["rsync", "-av", str(app_content) + "/", str(data_content) + "/"],
        capture_output=True,
        text=True,
        timeout=120,
    )

    if result.returncode != 0:
        # Restore backup if copy failed
        if backup_path.exists():
            logger.error("Restore failed, restoring backup...")
            shutil.move(str(backup_path), str(data_content))
        raise HTTPException(
            status_code=500, detail=f"Failed to copy content: {result.stderr}"
        )

    # Clean up backup
    if backup_path.exists():
        logger.info(f"Removing backup {backup_path}")
        shutil.rmtree(backup_path)

    logger.warning("EMERGENCY RESTORE: Successfully restored /data/content from GitHub")

    return JSONResponse(
        content={
            "status": "success",
            "message": "Emergency restore completed - /data/content restored from GitHub",
            "warning": "Volume content was overwritten with repository content",
        }
    )


@app.post("/api/sync-pages-from-repo")
async def sync_pages_from_repo():
    """
    Safely sync just the pages directory from GitHub repository to volume
    Only updates /data/content/pages/ with repository content
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting safe pages sync from GitHub repository...")

    # Pages are already in /app/content/pages from the Docker build — no git pull needed
    app_pages = Path("/app/content/pages")
    if not app_pages.exists():
        raise HTTPException(status_code=500, detail="/app/content/pages does not exist")

    # Ensure /data/content/pages directory exists
    data_pages = Path("/data/content/pages")
    data_pages.mkdir(parents=True, exist_ok=True)

    # Backup current pages as .md-old files (including subdirectories)
    if data_pages.exists() and any(data_pages.iterdir()):
        logger.info("Backing up current pages as .md-old files")
        for md_file in data_pages.rglob("*.md"):
            backup_file = md_file.with_suffix(".md-old")
            logger.info(
                f"Backing up {md_file.relative_to(data_pages)} to {backup_file.relative_to(data_pages)}"
            )
            shutil.copy2(str(md_file), str(backup_file))

    # Copy pages from repository to volume
    logger.info("Copying pages from /app/content/pages to /data/content/pages...")
    result = subprocess.run(
        ["rsync", "-av", "--delete", str(app_pages) + "/", str(data_pages) + "/"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        # Restore from .md-old files if copy failed (including subdirectories)
        logger.error("Pages sync failed, restoring from .md-old files...")
        for backup_file in data_pages.rglob("*.md-old"):
            original_file = backup_file.with_suffix(".md")
            logger.info(
                f"Restoring {original_file.relative_to(data_pages)} from {backup_file.relative_to(data_pages)}"
            )
            shutil.copy2(str(backup_file), str(original_file))
        raise HTTPException(
            status_code=500, detail=f"Failed to sync pages: {result.stderr}"
        )

    # Count synced files (including subdirectories)
    synced_files = list(data_pages.rglob("*.md"))

    logger.info(f"Successfully synced {len(synced_files)} page files from repository")

    return JSONResponse(
        content={
            "status": "success",
            "message": f"Pages synced successfully - {len(synced_files)} files updated",
            "files_synced": [f.name for f in synced_files],
            "sync_details": "Synced from /app/content/pages to /data/content/pages",
        }
    )


@app.post("/api/upload-image")
async def upload_image(
    request: Request, image: UploadFile = File(None), file: UploadFile = File(None)
):
    """Upload an image from the admin editor. Saves to static/images/uploads/ and returns a URL."""
    logger = logging.getLogger(__name__)

    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    # Accept field name 'image' (EasyMDE imageUploadEndpoint) or 'file' (custom)
    upload = image or file
    if not upload:
        raise HTTPException(status_code=400, detail="No file provided")

    date_prefix = datetime.now().strftime("%Y-%m-%d")
    original = Path(upload.filename or "upload")
    stem = original.stem or "upload"
    ext = original.suffix or ".bin"
    data = await upload.read()

    root_dir = config["root_dir"]

    # 1. Source — included in git sync
    source_dir = root_dir / "static" / "images" / "uploads"
    source_dir.mkdir(parents=True, exist_ok=True)

    # Generate yyyy-mm-dd-originalname.ext filename using exclusive create to avoid
    # races. If a file with that name already exists, append -N before the extension.
    # open(..., 'xb') is atomic: raises FileExistsError if the file already exists.
    filename = f"{date_prefix}-{stem}{ext}"
    try:
        with open(source_dir / filename, "xb") as f:
            f.write(data)
    except FileExistsError:
        n = 2
        while True:
            filename = f"{date_prefix}-{stem}-{n}{ext}"
            try:
                with open(source_dir / filename, "xb") as f:
                    f.write(data)
                break
            except FileExistsError:
                n += 1

    # 2. Output — served immediately (use configured output_dir, not Path.cwd())
    output_dir = config["output_dir"] / "static" / "images" / "uploads"
    output_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_dir / filename, output_dir / filename)

    # 3. Volume backup
    try:
        volume_dir = Path("/data") / "static" / "images" / "uploads"
        volume_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_dir / filename, volume_dir / filename)
    except Exception as e:
        logger.warning(f"Volume backup failed for uploaded image {filename}: {e}")

    url = f"/static/images/uploads/{filename}"
    logger.info(f"Image uploaded: {url}")
    # Return both formats: EasyMDE imageUploadEndpoint expects data.filePath,
    # custom imageUploadFunction uses url
    return JSONResponse(content={"data": {"filePath": url}, "url": url})


@app.get("/api/admin-status")
async def get_admin_status(request: Request):
    """Check if current user is authenticated as admin"""
    # If no admin password is set, allow access without authentication
    if not config["admin_password"]:
        return JSONResponse(content={"authenticated": True})

    # Check if admin is authenticated via session
    return JSONResponse(content={"authenticated": is_admin_authenticated(request)})


@app.get("/admin-stats.html")
async def serve_admin_stats(request: Request):
    """Serve the pre-generated static stats page."""
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    stats_file = config["output_dir"] / "admin-stats.html"
    if stats_file.exists():
        return HTMLResponse(content=stats_file.read_text(encoding="utf-8"))
    return HTMLResponse(content="<p>Stats not yet generated.</p>")


def _build_stats_for_period(counter, period):
    counts = counter.get_all(period=period)
    total = sum(sum(types.values()) for _, types in counts)
    return {
        "counts": [
            {"path": p, "total": sum(t.values()), "by_type": t} for p, t in counts
        ],
        "total": total,
        "period": period,
    }


_STATS_PLACEHOLDER = (
    "<html><body><p class='p-3 text-muted'>Stats loading...</p></body></html>"
)

STATS_PERIODS = [
    ("today", "Today"),
    ("this_week", "This Week"),
    ("this_month", "This Month"),
    ("this_year", "This Year"),
    ("all", "All Time"),
]


def generate_stats_cache():
    """Render stats for all periods into a static admin-stats.html file."""
    output_dir = config.get("output_dir")
    if not output_dir:
        return
    counter = get_counter()
    stats = {}
    for key, _ in STATS_PERIODS:
        period = None if key == "all" else key
        stats[key] = _build_stats_for_period(counter, period)
    jinja_env = config.get("jinja_env")
    if not jinja_env:
        return
    tmpl = jinja_env.get_template("stats_page.html")
    html = tmpl.render(
        stats=stats,
        periods=STATS_PERIODS,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )
    (output_dir / "admin-stats.html").write_text(html, encoding="utf-8")


def generate_posts_index_cache():
    """Write a lightweight index of all blog posts and pages (filename, title,
    date, type) to output/admin-posts-index.json, so the admin "All Posts"
    list (TF42.2) loads instantly instead of scanning thousands of files per
    request — same pre-generated-static-file pattern as generate_stats_cache().

    Also writes output/top-tags.json (TF45.0): the 100 most-used tags across
    blog posts, for the post editor's tag picklist (F45). Computed here rather
    than in a separate pass since every post's frontmatter is already being
    read for the posts index — no extra file I/O to tally tags alongside it.
    """
    output_dir = config.get("output_dir")
    if not output_dir:
        return

    entries = []
    blog_tag_lists = []
    for content_type in ("blog", "pages"):
        content_dir = get_content_directory(content_type)
        if not content_dir.exists():
            continue
        for md_file in sorted(content_dir.glob("*.md")):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)
            except Exception as e:
                logging.getLogger(__name__).warning(
                    f"Skipping {md_file} while building posts index: {e}"
                )
                continue
            if post.metadata.get("draft"):
                continue
            entries.append(
                {
                    "filename": md_file.name,
                    "title": post.metadata.get("title", md_file.stem),
                    "date": str(post.metadata.get("date", "")),
                    "content_type": content_type,
                }
            )
            if content_type == "blog":
                blog_tag_lists.append(post.metadata.get("tags", []))

    entries.sort(key=lambda e: e["date"], reverse=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "admin-posts-index.json").write_text(
        json.dumps(entries), encoding="utf-8"
    )
    (output_dir / "top-tags.json").write_text(
        json.dumps(top_tags_by_frequency(blog_tag_lists, always_include=BLOG_TAGS)),
        encoding="utf-8",
    )


def load_top_tags() -> list:
    """Read the cached top-100-tags list (TF45.0) for the post editor's tag
    picklist. Falls back to an empty list before the cache is first
    generated (fresh install) — tag suggestions are a convenience, not
    critical data, so there's nothing to error on here.
    """
    output_dir = config.get("output_dir")
    tags_file = output_dir / "top-tags.json" if output_dir else None
    if not tags_file or not tags_file.exists():
        return []
    try:
        return json.loads(tags_file.read_text(encoding="utf-8"))
    except Exception as e:
        logging.getLogger(__name__).warning(f"Could not read top-tags.json: {e}")
        return []


@app.get("/admin/edit-post/{filename}")
async def edit_post_page(filename: str, request: Request):
    """Serve edit post page with actual post content"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    # Load the post using shared function
    post_data = load_content_item(filename, "blog")

    # Render edit form using template with post context
    context = {
        "filename": filename,
        "content_type": "blog",
        "content_type_title": "Post",
        "action_url": f"/admin/edit-post/{filename}",
        "cancel_url": "/blog/",
        "blog_tags": load_top_tags(),
        "is_edit": True,
        **post_data,
    }
    return HTMLResponse(content=render_template("post_editor.html", context))


@app.post("/admin/edit-post/{filename}")
async def save_edited_post(
    filename: str,
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    date: str = Form(...),
    type: str = Form(...),
    content: str = Form(...),
    tags: List[str] = Form(default=[]),
    image_size: str = Form(default=""),
    category: str = Form(default=""),
    loaded_mtime: str = Form(default=""),
):
    """Save edited post to file and regenerate site"""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    content_dir = get_content_directory("blog")
    content_file = content_dir / filename
    if not content_file.exists():
        raise HTTPException(status_code=404, detail=f"Post not found: {filename}")

    check_no_concurrent_edit(content_file, loaded_mtime)

    new_mtime = save_content_item(
        filename,
        "blog",
        ContentFields(title, date, type, content, tags, image_size, category),
    )
    background_tasks.add_task(_regenerate_in_background, filename, "blog")
    background_tasks.add_task(generate_posts_index_cache)
    return JSONResponse(
        content={
            "status": "success",
            "message": "Post updated successfully",
            "filename": filename,
            "loaded_mtime": new_mtime,
        }
    )


@app.get("/admin/new-post")
async def new_post_page(request: Request):
    """Serve new post creation page with form"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    context = {
        "content_type": "blog",
        "content_type_title": "Post",
        "action_url": "/admin/new-post",
        "cancel_url": "/blog/",
        "blog_tags": load_top_tags(),
        "is_edit": False,
    }
    return HTMLResponse(content=render_template("post_editor.html", context))


@app.post("/admin/new-post")
async def create_new_post(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    date: str = Form(...),
    type: str = Form(...),
    content: str = Form(...),
    tags: List[str] = Form(default=[]),
    image_size: str = Form(default=""),
    category: str = Form(default=""),
):
    """Create a new blog post with generated filename"""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        filename = create_filename_for_content(title.strip(), date, "blog")
        content_dir = get_content_directory("blog")
        if (content_dir / filename).exists():
            raise HTTPException(
                status_code=400,
                detail=f"A post with filename '{filename}' already exists",
            )

        save_content_item(
            filename,
            "blog",
            ContentFields(title, date, type, content, tags, image_size, category),
        )
        background_tasks.add_task(_regenerate_in_background, filename, "blog")
        background_tasks.add_task(generate_posts_index_cache)
        return JSONResponse(
            content={
                "status": "success",
                "message": "Post created successfully",
                "filename": filename,
                "url": f"/blog/{filename.replace('.md', '.html')}",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating new post: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")


# Page editing endpoints (reusing shared code)
@app.get("/admin/edit-page/{filename}")
async def edit_page_page(filename: str, request: Request):
    """Serve edit page form with actual page content"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    # Ensure filename has .md extension if not present
    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    # Load the page using shared function
    page_data = load_content_item(filename, "pages")

    # Render edit form using template with page context
    context = {
        "filename": filename,
        "content_type": "page",
        "content_type_title": "Page",
        "action_url": f"/admin/edit-page/{filename}",
        "cancel_url": "/pages/",
        "is_edit": True,
        **page_data,
    }
    return HTMLResponse(content=render_template("post_editor.html", context))


@app.post("/admin/edit-page/{filename}")
async def save_edited_page(
    filename: str,
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    date: str = Form(...),
    type: str = Form(...),
    content: str = Form(...),
    loaded_mtime: str = Form(default=""),
):
    """Save edited page to file and regenerate site"""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    content_dir = get_content_directory("pages")
    content_file = content_dir / filename
    if not content_file.exists():
        raise HTTPException(status_code=404, detail=f"Page not found: {filename}")

    check_no_concurrent_edit(content_file, loaded_mtime)

    new_mtime = save_content_item(
        filename, "pages", ContentFields(title, date, type, content, [])
    )
    background_tasks.add_task(_regenerate_in_background, filename, "pages")
    background_tasks.add_task(generate_posts_index_cache)
    return JSONResponse(
        content={
            "status": "success",
            "message": "Page updated successfully",
            "filename": filename,
            "loaded_mtime": new_mtime,
        }
    )


@app.get("/admin/new-page")
async def new_page_page(request: Request):
    """Serve new page creation form"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    context = {
        "content_type": "page",
        "content_type_title": "Page",
        "action_url": "/admin/new-page",
        "cancel_url": "/pages/",
        "is_edit": False,
    }
    return HTMLResponse(content=render_template("post_editor.html", context))


@app.post("/admin/new-page")
async def create_new_page(
    request: Request,
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    date: str = Form(...),
    type: str = Form(...),
    content: str = Form(...),
):
    """Create a new page"""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        filename = create_filename_for_content(title.strip(), date, "pages")
        content_dir = get_content_directory("pages")
        if (content_dir / filename).exists():
            raise HTTPException(
                status_code=400,
                detail=f"A page with filename '{filename}' already exists",
            )

        save_content_item(
            filename, "pages", ContentFields(title, date, type, content, [])
        )
        background_tasks.add_task(_regenerate_in_background, filename, "pages")
        background_tasks.add_task(generate_posts_index_cache)
        return JSONResponse(
            content={
                "status": "success",
                "message": "Page created successfully",
                "filename": filename,
                "url": f"/pages/{filename.replace('.md', '.html')}",
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating new page: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating page: {str(e)}")


@app.post("/admin/delete-post/{filename}")
async def delete_post_endpoint(
    filename: str, request: Request, background_tasks: BackgroundTasks
):
    """Delete a blog post from disk and regenerate the site."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    content_dir = get_content_directory("blog")
    delete_content_item(content_dir, filename)
    background_tasks.add_task(regenerate_after_deletion_in_background, filename, "blog")
    background_tasks.add_task(generate_posts_index_cache)
    return JSONResponse(
        content={
            "status": "success",
            "message": "Post deleted successfully",
            "filename": filename,
        }
    )


@app.post("/admin/delete-page/{filename}")
async def delete_page_endpoint(
    filename: str, request: Request, background_tasks: BackgroundTasks
):
    """Delete a page from disk and regenerate the site."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    content_dir = get_content_directory("pages")
    delete_content_item(content_dir, filename)
    background_tasks.add_task(
        regenerate_after_deletion_in_background, filename, "pages"
    )
    background_tasks.add_task(generate_posts_index_cache)
    return JSONResponse(
        content={
            "status": "success",
            "message": "Page deleted successfully",
            "filename": filename,
        }
    )


@app.post("/admin/delete-raindrop/{filename}")
async def delete_raindrop_endpoint(
    filename: str, request: Request, background_tasks: BackgroundTasks
):
    """Delete a raindrop (link blog entry) from disk and regenerate the site.

    Found while wiring up post/page delete (F42): raindrop_post.html's delete
    button was calling the blog delete endpoint, which 404s since raindrops
    live in a different content directory — a separate bug from the same
    "dead delete button" family.
    """
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    content_dir = get_content_directory("raindrops")
    delete_content_item(content_dir, filename)
    background_tasks.add_task(
        regenerate_after_deletion_in_background, filename, "raindrops"
    )
    return JSONResponse(
        content={
            "status": "success",
            "message": "Raindrop deleted successfully",
            "filename": filename,
        }
    )


@app.post("/admin/preview-markdown")
async def preview_markdown(request: Request, content: str = Form(...)):
    """Convert markdown content to HTML for preview"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        # Use standardized markdown processing
        html = process_markdown_to_html(content)

        return JSONResponse(content={"status": "success", "html": html})

    except Exception as e:
        logging.getLogger(__name__).error(f"Error rendering markdown preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")


# Raindrop sync and site generation endpoints with simplified logic
@app.get("/api/sync-raindrops")
async def sync_raindrops(request: Request):
    """Trigger raindrop sync and regenerate site (admin only)"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    def do_sync():
        sync_status["running"] = True
        sync_status["message"] = "Downloading raindrops..."

        # Download new raindrops
        downloader = RaindropDownloader()
        new_filenames = downloader.download_raindrops()

        logging.getLogger(__name__).info(
            f"Sync result: new_filenames = {new_filenames}"
        )

        # Only regenerate if there are new raindrops
        if new_filenames:
            logging.getLogger(__name__).info(
                f"Processing {len(new_filenames)} new raindrops"
            )

            # Check if this is a first sync
            env_timestamp = os.getenv("RAINDROP_LAST_SYNC")
            cache_file = Path("/data/content/.rd_cache.json")
            is_first_sync = not env_timestamp and not cache_file.exists()

            if is_first_sync and len(new_filenames) > 10:
                # Full regeneration for first sync
                sync_status["message"] = (
                    f"First sync: doing full site regeneration for {len(new_filenames)} raindrops..."
                )
                generator = SiteGenerator()
                generator.generate_site()
                result = {
                    "status": "success",
                    "message": f"First sync: regenerated entire site with {len(new_filenames)} new raindrops",
                }
            else:
                # Incremental regeneration
                sync_status["message"] = (
                    f"Regenerating {len(new_filenames)} raindrop pages..."
                )
                generator = SiteGenerator()

                for i, filename in enumerate(new_filenames, 1):
                    sync_status["message"] = (
                        f"Regenerating {i}/{len(new_filenames)}: {filename[:30]}..."
                    )
                    generator.incremental_regenerate_post(filename, "raindrops")

                result = {
                    "status": "success",
                    "message": f"Synced {len(new_filenames)} new raindrops and regenerated pages",
                }
        else:
            result = {"status": "success", "message": "No new raindrops to sync"}

        sync_status["running"] = False
        sync_status["message"] = result["message"]
        return result

    # Check if already running
    if sync_status["running"]:
        return JSONResponse(
            content={"status": "running", "message": sync_status["message"]}
        )

    # Start async execution
    async def run_sync():
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, do_sync)

    asyncio.create_task(run_sync())

    return JSONResponse(
        content={
            "status": "started",
            "message": "Raindrop sync started. Check /api/sync-status for progress.",
        }
    )


@app.get("/api/sync-status")
async def get_sync_status():
    """Get current raindrop sync status"""
    return JSONResponse(content=sync_status)


@app.get("/api/regenerate")
async def regenerate_site(request: Request):
    """Regenerate the static site (admin only)"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    def do_regenerate():
        global _generation_count, _last_generation_time
        generator = SiteGenerator()
        generator.generate_site()
        _generation_count += 1
        _last_generation_time = datetime.now()
        return {"status": "success", "message": "Site regenerated successfully"}

    # Run regeneration in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, do_regenerate)
    return JSONResponse(content=result)


@app.get("/api/propose")
async def propose_posts(request: Request):
    """Return 5 random high-scoring old blog posts for reposting."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    blog_dir = get_content_directory("blog")
    loop = asyncio.get_event_loop()
    pool = _cfg("propose", "pool_size", default=50)
    count = _cfg("propose", "count", default=5)
    posts = await loop.run_in_executor(None, lambda: get_proposed_posts(blog_dir, pool))
    sample = random.sample(posts, min(count, len(posts)))
    return JSONResponse(
        content=[
            {
                "filename": p.filename,
                "title": p.title,
                "date": p.date,
                "url": p.url,
                "score": round(p.score, 1),
            }
            for p in sample
        ]
    )


@app.get("/api/propose-drops")
async def propose_drops(request: Request):
    """Return popular raindrop link posts suitable for draft generation."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    drops_dir = get_content_directory("raindrops")
    loop = asyncio.get_event_loop()
    filt = DropFilter(
        min_age_months=_cfg("propose", "drops_min_age_months", default=3),
        min_visits=_cfg("propose", "drops_min_visits", default=5),
        top_n=_cfg("propose", "pool_size", default=50),
    )
    count = _cfg("propose", "count", default=5)
    drops = await loop.run_in_executor(
        None, lambda: get_proposed_drops(drops_dir, get_counter(), filt)
    )
    sample = random.sample(drops, min(count, len(drops)))
    return JSONResponse(content=sample)


@app.post("/api/generate-draft")
async def generate_draft(request: Request):
    """Generate a draft blog post from a raindrop file."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    body = await request.json()
    filename = body.get("filename", "")
    if not filename:
        raise HTTPException(status_code=400, detail="filename required")

    drops_dir = get_content_directory("raindrops")
    drop_file = drops_dir / filename
    if not drop_file.exists():
        raise HTTPException(status_code=404, detail=f"Raindrop not found: {filename}")

    with open(drop_file, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)

    drop = {
        "filename": filename,
        "title": post.metadata.get("title", ""),
        "url": post.metadata.get("url", ""),
        "note": post.metadata.get("note", ""),
        "domain": post.metadata.get("domain", ""),
        "excerpt": post.metadata.get("excerpt", ""),
        "tags": post.metadata.get("tags", []),
    }

    stem = filename.replace(".md", "")
    draft_filename = f"draft-{stem}.md"
    blog_dirs = [get_content_directory("blog"), Path("/app/content/blog")]

    def _generate_and_save():
        content = generate_draft_from_drop(drop)
        save_draft(content, draft_filename, blog_dirs)

    try:
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _generate_and_save)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Claude API error: {e}")

    return JSONResponse(content={"filename": draft_filename})


@app.get("/api/admin-posts")
async def list_admin_posts(request: Request):
    """List all blog posts and pages for the admin 'All Posts' view (TF42.2).

    Serves the pre-generated output/admin-posts-index.json when present
    (refreshed after every create/edit/delete and periodically) rather than
    scanning content directories on every request. Falls back to a live scan
    only if the cache hasn't been generated yet.
    """
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    output_dir = config.get("output_dir")
    index_file = output_dir / "admin-posts-index.json" if output_dir else None
    if index_file and index_file.exists():
        return JSONResponse(content=json.loads(index_file.read_text(encoding="utf-8")))

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, generate_posts_index_cache)
    if index_file and index_file.exists():
        return JSONResponse(content=json.loads(index_file.read_text(encoding="utf-8")))
    return JSONResponse(content=[])


@app.get("/api/drafts")
async def list_drafts(request: Request):
    """List all draft blog posts."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    blog_dir = get_content_directory("blog")

    def _load():
        drafts = []
        for md_file in sorted(blog_dir.glob("draft-*.md")):
            try:
                with open(md_file, "r", encoding="utf-8") as f:
                    post = frontmatter.load(f)
                if not post.metadata.get("draft"):
                    continue
                drafts.append(
                    {
                        "filename": md_file.name,
                        "title": post.metadata.get("title", md_file.stem),
                        "date": str(post.metadata.get("date", "")),
                        "source_raindrop": post.metadata.get("source_raindrop", ""),
                        "source_url": post.metadata.get("source_url", ""),
                        "body": post.content or "",
                    }
                )
            except OSError:
                continue
        return drafts

    loop = asyncio.get_event_loop()
    drafts = await loop.run_in_executor(None, _load)
    return JSONResponse(content=drafts)


@app.post("/api/publish-draft")
async def publish_draft(request: Request):
    """Publish a draft by removing the draft flag and regenerating."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    body = await request.json()
    filename = body.get("filename", "")
    if not filename:
        raise HTTPException(status_code=400, detail="filename required")

    blog_dir = get_content_directory("blog")
    draft_file = blog_dir / filename
    if not draft_file.exists():
        raise HTTPException(status_code=404, detail=f"Draft not found: {filename}")

    with open(draft_file, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)

    del post.metadata["draft"]
    post.metadata["date"] = date.today().isoformat()
    draft_file.write_text(frontmatter.dumps(post), encoding="utf-8")

    app_blog = Path("/app/content/blog") / filename
    if app_blog.exists():
        with open(app_blog, "r", encoding="utf-8") as f:
            app_post = frontmatter.load(f)
        del app_post.metadata["draft"]
        app_post.metadata["date"] = date.today().isoformat()
        app_blog.write_text(frontmatter.dumps(app_post), encoding="utf-8")

    generator = SiteGenerator()
    generator.incremental_regenerate_post(filename, "blog")

    return JSONResponse(content={"status": "published", "filename": filename})


@app.post("/api/delete-draft")
async def delete_draft(request: Request):
    """Delete a draft blog post."""
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")

    body = await request.json()
    filename = body.get("filename", "")
    if not filename:
        raise HTTPException(status_code=400, detail="filename required")

    blog_dir = get_content_directory("blog")
    draft_file = blog_dir / filename
    if not draft_file.exists():
        raise HTTPException(status_code=404, detail=f"Draft not found: {filename}")

    draft_file.unlink()
    app_blog = Path("/app/content/blog") / filename
    if app_blog.exists():
        app_blog.unlink()

    return JSONResponse(content={"status": "deleted", "filename": filename})


@app.get("/admin/repost/{filename}")
async def repost_page(filename: str, request: Request):
    """Open the new-post UI pre-filled with an existing post's content"""
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)

    if not filename.endswith(".md"):
        filename = f"{filename}.md"

    post_data = load_content_item(filename, "blog")
    context = {
        "content_type": "blog",
        "content_type_title": "Post",
        "action_url": "/admin/new-post",
        "cancel_url": "/blog/",
        "blog_tags": load_top_tags(),
        "is_edit": False,
        "prefill_title": post_data["title"],
        "prefill_content": post_data["content"],
        "prefill_tags": post_data.get("tags", []),
    }
    return HTMLResponse(content=render_template("post_editor.html", context))


# RSD and XML-RPC endpoints
@app.get("/rsd.xml")
async def serve_rsd(request: Request):
    """Serve RSD (Really Simple Discovery) XML for blog API autodiscovery"""
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    api_type = os.getenv("RSD_API_TYPE", "metaweblog").lower()

    if api_type == "blogger":
        api_name = "Blogger"
        docs_url = "http://plant.blogger.com/api/index.html"
    else:
        api_name = "MetaWeblog"
        docs_url = "http://www.xmlrpc.com/metaWeblogApi"

    rsd_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rsd version="1.0" xmlns="http://archipelago.phrasewise.com/rsd">
  <service>
    <engineName>Salasblog2</engineName>
    <engineLink>https://github.com/pitosalas/salasblog2</engineLink>
    <homePageLink>{base_url}/</homePageLink>
    <apis>
      <api name="{api_name}" apiLink="{base_url}/xmlrpc" preferred="true" blogID="salasblog2">
        <settings>
          <docs>{docs_url}</docs>
        </settings>
      </api>
    </apis>
  </service>
</rsd>"""

    return Response(
        content=rsd_content,
        media_type="application/rsd+xml",
        headers={"Content-Type": "application/rsd+xml; charset=utf-8"},
    )


@app.get("/xmlrpc")
async def xmlrpc_get_endpoint(request: Request):
    """Handle GET requests to XML-RPC endpoint for debugging"""
    logging.getLogger(__name__).info("GET request received at /xmlrpc endpoint")
    return Response(
        content="XML-RPC endpoint ready. Use POST with XML-RPC payload.",
        media_type="text/plain",
    )


def call_xmlrpc_method(api, method_name, method_args, background_tasks):
    """Look up and invoke the right BloggerAPI method for an XML-RPC call.

    Methods that create/edit/delete a post trigger site regeneration, so they
    get background_tasks threaded through — this is what lets MarsEdit's
    Post/Save return promptly instead of blocking on regeneration (same
    pattern as the web admin form's saves). Read-only methods don't need it.
    Raises HTTPException(400) for an unrecognized method name; whatever the
    called method itself raises (Fault, etc.) propagates to the caller.
    """
    regenerating_methods = {
        "blogger.newPost": api.blogger_newPost,
        "blogger.editPost": api.blogger_editPost,
        "blogger.deletePost": api.blogger_deletePost,
        "metaWeblog.newPost": api.metaweblog_newPost,
        "metaWeblog.editPost": api.metaweblog_editPost,
    }
    other_methods = {
        "blogger.getRecentPosts": api.blogger_getRecentPosts,
        "blogger.getUsersBlogs": api.blogger_getUsersBlogs,
        "blogger.getPost": api.blogger_getPost,
        "metaWeblog.getPost": api.metaweblog_getPost,
        "metaWeblog.getRecentPosts": api.metaweblog_getRecentPosts,
        "metaWeblog.getCategories": api.metaweblog_getCategories,
        "metaWeblog.newMediaObject": api.metaweblog_newMediaObject,
    }
    if method_name in regenerating_methods:
        return regenerating_methods[method_name](
            *method_args, background_tasks=background_tasks
        )
    if method_name in other_methods:
        return other_methods[method_name](*method_args)
    logging.getLogger(__name__).error(f"Unknown XML-RPC method: {method_name}")
    raise HTTPException(status_code=400, detail=f"Unknown method: {method_name}")


@app.post("/xmlrpc")
async def xmlrpc_endpoint(request: Request, background_tasks: BackgroundTasks):
    """XML-RPC endpoint for Blogger API"""
    logger = logging.getLogger(__name__)

    body = await request.body()
    user_agent = request.headers.get("user-agent", "unknown")
    logger.info(
        f"Received XML-RPC request, body length: {len(body)}, user-agent: {user_agent}"
    )

    # Parse XML-RPC request using the standard library's own marshalling, which
    # correctly handles every XML-RPC type (dateTime.iso8601, array, nested struct,
    # base64, nil) — the hand-rolled ElementTree parser this replaced only understood
    # string/boolean/int/base64/one-level struct and silently dropped everything else.
    try:
        raw_params, method_name = xmlrpc_client.loads(body)
    except Exception as e:
        logger.exception(f"Malformed XML-RPC request: {e}")
        fault_xml = create_xmlrpc_fault_with_code(
            400, f"Malformed XML-RPC request: {e}"
        )
        return Response(content=fault_xml, media_type="text/xml", status_code=200)

    # xmlrpc.client.loads() decodes <base64> values as xmlrpc.client.Binary wrappers,
    # not plain bytes. Unwrap them here so blogger_api.py's methods keep receiving
    # plain bytes as they already expect, rather than leaking an XML-RPC library type
    # into the business-logic layer.
    method_args = [unwrap_xmlrpc_binary(p) for p in raw_params]
    logger.info(f"XML-RPC method: {method_name}, {len(method_args)} parameters")

    try:
        api = BloggerAPI()
    except Exception:
        logger.exception(f"BloggerAPI() construction failed for method {method_name}")
        response_xml = xmlrpc_client.dumps(
            xmlrpc_client.Fault(500, "Server failed to initialize BloggerAPI")
        )
        return Response(content=response_xml, media_type="text/xml", status_code=200)

    try:
        result = call_xmlrpc_method(api, method_name, method_args, background_tasks)
    except xmlrpc_client.Fault as fault:
        logger.info(f"XML-RPC Fault {fault.faultCode}: {fault.faultString}")
        response_xml = xmlrpc_client.dumps(fault)
        return Response(content=response_xml, media_type="text/xml", status_code=200)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"XML-RPC method {method_name} failed")
        response_xml = xmlrpc_client.dumps(xmlrpc_client.Fault(500, str(e)))
        return Response(content=response_xml, media_type="text/xml", status_code=200)

    logger.info(
        f"Method {method_name} completed successfully, "
        f"result type={type(result).__name__}, result repr={repr(result)[:1000]}"
    )

    # Marshalling happens here, after the method has already succeeded — if xmlrpc_client
    # can't serialize whatever the method returned, this must not crash uncaught, since an
    # unhandled exception here makes FastAPI return a plain HTML 500 page instead of XML,
    # which is exactly what produces MarsEdit's "XMLRPC Response Parsing Failed: (null)".
    try:
        response_xml = create_xmlrpc_response(result)
    except Exception:
        logger.exception(
            f"Failed to marshal XML-RPC response for method {method_name}, "
            f"result type={type(result).__name__}, result repr={repr(result)[:1000]}"
        )
        response_xml = xmlrpc_client.dumps(
            xmlrpc_client.Fault(
                500, f"Server failed to marshal response for {method_name}"
            )
        )
        return Response(content=response_xml, media_type="text/xml", status_code=200)

    logger.info(f"XML-RPC response length: {len(response_xml)}")
    return Response(content=response_xml, media_type="text/xml")


def unwrap_xmlrpc_binary(value):
    """Recursively replace xmlrpc.client.Binary wrappers with plain bytes."""
    if isinstance(value, xmlrpc_client.Binary):
        return value.data
    if isinstance(value, dict):
        return {k: unwrap_xmlrpc_binary(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [unwrap_xmlrpc_binary(v) for v in value]
    return value


def create_xmlrpc_response(result):
    """Create an XML-RPC methodResponse using the standard library's marshaller.

    This correctly escapes string content (the old hand-built f-string version did
    not, so a title/content containing `&`, `<`, or `>` produced invalid XML) and
    correctly encodes datetime values as dateTime.iso8601 instead of a plain string.
    """
    return xmlrpc_client.dumps((result,), methodresponse=True)


def create_xmlrpc_fault_with_code(fault_code, message):
    """Create an XML-RPC fault response using the standard library's marshaller."""
    return xmlrpc_client.dumps(xmlrpc_client.Fault(fault_code, message))


# Catch-all route moved to end of file to ensure proper precedence


# Root level files served by catch-all route (index.html, etc.)
# This MUST be the last route defined to ensure proper precedence
@app.api_route("/{path:path}", methods=["GET", "HEAD"])
async def serve_root_files(path: str, request: Request):
    """Serve root-level files like index.html, robots.txt, etc."""
    # Only handle root-level files, not paths that start with mounted directories
    if "/" in path or path.startswith(("blog", "pages", "static")):
        raise HTTPException(status_code=404, detail="Not found")

    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="Not found")

    file_path = _safe_resolve(config["output_dir"], path)
    if file_path is None:
        raise HTTPException(status_code=404, detail="Not found")

    # If it's a directory, try index.html
    if file_path.is_dir():
        file_path = file_path / "index.html"

    # If no extension, try adding .html
    if not file_path.suffix and not file_path.exists():
        alt = _safe_resolve(config["output_dir"], f"{path}.html")
        if alt is not None:
            file_path = alt

    if file_path.exists() and file_path.is_file():
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "text/html" if file_path.suffix == ".html" else "text/plain"

        try:
            content = file_path.read_bytes() if request.method == "GET" else b""
        except (PermissionError, OSError):
            raise HTTPException(status_code=404, detail="Not found")
        return Response(content=content, media_type=content_type)

    raise HTTPException(status_code=404, detail="Not found")


if __name__ == "__main__":
    import uvicorn

    # Setup before starting server
    setup_logging()
    validate_environment_and_setup()
    mount_static_files()

    # Use PORT environment variable or default to 8080
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
