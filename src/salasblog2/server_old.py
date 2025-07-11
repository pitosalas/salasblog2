"""
FastAPI server for Salasblog2 - serves static files + API endpoints
Includes Blogger API (XML-RPC) support for blog editors
"""
import os
import time
import xml.etree.ElementTree as ET
import logging
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, Form, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse, Response, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from starlette.middleware.sessions import SessionMiddleware
from contextlib import asynccontextmanager
from .generator import SiteGenerator
from .raindrop import RaindropDownloader
from .blogger_api import BloggerAPI
from .scheduler import get_scheduler

# Instructions for Claude
# Delete these once you implement them
# 1. There should be no big chunks of html in this file. That is a nono
# 2. Instead of constantly checking if things are as you expect them, home directory, output directory, content directory, and many more, write a function that is run once that checks every assumption, and reports problems, and if they are serious, stop the server
# 3. THen remove all the inline checks and try catches. I think it will be cleaner and a net savings
# 4. Fail if any required environment variables are not set, dont bother checking and applying defaults. Just check it once early and be done with it.
# 5. All imports should be at the top, never inline


# Global status tracking
sync_status = {"running": False, "message": "Ready"}
regen_status = {"running": False, "message": "Ready"}

# Set up logging
log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
log_level_value = getattr(logging, log_level, logging.INFO)

# Configure logging format for all loggers
log_format = '%(asctime)s [%(levelname)s] %(message)s'
date_format = '%M:%S'

logging.basicConfig(
    level=log_level_value,
    format=log_format,
    datefmt=date_format,
    force=True  # Override any existing configuration
)

# Also configure uvicorn loggers specifically
uvicorn_logger = logging.getLogger("uvicorn")
uvicorn_access_logger = logging.getLogger("uvicorn.access")

# Create a formatter and apply it to uvicorn loggers
formatter = logging.Formatter(log_format, datefmt=date_format)

# Update handlers for uvicorn loggers
for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error"]:
    logger_obj = logging.getLogger(logger_name)
    logger_obj.setLevel(log_level_value)
    for handler in logger_obj.handlers:
        handler.setFormatter(formatter)

logger = logging.getLogger(__name__)


def _check_single_instance():
    """Check if this is the only instance running and error if not."""
    import os
    import subprocess
    
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
            import json
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
    # Startup
    logger.info("Starting Salasblog2 server")
    
    # Check if we're the only instance running
    _check_single_instance()
    
    # Start the scheduler for both Git and Raindrop sync
    scheduler = get_scheduler()
    scheduler.start_scheduler()  # Use SCHED_GITSYNC_HRS and SCHED_RAINSYNC_HRS env vars
    
    import asyncio
    
    yield
    
    # Shutdown
    logger.info("Shutting down Salasblog2 server")
    
    # Stop the scheduler
    scheduler.stop_scheduler()


app = FastAPI(
    title="Salasblog2", 
    description="Static site generator with API endpoints",
    lifespan=lifespan
)

# Add session middleware for admin authentication
app.add_middleware(SessionMiddleware, secret_key=os.getenv("SESSION_SECRET", "salasblog2-default-secret-key"))

# Get paths
root_dir = Path(__file__).parent.parent.parent
output_dir = root_dir / "output"

# Mount static files
if output_dir.exists():
    app.mount("/static", StaticFiles(directory=output_dir / "static"), name="static")

# Admin authentication helpers
def get_admin_password():
    """Get admin password from environment variable"""
    return os.getenv("ADMIN_PASSWORD")

def is_admin_authenticated(request: Request) -> bool:
    """Check if admin is authenticated via session"""
    return request.session.get("admin_authenticated", False)

def create_login_form_html():
    """Generate HTML for admin login form"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Admin Login - Salas Blog</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                background: #f5f5f5; 
                display: flex; 
                justify-content: center; 
                align-items: center; 
                min-height: 100vh; 
                margin: 0; 
            }
            .login-container { 
                background: white; 
                padding: 40px; 
                border-radius: 8px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                width: 100%; 
                max-width: 400px; 
            }
            .login-container h1 { 
                text-align: center; 
                margin-bottom: 30px; 
                color: #333; 
            }
            .form-group { 
                margin-bottom: 20px; 
            }
            label { 
                display: block; 
                margin-bottom: 5px; 
                color: #555; 
                font-weight: bold; 
            }
            input[type="password"] { 
                width: 100%; 
                padding: 12px; 
                border: 1px solid #ddd; 
                border-radius: 4px; 
                font-size: 16px; 
                box-sizing: border-box; 
            }
            .login-btn { 
                width: 100%; 
                padding: 12px; 
                background: #007cba; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                font-size: 16px; 
                cursor: pointer; 
                transition: background-color 0.2s; 
            }
            .login-btn:hover { 
                background: #005a87; 
            }
            .error { 
                color: #e74c3c; 
                margin-top: 10px; 
                text-align: center; 
            }
            .back-link { 
                text-align: center; 
                margin-top: 20px; 
            }
            .back-link a { 
                color: #007cba; 
                text-decoration: none; 
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>Admin Login</h1>
            <form method="post" action="/admin">
                <div class="form-group">
                    <label for="password">Password:</label>
                    <input type="password" id="password" name="password" required autofocus>
                </div>
                <button type="submit" class="login-btn">Login</button>
            </form>
            <div class="back-link">
                <a href="/">← Back to Blog</a>
            </div>
        </div>
    </body>
    </html>
    """

@app.get("/")
async def serve_home():
    """Serve the home page"""
    home_file = output_dir / "index.html"
    if home_file.exists():
        return HTMLResponse(content=home_file.read_text(encoding='utf-8'))
    raise HTTPException(status_code=404, detail="Site not generated yet")

@app.get("/admin")
async def serve_admin_get(request: Request):
    """Serve admin login form or admin page"""
    admin_password = get_admin_password()
    
    # If no admin password is set, allow access without authentication
    if not admin_password:
        logger.warning("No ADMIN_PASSWORD set - allowing unrestricted admin access")
        admin_file = root_dir / "templates" / "admin.html"
        if admin_file.exists():
            return HTMLResponse(content=admin_file.read_text(encoding='utf-8'))
        raise HTTPException(status_code=404, detail="Admin page not found")
    
    # Check if admin is authenticated
    if is_admin_authenticated(request):
        admin_file = root_dir / "templates" / "admin.html"
        if admin_file.exists():
            return HTMLResponse(content=admin_file.read_text(encoding='utf-8'))
        raise HTTPException(status_code=404, detail="Admin page not found")
    
    # Show login form
    return HTMLResponse(content=create_login_form_html())

@app.post("/admin")
async def serve_admin_post(request: Request, password: str = Form(...)):
    """Handle admin login"""
    admin_password = get_admin_password()
    
    # If no admin password is set, redirect to admin page
    if not admin_password:
        return RedirectResponse(url="/admin", status_code=302)
    
    # Check password
    if password == admin_password:
        request.session["admin_authenticated"] = True
        logger.info("Admin authentication successful")
        return RedirectResponse(url="/admin", status_code=302)
    else:
        logger.warning("Admin authentication failed - incorrect password")
        # Return login form with error
        error_html = create_login_form_html().replace(
            '<button type="submit" class="login-btn">Login</button>',
            '<button type="submit" class="login-btn">Login</button>\n                <div class="error">Incorrect password. Please try again.</div>'
        )
        return HTMLResponse(content=error_html, status_code=401)

