"""
Scheduled tasks for automatic Git synchronization
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

class GitScheduler:
    """Handles scheduled Git operations to sync content to GitHub"""
    
    def __init__(self, content_dir: Path = Path("/app/content")):
        self.content_dir = content_dir
        self.git_dir = Path("/app")
        self.is_running = False
        self.last_sync = None
        
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
            
            # Check if there are any changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, timeout=10
            )
            
            if not result.stdout.strip():
                logger.info("No changes to sync to GitHub")
                return True
            
            # Add all changes in content directory
            logger.info("Adding content changes to git...")
            subprocess.run(
                ["git", "add", "content/"],
                capture_output=True, text=True, timeout=30, check=True
            )
            
            # Create commit with timestamp
            commit_message = f"Automated sync from blog API - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            logger.info(f"Creating commit: {commit_message}")
            
            subprocess.run(
                ["git", "commit", "-m", commit_message],
                capture_output=True, text=True, timeout=30, check=True
            )
            
            # Push to GitHub
            logger.info("Pushing to GitHub...")
            result = subprocess.run(
                ["git", "push", "origin", "persistent-volume"],
                capture_output=True, text=True, timeout=60
            )
            
            if result.returncode == 0:
                logger.info("Successfully synced content to GitHub")
                self.last_sync = datetime.now()
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
    
    def _sync_wrapper(self):
        """Wrapper for the async sync function to run in scheduler"""
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
            logger.error(f"Error in scheduled sync: {e}")
    
    def start_scheduler(self, interval_hours: int = 6):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
        
        logger.info(f"Starting Git scheduler - will sync every {interval_hours} hours")
        
        # Schedule the sync job
        schedule.every(interval_hours).hours.do(self._sync_wrapper)
        
        # Also run a sync 10 minutes after startup (to catch any missed changes)
        schedule.every(10).minutes.do(self._sync_wrapper).tag('startup')
        
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
        scheduler_thread = Thread(target=run_scheduler, daemon=True, name="GitScheduler")
        scheduler_thread.start()
        
        logger.info("Git scheduler started successfully")
    
    def stop_scheduler(self):
        """Stop the background scheduler"""
        self.is_running = False
        schedule.clear()
        logger.info("Git scheduler stopped")
    
    def get_status(self) -> dict:
        """Get scheduler status information"""
        return {
            "running": self.is_running,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "next_jobs": [str(job) for job in schedule.jobs],
            "git_configured": self._check_git_credentials()
        }

# Global scheduler instance
_scheduler_instance: Optional[GitScheduler] = None

def get_scheduler() -> GitScheduler:
    """Get the global scheduler instance"""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = GitScheduler()
    return _scheduler_instance