"""
FastAPI server for Salasblog2 - serves static files + API endpoints
Includes Blogger API (XML-RPC) support for blog editors
"""
import os
import time
import xml.etree.ElementTree as ET
import logging
import subprocess
import asyncio
import json
import shutil
import re
import frontmatter
import markdown
import mimetypes
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from jinja2 import Environment, FileSystemLoader
from .generator import SiteGenerator
from .raindrop import RaindropDownloader
from .blogger_api import BloggerAPI
from .scheduler import get_scheduler
from .utils import process_markdown_to_html

# Global status tracking
sync_status = {"running": False, "message": "Ready"}
regen_status = {"running": False, "message": "Ready"}

# Global configuration
config = {
    "root_dir": None,
    "output_dir": None,
    "templates_dir": None,
    "admin_password": None,
    "session_secret": None,
    "jinja_env": None
}

def validate_environment_and_setup():
    """Validate all environment variables and system assumptions at startup"""
    logger = logging.getLogger(__name__)
    
    # Required environment variables
    required_env_vars = {
        "SESSION_SECRET": "Session secret key for admin authentication"
    }
    
    # Check required environment variables
    for var, description in required_env_vars.items():
        if not os.getenv(var):
            error_msg = f"Required environment variable {var} not set: {description}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
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
        logger.error(f"Contents of root dir: {list(config['root_dir'].iterdir()) if config['root_dir'].exists() else 'N/A'}")
        error_msg = f"Templates directory not found: {config['templates_dir']}"
        raise RuntimeError(error_msg)
    
    # Set up Jinja2 environment
    config["jinja_env"] = Environment(loader=FileSystemLoader(config["templates_dir"]))
    
    # Store configuration
    config["admin_password"] = os.getenv("ADMIN_PASSWORD")
    config["session_secret"] = os.getenv("SESSION_SECRET")
    
    # Create output directory if needed
    config["output_dir"].mkdir(exist_ok=True)
    
    logger.info(f"✓ Environment validation complete")
    logger.info(f"✓ Root directory: {config['root_dir']}")
    logger.info(f"✓ Output directory: {config['output_dir']}")
    logger.info(f"✓ Templates directory: {config['templates_dir']}")
    
    return True