@app.post("/admin/logout")
async def admin_logout(request: Request):
    """Logout admin user"""
    request.session.pop("admin_authenticated", None)
    logger.info("Admin logged out")
    return RedirectResponse(url="/", status_code=302)

@app.post("/api/sync-to-volume")
async def sync_to_volume():
    """Sync content from /app/content/ to /data/content/"""
    try:
        # Ensure data directory exists
        data_dir = Path("/data/content")
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # Use rsync with checksum comparison (content-based sync)
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
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Sync operation timed out")
    except Exception as e:
        logger.error(f"Sync to volume error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@app.post("/api/sync-from-volume")
async def sync_from_volume():
    """Sync content from /data/content/ to /app/content/"""
    try:
        # Ensure app content directory exists
        app_dir = Path("/app/content")
        app_dir.mkdir(parents=True, exist_ok=True)
        
        # Use rsync for bidirectional sync (newer files win)
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
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Sync operation timed out")
    except Exception as e:
        logger.error(f"Sync from volume error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@app.post("/api/bidirectional-sync")
async def bidirectional_sync():
    """Perform bidirectional sync between /app/content/ and /data/content/"""
    try:
        # Ensure both directories exist
        app_dir = Path("/app/content")
        data_dir = Path("/data/content")
        app_dir.mkdir(parents=True, exist_ok=True)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # First sync: app to data (newer files win)
        result1 = subprocess.run([
            "rsync", "-av", "--update", 
            "/app/content/", "/data/content/"
        ], capture_output=True, text=True, timeout=30)
        
        if result1.returncode != 0:
            logger.error(f"Bidirectional sync (app->data) failed: {result1.stderr}")
            raise HTTPException(status_code=500, detail=f"Sync failed: {result1.stderr}")
        
        # Second sync: data to app (newer files win)
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
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Sync operation timed out")
    except Exception as e:
        logger.error(f"Bidirectional sync error: {e}")
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@app.get("/api/scheduler/status")
async def get_scheduler_status():
    """Get the current status of the scheduler"""
    scheduler = get_scheduler()
    status = scheduler.get_status()
    return JSONResponse(content=status)

@app.post("/api/scheduler/sync-now")
async def trigger_git_sync():
    """Manually trigger a Git sync to GitHub"""
    scheduler = get_scheduler()
    try:
        success = await scheduler.sync_to_github()
        if success:
            return JSONResponse(content={
                "status": "success",
                "message": "Content successfully synced to GitHub"
            })
        else:
            raise HTTPException(status_code=500, detail="Git sync failed - check logs for details")
    except Exception as e:
        logger.error(f"Manual Git sync failed: {e}")
        raise HTTPException(status_code=500, detail=f"Git sync error: {str(e)}")

@app.post("/api/scheduler/sync-raindrops-now")
async def trigger_raindrop_sync():
    """Manually trigger a Raindrop sync"""
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
    scheduler.stop_scheduler()  # Stop if already running
    scheduler.start_scheduler(git_interval_hours=git_hours, raindrop_interval_hours=raindrop_hours)
    
    # Get actual intervals used (from env vars if not specified)
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
    import subprocess
    import shutil
    from pathlib import Path
    
    try:
        logger.warning("EMERGENCY RESTORE: Starting restoration from GitHub to /data/content")
        
        # Ensure we're in the git directory
        git_dir = Path("/app")
        if not (git_dir / ".git").exists():
            raise HTTPException(status_code=500, detail="Git repository not found in /app")
        
        # Pull latest from GitHub to ensure /app/content is up to date
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
        
        # Backup current /data/content if it exists
        data_content = Path("/data/content")
        backup_path = Path("/data/content_backup_" + str(int(time.time())))
        
        if data_content.exists():
            logger.info(f"Backing up current /data/content to {backup_path}")
            shutil.move(str(data_content), str(backup_path))
        
        # Create /data/content directory
        data_content.mkdir(parents=True, exist_ok=True)
        
        # Copy /app/content to /data/content
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
        
        # Clean up backup after successful restore
        if backup_path.exists():
            logger.info(f"Removing backup {backup_path}")
            shutil.rmtree(backup_path)
        
        logger.warning("EMERGENCY RESTORE: Successfully restored /data/content from GitHub")
        
        return JSONResponse(content={
            "status": "success", 
            "message": "Emergency restore completed - /data/content restored from GitHub",
            "warning": "Volume content was overwritten with repository content"
        })
        
    except subprocess.TimeoutExpired:
        logger.error("Emergency restore timed out")
        raise HTTPException(status_code=500, detail="Emergency restore operation timed out")
    except Exception as e:
        logger.error(f"Emergency restore failed: {e}")
        raise HTTPException(status_code=500, detail=f"Emergency restore failed: {str(e)}")

@app.get("/api/sync-raindrops")
async def sync_raindrops():
    """Trigger raindrop sync and regenerate site"""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    def do_sync():
        try:
            sync_status["running"] = True
            sync_status["message"] = "Downloading raindrops..."
            
            # Download new raindrops
            downloader = RaindropDownloader()
            new_filenames = downloader.download_raindrops()
            
            logger.info(f"Sync result: new_filenames = {new_filenames}")
            
            # Only regenerate if there are new raindrops
            if new_filenames:
                logger.info(f"Processing {len(new_filenames)} new raindrops")
                
                # Check if this is a first sync (no cache) with many files
                env_timestamp = os.getenv("RAINDROP_LAST_SYNC")
                cache_file = Path("/data/content/.rd_cache.json")
                is_first_sync = not env_timestamp and not cache_file.exists()
                
                if is_first_sync and len(new_filenames) > 10:
                    # Full regeneration for first sync with many files
                    sync_status["message"] = f"First sync: doing full site regeneration for {len(new_filenames)} raindrops..."
                    logger.info(f"First sync with {len(new_filenames)} files - doing full regeneration")
                    generator = SiteGenerator()
                    generator.generate_site()
                    result = {
                        "status": "success",
                        "message": f"First sync: regenerated entire site with {len(new_filenames)} new raindrops"
                    }
                else:
                    # Incremental regeneration for small updates
                    sync_status["message"] = f"Regenerating {len(new_filenames)} raindrop pages..."
                    generator = SiteGenerator()
                    
                    for i, filename in enumerate(new_filenames, 1):
                        sync_status["message"] = f"Regenerating {i}/{len(new_filenames)}: {filename[:30]}..."
                        logger.info(f"Regenerating for: {filename}")
                        generator.incremental_regenerate_post(filename, 'raindrops')
                    
                    result = {
                        "status": "success",
                        "message": f"Synced {len(new_filenames)} new raindrops and regenerated pages"
                    }
            else:
                logger.info("No new raindrops found - skipping regeneration")
                result = {
                    "status": "success",
                    "message": "No new raindrops to sync"
                }
            
            sync_status["running"] = False
            sync_status["message"] = result["message"]
            return result
            
        except Exception as e:
            sync_status["running"] = False
            sync_status["message"] = f"Error: {str(e)}"
            raise
    
    try:
        # Check if already running
        if sync_status["running"]:
            return JSONResponse(content={
                "status": "running",
                "message": sync_status["message"]
            })
        
        # Start async execution in background
        async def run_sync():
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, do_sync)
        
        asyncio.create_task(run_sync())
        
        return JSONResponse(content={
            "status": "started",
            "message": "Raindrop sync started. Check /api/sync-status for progress."
        })
    except Exception as e:
        sync_status["running"] = False
        sync_status["message"] = f"Error: {str(e)}"
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@app.get("/api/sync-status")
async def get_sync_status():
    """Get current raindrop sync status"""
    return JSONResponse(content=sync_status)

@app.get("/api/regenerate")
async def regenerate_site():
    """Regenerate the static site"""
    import asyncio
    
    def do_regenerate():
        generator = SiteGenerator()
        generator.generate_site()
        return {
            "status": "success", 
            "message": "Site regenerated successfully",
            "theme": generator.theme
        }
    
    try:
        # Run regeneration in a thread pool to avoid blocking other requests
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, do_regenerate)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")

