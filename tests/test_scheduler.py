"""
Tests for the refactored scheduler module.

Run with: uv run pytest tests/test_scheduler.py -v
"""

import pytest
import asyncio
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import subprocess
from datetime import datetime

from salasblog2.scheduler import Scheduler, SchedulerConfig, get_scheduler


class TestSchedulerConfig:
    """Test the SchedulerConfig class"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = SchedulerConfig()
        
        assert config.data_dir == Path("/data/content")
        assert config.app_dir == Path("/app")
        assert config.content_dir == Path("/app/content")
        assert config.git_branch == "main"
        assert config.git_sync_hours == 6.0  # default value
        assert config.raindrop_sync_hours == 2.0  # default value
    
    def test_env_var_config(self):
        """Test configuration from environment variables"""
        with patch.dict(os.environ, {
            'SCHED_GITSYNC_HRS': '12.5',
            'SCHED_RAINSYNC_HRS': '4.0',
            'GIT_BRANCH': 'develop'
        }):
            config = SchedulerConfig()
            
            assert config.git_sync_hours == 12.5
            assert config.raindrop_sync_hours == 4.0
            assert config.git_branch == "develop"


class TestScheduler:
    """Test the Scheduler class"""
    
    @pytest.fixture
    def scheduler(self):
        """Create a scheduler instance for testing"""
        return Scheduler()
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for testing"""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            data_dir = temp_path / "data_content"
            app_dir = temp_path / "app"
            content_dir = app_dir / "content"
            
            data_dir.mkdir()
            app_dir.mkdir()
            
            yield {
                "data_dir": data_dir,
                "app_dir": app_dir,
                "content_dir": content_dir
            }
    
    def test_scheduler_init(self, scheduler):
        """Test scheduler initialization"""
        assert scheduler.is_running is False
        assert scheduler.last_git_sync is None
        assert scheduler.last_raindrop_sync is None
        assert scheduler.recent_errors == []
        assert isinstance(scheduler.config, SchedulerConfig)
    
    def test_scheduler_init_with_custom_content_dir(self):
        """Test scheduler initialization with custom content directory"""
        custom_dir = Path("/custom/content")
        scheduler = Scheduler(content_dir=custom_dir)
        
        assert scheduler.config.content_dir == custom_dir
    
    def test_log_error(self, scheduler):
        """Test error logging functionality"""
        scheduler._log_error("Test error 1")
        scheduler._log_error("Test error 2")
        
        assert len(scheduler.recent_errors) == 2
        assert "Test error 1" in scheduler.recent_errors[0]
        assert "Test error 2" in scheduler.recent_errors[1]
    
    def test_log_error_max_capacity(self, scheduler):
        """Test that error log maintains max capacity"""
        # Add 12 errors (more than the 10 max)
        for i in range(12):
            scheduler._log_error(f"Error {i}")
        
        # Should only keep the last 10
        assert len(scheduler.recent_errors) == 10
        assert "Error 2" in scheduler.recent_errors[0]  # First error should be index 2
        assert "Error 11" in scheduler.recent_errors[9]  # Last error should be index 11
    
    def test_run_command_with_retry_success(self, scheduler):
        """Test successful command execution"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="success")
            
            result = scheduler._run_command_with_retry(["echo", "test"])
            
            assert mock_run.call_count == 1
            assert result.returncode == 0
    
    def test_run_command_with_retry_failure_then_success(self, scheduler):
        """Test command retry logic"""
        with patch('subprocess.run') as mock_run, \
             patch('time.sleep') as mock_sleep:
            
            # First call fails, second succeeds
            mock_run.side_effect = [
                subprocess.CalledProcessError(1, "test"),
                Mock(returncode=0, stdout="success")
            ]
            
            result = scheduler._run_command_with_retry(["test", "command"])
            
            assert mock_run.call_count == 2
            assert mock_sleep.call_count == 1
            assert result.returncode == 0
    
    def test_run_command_with_retry_all_failures(self, scheduler):
        """Test command retry exhaustion"""
        with patch('subprocess.run') as mock_run, \
             patch('time.sleep') as mock_sleep:
            
            mock_run.side_effect = subprocess.CalledProcessError(1, "test")
            
            with pytest.raises(subprocess.CalledProcessError):
                scheduler._run_command_with_retry(["test", "command"], retries=2)
            
            assert mock_run.call_count == 3  # Initial + 2 retries
            assert mock_sleep.call_count == 2
    
    def test_get_git_remote_success(self, scheduler):
        """Test getting git remote successfully"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="origin\tgit@github.com:user/repo.git (fetch)\n"
            )
            
            result = scheduler._get_git_remote()
            
            assert "github.com:user/repo.git" in result
    
    def test_get_git_remote_failure(self, scheduler):
        """Test getting git remote with failure"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Git not found")
            
            result = scheduler._get_git_remote()
            
            assert result == "Error getting remote"
    
    def test_check_git_credentials_no_credentials(self, scheduler):
        """Test git credential check with no credentials"""
        with patch.dict(os.environ, {}, clear=True):
            result = scheduler._check_git_credentials()
            assert result is False
    
    def test_check_git_credentials_with_token(self, scheduler):
        """Test git credential check with token"""
        with patch.dict(os.environ, {'GIT_TOKEN': 'fake_token'}), \
             patch('subprocess.run') as mock_run:
            
            mock_run.return_value = Mock(
                returncode=0,
                stdout="origin\tgit@github.com:user/repo.git (fetch)\n"
            )
            
            result = scheduler._check_git_credentials()
            assert result is True
    
    def test_check_git_credentials_with_ssh_key(self, scheduler):
        """Test git credential check with SSH key"""
        with patch.dict(os.environ, {'SSH_PRIVATE_KEY': 'fake_key'}), \
             patch('subprocess.run') as mock_run:
            
            mock_run.return_value = Mock(
                returncode=0,
                stdout="origin\tgit@github.com:user/repo.git (fetch)\n"
            )
            
            result = scheduler._check_git_credentials()
            assert result is True
    
    def test_copy_content_to_git_no_data_dir(self, scheduler, temp_dirs):
        """Test copying content when data directory doesn't exist"""
        scheduler.config.data_dir = temp_dirs["data_dir"] / "nonexistent"
        scheduler.config.content_dir = temp_dirs["content_dir"]
        
        result = scheduler._copy_content_to_git()
        
        assert result is False
        assert len(scheduler.recent_errors) > 0
        assert "does not exist" in scheduler.recent_errors[0]
    
    def test_copy_content_to_git_success(self, scheduler, temp_dirs):
        """Test successful content copying"""
        scheduler.config.data_dir = temp_dirs["data_dir"]
        scheduler.config.content_dir = temp_dirs["content_dir"]
        
        # Create a test file in data directory
        test_file = temp_dirs["data_dir"] / "test.txt"
        test_file.write_text("test content")
        
        with patch.object(scheduler, '_run_command_with_retry') as mock_retry:
            mock_retry.return_value = Mock(returncode=0)
            
            result = scheduler._copy_content_to_git()
            
            assert result is True
            assert mock_retry.called
            # Check that rsync was called with correct parameters
            call_args = mock_retry.call_args[0][0]
            assert call_args[0] == "rsync"
            assert "--delete" in call_args
    
    def test_copy_content_to_git_rsync_failure(self, scheduler, temp_dirs):
        """Test content copying with rsync failure"""
        scheduler.config.data_dir = temp_dirs["data_dir"]
        scheduler.config.content_dir = temp_dirs["content_dir"]
        
        with patch.object(scheduler, '_run_command_with_retry') as mock_retry:
            mock_retry.side_effect = Exception("rsync failed")
            
            result = scheduler._copy_content_to_git()
            
            assert result is False
            assert len(scheduler.recent_errors) > 0
            assert "rsync failed" in scheduler.recent_errors[0]
    
    def test_has_git_changes_with_changes(self, scheduler):
        """Test checking for git changes when changes exist"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="content/file1.txt\ncontent/file2.txt\n"
            )
            
            result = scheduler._has_git_changes()
            
            assert result is True
    
    def test_has_git_changes_no_changes(self, scheduler):
        """Test checking for git changes when no changes exist"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="")
            
            result = scheduler._has_git_changes()
            
            assert result is False
    
    def test_has_git_changes_command_failure(self, scheduler):
        """Test checking for git changes with command failure"""
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = Exception("Git command failed")
            
            result = scheduler._has_git_changes()
            
            assert result is False
            assert len(scheduler.recent_errors) > 0
    
    def test_commit_and_push_success(self, scheduler):
        """Test successful commit and push"""
        with patch.object(scheduler, '_run_command_with_retry') as mock_retry:
            mock_retry.return_value = Mock(returncode=0)
            
            result = scheduler._commit_and_push()
            
            assert result is True
            assert mock_retry.call_count == 2  # commit + push
    
    def test_commit_and_push_failure(self, scheduler):
        """Test commit and push with failure"""
        with patch.object(scheduler, '_run_command_with_retry') as mock_retry:
            mock_retry.side_effect = Exception("Git push failed")
            
            result = scheduler._commit_and_push()
            
            assert result is False
            assert len(scheduler.recent_errors) > 0
    
    @pytest.mark.asyncio
    async def test_sync_to_github_no_credentials(self, scheduler):
        """Test GitHub sync with no credentials"""
        with patch.object(scheduler, '_check_git_credentials', return_value=False):
            result = await scheduler.sync_to_github()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_sync_to_github_copy_failure(self, scheduler):
        """Test GitHub sync with copy failure"""
        with patch.object(scheduler, '_check_git_credentials', return_value=True), \
             patch.object(scheduler, '_copy_content_to_git', return_value=False):
            
            result = await scheduler.sync_to_github()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_sync_to_github_no_changes(self, scheduler):
        """Test GitHub sync with no changes"""
        with patch.object(scheduler, '_check_git_credentials', return_value=True), \
             patch.object(scheduler, '_copy_content_to_git', return_value=True), \
             patch.object(scheduler, '_has_git_changes', return_value=False), \
             patch('subprocess.run') as mock_run, \
             patch('os.chdir'):
            
            mock_run.return_value = Mock(returncode=0)
            
            result = await scheduler.sync_to_github()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_sync_to_github_success(self, scheduler):
        """Test successful GitHub sync"""
        with patch.object(scheduler, '_check_git_credentials', return_value=True), \
             patch.object(scheduler, '_copy_content_to_git', return_value=True), \
             patch.object(scheduler, '_has_git_changes', return_value=True), \
             patch.object(scheduler, '_commit_and_push', return_value=True), \
             patch('subprocess.run') as mock_run, \
             patch('os.chdir'):
            
            mock_run.return_value = Mock(returncode=0)
            
            result = await scheduler.sync_to_github()
            
            assert result is True
            assert scheduler.last_git_sync is not None
    
    @pytest.mark.asyncio
    async def test_sync_raindrops_no_token(self, scheduler):
        """Test raindrop sync with no token"""
        with patch.dict(os.environ, {}, clear=True):
            result = await scheduler.sync_raindrops()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_sync_raindrops_no_new_files(self, scheduler):
        """Test raindrop sync with no new files"""
        with patch.dict(os.environ, {'RAINDROP_TOKEN': 'fake_token'}), \
             patch('salasblog2.raindrop.RaindropDownloader') as mock_downloader:
            
            mock_instance = Mock()
            mock_instance.download_raindrops.return_value = []
            mock_downloader.return_value = mock_instance
            
            result = await scheduler.sync_raindrops()
            
            assert result is True
    
    @pytest.mark.asyncio
    async def test_sync_raindrops_success(self, scheduler):
        """Test successful raindrop sync"""
        with patch.dict(os.environ, {'RAINDROP_TOKEN': 'fake_token'}), \
             patch('salasblog2.raindrop.RaindropDownloader') as mock_downloader, \
             patch('salasblog2.generator.SiteGenerator') as mock_generator:
            
            mock_dl_instance = Mock()
            mock_dl_instance.download_raindrops.return_value = ['file1.md', 'file2.md']
            mock_downloader.return_value = mock_dl_instance
            
            mock_gen_instance = Mock()
            mock_generator.return_value = mock_gen_instance
            
            result = await scheduler.sync_raindrops()
            
            assert result is True
            assert scheduler.last_raindrop_sync is not None
            assert mock_gen_instance.generate_site.called
    
    def test_sync_wrapper_git_success(self, scheduler):
        """Test sync wrapper for git sync"""
        with patch.object(scheduler, '_run_async_in_thread', return_value=True) as mock_run, \
             patch.object(scheduler, '_handle_sync_result') as mock_handle, \
             patch.object(scheduler, 'sync_to_github') as mock_sync:
            
            scheduler._sync_wrapper('git', is_startup=False)
            
            mock_run.assert_called_once()
            mock_handle.assert_called_once_with(True, "Git", False)
    
    def test_sync_wrapper_raindrop_success(self, scheduler):
        """Test sync wrapper for raindrop sync"""
        with patch.object(scheduler, '_run_async_in_thread', return_value=True) as mock_run, \
             patch.object(scheduler, '_handle_sync_result') as mock_handle, \
             patch.object(scheduler, 'sync_raindrops') as mock_sync:
            
            scheduler._sync_wrapper('raindrop', is_startup=False)
            
            mock_run.assert_called_once()
            mock_handle.assert_called_once_with(True, "Raindrop", False)
    
    def test_sync_wrapper_startup_cancellation(self, scheduler):
        """Test that startup sync jobs are cancelled after running"""
        with patch.object(scheduler, '_run_async_in_thread', return_value=True), \
             patch.object(scheduler, '_handle_sync_result'), \
             patch.object(scheduler, '_cleanup_startup_job') as mock_cleanup:
            
            scheduler._sync_wrapper('git', is_startup=True)
            
            mock_cleanup.assert_called_once_with('git', 'Git')
    
    def test_get_sync_method_git(self, scheduler):
        """Test _get_sync_method for git sync"""
        method, operation = scheduler._get_sync_method('git')
        assert method == scheduler.sync_to_github
        assert operation == "Git"
    
    def test_get_sync_method_raindrop(self, scheduler):
        """Test _get_sync_method for raindrop sync"""
        method, operation = scheduler._get_sync_method('raindrop')
        assert method == scheduler.sync_raindrops
        assert operation == "Raindrop"
    
    def test_handle_sync_result_success_scheduled(self, scheduler):
        """Test _handle_sync_result for successful scheduled sync"""
        with patch('salasblog2.scheduler.logger') as mock_logger:
            scheduler._handle_sync_result(True, "Git", False)
            mock_logger.info.assert_called_once_with("Scheduled Git sync completed successfully")
    
    def test_handle_sync_result_failure_startup(self, scheduler):
        """Test _handle_sync_result for failed startup sync"""
        with patch('salasblog2.scheduler.logger') as mock_logger:
            scheduler._handle_sync_result(False, "Raindrop", True)
            mock_logger.warning.assert_called_once_with("Startup Raindrop sync failed")
    
    def test_cleanup_startup_job(self, scheduler):
        """Test _cleanup_startup_job"""
        with patch('schedule.clear') as mock_clear, \
             patch('salasblog2.scheduler.logger') as mock_logger:
            
            scheduler._cleanup_startup_job('git', 'Git')
            
            mock_clear.assert_called_once_with('git_startup')
            mock_logger.info.assert_called_once_with("Startup Git sync job cancelled (one-time only)")
    
    def test_start_scheduler_already_running(self, scheduler):
        """Test starting scheduler when already running"""
        scheduler.is_running = True
        
        with patch('schedule.every') as mock_every:
            scheduler.start_scheduler()
            
            # Should not schedule anything
            assert not mock_every.called
    
    def test_start_scheduler_success(self, scheduler):
        """Test successful scheduler start"""
        with patch('schedule.every') as mock_every, \
             patch('salasblog2.scheduler.Thread') as mock_thread:
            
            mock_job = Mock()
            mock_every.return_value.minutes.do.return_value = mock_job
            mock_thread_instance = Mock()
            mock_thread.return_value = mock_thread_instance
            
            scheduler.start_scheduler(git_interval_hours=1.0, raindrop_interval_hours=0.5)
            
            assert scheduler.is_running is True
            assert mock_thread.called
            assert mock_thread_instance.start.called
    
    def test_stop_scheduler(self, scheduler):
        """Test stopping scheduler"""
        scheduler.is_running = True
        
        with patch('schedule.clear') as mock_clear:
            scheduler.stop_scheduler()
            
            assert scheduler.is_running is False
            assert mock_clear.called
    
    def test_get_status(self, scheduler):
        """Test getting scheduler status"""
        with patch.dict(os.environ, {'RAINDROP_TOKEN': 'fake_token'}), \
             patch.object(scheduler, '_check_git_credentials', return_value=True), \
             patch('schedule.jobs', []):
            
            status = scheduler.get_status()
            
            assert status['running'] is False
            assert status['git_configured'] is True
            assert status['raindrop_configured'] is True
            assert status['git_interval_hours'] == 6.0
            assert status['raindrop_interval_hours'] == 2.0
    
    def test_get_detailed_status(self, scheduler, temp_dirs):
        """Test getting detailed scheduler status"""
        scheduler.config.data_dir = temp_dirs["data_dir"]
        scheduler.config.content_dir = temp_dirs["content_dir"]
        scheduler.recent_errors = ["Test error"]
        
        # Create some test files
        test_file = temp_dirs["data_dir"] / "test.txt"
        test_file.write_text("test")
        
        with patch.object(scheduler, '_get_git_remote', return_value="test_remote"):
            status = scheduler.get_detailed_status()
            
            assert status['data_dir_exists'] is True
            assert status['content_dir_exists'] is False  # Wasn't created
            assert status['git_remote'] == "test_remote"
            assert status['last_sync_errors'] == ["Test error"]
            assert status['file_counts']['data_content'] == 1
            assert 'config' in status


class TestGlobalScheduler:
    """Test the global scheduler instance"""
    
    def test_get_scheduler_singleton(self):
        """Test that get_scheduler returns the same instance"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        
        assert scheduler1 is scheduler2
    
    def test_get_scheduler_type(self):
        """Test that get_scheduler returns a Scheduler instance"""
        scheduler = get_scheduler()
        
        assert isinstance(scheduler, Scheduler)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])