def setup_logging():
    """Configure logging with custom format"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level_value = getattr(logging, log_level, logging.INFO)
    
    log_format = '%(asctime)s [%(levelname)s] %(message)s'
    date_format = '%M:%S'
    
    logging.basicConfig(
        level=log_level_value,
        format=log_format,
        datefmt=date_format,
        force=True
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
    if not os.getenv('FLY_APP_NAME'):
        logger.info("Not running on Fly.io, skipping instance check")
        return
    
    try:
        # Get list of machines for this app
        result = subprocess.run(
            ['fly', 'machines', 'list', '--json'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            machines = json.loads(result.stdout)
            
            # Count running machines
            running_machines = [m for m in machines if m.get('state') == 'started']
            
            if len(running_machines) > 1:
                machine_ids = [m.get('id', 'unknown') for m in running_machines]
                error_msg = f"CRITICAL: Multiple instances detected! Running machines: {machine_ids}. This app requires exactly 1 machine for data consistency."
                logger.error(error_msg)
                raise RuntimeError(error_msg)
            else:
                logger.info(f"Single instance check passed: {len(running_machines)} machine(s) running")
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
    
    # Start the scheduler for both Git and Raindrop sync
    scheduler = get_scheduler()
    scheduler.start_scheduler()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Salasblog2 server")
    scheduler.stop_scheduler()

# Create FastAPI app with validated configuration
app = FastAPI(
    title="Salasblog2", 
    description="Static site generator with API endpoints",
    lifespan=lifespan
)

# Add session middleware with validated secret
app.add_middleware(SessionMiddleware, secret_key=config.get("session_secret", "fallback-key"))

# Custom endpoints to fix FastAPI StaticFiles HEAD/GET inconsistency
@app.api_route("/static/{file_path:path}", methods=["GET", "HEAD"])
async def serve_static_files(file_path: str, request: Request):
    """Custom static file serving with consistent GET/HEAD behavior"""
    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="No output directory configured")
    
    full_path = config["output_dir"] / "static" / file_path
    
    if not full_path.exists() or not full_path.is_file():
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
    
    # Return content for GET, empty for HEAD
    content = full_path.read_bytes() if request.method == "GET" else b""
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
    
    # Return content for GET, empty for HEAD
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
    
    full_path = config["output_dir"] / "raindrops" / file_path
    
    # Handle directory index
    if full_path.is_dir():
        full_path = full_path / "index.html"
    
    if not full_path.exists() or not full_path.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    
    content_type, _ = mimetypes.guess_type(str(full_path))
    if not content_type:
        content_type = "text/html"
    
    # Return content for GET, empty for HEAD
    content = full_path.read_bytes() if request.method == "GET" else b""
    return Response(content=content, media_type=content_type)

# Mount static files if output directory exists
def mount_static_files():
    if config["output_dir"] and config["output_dir"].exists():
        logging.getLogger(__name__).info(f"mounting static directory at {config['output_dir'] / 'static'}")
        # Mount static assets (CSS, JS, images, etc.) - this handles proper MIME types automatically
        app.mount("/static", StaticFiles(directory=config["output_dir"] / "static"), name="static")
        
        logging.getLogger(__name__).info(f"mounting blog content at {config['output_dir'] / 'blog'}")
        # Mount blog content directory
        blog_dir = config["output_dir"] / "blog"
        if blog_dir.exists():
            app.mount("/blog", StaticFiles(directory=blog_dir, html=True), name="blog")
            
        logging.getLogger(__name__).info(f"mounting pages content at {config['output_dir'] / 'pages'}")
        # Mount pages content directory  
        pages_dir = config["output_dir"] / "pages"
        if pages_dir.exists():
            app.mount("/pages", StaticFiles(directory=pages_dir, html=True), name="pages")
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
    safe_title = re.sub(r'[^\w\s-]', '', title.lower())
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    safe_title = safe_title.strip('-')
    
    if content_type == 'blog':
        return f"{date}-{safe_title}.md"  # Date prefix for blog posts
    else:  # pages
        return f"{safe_title}.md"  # No date prefix for pages

def load_content_item(filename: str, content_type: str):
    """Load and parse frontmatter for any content type"""
    content_dir = get_content_directory(content_type)
    content_file = content_dir / filename
    
    if not content_file.exists():
        raise HTTPException(status_code=404, detail=f"{content_type.title()} not found: {filename}")
    
    try:
        with open(content_file, 'r', encoding='utf-8') as f:
            item = frontmatter.load(f)
        
        return {
            'title': item.metadata.get('title', ''),
            'date': item.metadata.get('date', ''),
            'category': item.metadata.get('category', 'General'),
            'type': item.metadata.get('type', content_type.rstrip('s')),  # 'blog' or 'page'
            'content': item.content
        }
    except Exception as e:
        logging.getLogger(__name__).error(f"Error loading {content_type} {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading {content_type}: {str(e)}")

def save_content_item(filename: str, content_type: str, title: str, date: str, 
                     category: str, item_type: str, content: str):
    """Save content item with frontmatter and regenerate site"""
    logger = logging.getLogger(__name__)
    
    content_dir = get_content_directory(content_type)
    content_dir.mkdir(parents=True, exist_ok=True)
    content_file = content_dir / filename
    
    try:
        # Create the content item with frontmatter
        item = frontmatter.Post(content.strip())
        item.metadata = {
            'title': title.strip(),
            'date': date,
            'category': category.strip() if category.strip() else 'General',
            'type': item_type
        }
        
        # Write the content back to file
        with open(content_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(item))
            f.flush()
            os.fsync(f.fileno())
        
        logger.info(f"{content_type.title()} saved successfully: {filename}")
        
        # Regenerate affected content
        try:
            generator = SiteGenerator()
            generator.incremental_regenerate_post(filename, content_type)
            logger.info(f"Site regenerated after saving {content_type}: {filename}")
        except Exception as regen_error:
            logger.error(f"Site regeneration failed after saving {content_type} {filename}: {regen_error}")
        
        return True
    except Exception as e:
        logger.error(f"Error saving {content_type} {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving {content_type}: {str(e)}")

# API Routes
@app.get("/")
async def serve_home():
    """Serve the home page"""
    home_file = config["output_dir"] / "index.html"
    if home_file.exists():
        return HTMLResponse(content=home_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Site not generated yet")

@app.get("/admin")
async def serve_admin_get(request: Request):
    """Serve admin login form or admin page"""
    # If no admin password is set, allow access without authentication
    if not config["admin_password"]:
        logging.getLogger(__name__).warning("No ADMIN_PASSWORD set - allowing unrestricted admin access")
        admin_file = config["templates_dir"] / "admin.html"
        return HTMLResponse(content=admin_file.read_text(encoding='utf-8'))
    
    # Check if admin is authenticated
    if is_admin_authenticated(request):
        admin_file = config["templates_dir"] / "admin.html"
        return HTMLResponse(content=admin_file.read_text(encoding='utf-8'))
    
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
            status_code=401
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
    result = subprocess.run([
        "rsync", "-av", "--checksum", 
        "/app/content/", "/data/content/"
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode != 0:
        logger.error(f"Sync to volume failed: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result.stderr}")
    
    logger.info("Successfully synced content to volume")
    return JSONResponse(content={
        "status": "success",
        "message": "Content synced to volume successfully",
        "output": result.stdout
    })

@app.post("/api/sync-from-volume")
async def sync_from_volume():
    """Sync content from /data/content/ to /app/content/"""
    logger = logging.getLogger(__name__)
    
    # Ensure app content directory exists
    app_dir = Path("/app/content")
    app_dir.mkdir(parents=True, exist_ok=True)
    
    # Use rsync for bidirectional sync
    result = subprocess.run([
        "rsync", "-av", "--update", 
        "/data/content/", "/app/content/"
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode != 0:
        logger.error(f"Sync from volume failed: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result.stderr}")
    
    logger.info("Successfully synced content from volume")
    return JSONResponse(content={
        "status": "success",
        "message": "Content synced from volume successfully",
        "output": result.stdout
    })

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
    result1 = subprocess.run([
        "rsync", "-av", "--update", 
        "/app/content/", "/data/content/"
    ], capture_output=True, text=True, timeout=30)
    
    if result1.returncode != 0:
        logger.error(f"Bidirectional sync (app->data) failed: {result1.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result1.stderr}")
    
    # Second sync: data to app
    result2 = subprocess.run([
        "rsync", "-av", "--update", 
        "/data/content/", "/app/content/"
    ], capture_output=True, text=True, timeout=30)
    
    if result2.returncode != 0:
        logger.error(f"Bidirectional sync (data->app) failed: {result2.stderr}")
        raise HTTPException(status_code=500, detail=f"Sync failed: {result2.stderr}")
    
    logger.info("Successfully completed bidirectional sync")
    return JSONResponse(content={
        "status": "success",
        "message": "Bidirectional sync completed successfully",
        "app_to_data": result1.stdout,
        "data_to_app": result2.stdout
    })

# Scheduler API endpoints
@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get the current status of the scheduler"""
    scheduler = get_scheduler()
    status = scheduler.get_status()
    return JSONResponse(content=status)

