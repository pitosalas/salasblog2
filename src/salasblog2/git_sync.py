"""
Asynchronous Git synchronization service for Salasblog2.
Handles batched Git operations to improve performance and user experience.
"""
import asyncio
import subprocess
import logging
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)


@dataclass
class GitOperation:
    """Represents a pending Git operation."""
    operation_type: str  # 'create', 'edit', 'delete'
    filename: str
    timestamp: datetime


class GitSyncService:
    """
    Background service that batches Git operations and syncs with GitHub periodically.
    
    Features:
    - Immediate file operations (no blocking)
    - Batched Git commits (reduce Git overhead)
    - Periodic sync to GitHub (configurable interval)
    - Conflict resolution
    - Graceful degradation if Git fails
    """
    
    def __init__(self, sync_interval_minutes: int = 5, max_operations_per_batch: int = 10):
        self.root_dir = Path.cwd()
        self.pending_operations: List[GitOperation] = []
        self.operations_lock = Lock()
        self.sync_interval = sync_interval_minutes * 60  # Convert to seconds
        self.max_operations_per_batch = max_operations_per_batch
        self.git_initialized = False
        self.sync_task = None
        self.is_running = False
        
        # Initialize Git repository once
        self._setup_git_repo()
    
    def _setup_git_repo(self):
        """One-time git repository setup."""
        try:
            # Check if git repo exists
            git_dir = self.root_dir / '.git'
            if not git_dir.exists():
                logger.info("Setting up git repository")
                # Initialize git repo and connect to remote
                subprocess.run(['git', 'init'], check=True, cwd=self.root_dir)
                subprocess.run(['git', 'remote', 'add', 'origin', 'https://github.com/pitosalas/salasblog2.git'], 
                             check=True, cwd=self.root_dir)
                subprocess.run(['git', 'branch', '-M', 'main'], check=True, cwd=self.root_dir)
                
                # Pull the existing content including cache
                try:
                    subprocess.run(['git', 'pull', 'origin', 'main'], check=True, cwd=self.root_dir)
                    logger.info("Git repository synchronized with remote")
                except subprocess.CalledProcessError:
                    logger.warning("Could not pull from remote - will sync on first commit")
            
            # Configure git user
            git_email = os.getenv('GIT_EMAIL', 'blog-api@salasblog2.com')
            git_name = os.getenv('GIT_NAME', 'Salasblog2 API')
            
            subprocess.run(['git', 'config', 'user.email', git_email], check=True, cwd=self.root_dir)
            subprocess.run(['git', 'config', 'user.name', git_name], check=True, cwd=self.root_dir)
            
            # Set up GitHub token authentication
            git_token = os.getenv('GIT_TOKEN')
            if git_token:
                subprocess.run(['git', 'config', 'credential.helper', 'store'], check=True, cwd=self.root_dir)
                git_credentials = f"https://oauth2:{git_token}@github.com"
                subprocess.run(['git', 'remote', 'set-url', 'origin', f"{git_credentials}/pitosalas/salasblog2.git"], 
                             check=True, cwd=self.root_dir)
            
            self._sync_with_remote()
            self.git_initialized = True
            logger.info("Git repository setup completed")
            
        except Exception as e:
            logger.error(f"Git setup failed: {e}")
            self.git_initialized = False
    
    def _sync_with_remote(self):
        """Sync with remote repository."""
        try:
            # Check if upstream is set
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', '--symbolic-full-name', '@{u}'], 
                                  capture_output=True, cwd=self.root_dir)
            
            if result.returncode == 0:
                # Upstream configured, pull changes
                subprocess.run(['git', 'pull'], check=True, cwd=self.root_dir)
                logger.info("Synced with remote repository")
            else:
                # No upstream, fetch and set up tracking
                subprocess.run(['git', 'fetch', 'origin'], check=True, cwd=self.root_dir)
                try:
                    subprocess.run(['git', 'branch', '--set-upstream-to=origin/main', 'main'], 
                                 check=True, cwd=self.root_dir)
                    subprocess.run(['git', 'pull', '--allow-unrelated-histories'], 
                                 check=True, cwd=self.root_dir)
                    logger.info("Synced with existing remote main branch")
                except subprocess.CalledProcessError:
                    logger.info("Remote main branch doesn't exist, will create on first push")
                    
        except Exception as e:
            logger.warning(f"Remote sync failed: {e}")
    
    def queue_operation(self, operation_type: str, filename: str):
        """
        Queue a Git operation for later batch processing.
        This is non-blocking and returns immediately.
        """
        if not self.git_initialized:
            logger.warning(f"Git not initialized, skipping {operation_type} of {filename}")
            return
        
        operation = GitOperation(
            operation_type=operation_type.lower(),
            filename=filename,
            timestamp=datetime.now()
        )
        
        with self.operations_lock:
            # Remove any previous operations for the same file (keep only latest)
            self.pending_operations = [
                op for op in self.pending_operations 
                if op.filename != filename
            ]
            self.pending_operations.append(operation)
            
        logger.info(f"Queued {operation_type} operation for {filename}")
        
        # If we have too many operations, trigger immediate sync
        if len(self.pending_operations) >= self.max_operations_per_batch:
            logger.info("Max operations reached, triggering immediate sync")
            asyncio.create_task(self._sync_immediately())
    
    async def start_background_sync(self):
        """Start the background sync process."""
        if self.is_running:
            logger.warning("Background sync already running")
            return
            
        self.is_running = True
        logger.info(f"Starting background Git sync (interval: {self.sync_interval}s)")
        
        while self.is_running:
            try:
                await asyncio.sleep(self.sync_interval)
                if self.pending_operations:
                    await self._sync_immediately()
            except Exception as e:
                logger.error(f"Background sync error: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retrying
    
    async def _sync_immediately(self):
        """Immediately process all pending operations."""
        if not self.pending_operations:
            return
            
        with self.operations_lock:
            operations_to_process = self.pending_operations.copy()
            self.pending_operations.clear()
        
        if not operations_to_process:
            return
            
        logger.info(f"Processing {len(operations_to_process)} pending Git operations")
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self._process_operations_batch, operations_to_process
            )
        except Exception as e:
            logger.error(f"Failed to process Git operations batch: {e}")
            # Re-queue failed operations for retry
            with self.operations_lock:
                self.pending_operations.extend(operations_to_process)
    
    def _process_operations_batch(self, operations: List[GitOperation]):
        """Process a batch of Git operations synchronously."""
        try:
            # Group operations by type for better commit messages
            created_files = []
            edited_files = []
            deleted_files = []
            
            for op in operations:
                if op.operation_type == 'create':
                    created_files.append(op.filename)
                elif op.operation_type == 'edit':
                    edited_files.append(op.filename)
                elif op.operation_type == 'delete':
                    deleted_files.append(op.filename)
            
            # Process each operation type
            if deleted_files:
                for filename in deleted_files:
                    subprocess.run(['git', 'rm', f'content/blog/{filename}'], 
                                 check=True, cwd=self.root_dir)
            
            if created_files or edited_files:
                for filename in created_files + edited_files:
                    subprocess.run(['git', 'add', f'content/blog/{filename}'], 
                                 check=True, cwd=self.root_dir)
                
                # Also add the raindrop cache file to persist it across deployments
                cache_file = self.root_dir / 'content' / '.rd_cache.json'
                if cache_file.exists():
                    subprocess.run(['git', 'add', 'content/.rd_cache.json'], 
                                 check=True, cwd=self.root_dir)
            
            # Create descriptive commit message
            commit_parts = []
            if created_files:
                if len(created_files) == 1:
                    commit_parts.append(f"Create blog post: {created_files[0]}")
                else:
                    commit_parts.append(f"Create {len(created_files)} blog posts")
            
            if edited_files:
                if len(edited_files) == 1:
                    commit_parts.append(f"Edit blog post: {edited_files[0]}")
                else:
                    commit_parts.append(f"Edit {len(edited_files)} blog posts")
            
            if deleted_files:
                if len(deleted_files) == 1:
                    commit_parts.append(f"Delete blog post: {deleted_files[0]}")
                else:
                    commit_parts.append(f"Delete {len(deleted_files)} blog posts")
            
            commit_msg = "; ".join(commit_parts)
            
            # Commit changes
            subprocess.run(['git', 'commit', '-m', commit_msg], check=True, cwd=self.root_dir)
            
            # Push to remote with conflict resolution
            self._push_with_retry()
            
            logger.info(f"Successfully synced {len(operations)} operations to GitHub")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Git batch operation failed: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Git batch operation: {e}")
            raise
    
    def _push_with_retry(self):
        """Push to remote with conflict resolution."""
        try:
            subprocess.run(['git', 'push'], check=True, cwd=self.root_dir)
        except subprocess.CalledProcessError:
            logger.warning("Push failed, attempting to sync and retry")
            try:
                # Pull with rebase and retry
                subprocess.run(['git', 'pull', '--rebase', '--allow-unrelated-histories'], 
                             check=True, cwd=self.root_dir)
                subprocess.run(['git', 'push'], check=True, cwd=self.root_dir)
            except subprocess.CalledProcessError:
                # Last resort: force push
                logger.warning("Attempting force push with upstream")
                subprocess.run(['git', 'push', '--set-upstream', 'origin', 'main', '--force'], 
                             check=True, cwd=self.root_dir)
    
    async def stop_background_sync(self):
        """Stop the background sync process."""
        self.is_running = False
        logger.info("Stopping background Git sync")
        
        # Process any remaining operations before stopping
        if self.pending_operations:
            logger.info("Processing remaining operations before shutdown")
            await self._sync_immediately()
    
    def force_sync_now(self) -> bool:
        """
        Force immediate synchronization of pending operations.
        Returns True if successful, False otherwise.
        """
        if not self.pending_operations:
            logger.info("No pending operations to sync")
            return True
            
        try:
            asyncio.create_task(self._sync_immediately())
            return True
        except Exception as e:
            logger.error(f"Force sync failed: {e}")
            return False
    
    def get_pending_operations_count(self) -> int:
        """Get the number of pending operations."""
        with self.operations_lock:
            return len(self.pending_operations)


# Global instance
_git_sync_service = None


def get_git_sync_service() -> GitSyncService:
    """Get the global Git sync service instance."""
    global _git_sync_service
    if _git_sync_service is None:
        _git_sync_service = GitSyncService()
    return _git_sync_service


async def start_git_sync_service():
    """Start the global Git sync service."""
    service = get_git_sync_service()
    await service.start_background_sync()


async def stop_git_sync_service():
    """Stop the global Git sync service."""
    global _git_sync_service
    if _git_sync_service:
        await _git_sync_service.stop_background_sync()