"""
Scheduled tasks for automatic Git synchronization and Raindrop sync
"""

import asyncio
import logging
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from threading import Thread
from typing import Optional

import schedule

logger = logging.getLogger(__name__)

class Scheduler:
    """Handles scheduled Git synchronization and Raindrop sync operations"""
    
    def __init__(self, content_dir: Path = Path("/app/content")):
        self.content_dir = content_dir
        self.git_dir = Path("/app")
        self.is_running = False
        self.last_git_sync = None
        self.last_raindrop_sync = None
        
    async def sync_to_github(self) -> bool:
        """
        Sync /app/content to GitHub repository
        Returns True if successful, False otherwise
        """
        try:
            logger.info("Starting scheduled Git sync to GitHub...")
            
            # Change to git directory
            os.chdir(self.git_dir)
            
            # Check if we have git credentials
            if not self._check_git_credentials():
                logger.warning("Git credentials not configured, skipping sync")
                return False
            
            # Add content directory changes
            logger.info("Adding content changes to git...")
            subprocess.run(
                ["git", "add", "content/"],
                capture_output=True, text=True, timeout=30, check=True
            )
            
            # Check if there are any staged changes (content-related)
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, timeout=10
            )
            
            if not result.stdout.strip():
                logger.info("No content changes to sync to GitHub")
                return True
            
            logger.info(f"Content files to commit: {result.stdout.strip()}")
            
            # Create commit with timestamp
            commit_message = f"Automated sync from blog API - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(f"Creating commit: {commit_message}")
            
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True, text=True, timeout=30, check=True
            )
            
            # Push to GitHub
            git_branch = os.getenv("GIT_BRANCH", "main")
            logger.info(f"Pushing to GitHub branch: {git_branch}")
            result = subprocess.run(
                ["git", "push", "origin", git_branch],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Successfully synced content to GitHub")
                self.last_git_sync = datetime.now()
                return True
            else:
                logger.error(f"Git push failed: {result.stderr}")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"Git command failed: {e.stderr if e.stderr else str(e)}")
            return False
        except subprocess.TimeoutExpired:
            logger.error("Git operation timed out")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during Git sync: {e}")
            return False
    
    async def sync_raindrops(self) -> bool:
        """
        Sync raindrops from Raindrop.io and regenerate site
        Returns True if successful, False otherwise
        """
        try:
            logger.info("Starting scheduled Raindrop sync...")
            
            # Check if we have Raindrop credentials
            raindrop_token = os.getenv("RAINDROP_TOKEN")
            if not raindrop_token:
                logger.warning("RAINDROP_TOKEN not configured, skipping raindrop sync")
                return False
            
            # Import raindrop module
            from .raindrop import RaindropDownloader
            from .generator import SiteGenerator
            
            # Download new raindrops
            downloader = RaindropDownloader()
            created_files = downloader.download_raindrops(reset=False, count=None)
            
            if not created_files:
                logger.info("No new raindrops to sync")
                return True
            
            logger.info(f"Downloaded {len(created_files)} new raindrops")
            
            # Regenerate site to include new raindrops
            logger.info("Regenerating site with new raindrops...")
            theme = os.environ.get('THEME', 'claude')
            generator = SiteGenerator(theme=theme)
            generator.generate_site()
            
            logger.info("Successfully synced raindrops and regenerated site")
            self.last_raindrop_sync = datetime.now()
            return True
            
        except Exception as e:
            logger.error(f"Unexpected error during Raindrop sync: {e}")
            return False
    
    def _check_git_credentials(self) -> bool:
        """Check if Git credentials are properly configured"""
        try:
            # Check if we have a Git token or SSH key
            git_token = os.getenv("GIT_TOKEN")
            ssh_key = os.getenv("SSH_PRIVATE_KEY")
            
            if not git_token and not ssh_key:
                return False
            
            # Test if we can access the remote
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True, text=True, timeout=5
            )
            
            return result.returncode == 0 and "github.com" in result.stdout
            
        except Exception:
            return False
    
    def _git_sync_wrapper(self):
        """Wrapper for the async git sync function to run in scheduler"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self.sync_to_github())
            loop.close()
            
            if success:
                logger.info("Scheduled Git sync completed successfully")
            else:
                logger.warning("Scheduled Git sync failed")
                
        except Exception as e:
            logger.error(f"Error in scheduled git sync: {e}")
    
    def _raindrop_sync_wrapper(self):
        """Wrapper for the async raindrop sync function to run in scheduler"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            success = loop.run_until_complete(self.sync_raindrops())
            loop.close()
            
            if success:
                logger.info("Scheduled Raindrop sync completed successfully")
            else:
                logger.warning("Scheduled Raindrop sync failed")
                
        except Exception as e:
            logger.error(f"Error in scheduled raindrop sync: {e}")
    
    def start_scheduler(self, git_interval_hours: float = None, raindrop_interval_hours: float = None):
        """Start the background scheduler with support for fractional hours"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Get intervals from environment variables with new names
        if git_interval_hours is None:
            git_interval_hours = float(os.environ.get('SCHED_GITSYNC_HRS', 6.0))
        
        if raindrop_interval_hours is None:
            raindrop_interval_hours = float(os.environ.get('SCHED_RAINSYNC_HRS', 2.0))
        
        logger.info(f"Starting scheduler:")
        logger.info(f"  Git sync: every {git_interval_hours} hours")
        logger.info(f"  Raindrop sync: every {raindrop_interval_hours} hours")
        
        # Convert fractional hours to minutes for the schedule library
        git_minutes = int(git_interval_hours * 60)
        raindrop_minutes = int(raindrop_interval_hours * 60)
        
        # Schedule the sync jobs
        if git_minutes > 0:
            schedule.every(git_minutes).minutes.do(self._git_sync_wrapper).tag('git_sync')
            # Also run a git sync 10 minutes after startup
            schedule.every(10).minutes.do(self._git_sync_wrapper).tag('git_startup')
        
        if raindrop_minutes > 0:
            schedule.every(raindrop_minutes).minutes.do(self._raindrop_sync_wrapper).tag('raindrop_sync')
            # Also run a raindrop sync 5 minutes after startup
            schedule.every(5).minutes.do(self._raindrop_sync_wrapper).tag('raindrop_startup')
        
        self.is_running = True
        
        def run_scheduler():
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    logger.error(f"Scheduler error: {e}")
                    time.sleep(60)
        
        # Start scheduler in daemon thread
        scheduler_thread = Thread(target=run_scheduler, daemon=True, name="SyncScheduler")
        scheduler_thread.start()
        
        logger.info("Scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Git scheduler stopped")
    
    def get_status(self) -> dict:
        """Get scheduler status information"""
        raindrop_token = os.getenv("RAINDROP_TOKEN")
        return {
            "running": self.is_running,
            "last_git_sync": self.last_git_sync.isoformat() if self.last_git_sync else None,
            "last_raindrop_sync": self.last_raindrop_sync.isoformat() if self.last_raindrop_sync else None,
            "next_jobs": [str(job) for job in schedule.jobs],
            "git_configured": self._check_git_credentials(),
            "raindrop_configured": bool(raindrop_token),
            "git_interval_hours": float(os.environ.get('SCHED_GITSYNC_HRS', 6.0)),
            "raindrop_interval_hours": float(os.environ.get('SCHED_RAINSYNC_HRS', 2.0))
        }

# Global scheduler instance
_scheduler_instance: Optional[Scheduler] = None

def get_scheduler() -> Scheduler:
    """Get the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = Scheduler()
    return _scheduler_instance