@app.post("/api/scheduler/sync-now")
async def trigger_git_sync():
    """Manually trigger a Git sync to GitHub"""
    logger = logging.getLogger(__name__)
    scheduler = get_scheduler()
    
    success = await scheduler.sync_to_github()
    if success:
        return JSONResponse(content={
            "status": "success",
            "message": "Content successfully synced to GitHub"
        })
    else:
        raise HTTPException(status_code=500, detail="Git sync failed - check logs for details")

@app.post("/api/scheduler/sync-raindrops-now")
async def trigger_raindrop_sync():
    """Manually trigger a Raindrop sync"""
    logger = logging.getLogger(__name__)
    scheduler = get_scheduler()
    
    try:
        success = await scheduler.sync_raindrops()
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": "Raindrops successfully synced and site regenerated"
            })
        else:
            raise HTTPException(status_code=500, detail="Raindrop sync failed - check logs for details")
    except Exception as e:
        logger.error(f"Manual Raindrop sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Raindrop sync error: {str(e)}")

@app.post("/api/scheduler/start")
async def start_scheduler(git_hours: float = None, raindrop_hours: float = None):
    """Start or restart the scheduler with specified intervals"""
    if git_hours is not None and (git_hours < 0.1 or git_hours > 24):
        raise HTTPException(status_code=400, detail="Git interval must be between 0.1 and 24 hours")
    if raindrop_hours is not None and (raindrop_hours < 0.1 or raindrop_hours > 24):
        raise HTTPException(status_code=400, detail="Raindrop interval must be between 0.1 and 24 hours")
    
    scheduler = get_scheduler()
    scheduler.stop_scheduler()
    scheduler.start_scheduler(git_interval_hours=git_hours, raindrop_interval_hours=raindrop_hours)
    
    # Get actual intervals used
    actual_git_hours = git_hours if git_hours is not None else float(os.environ.get('SCHED_GITSYNC_HRS', 6.0))
    actual_raindrop_hours = raindrop_hours if raindrop_hours is not None else float(os.environ.get('SCHED_RAINSYNC_HRS', 2.0))
    
    return JSONResponse(content={
        "status": "success",
        "message": f"Scheduler started - Git sync every {actual_git_hours} hours, Raindrop sync every {actual_raindrop_hours} hours"
    })