@app.get("/api/admin-status")
async def get_admin_status(request: Request):
    """Check if current user is authenticated as admin"""
    admin_password = get_admin_password()
    
    # If no admin password is set, allow access without authentication
    if not admin_password:
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
    admin_password = get_admin_password()
    
    # Check authentication (same logic as admin-status API)
    if admin_password and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    
    # Load the post file
    import frontmatter
    blog_dir = root_dir / "content" / "blog"
    post_file = blog_dir / filename
    
    if not post_file.exists():
        raise HTTPException(status_code=404, detail=f"Post not found: {filename}")
    
    try:
        with open(post_file, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Extract metadata
        title = post.metadata.get('title', '')
        date = post.metadata.get('date', '')
        category = post.metadata.get('category', 'General')
        post_type = post.metadata.get('type', 'blog')
        content = post.content
        
        # Create the edit form HTML
        edit_form_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Edit Post - {title}</title>
            <style>
                body {{ 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0; 
                    background: #f5f6fa; 
                    line-height: 1.6;
                }}
                .header {{
                    background: #2c3e50;
                    color: white;
                    padding: 1rem 2rem;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 1.5rem;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 2rem auto;
                    background: white;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    overflow: hidden;
                }}
                .form-section {{
                    padding: 2rem;
                }}
                .form-grid {{
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 1rem;
                    margin-bottom: 1.5rem;
                }}
                .form-group {{
                    margin-bottom: 1.5rem;
                }}
                .form-group.full-width {{
                    grid-column: 1 / -1;
                }}
                label {{
                    display: block;
                    margin-bottom: 0.5rem;
                    font-weight: 600;
                    color: #2c3e50;
                }}
                input, textarea, select {{
                    width: 100%;
                    padding: 0.75rem;
                    border: 2px solid #e1e8ed;
                    border-radius: 4px;
                    font-size: 1rem;
                    transition: border-color 0.2s;
                    font-family: inherit;
                    box-sizing: border-box;
                }}
                input:focus, textarea:focus, select:focus {{
                    outline: none;
                    border-color: #3498db;
                }}
                #content {{
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                    min-height: 400px;
                    resize: vertical;
                }}
                .button-group {{
                    display: flex;
                    gap: 1rem;
                    justify-content: flex-end;
                    padding: 1.5rem 2rem;
                    background: #f8f9fa;
                    border-top: 1px solid #e1e8ed;
                }}
                .btn {{
                    padding: 0.75rem 1.5rem;
                    border: none;
                    border-radius: 4px;
                    font-size: 1rem;
                    cursor: pointer;
                    text-decoration: none;
                    display: inline-block;
                    transition: all 0.2s;
                    font-weight: 500;
                }}
                .btn-primary {{
                    background: #3498db;
                    color: white;
                }}
                .btn-primary:hover {{
                    background: #2980b9;
                }}
                .btn-secondary {{
                    background: #95a5a6;
                    color: white;
                }}
                .btn-secondary:hover {{
                    background: #7f8c8d;
                }}
                .btn-success {{
                    background: #27ae60;
                    color: white;
                }}
                .btn-success:hover {{
                    background: #229954;
                }}
                .status-message {{
                    padding: 1rem;
                    margin: 1rem 0;
                    border-radius: 4px;
                    display: none;
                }}
                .status-success {{
                    background: #d4edda;
                    color: #155724;
                    border: 1px solid #c3e6cb;
                }}
                .status-error {{
                    background: #f8d7da;
                    color: #721c24;
                    border: 1px solid #f5c6cb;
                }}
                @media (max-width: 768px) {{
                    .form-grid {{
                        grid-template-columns: 1fr;
                    }}
                    .container {{
                        margin: 1rem;
                    }}
                    .header {{
                        padding: 1rem;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>✏️ Edit Post: {title}</h1>
            </div>
            
            <div class="container">
                <form id="editForm" class="form-section">
                    <div id="statusMessage" class="status-message"></div>
                    
                    <div class="form-grid">
                        <div class="form-group">
                            <label for="title">Post Title</label>
                            <input type="text" id="title" name="title" value="{title}" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="date">Date</label>
                            <input type="date" id="date" name="date" value="{date}" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="category">Category</label>
                            <input type="text" id="category" name="category" value="{category}">
                        </div>
                        
                        <div class="form-group">
                            <label for="type">Type</label>
                            <select id="type" name="type">
                                <option value="blog" {"selected" if post_type == "blog" else ""}>Blog Post</option>
                                <option value="page" {"selected" if post_type == "page" else ""}>Page</option>
                            </select>
                        </div>
                    </div>
                    
                    <div class="form-group full-width">
                        <label for="content">Content (Markdown)</label>
                        <textarea id="content" name="content" placeholder="Write your post content in Markdown...">{content}</textarea>
                    </div>
                </form>
                
                <div class="button-group">
                    <a href="/blog/" class="btn btn-secondary">Cancel</a>
                    <button type="button" class="btn btn-primary" onclick="previewPost()">Preview</button>
                    <button type="button" class="btn btn-success" onclick="savePost()">Save Post</button>
                </div>
            </div>
            
            <script>
                async function savePost() {{
                    const form = document.getElementById('editForm');
                    const statusMessage = document.getElementById('statusMessage');
                    
                    // Validate form
                    const title = document.getElementById('title').value.trim();
                    const date = document.getElementById('date').value;
                    const content = document.getElementById('content').value.trim();
                    
                    if (!title) {{
                        statusMessage.className = 'status-message status-error';
                        statusMessage.textContent = '✗ Please enter a post title';
                        statusMessage.style.display = 'block';
                        return;
                    }}
                    
                    if (!date) {{
                        statusMessage.className = 'status-message status-error';
                        statusMessage.textContent = '✗ Please select a date';
                        statusMessage.style.display = 'block';
                        return;
                    }}
                    
                    if (!content) {{
                        statusMessage.className = 'status-message status-error';
                        statusMessage.textContent = '✗ Please enter some content';
                        statusMessage.style.display = 'block';
                        return;
                    }}
                    
                    const formData = new FormData(form);
                    
                    // Show loading state
                    const saveBtn = event.target;
                    const originalText = saveBtn.textContent;
                    saveBtn.textContent = 'Saving...';
                    saveBtn.disabled = true;
                    
                    try {{
                        const response = await fetch('/admin/edit-post/{filename}', {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        const result = await response.json();
                        
                        if (response.ok) {{
                            statusMessage.className = 'status-message status-success';
                            statusMessage.textContent = '✓ Post saved successfully!';
                            statusMessage.style.display = 'block';
                            
                            // Auto-hide success message after 3 seconds
                            setTimeout(() => {{
                                statusMessage.style.display = 'none';
                            }}, 3000);
                        }} else {{
                            throw new Error(result.detail || 'Save failed');
                        }}
                    }} catch (error) {{
                        statusMessage.className = 'status-message status-error';
                        statusMessage.textContent = '✗ Error: ' + error.message;
                        statusMessage.style.display = 'block';
                    }} finally {{
                        // Restore button state
                        saveBtn.textContent = originalText;
                        saveBtn.disabled = false;
                    }}
                }}
                
                function previewPost() {{
                    const content = document.getElementById('content').value;
                    const title = document.getElementById('title').value;
                    const date = document.getElementById('date').value;
                    const category = document.getElementById('category').value;
                    const type = document.getElementById('type').value;
                    
                    if (!content.trim()) {{
                        alert('Please enter some content to preview');
                        return;
                    }}
                    
                    // Create a form and submit to preview endpoint
                    const form = document.createElement('form');
                    form.method = 'POST';
                    form.action = '/admin/preview-post';
                    form.target = '_blank';
                    
                    const titleInput = document.createElement('input');
                    titleInput.type = 'hidden';
                    titleInput.name = 'title';
                    titleInput.value = title;
                    form.appendChild(titleInput);
                    
                    const contentInput = document.createElement('input');
                    contentInput.type = 'hidden';
                    contentInput.name = 'content';
                    contentInput.value = content;
                    form.appendChild(contentInput);
                    
                    const dateInput = document.createElement('input');
                    dateInput.type = 'hidden';
                    dateInput.name = 'date';
                    dateInput.value = date;
                    form.appendChild(dateInput);
                    
                    const categoryInput = document.createElement('input');
                    categoryInput.type = 'hidden';
                    categoryInput.name = 'category';
                    categoryInput.value = category;
                    form.appendChild(categoryInput);
                    
                    const typeInput = document.createElement('input');
                    typeInput.type = 'hidden';
                    typeInput.name = 'type';
                    typeInput.value = type;
                    form.appendChild(typeInput);
                    
                    // Add filename from current URL
                    const filename = window.location.pathname.split('/').pop();
                    const filenameInput = document.createElement('input');
                    filenameInput.type = 'hidden';
                    filenameInput.name = 'filename';
                    filenameInput.value = filename;
                    form.appendChild(filenameInput);
                    
                    document.body.appendChild(form);
                    form.submit();
                    document.body.removeChild(form);
                }}
                
                // Auto-save functionality (optional)
                let autoSaveTimeout;
                function scheduleAutoSave() {{
                    clearTimeout(autoSaveTimeout);
                    autoSaveTimeout = setTimeout(() => {{
                        // Could implement auto-save to drafts here
                        console.log('Auto-save could be triggered here');
                    }}, 30000); // 30 seconds
                }}
                
                // Add event listeners for auto-save
                document.getElementById('content').addEventListener('input', scheduleAutoSave);
                document.getElementById('title').addEventListener('input', scheduleAutoSave);
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=edit_form_html)
        
    except Exception as e:
        logger.error(f"Error loading post {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading post: {str(e)}")

@app.post("/admin/edit-post/{filename}")
async def save_edited_post(filename: str, request: Request, title: str = Form(...), 
                          date: str = Form(...), category: str = Form(...), 
                          type: str = Form(...), content: str = Form(...)):
    """Save edited post to file and regenerate site"""
    admin_password = get_admin_password()
    
    # Check authentication (same logic as admin-status API)
    if admin_password and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    import frontmatter
    from .generator import SiteGenerator
    
    blog_dir = root_dir / "content" / "blog"
    post_file = blog_dir / filename
    
    if not post_file.exists():
        raise HTTPException(status_code=404, detail=f"Post not found: {filename}")
    
    try:
        # Create the updated post with frontmatter
        post = frontmatter.Post(content)
        post.metadata = {
            'title': title.strip(),
            'date': date,
            'category': category.strip() if category.strip() else 'General',
            'type': type
        }
        
        # Write the updated post back to file
        with open(post_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
            f.flush()
            os.fsync(f.fileno())  # Force disk write
        
        logger.info(f"Post updated successfully: {filename}")
        
        # Regenerate affected pages
        try:
            generator = SiteGenerator()
            generator.incremental_regenerate_post(filename, 'blog')
            logger.info(f"Site regenerated after editing: {filename}")
        except Exception as regen_error:
            logger.error(f"Site regeneration failed after editing {filename}: {regen_error}")
            # Don't fail the save operation if regeneration fails
        
        return JSONResponse(content={
            "status": "success",
            "message": "Post updated successfully",
            "filename": filename
        })
        
    except Exception as e:
        logger.error(f"Error saving post {filename}: {e}")
        raise HTTPException(status_code=500, detail=f"Error saving post: {str(e)}")

@app.post("/admin/preview-markdown")
async def preview_markdown(request: Request, content: str = Form(...)):
    """Convert markdown content to HTML for preview"""
    admin_password = get_admin_password()
    
    # Check authentication (same logic as admin-status API)
    if admin_password and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        import markdown
        from markdown.extensions import codehilite, tables, toc
        
        # Configure markdown with extensions
        md = markdown.Markdown(extensions=[
            'codehilite',
            'tables', 
            'toc',
            'fenced_code',
            'nl2br'
        ])
        
        # Convert markdown to HTML
        html = md.convert(content)
        
        return JSONResponse(content={
            "status": "success",
            "html": html
        })
        
    except Exception as e:
        logger.error(f"Error rendering markdown preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")

@app.post("/admin/preview-post")
async def preview_post_html(request: Request, title: str = Form(...), content: str = Form(...), 
                           date: str = Form(...), category: str = Form(...), 
                           type: str = Form(...), filename: str = Form(...)):
    """Render complete preview page with HTML"""
    admin_password = get_admin_password()
    
    # Check authentication (same logic as admin-status API)
    if admin_password and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        import markdown
        
        # Configure markdown with extensions
        md = markdown.Markdown(extensions=[
            'codehilite',
            'tables', 
            'toc',
            'fenced_code',
            'nl2br'
        ])
        
        # Convert markdown to HTML
        html_content = md.convert(content)
        
        # Create complete HTML page
        preview_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Preview: {title}</title>
            <style>
                body {{ 
                    font-family: Georgia, serif; 
                    max-width: 800px; 
                    margin: 2rem auto; 
                    padding: 0 2rem; 
                    line-height: 1.6; 
                    color: #333;
                }}
                h1, h2, h3, h4, h5, h6 {{ 
                    color: #2c3e50; 
                    margin-top: 2rem; 
                    margin-bottom: 1rem; 
                }}
                h1 {{ font-size: 2.5rem; border-bottom: 2px solid #3498db; padding-bottom: 0.5rem; }}
                h2 {{ font-size: 2rem; }}
                h3 {{ font-size: 1.5rem; }}
                p {{ margin-bottom: 1rem; }}
                pre {{ 
                    background: #f8f9fa; 
                    padding: 1rem; 
                    border-radius: 4px; 
                    overflow-x: auto; 
                    border: 1px solid #e9ecef;
                }}
                code {{
                    background: #f8f9fa;
                    padding: 0.2rem 0.4rem;
                    border-radius: 3px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                }}
                blockquote {{ 
                    border-left: 4px solid #3498db; 
                    margin: 1rem 0; 
                    padding-left: 1rem; 
                    color: #666; 
                    font-style: italic;
                }}
                a {{ color: #3498db; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                ul, ol {{ margin-bottom: 1rem; }}
                li {{ margin-bottom: 0.5rem; }}
                img {{ max-width: 100%; height: auto; }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 1rem 0; 
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 0.5rem; 
                    text-align: left; 
                }}
                th {{ background: #f8f9fa; font-weight: bold; }}
                .preview-header {{
                    background: #e8f4f8;
                    padding: 1rem;
                    margin: -2rem -2rem 2rem -2rem;
                    border-bottom: 1px solid #3498db;
                }}
                .preview-actions {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: white;
                    padding: 10px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    z-index: 1000;
                }}
                .btn {{
                    padding: 8px 16px;
                    margin: 0 5px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .btn-success {{
                    background: #27ae60;
                    color: white;
                }}
                .btn-success:hover {{
                    background: #229954;
                }}
                .btn-secondary {{
                    background: #95a5a6;
                    color: white;
                }}
                .btn-secondary:hover {{
                    background: #7f8c8d;
                }}
            </style>
        </head>
        <body>
            <div class="preview-actions">
                <button class="btn btn-success" onclick="saveAndClose()">💾 Save & Close</button>
                <button class="btn btn-secondary" onclick="window.close()">✕ Close</button>
            </div>
            
            <div class="preview-header">
                <h1 style="margin: 0; border: none; font-size: 1.5rem;">📝 Preview: {title}</h1>
                <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">This is how your post will appear on the blog</p>
            </div>
            <h1>{title}</h1>
            {html_content}
            
            <script>
                // Form data passed from the edit page
                const postData = {{
                    title: `{title}`,
                    content: `{content.replace('`', '\\`').replace('$', '\\$')}`,
                    date: `{date}`,
                    category: `{category}`,
                    type: `{type}`,
                    filename: `{filename}`
                }};
                
                async function saveAndClose() {{
                    const saveBtn = event.target;
                    const originalText = saveBtn.textContent;
                    saveBtn.textContent = '💾 Saving...';
                    saveBtn.disabled = true;
                    
                    try {{
                        // Create form data with the current post data
                        const formData = new FormData();
                        formData.append('title', postData.title);
                        formData.append('content', postData.content);
                        formData.append('date', postData.date);
                        formData.append('category', postData.category);
                        formData.append('type', postData.type);
                        
                        const response = await fetch(`/admin/edit-post/${{postData.filename}}`, {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        const result = await response.json();
                        
                        if (response.ok) {{
                            alert('✓ Post saved successfully!');
                            window.close();
                        }} else {{
                            throw new Error(result.detail || 'Save failed');
                        }}
                    }} catch (error) {{
                        alert('✗ Error saving: ' + error.message);
                    }} finally {{
                        saveBtn.textContent = originalText;
                        saveBtn.disabled = false;
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=preview_html)
        
    except Exception as e:
        logger.error(f"Error rendering post preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")

@app.get("/admin/new-post")
async def new_post_page(request: Request):
    """Serve new post creation page with form"""
    admin_password = get_admin_password()
    
    # Check authentication (same logic as admin-status API)
    if admin_password and not is_admin_authenticated(request):
        return RedirectResponse(url="/admin", status_code=302)
    
    # Get current date for default
    from datetime import datetime
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    # Create the new post form HTML
    new_post_form_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Create New Post - Salas Blog</title>
        <style>
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0; 
                background: #f5f6fa; 
                line-height: 1.6;
            }}
            .header {{
                background: #27ae60;
                color: white;
                padding: 1rem 2rem;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .header h1 {{
                margin: 0;
                font-size: 1.5rem;
            }}
            .container {{
                max-width: 1200px;
                margin: 2rem auto;
                background: white;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .form-section {{
                padding: 2rem;
            }}
            .form-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 1rem;
                margin-bottom: 1.5rem;
            }}
            .form-group {{
                margin-bottom: 1.5rem;
            }}
            .form-group.full-width {{
                grid-column: 1 / -1;
            }}
            label {{
                display: block;
                margin-bottom: 0.5rem;
                font-weight: 600;
                color: #2c3e50;
            }}
            input, textarea, select {{
                width: 100%;
                padding: 0.75rem;
                border: 2px solid #e1e8ed;
                border-radius: 4px;
                font-size: 1rem;
                transition: border-color 0.2s;
                font-family: inherit;
                box-sizing: border-box;
            }}
            input:focus, textarea:focus, select:focus {{
                outline: none;
                border-color: #27ae60;
            }}
            #content {{
                font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                min-height: 400px;
                resize: vertical;
            }}
            .button-group {{
                display: flex;
                gap: 1rem;
                justify-content: flex-end;
                padding: 1.5rem 2rem;
                background: #f8f9fa;
                border-top: 1px solid #e1e8ed;
            }}
            .btn {{
                padding: 0.75rem 1.5rem;
                border: none;
                border-radius: 4px;
                font-size: 1rem;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                transition: all 0.2s;
                font-weight: 500;
            }}
            .btn-primary {{
                background: #3498db;
                color: white;
            }}
            .btn-primary:hover {{
                background: #2980b9;
            }}
            .btn-secondary {{
                background: #95a5a6;
                color: white;
            }}
            .btn-secondary:hover {{
                background: #7f8c8d;
            }}
            .btn-success {{
                background: #27ae60;
                color: white;
            }}
            .btn-success:hover {{
                background: #229954;
            }}
            .status-message {{
                padding: 1rem;
                margin: 1rem 0;
                border-radius: 4px;
                display: none;
            }}
            .status-success {{
                background: #d4edda;
                color: #155724;
                border: 1px solid #c3e6cb;
            }}
            .status-error {{
                background: #f8d7da;
                color: #721c24;
                border: 1px solid #f5c6cb;
            }}
            .help-text {{
                font-size: 0.875rem;
                color: #666;
                margin-top: 0.25rem;
            }}
            @media (max-width: 768px) {{
                .form-grid {{
                    grid-template-columns: 1fr;
                }}
                .container {{
                    margin: 1rem;
                }}
                .header {{
                    padding: 1rem;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>✨ Create New Post</h1>
        </div>
        
        <div class="container">
            <form id="newPostForm" class="form-section">
                <div id="statusMessage" class="status-message"></div>
                
                <div class="form-grid">
                    <div class="form-group">
                        <label for="title">Post Title *</label>
                        <input type="text" id="title" name="title" required placeholder="Enter your post title">
                        <div class="help-text">This will be used to generate the filename</div>
                    </div>
                    
                    <div class="form-group">
                        <label for="date">Date *</label>
                        <input type="date" id="date" name="date" value="{current_date}" required>
                    </div>
                    
                    <div class="form-group">
                        <label for="category">Category</label>
                        <input type="text" id="category" name="category" value="General" placeholder="General">
                    </div>
                    
                    <div class="form-group">
                        <label for="type">Type</label>
                        <select id="type" name="type">
                            <option value="blog" selected>Blog Post</option>
                            <option value="page">Page</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group full-width">
                    <label for="content">Content (Markdown) *</label>
                    <textarea id="content" name="content" placeholder="Write your post content in Markdown..." required></textarea>
                    <div class="help-text">Use Markdown syntax for formatting. You can preview before saving.</div>
                </div>
            </form>
            
            <div class="button-group">
                <a href="/blog/" class="btn btn-secondary">Cancel</a>
                <button type="button" class="btn btn-primary" onclick="previewPost()">Preview</button>
                <button type="button" class="btn btn-success" onclick="createPost()">Create Post</button>
            </div>
        </div>
        
        <script>
            async function createPost() {{
                const form = document.getElementById('newPostForm');
                const statusMessage = document.getElementById('statusMessage');
                
                // Validate form
                const title = document.getElementById('title').value.trim();
                const date = document.getElementById('date').value;
                const content = document.getElementById('content').value.trim();
                
                if (!title) {{
                    statusMessage.className = 'status-message status-error';
                    statusMessage.textContent = '✗ Please enter a post title';
                    statusMessage.style.display = 'block';
                    return;
                }}
                
                if (!date) {{
                    statusMessage.className = 'status-message status-error';
                    statusMessage.textContent = '✗ Please select a date';
                    statusMessage.style.display = 'block';
                    return;
                }}
                
                if (!content) {{
                    statusMessage.className = 'status-message status-error';
                    statusMessage.textContent = '✗ Please enter some content';
                    statusMessage.style.display = 'block';
                    return;
                }}
                
                const formData = new FormData(form);
                
                // Show loading state
                const createBtn = event.target;
                const originalText = createBtn.textContent;
                createBtn.textContent = 'Creating...';
                createBtn.disabled = true;
                
                try {{
                    const response = await fetch('/admin/new-post', {{
                        method: 'POST',
                        body: formData
                    }});
                    
                    const result = await response.json();
                    
                    if (response.ok) {{
                        statusMessage.className = 'status-message status-success';
                        statusMessage.textContent = `✓ Post created successfully! Filename: ${{result.filename}}`;
                        statusMessage.style.display = 'block';
                        
                        // Clear form
                        form.reset();
                        document.getElementById('date').value = '{current_date}';
                        
                        // Auto-hide success message and redirect after 3 seconds
                        setTimeout(() => {{
                            window.location.href = `/blog/${{result.filename.replace('.md', '.html')}}`;
                        }}, 2000);
                    }} else {{
                        throw new Error(result.detail || 'Creation failed');
                    }}
                }} catch (error) {{
                    statusMessage.className = 'status-message status-error';
                    statusMessage.textContent = '✗ Error: ' + error.message;
                    statusMessage.style.display = 'block';
                }} finally {{
                    // Restore button state
                    createBtn.textContent = originalText;
                    createBtn.disabled = false;
                }}
            }}
            
            function previewPost() {{
                const content = document.getElementById('content').value;
                const title = document.getElementById('title').value;
                const date = document.getElementById('date').value;
                const category = document.getElementById('category').value;
                const type = document.getElementById('type').value;
                
                if (!content.trim()) {{
                    alert('Please enter some content to preview');
                    return;
                }}
                
                if (!title.trim()) {{
                    alert('Please enter a title to preview');
                    return;
                }}
                
                // Create a form and submit to preview endpoint
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = '/admin/preview-new-post';
                form.target = '_blank';
                
                const titleInput = document.createElement('input');
                titleInput.type = 'hidden';
                titleInput.name = 'title';
                titleInput.value = title;
                form.appendChild(titleInput);
                
                const contentInput = document.createElement('input');
                contentInput.type = 'hidden';
                contentInput.name = 'content';
                contentInput.value = content;
                form.appendChild(contentInput);
                
                const dateInput = document.createElement('input');
                dateInput.type = 'hidden';
                dateInput.name = 'date';
                dateInput.value = date;
                form.appendChild(dateInput);
                
                const categoryInput = document.createElement('input');
                categoryInput.type = 'hidden';
                categoryInput.name = 'category';
                categoryInput.value = category;
                form.appendChild(categoryInput);
                
                const typeInput = document.createElement('input');
                typeInput.type = 'hidden';
                typeInput.name = 'type';
                typeInput.value = type;
                form.appendChild(typeInput);
                
                document.body.appendChild(form);
                form.submit();
                document.body.removeChild(form);
            }}
            
            // Auto-generate filename preview
            function updateFilenamePreview() {{
                const title = document.getElementById('title').value.trim();
                const date = document.getElementById('date').value;
                const helpText = document.querySelector('.help-text');
                
                if (title && date) {{
                    // Generate filename
                    const safeTitle = title.toLowerCase()
                        .replace(/[^\\w\\s-]/g, '')  // Remove special chars
                        .replace(/[-\\s]+/g, '-')    // Replace spaces/dashes with single dash
                        .replace(/^-+|-+$/g, '');    // Remove leading/trailing dashes
                    
                    const filename = `${{date}}-${{safeTitle}}.md`;
                    helpText.textContent = `Filename will be: ${{filename}}`;
                }} else {{
                    helpText.textContent = 'This will be used to generate the filename';
                }}
            }}
            
            // Add event listeners for filename preview
            document.getElementById('title').addEventListener('input', updateFilenamePreview);
            document.getElementById('date').addEventListener('change', updateFilenamePreview);
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=new_post_form_html)

@app.post("/admin/new-post")
async def create_new_post(request: Request, title: str = Form(...), 
                         date: str = Form(...), category: str = Form(...), 
                         type: str = Form(...), content: str = Form(...)):
    """Create a new blog post with generated filename"""
    admin_password = get_admin_password()
    
    # Check authentication (same logic as admin-status API)
    if admin_password and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    import frontmatter
    import re
    from datetime import datetime
    from .generator import SiteGenerator
    
    try:
        # Generate filename from title and date
        def create_filename_from_title(title: str, date: str) -> str:
            """Create safe filename from post title and date."""
            # Remove special characters and convert to lowercase
            safe_title = re.sub(r'[^\w\s-]', '', title.lower())
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            safe_title = safe_title.strip('-')  # Remove leading/trailing dashes
            
            return f"{date}-{safe_title}.md"
        
        filename = create_filename_from_title(title.strip(), date)
        
        # Check if file already exists
        blog_dir = root_dir / "content" / "blog"
        blog_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
        post_file = blog_dir / filename
        
        if post_file.exists():
            raise HTTPException(status_code=400, detail=f"A post with filename '{filename}' already exists")
        
        # Create the new post with frontmatter
        post = frontmatter.Post(content.strip())
        post.metadata = {
            'title': title.strip(),
            'date': date,
            'category': category.strip() if category.strip() else 'General',
            'type': type
        }
        
        # Write the new post to file
        with open(post_file, 'w', encoding='utf-8') as f:
            f.write(frontmatter.dumps(post))
            f.flush()
            os.fsync(f.fileno())  # Force disk write
        
        logger.info(f"New post created successfully: {filename}")
        
        # Regenerate affected pages
        try:
            generator = SiteGenerator()
            generator.incremental_regenerate_post(filename, 'blog')
            logger.info(f"Site regenerated after creating: {filename}")
        except Exception as regen_error:
            logger.error(f"Site regeneration failed after creating {filename}: {regen_error}")
            # Don't fail the creation operation if regeneration fails
        
        return JSONResponse(content={
            "status": "success",
            "message": "Post created successfully",
            "filename": filename,
            "url": f"/blog/{filename.replace('.md', '.html')}"
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions (like file exists)
        raise
    except Exception as e:
        logger.error(f"Error creating new post: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating post: {str(e)}")

@app.post("/admin/preview-new-post")
async def preview_new_post_html(request: Request, title: str = Form(...), content: str = Form(...), 
                               date: str = Form(...), category: str = Form(...), 
                               type: str = Form(...)):
    """Render complete preview page for new post with HTML"""
    admin_password = get_admin_password()
    
    # Check authentication (same logic as admin-status API)
    if admin_password and not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    try:
        import markdown
        import re
        
        # Configure markdown with extensions
        md = markdown.Markdown(extensions=[
            'codehilite',
            'tables', 
            'toc',
            'fenced_code',
            'nl2br'
        ])
        
        # Convert markdown to HTML
        html_content = md.convert(content)
        
        # Generate filename preview
        def create_filename_from_title(title: str, date: str) -> str:
            safe_title = re.sub(r'[^\w\s-]', '', title.lower())
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            safe_title = safe_title.strip('-')
            return f"{date}-{safe_title}.md"
        
        filename = create_filename_from_title(title.strip(), date)
        
        # Create complete HTML page
        preview_html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Preview: {title}</title>
            <style>
                body {{ 
                    font-family: Georgia, serif; 
                    max-width: 800px; 
                    margin: 2rem auto; 
                    padding: 0 2rem; 
                    line-height: 1.6; 
                    color: #333;
                }}
                h1, h2, h3, h4, h5, h6 {{ 
                    color: #2c3e50; 
                    margin-top: 2rem; 
                    margin-bottom: 1rem; 
                }}
                h1 {{ font-size: 2.5rem; border-bottom: 2px solid #27ae60; padding-bottom: 0.5rem; }}
                h2 {{ font-size: 2rem; }}
                h3 {{ font-size: 1.5rem; }}
                p {{ margin-bottom: 1rem; }}
                pre {{ 
                    background: #f8f9fa; 
                    padding: 1rem; 
                    border-radius: 4px; 
                    overflow-x: auto; 
                    border: 1px solid #e9ecef;
                }}
                code {{
                    background: #f8f9fa;
                    padding: 0.2rem 0.4rem;
                    border-radius: 3px;
                    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
                }}
                blockquote {{ 
                    border-left: 4px solid #27ae60; 
                    margin: 1rem 0; 
                    padding-left: 1rem; 
                    color: #666; 
                    font-style: italic;
                }}
                a {{ color: #27ae60; text-decoration: none; }}
                a:hover {{ text-decoration: underline; }}
                ul, ol {{ margin-bottom: 1rem; }}
                li {{ margin-bottom: 0.5rem; }}
                img {{ max-width: 100%; height: auto; }}
                table {{ 
                    border-collapse: collapse; 
                    width: 100%; 
                    margin: 1rem 0; 
                }}
                th, td {{ 
                    border: 1px solid #ddd; 
                    padding: 0.5rem; 
                    text-align: left; 
                }}
                th {{ background: #f8f9fa; font-weight: bold; }}
                .preview-header {{
                    background: #e8f5e8;
                    padding: 1rem;
                    margin: -2rem -2rem 2rem -2rem;
                    border-bottom: 1px solid #27ae60;
                }}
                .preview-actions {{
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    background: white;
                    padding: 10px;
                    border-radius: 8px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
                    z-index: 1000;
                }}
                .btn {{
                    padding: 8px 16px;
                    margin: 0 5px;
                    border: none;
                    border-radius: 4px;
                    cursor: pointer;
                    font-size: 14px;
                    text-decoration: none;
                    display: inline-block;
                }}
                .btn-success {{
                    background: #27ae60;
                    color: white;
                }}
                .btn-success:hover {{
                    background: #219a52;
                }}
                .btn-secondary {{
                    background: #95a5a6;
                    color: white;
                }}
                .btn-secondary:hover {{
                    background: #7f8c8d;
                }}
                .filename-info {{
                    background: #f8f9fa;
                    padding: 0.5rem;
                    border-radius: 4px;
                    font-size: 0.875rem;
                    color: #666;
                    margin-bottom: 1rem;
                }}
            </style>
        </head>
        <body>
            <div class="preview-actions">
                <button class="btn btn-success" onclick="createAndClose()">✨ Create & View</button>
                <button class="btn btn-secondary" onclick="window.close()">✕ Close</button>
            </div>
            
            <div class="preview-header">
                <h1 style="margin: 0; border: none; font-size: 1.5rem;">📝 Preview: {title}</h1>
                <p style="margin: 0.5rem 0 0 0; color: #666; font-size: 0.9rem;">This is how your new post will appear on the blog</p>
                <div class="filename-info">Filename: {filename}</div>
            </div>
            <h1>{title}</h1>
            {html_content}
            
            <script>
                // Form data passed from the new post page
                const postData = {{
                    title: `{title}`,
                    content: `{content.replace('`', '\\`').replace('$', '\\$')}`,
                    date: `{date}`,
                    category: `{category}`,
                    type: `{type}`
                }};
                
                async function createAndClose() {{
                    const createBtn = event.target;
                    const originalText = createBtn.textContent;
                    createBtn.textContent = '✨ Creating...';
                    createBtn.disabled = true;
                    
                    try {{
                        // Create form data with the current post data
                        const formData = new FormData();
                        formData.append('title', postData.title);
                        formData.append('content', postData.content);
                        formData.append('date', postData.date);
                        formData.append('category', postData.category);
                        formData.append('type', postData.type);
                        
                        const response = await fetch('/admin/new-post', {{
                            method: 'POST',
                            body: formData
                        }});
                        
                        const result = await response.json();
                        
                        if (response.ok) {{
                            alert('✓ Post created successfully!');
                            // Navigate to the new post
                            window.location.href = result.url;
                        }} else {{
                            throw new Error(result.detail || 'Creation failed');
                        }}
                    }} catch (error) {{
                        alert('✗ Error creating: ' + error.message);
                    }} finally {{
                        createBtn.textContent = originalText;
                        createBtn.disabled = false;
                    }}
                }}
            </script>
        </body>
        </html>
        """
        
        return HTMLResponse(content=preview_html)
        
    except Exception as e:
        logger.error(f"Error rendering new post preview: {e}")
        raise HTTPException(status_code=500, detail=f"Preview error: {str(e)}")

@app.post("/admin/delete-post/{filename}")
async def delete_post_endpoint(filename: str, request: Request):
    """Delete a blog post (placeholder for Phase 2)"""
    if not is_admin_authenticated(request):
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # TODO: Phase 2 - Implement actual post deletion
    # For now, return a placeholder response
    return JSONResponse(content={
        "status": "error",
        "detail": f"Post deletion not yet implemented. Would delete: {filename}"
    }, status_code=501)

@app.get("/rsd.xml")
async def serve_rsd(request: Request):
    """Serve RSD (Really Simple Discovery) XML for blog API autodiscovery"""
    # Get the base URL from the request
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    
    # Get API type from environment variable (default to metaweblog)
    api_type = os.getenv("RSD_API_TYPE", "metaweblog").lower()
    
    # Set API name and documentation based on type
    if api_type == "blogger":
        api_name = "Blogger"
        docs_url = "http://plant.blogger.com/api/index.html"
    else:
        # Default to MetaWeblog API
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
    logger.info("GET request received at /xmlrpc endpoint")
    return Response(
        content="XML-RPC endpoint ready. Use POST with XML-RPC payload.",
        media_type="text/plain"
    )

@app.post("/xmlrpc")
async def xmlrpc_endpoint(request: Request):
    """XML-RPC endpoint for Blogger API"""
    try:
        body = await request.body()
        logger.info(f"Received XML-RPC request, body length: {len(body)}")
        logger.info(f"Raw XML-RPC request body: {body.decode('utf-8')}")
        
        # Parse XML-RPC request
        root = ET.fromstring(body.decode('utf-8'))
        method_name = root.find('.//methodName').text
        logger.info(f"XML-RPC method: {method_name}")
        params = []
        
        # Extract parameters
        param_nodes = root.findall('.//param/value')
        logger.info(f"Found {len(param_nodes)} parameters")
        for i, param in enumerate(param_nodes):
            logger.info(f"Processing parameter {i+1}: {ET.tostring(param, encoding='unicode')}")
            # Handle different value types
            if param.find('string') is not None:
                value = param.find('string').text or ""
                params.append(value)
                logger.info(f"Parameter {i+1} (string): {repr(value)}")
            elif param.find('boolean') is not None:
                value = param.find('boolean').text == '1'
                params.append(value)
                logger.info(f"Parameter {i+1} (boolean): {value}")
            elif param.find('int') is not None:
                value = int(param.find('int').text)
                params.append(value)
                logger.info(f"Parameter {i+1} (int): {value}")
            elif param.find('i4') is not None:
                value = int(param.find('i4').text)
                params.append(value)
                logger.info(f"Parameter {i+1} (i4): {value}")
            elif param.find('struct') is not None:
                # Parse struct (dictionary) for structured content
                struct_elem = param.find('struct')
                struct_dict = {}
                for member in struct_elem.findall('member'):
                    name_elem = member.find('name')
                    value_elem = member.find('value')
                    if name_elem is not None and value_elem is not None:
                        key = name_elem.text
                        # Get the value from the value element
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
                params.append(struct_dict)
                logger.info(f"Parameter {i+1} (struct): {struct_dict}")
            else:
                value = param.text or ""
                params.append(value)
                logger.info(f"Parameter {i+1} (raw): {repr(value)}")
        
        # Handle Blogger API methods
        api = BloggerAPI()
        logger.info(f"Calling {method_name} with {len(params)} parameters")
        logger.info(f"All parsed parameters: {[repr(p) for p in params]}")
        
        try:
            if method_name == "blogger.newPost":
                logger.info("Executing blogger.newPost")
                result = api.blogger_newPost(*params)
            elif method_name == "blogger.editPost":
                logger.info("Executing blogger.editPost")
                result = api.blogger_editPost(*params)
            elif method_name == "blogger.deletePost":
                logger.info("Executing blogger.deletePost")
                result = api.blogger_deletePost(*params)
            elif method_name == "blogger.getRecentPosts":
                logger.info("Executing blogger.getRecentPosts")
                result = api.blogger_getRecentPosts(*params)
            elif method_name == "blogger.getUsersBlogs":
                logger.info("Executing blogger.getUsersBlogs")
                result = api.blogger_getUsersBlogs(*params)
            elif method_name == "blogger.getPost":
                logger.info("Executing blogger.getPost")
                result = api.blogger_getPost(*params)
            # MetaWeblog API methods (different parameter signatures)
            elif method_name == "metaWeblog.newPost":
                logger.info("Executing metaWeblog.newPost")
                result = api.metaweblog_newPost(*params)
            elif method_name == "metaWeblog.editPost":
                logger.info("Executing metaWeblog.editPost")
                result = api.metaweblog_editPost(*params)
            elif method_name == "metaWeblog.getPost":
                logger.info("Executing metaWeblog.getPost")
                result = api.metaweblog_getPost(*params)
            elif method_name == "metaWeblog.getRecentPosts":
                logger.info("Executing metaWeblog.getRecentPosts")
                result = api.metaweblog_getRecentPosts(*params)
            elif method_name == "metaWeblog.getCategories":
                logger.info("Executing metaWeblog.getCategories")
                result = api.metaweblog_getCategories(*params)
            else:
                logger.error(f"Unknown method: {method_name}")
                raise HTTPException(status_code=400, detail=f"Unknown method: {method_name}")
        except Exception as e:
            if "Authentication failed" in str(e):
                logger.info("Authentication failed - returning XML-RPC fault with code 403")
                fault_xml = create_xmlrpc_fault_with_code(403, "Incorrect username or password.")
                return Response(
                    content=fault_xml,
                    media_type="text/xml",
                    status_code=200
                )
            else:
                raise
        
        # Create XML-RPC response
        logger.info(f"Method {method_name} completed successfully, result type: {type(result)}")
        response_xml = create_xmlrpc_response(result)
        
        return Response(
            content=response_xml,
            media_type="text/xml",
            headers={"Content-Type": "text/xml"}
        )
        
    except Exception as e:
        # Return XML-RPC fault
        logger.error(f"XML-RPC error: {str(e)}", exc_info=True)
        fault_xml = create_xmlrpc_fault(str(e))
        return Response(
            content=fault_xml,
            media_type="text/xml",
            status_code=500
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
        # Handle single dictionary (for blogger.getPost)
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


def create_xmlrpc_fault(message):
    """Create XML-RPC fault response"""
    return f"""<?xml version="1.0"?>
<methodResponse>
    <fault>
        <value>
            <struct>
                <member>
                    <name>faultCode</name>
                    <value><int>1</int></value>
                </member>
                <member>
                    <name>faultString</name>
                    <value><string>{message}</string></value>
                </member>
            </struct>
        </value>
    </fault>
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



# Serve all other routes as static files or 404
@app.get("/{path:path}")
async def serve_static_or_404(path: str):
    """Serve static files or custom 404 page"""
    # Try to serve as static file
    file_path = output_dir / path
    
    # If it's a directory, try index.html
    if file_path.is_dir():
        file_path = file_path / "index.html"
    
    # If no extension, try adding .html
    if not file_path.suffix and not file_path.exists():
        file_path = output_dir / f"{path}.html"
    
    if file_path.exists() and file_path.is_file():
        content_type = "text/html" if file_path.suffix == ".html" else None
        return HTMLResponse(
            content=file_path.read_text(encoding='utf-8'),
            media_type=content_type
        )
    
    # Return custom 404 page
    return await serve_404_page()

async def serve_404_page():
    """Serve custom 404 error page"""
    # Try to find a generated 404 page first
    error_404_path = output_dir / "404.html"
    if error_404_path.exists():
        return HTMLResponse(
            content=error_404_path.read_text(encoding='utf-8'),
            status_code=404
        )
    
    # Fallback to simple 404 message
    return HTMLResponse(
        content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>404 - Page Not Found</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
                h1 { color: #e74c3c; }
                .btn { display: inline-block; background: #3498db; color: white; 
                       padding: 10px 20px; text-decoration: none; border-radius: 5px; margin: 10px; }
            </style>
        </head>
        <body>
            <h1>404 - Page Not Found</h1>
            <p>The page you're looking for doesn't exist.</p>
            <a href="/" class="btn">Go Home</a>
            <a href="/blog/" class="btn">Browse Blog</a>
        </body>
        </html>
        """,
        status_code=404
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)