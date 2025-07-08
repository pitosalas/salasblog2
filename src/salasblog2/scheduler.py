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
from typing import Optional, List

import schedule

logger = logging.getLogger(__name__)


class SchedulerConfig:
    """Configuration for scheduler paths and intervals"""
    
    def __init__(self):
        self.data_dir = Path("/data/content")
        self.app_dir = Path("/app")
        self.content_dir = Path("/app/content")
        self.git_sync_hours = float(os.environ.get('SCHED_GITSYNC_HRS', 6.0))
        self.raindrop_sync_hours = float(os.environ.get('SCHED_RAINSYNC_HRS', 2.0))
        self.git_branch = os.getenv("GIT_BRANCH", "main")


class Scheduler:
    """Handles scheduled Git synchronization and Raindrop sync operations"""
    
    def __init__(self, content_dir: Path = None):
        self.config = SchedulerConfig()
        if content_dir:
            self.config.content_dir = content_dir
        self.is_running = False
        self.last_git_sync = None
        self.last_raindrop_sync = None
        self.recent_errors = []
        
    def _run_command_with_retry(self, cmd: List[str], retries: int = 2, timeout: int = 60) -> subprocess.CompletedProcess:
        """Run command with simple retry logic"""
        for attempt in range(retries + 1):
            try:
                return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=True)
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                if attempt == retries:
                    raise
                logger.warning(f"Command failed (attempt {attempt + 1}), retrying: {e}")
                time.sleep(5)
    
    def _log_error(self, error: str):
        """Log error and keep recent errors for debugging"""
        logger.error(error)
        self.recent_errors.append(f"{datetime.now().strftime('%H:%M:%S')}: {error}")
        # Keep only last 10 errors
        if len(self.recent_errors) > 10:
            self.recent_errors.pop(0)
    
    def _copy_content_to_git(self) -> bool:
        """Copy /data/content to /app/content for git operations"""
        if not self.config.data_dir.exists():
            self._log_error("/data/content does not exist, cannot sync to GitHub")
            return False
            
        # Ensure /app/content exists
        self.config.content_dir.mkdir(parents=True, exist_ok=True)
        
        # Use rsync to sync /data/content to /app/content
        try:
            result = self._run_command_with_retry([
                "rsync", "-av", "--delete", 
                f"{self.config.data_dir}/", 
                f"{self.config.content_dir}/"
            ])
            logger.info("Successfully copied /data/content to /app/content")
            return True
        except Exception as e:
            self._log_error(f"Failed to copy /data/content to /app/content: {e}")
            return False
    
    def _has_git_changes(self) -> bool:
        """Check if there are any staged changes"""
        try:
            result = subprocess.run(
                ["git", "diff", "--cached", "--name-only"],
                capture_output=True, text=True, timeout=10
            )
            has_changes = bool(result.stdout.strip())
            if has_changes:
                logger.info(f"Content files to commit: {result.stdout.strip()}")
            return has_changes
        except Exception as e:
            self._log_error(f"Failed to check git changes: {e}")
            return False
    
    def _commit_and_push(self) -> bool:
        """Create commit and push to GitHub"""
        try:
            # Create commit with timestamp
            commit_message = f"Automated sync from /data/content - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(f"Creating commit: {commit_message}")
            
            self._run_command_with_retry(["git", "commit", "-m", commit_message], timeout=30)
            
            # Push to GitHub
            logger.info(f"Pushing to GitHub branch: {self.config.git_branch}")
            self._run_command_with_retry(["git", "push", "origin", self.config.git_branch], timeout=60)
            
            logger.info("Successfully synced content to GitHub")
            return True
            
        except Exception as e:
            self._log_error(f"Failed to commit and push: {e}")
            return False
    
    def _get_git_remote(self) -> str:
        """Get git remote URL for debugging"""
        try:
            result = subprocess.run(
                ["git", "remote", "-v"],
                capture_output=True, text=True, timeout=5
            )
            return result.stdout.strip() if result.returncode == 0 else "Unknown"
        except Exception:
            return "Error getting remote"

    async def sync_to_github(self) -> bool:
        """
        Sync /data/content to GitHub repository via /app/content
        Volume-first architecture: /data/content → /app/content → GitHub
        """
        try:
            logger.info("Starting scheduled Git sync to GitHub...")
            
            # Change to git directory
            os.chdir(self.config.app_dir)
            
            # Check if we have git credentials
            if not self._check_git_credentials():
                logger.warning("Git credentials not configured, skipping sync")
                return False
            
            # Copy content from data to app directory
            if not self._copy_content_to_git():
                return False
            
            # Add content directory changes
            logger.info("Adding content changes to git...")
            try:
                subprocess.run(
                    ["git", "add", "content/"],
                    capture_output=True, text=True, timeout=30, check=True
                )
            except Exception as e:
                self._log_error(f"Failed to add content to git: {e}")
                return False
            
            # Check if there are any changes
            if not self._has_git_changes():
                logger.info("No content changes to sync to GitHub")
                return True
            
            # Commit and push changes
            success = self._commit_and_push()
            if success:
                self.last_git_sync = datetime.now()
            return success
                
        except Exception as e:
            self._log_error(f"Unexpected error during Git sync: {e}")
            return False

    async def sync_raindrops(self) -> bool:
        """Sync raindrops from Raindrop.io and regenerate site"""
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
            self._log_error(f"Unexpected error during Raindrop sync: {e}")
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

    def _sync_wrapper(self, sync_type: str, is_startup: bool = False):
        """Generic wrapper for sync operations"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            if sync_type == 'git':
                success = loop.run_until_complete(self.sync_to_github())
                operation = "Git"
            else:
                success = loop.run_until_complete(self.sync_raindrops())
                operation = "Raindrop"
                
            loop.close()
            
            status = "Startup" if is_startup else "Scheduled"
            if success:
                logger.info(f"{status} {operation} sync completed successfully")
            else:
                logger.warning(f"{status} {operation} sync failed")
                
        except Exception as e:
            logger.error(f"Error in {sync_type} sync: {e}")
        finally:
            if is_startup:
                schedule.clear(f'{sync_type}_startup')
                logger.info(f"Startup {operation} sync job cancelled (one-time only)")

    def start_scheduler(self, git_interval_hours: float = None, raindrop_interval_hours: float = None):
        """Start the background scheduler with support for fractional hours"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        # Use provided intervals or config defaults
        git_hours = git_interval_hours or self.config.git_sync_hours
        raindrop_hours = raindrop_interval_hours or self.config.raindrop_sync_hours
        
        logger.info(f"Starting scheduler:")
        logger.info(f"  Git sync: every {git_hours} hours")
        logger.info(f"  Raindrop sync: every {raindrop_hours} hours")
        
        # Convert fractional hours to minutes for the schedule library
        git_minutes = int(git_hours * 60)
        raindrop_minutes = int(raindrop_hours * 60)
        
        # Schedule the sync jobs
        if git_minutes > 0:
            schedule.every(git_minutes).minutes.do(
                lambda: self._sync_wrapper('git', False)
            ).tag('git_sync')
            # Run a one-time git sync 10 minutes after startup
            schedule.every(10).minutes.do(
                lambda: self._sync_wrapper('git', True)
            ).tag('git_startup')
        
        if raindrop_minutes > 0:
            schedule.every(raindrop_minutes).minutes.do(
                lambda: self._sync_wrapper('raindrop', False)
            ).tag('raindrop_sync')
            # Run a one-time raindrop sync 5 minutes after startup
            schedule.every(5).minutes.do(
                lambda: self._sync_wrapper('raindrop', True)
            ).tag('raindrop_startup')
        
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
            "git_interval_hours": self.config.git_sync_hours,
            "raindrop_interval_hours": self.config.raindrop_sync_hours
        }

    def get_detailed_status(self) -> dict:
        """Get detailed status for debugging"""
        return {
            **self.get_status(),
            "data_dir_exists": self.config.data_dir.exists(),
            "content_dir_exists": self.config.content_dir.exists(),
            "git_remote": self._get_git_remote(),
            "last_sync_errors": self.recent_errors,
            "file_counts": {
                "data_content": len(list(self.config.data_dir.glob("**/*"))) if self.config.data_dir.exists() else 0,
                "app_content": len(list(self.config.content_dir.glob("**/*"))) if self.config.content_dir.exists() else 0,
            },
            "config": {
                "data_dir": str(self.config.data_dir),
                "content_dir": str(self.config.content_dir),
                "git_branch": self.config.git_branch
            }
        }


# Global scheduler instance
_scheduler_instance: Optional[Scheduler] = None

def get_scheduler() -> Scheduler:
    """Get the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = Scheduler()
    return _scheduler_instance