@app.post("/api/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    scheduler = get_scheduler()
    scheduler.stop_scheduler()
    
    return JSONResponse(content={
        "status": "success",
        "message": "Scheduler stopped"
    })

@app.post("/api/emergency-restore")
async def emergency_restore_from_github():
    """
    EMERGENCY: Restore /data/content from GitHub repository
    WARNING: This overwrites the persistent volume with repository content!
    """
    logger = logging.getLogger(__name__)
    logger.warning("EMERGENCY RESTORE: Starting restoration from GitHub to /data/content")
    
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
        timeout=60
    )
    
    if result.returncode != 0:
        logger.error(f"Git pull failed: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Failed to pull from GitHub: {result.stderr}")
    
    # Check if /app/content exists
    app_content = git_dir / "content"
    if not app_content.exists():
        raise HTTPException(status_code=500, detail="/app/content does not exist after git pull")
    
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
        timeout=120
    )
    
    if result.returncode != 0:
        # Restore backup if copy failed
        if backup_path.exists():
            logger.error("Restore failed, restoring backup...")
            shutil.move(str(backup_path), str(data_content))
        raise HTTPException(status_code=500, detail=f"Failed to copy content: {result.stderr}")
    
    # Clean up backup
    if backup_path.exists():
        logger.info(f"Removing backup {backup_path}")
        shutil.rmtree(backup_path)
    
    logger.warning("EMERGENCY RESTORE: Successfully restored /data/content from GitHub")
    
    return JSONResponse(content={
        "status": "success", 
        "message": "Emergency restore completed - /data/content restored from GitHub",
        "warning": "Volume content was overwritten with repository content"
    })

@app.post("/api/sync-pages-from-repo")
async def sync_pages_from_repo():
    """
    Safely sync just the pages directory from GitHub repository to volume
    Only updates /data/content/pages/ with repository content
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting safe pages sync from GitHub repository...")
    
    # Ensure we're in the git directory
    git_dir = Path("/app")
    if not (git_dir / ".git").exists():
        raise HTTPException(status_code=500, detail="Git repository not found in /app")
    
    # Pull latest from GitHub first
    logger.info("Pulling latest content from GitHub...")
    result = subprocess.run(
        ["git", "pull", "origin", "main"],
        cwd=git_dir,
        capture_output=True,
        text=True,
        timeout=60
    )
    
    if result.returncode != 0:
        logger.error(f"Git pull failed: {result.stderr}")
        raise HTTPException(status_code=500, detail=f"Failed to pull from GitHub: {result.stderr}")
    
    # Check if /app/content/pages exists
    app_pages = git_dir / "content" / "pages"
    if not app_pages.exists():
        raise HTTPException(status_code=500, detail="/app/content/pages does not exist after git pull")
    
    # Ensure /data/content/pages directory exists
    data_pages = Path("/data/content/pages")
    data_pages.mkdir(parents=True, exist_ok=True)
    
    # Backup current pages as .md-old files (including subdirectories)
    if data_pages.exists() and any(data_pages.iterdir()):
        logger.info("Backing up current pages as .md-old files")
        for md_file in data_pages.rglob("*.md"):
            backup_file = md_file.with_suffix(".md-old")
            logger.info(f"Backing up {md_file.relative_to(data_pages)} to {backup_file.relative_to(data_pages)}")
            shutil.copy2(str(md_file), str(backup_file))
    
    # Copy pages from repository to volume
    logger.info("Copying pages from /app/content/pages to /data/content/pages...")
    result = subprocess.run(
        ["rsync", "-av", "--delete", str(app_pages) + "/", str(data_pages) + "/"],
        capture_output=True,
        text=True,
        timeout=30
    )
    
    if result.returncode != 0:
        # Restore from .md-old files if copy failed (including subdirectories)
        logger.error("Pages sync failed, restoring from .md-old files...")
        for backup_file in data_pages.rglob("*.md-old"):
            original_file = backup_file.with_suffix(".md")
            logger.info(f"Restoring {original_file.relative_to(data_pages)} from {backup_file.relative_to(data_pages)}")
            shutil.copy2(str(backup_file), str(original_file))
        raise HTTPException(status_code=500, detail=f"Failed to sync pages: {result.stderr}")
    
    # Count synced files (including subdirectories)
    synced_files = list(data_pages.rglob("*.md"))
    
    logger.info(f"Successfully synced {len(synced_files)} page files from repository")
    
    return JSONResponse(content={
        "status": "success",
        "message": f"Pages synced successfully - {len(synced_files)} files updated",
        "files_synced": [f.name for f in synced_files],
        "sync_details": f"Synced from /app/content/pages to /data/content/pages"
    })

@app.get("/api/admin-status")
async def get_admin_status(request: Request):
    """Check if current user is authenticated as admin"""
    # If no admin password is set, allow access without authentication
    if not config["admin_password"]:
        return JSONResponse(content={
            "authenticated": True
        })
    
    # Check if admin is authenticated via session
    return JSONResponse(content={
        "authenticated": is_admin_authenticated(request)
    })

@app.get("/admin/edit-post/{filename}")
async def edit_post_page(filename: str, request: Request):
    """Serve edit post page with actual post content"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    
    # Load the post using shared function
    post_data = load_content_item(filename, 'blog')
    
    # Render edit form using template with post context
    context = {
        'filename': filename,
        'content_type': 'blog',
        'content_type_title': 'Post',
        'action_url': f'/admin/edit-post/{filename}',
        'cancel_url': '/blog/',
        **post_data
    }
    return HTMLResponse(content=render_template("edit_post.html", context))

@app.post("/admin/edit-post/{filename}")
async def save_edited_post(filename: str, request: Request, title: str = Form(...), 
                          date: str = Form(...), category: str = Form(...), 
                          type: str = Form(...), content: str = Form(...)):
    """Save edited post to file and regenerate site"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if file exists
    content_dir = get_content_directory('blog')
    if not (content_dir / filename).exists():
        raise HTTPException(status_code=404, detail=f"Post not found: {filename}")
    
    # Save using shared function
    save_content_item(filename, 'blog', title, date, category, type, content)
    
    return JSONResponse(content={
        "status": "success",
        "message": "Post updated successfully",
        "filename": filename
    })

@app.get("/admin/new-post")
async def new_post_page(request: Request):
    """Serve new post creation page with form"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    
    context = {
        'content_type': 'blog',
        'content_type_title': 'Post',
        'action_url': '/admin/new-post',
        'cancel_url': '/blog/'
    }
    return HTMLResponse(content=render_template("new_post.html", context))

@app.post("/admin/new-post")
async def create_new_post(request: Request, title: str = Form(...), 
                         date: str = Form(...), category: str = Form(...), 
                         type: str = Form(...), content: str = Form(...)):
    """Create a new blog post with generated filename"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Generate filename using shared function
        filename = create_filename_for_content(title.strip(), date, 'blog')
        
        # Check if file already exists
        content_dir = get_content_directory('blog')
        if (content_dir / filename).exists():
            raise HTTPException(status_code=400, detail=f"A post with filename '{filename}' already exists")
        
        # Save using shared function
        save_content_item(filename, 'blog', title, date, category, type, content)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Post created successfully",
            "filename": filename,
            "url": f"/blog/{filename.replace('.md', '.html')}"
        })
        
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
    
    # Load the page using shared function
    page_data = load_content_item(filename, 'pages')
    
    # Render edit form using template with page context
    context = {
        'filename': filename,
        'content_type': 'page',
        'content_type_title': 'Page',
        'action_url': f'/admin/edit-page/{filename}',
        'cancel_url': '/pages/',
        **page_data
    }
    return HTMLResponse(content=render_template("edit_post.html", context))

@app.post("/admin/edit-page/{filename}")
async def save_edited_page(filename: str, request: Request, title: str = Form(...), 
                          date: str = Form(...), category: str = Form(...), 
                          type: str = Form(...), content: str = Form(...)):
    """Save edited page to file and regenerate site"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Check if file exists
    content_dir = get_content_directory('pages')
    if not (content_dir / filename).exists():
        raise HTTPException(status_code=404, detail=f"Page not found: {filename}")
    
    # Save using shared function
    save_content_item(filename, 'pages', title, date, category, type, content)
    
    return JSONResponse(content={
        "status": "success",
        "message": "Page updated successfully",
        "filename": filename
    })

@app.get("/admin/new-page")
async def new_page_page(request: Request):
    """Serve new page creation form"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    
    context = {
        'content_type': 'page',
        'content_type_title': 'Page',
        'action_url': '/admin/new-page',
        'cancel_url': '/pages/'
    }
    return HTMLResponse(content=render_template("new_post.html", context))

@app.post("/admin/new-page")
async def create_new_page(request: Request, title: str = Form(...), 
                         date: str = Form(...), category: str = Form(...), 
                         type: str = Form(...), content: str = Form(...)):
    """Create a new page"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Generate filename using shared function
        filename = create_filename_for_content(title.strip(), date, 'pages')
        
        # Check if file already exists
        content_dir = get_content_directory('pages')
        if (content_dir / filename).exists():
            raise HTTPException(status_code=400, detail=f"A page with filename '{filename}' already exists")
        
        # Save using shared function
        save_content_item(filename, 'pages', title, date, category, type, content)
        
        return JSONResponse(content={
            "status": "success",
            "message": "Page created successfully",
            "filename": filename,
            "url": f"/pages/{filename.replace('.md', '.html')}"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error(f"Error creating new page: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating page: {str(e)}")

@app.post("/admin/delete-post/{filename}")
async def delete_post_endpoint(filename: str, request: Request):
    """Delete a blog post"""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    return JSONResponse(content={
        "status": "error",
        "detail": f"Post deletion not yet implemented. Would delete: {filename}"
    }, status_code=501)

@app.post("/admin/preview-markdown")
async def preview_markdown(request: Request, content: str = Form(...)):
    """Convert markdown content to HTML for preview"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Use standardized markdown processing
        html = process_markdown_to_html(content)
        
        return JSONResponse(content={
            "status": "success",
            "html": html
        })
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error rendering markdown preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")

@app.post("/admin/preview-post")
async def preview_post_html(request: Request, title: str = Form(...), content: str = Form(...), 
                           date: str = Form(...), category: str = Form(...), 
                           type: str = Form(...), filename: str = Form(...)):
    """Render complete preview page with HTML"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Use standardized markdown processing
        html_content = process_markdown_to_html(content)
        
        context = {
            'title': title,
            'content': content,
            'html_content': html_content,
            'date': date,
            'category': category,
            'type': type,
            'filename': filename
        }
        return HTMLResponse(content=render_template("preview_post.html", context))
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error rendering post preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")

@app.post("/admin/preview-new-post")
async def preview_new_post_html(request: Request, title: str = Form(...), content: str = Form(...), 
                               date: str = Form(...), category: str = Form(...), 
                               type: str = Form(...)):
    """Render complete preview page for new post with HTML"""
    # Check authentication
    if config["admin_password"] and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        # Use standardized markdown processing
        html_content = process_markdown_to_html(content)
        
        # Generate filename preview
        def create_filename_from_title(title: str, date: str) -> str:
            safe_title = re.sub(r'[^\w\s-]', '', title.lower())
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            safe_title = safe_title.strip('-')
            return f"{date}-{safe_title}.md"
        
        filename = create_filename_from_title(title.strip(), date)
        
        context = {
            'title': title,
            'content': content,
            'html_content': html_content,
            'date': date,
            'category': category,
            'type': type,
            'filename': filename
        }
        return HTMLResponse(content=render_template("preview_new_post.html", context))
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Error rendering new post preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")

# Raindrop sync and site generation endpoints with simplified logic
@app.get("/api/sync-raindrops")
async def sync_raindrops():
    """Trigger raindrop sync and regenerate site"""
    
    def do_sync():
        sync_status["running"] = True
        sync_status["message"] = "Downloading raindrops..."
        
        # Download new raindrops
        downloader = RaindropDownloader()
        new_filenames = downloader.download_raindrops()
        
        logging.getLogger(__name__).info(f"Sync result: new_filenames = {new_filenames}")
        
        # Only regenerate if there are new raindrops
        if new_filenames:
            logging.getLogger(__name__).info(f"Processing {len(new_filenames)} new raindrops")
            
            # Check if this is a first sync
            env_timestamp = os.getenv("RAINDROP_LAST_SYNC")
            cache_file = Path("/data/content/.rd_cache.json")
            is_first_sync = not env_timestamp and not cache_file.exists()
            
            if is_first_sync and len(new_filenames) > 10:
                # Full regeneration for first sync
                sync_status["message"] = f"First sync: doing full site regeneration for {len(new_filenames)} raindrops..."
                generator = SiteGenerator()
                generator.generate_site()
                result = {
                    "status": "success",
                    "message": f"First sync: regenerated entire site with {len(new_filenames)} new raindrops"
                }
            else:
                # Incremental regeneration
                sync_status["message"] = f"Regenerating {len(new_filenames)} raindrop pages..."
                generator = SiteGenerator()
                
                for i, filename in enumerate(new_filenames, 1):
                    sync_status["message"] = f"Regenerating {i}/{len(new_filenames)}: {filename[:30]}..."
                    generator.incremental_regenerate_post(filename, 'raindrops')
                
                result = {
                    "status": "success",
                    "message": f"Synced {len(new_filenames)} new raindrops and regenerated pages"
                }
        else:
            result = {
                "status": "success",
                "message": "No new raindrops to sync"
            }
        
        sync_status["running"] = False
        sync_status["message"] = result["message"]
        return result
    
    # Check if already running
    if sync_status["running"]:
        return JSONResponse(content={
            "status": "running",
            "message": sync_status["message"]
        })
    
    # Start async execution
    async def run_sync():
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, do_sync)
    
    asyncio.create_task(run_sync())
    
    return JSONResponse(content={
        "status": "started",
        "message": "Raindrop sync started. Check /api/sync-status for progress."
    })

@app.get("/api/sync-status")
async def get_sync_status():
    """Get current raindrop sync status"""
    return JSONResponse(content=sync_status)

@app.get("/api/regenerate")
async def regenerate_site():
    """Regenerate the static site"""
    
    def do_regenerate():
        generator = SiteGenerator()
        generator.generate_site()
        return {
            "status": "success", 
            "message": "Site regenerated successfully",
            "theme": generator.theme
        }
    
    # Run regeneration in thread pool
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, do_regenerate)
    return JSONResponse(content=result)

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
        headers={"Content-Type": "application/rsd+xml; charset=utf-8"}
    )

@app.get("/xmlrpc")
async def xmlrpc_get_endpoint(request: Request):
    """Handle GET requests to XML-RPC endpoint for debugging"""
    logging.getLogger(__name__).info("GET request received at /xmlrpc endpoint")
    return Response(
        content="XML-RPC endpoint ready. Use POST with XML-RPC payload.",
        media_type="text/plain"
    )

@app.post("/xmlrpc")
async def xmlrpc_endpoint(request: Request):
    """XML-RPC endpoint for Blogger API"""
    logger = logging.getLogger(__name__)
    
    body = await request.body()
    logger.info(f"Received XML-RPC request, body length: {len(body)}")
    
    # Parse XML-RPC request
    root = ET.fromstring(body.decode('utf-8'))
    method_name = root.find('.//methodName').text
    logger.info(f"XML-RPC method: {method_name}")
    
    # Extract parameters (simplified parsing)
    params = []
    param_nodes = root.findall('.//param/value')
    
    for i, param in enumerate(param_nodes):
        if param.find('string') is not None:
            value = param.find('string').text or ""
        elif param.find('boolean') is not None:
            value = param.find('boolean').text == '1'
        elif param.find('int') is not None:
            value = int(param.find('int').text)
        elif param.find('i4') is not None:
            value = int(param.find('i4').text)
        elif param.find('struct') is not None:
            # Parse struct
            struct_elem = param.find('struct')
            struct_dict = {}
            for member in struct_elem.findall('member'):
                name_elem = member.find('name')
                value_elem = member.find('value')
                if name_elem is not None and value_elem is not None:
                    key = name_elem.text
                    if value_elem.find('string') is not None:
                        val = value_elem.find('string').text or ""
                    elif value_elem.find('boolean') is not None:
                        val = value_elem.find('boolean').text == '1'
                    elif value_elem.find('int') is not None:
                        val = int(value_elem.find('int').text)
                    elif value_elem.find('i4') is not None:
                        val = int(value_elem.find('i4').text)
                    else:
                        val = value_elem.text or ""
                    struct_dict[key] = val
            value = struct_dict
        else:
            value = param.text or ""
        
        params.append(value)
    
    # Handle Blogger API methods
    api = BloggerAPI()
    logger.info(f"Calling {method_name} with {len(params)} parameters")
    
    try:
        if method_name == "blogger.newPost":
            result = api.blogger_newPost(*params)
        elif method_name == "blogger.editPost":
            result = api.blogger_editPost(*params)
        elif method_name == "blogger.deletePost":
            result = api.blogger_deletePost(*params)
        elif method_name == "blogger.getRecentPosts":
            result = api.blogger_getRecentPosts(*params)
        elif method_name == "blogger.getUsersBlogs":
            result = api.blogger_getUsersBlogs(*params)
        elif method_name == "blogger.getPost":
            result = api.blogger_getPost(*params)
        elif method_name == "metaWeblog.newPost":
            result = api.metaweblog_newPost(*params)
        elif method_name == "metaWeblog.editPost":
            result = api.metaweblog_editPost(*params)
        elif method_name == "metaWeblog.getPost":
            result = api.metaweblog_getPost(*params)
        elif method_name == "metaWeblog.getRecentPosts":
            result = api.metaweblog_getRecentPosts(*params)
        elif method_name == "metaWeblog.getCategories":
            result = api.metaweblog_getCategories(*params)
        else:
            logger.error(f"Unknown method: {method_name}")
            raise HTTPException(status_code=400, detail=f"Unknown method: {method_name}")
    except Exception as e:
        if "Authentication failed" in str(e):
            logger.info("Authentication failed - returning XML-RPC fault with code 403")
            fault_xml = create_xmlrpc_fault_with_code(403, "Incorrect username or password.")
            return Response(content=fault_xml, media_type="text/xml", status_code=200)
        else:
            raise
    
    # Create XML-RPC response
    logger.info(f"Method {method_name} completed successfully")
    response_xml = create_xmlrpc_response(result)
    
    return Response(
        content=response_xml,
        media_type="text/xml",
        headers={"Content-Type": "text/xml"}
    )

def create_xmlrpc_response(result):
    """Create XML-RPC response"""
    if isinstance(result, str):
        value = f"<string>{result}</string>"
    elif isinstance(result, bool):
        value = f"<boolean>{'1' if result else '0'}</boolean>"
    elif isinstance(result, int):
        value = f"<int>{result}</int>"
    elif isinstance(result, dict):
        struct_members = ""
        for key, val in result.items():
            struct_members += f"<member><name>{key}</name><value><string>{val}</string></value></member>"
        value = f"<struct>{struct_members}</struct>"
    elif isinstance(result, list):
        array_items = ""
        for item in result:
            if isinstance(item, dict):
                struct_members = ""
                for key, val in item.items():
                    struct_members += f"<member><name>{key}</name><value><string>{val}</string></value></member>"
                array_items += f"<value><struct>{struct_members}</struct></value>"
            else:
                array_items += f"<value><string>{item}</string></value>"
        value = f"<array><data>{array_items}</data></array>"
    else:
        value = f"<string>{str(result)}</string>"
    
    return f"""<?xml version="1.0"?>
<methodResponse>
    <params>
        <param>
            <value>{value}</value>
        </param>
    </params>
</methodResponse>"""

def create_xmlrpc_fault_with_code(fault_code, message):
    """Create XML-RPC fault response with specific fault code"""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<methodResponse>
  <fault>
    <value>
      <struct>
        <member>
          <name>faultCode</name>
          <value><int>{fault_code}</int></value>
        </member>
        <member>
          <name>faultString</name>
          <value><string>{message}</string></value>
        </member>
      </struct>
    </value>
  </fault>
</methodResponse>"""

# Catch-all route moved to end of file to ensure proper precedence

# Root level files served by catch-all route (index.html, etc.)  
# This MUST be the last route defined to ensure proper precedence
@app.api_route("/{path:path}", methods=["GET", "HEAD"])
async def serve_root_files(path: str, request: Request):
    """Serve root-level files like index.html, robots.txt, etc."""
    # Only handle root-level files, not paths that start with mounted directories
    if '/' in path or path.startswith(('blog', 'pages', 'static')):
        raise HTTPException(status_code=404, detail="Not found")
    
    if not config.get("output_dir"):
        raise HTTPException(status_code=404, detail="Not found")
    
    file_path = config["output_dir"] / path
    
    # If it's a directory, try index.html
    if file_path.is_dir():
        file_path = file_path / "index.html"
    
    # If no extension, try adding .html
    if not file_path.suffix and not file_path.exists():
        file_path = config["output_dir"] / f"{path}.html"
    
    if file_path.exists() and file_path.is_file():
        # Use mimetypes module for automatic MIME type detection
        content_type, _ = mimetypes.guess_type(str(file_path))
        if not content_type:
            content_type = "text/html" if file_path.suffix == ".html" else "text/plain"
        
        # Return content for GET, empty for HEAD
        content = file_path.read_bytes() if request.method == "GET" else b""
        return Response(content=content, media_type=content_type)
    
    # Return 404 for missing files
    raise HTTPException(status_code=404, detail="Not found")

if __name__ == "__main__":
    import uvicorn
    
    # Setup before starting server
    setup_logging()
    validate_environment_and_setup()
    mount_static_files()
    
    # Use PORT environment variable or default to 8000 for local development
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)