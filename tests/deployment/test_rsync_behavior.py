"""
Tests for rsync behavior with --update flag used in volume synchronization.
Tests deployment scenarios for Fly.io persistent volume management.
"""
import pytest
import tempfile
import subprocess
import time
from pathlib import Path
import os


@pytest.fixture
def temp_directories():
    """Create temporary source and destination directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir) / "app_content" / "blog"
        dest_dir = Path(temp_dir) / "data_content" / "blog"
        
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)
        
        yield source_dir, dest_dir


def run_rsync_update(source, dest):
    """Run rsync with --update flag and return result."""
    cmd = ["rsync", "-av", "--update", f"{source}/", f"{dest}/"]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    return result


def create_test_post(directory, filename, content, title="Test Post"):
    """Create a test blog post with frontmatter."""
    post_content = f"""---
title: "{title}"
date: "2025-07-03"
type: "blog"
category: "General"
---

{content}
"""
    file_path = Path(directory) / filename
    with open(file_path, 'w') as f:
        f.write(post_content)
    return file_path


def get_file_info(file_path):
    """Get file modification time, size, and content."""
    if file_path.exists():
        stat = file_path.stat()
        return {
            'mtime': stat.st_mtime,
            'size': stat.st_size,
            'content': file_path.read_text()
        }
    return None


@pytest.mark.deployment
class TestRsyncUpdateBehavior:
    """Test rsync --update flag behavior for volume synchronization."""
    
    def test_initial_sync(self, temp_directories):
        """Test initial file sync to volume."""
        source_dir, dest_dir = temp_directories
        
        # Create initial post in source
        post_file = "test-post.md"
        source_post = create_test_post(source_dir, post_file, "Original content")
        source_info = get_file_info(source_post)
        
        # Initial sync
        result = run_rsync_update(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, f"Initial sync failed: {result.stderr}"
        
        # Verify file was copied
        dest_post = dest_dir / post_file
        assert dest_post.exists(), "File should be copied to destination"
        
        dest_info = get_file_info(dest_post)
        assert dest_info['content'] == source_info['content'], "Content should match"
    
    def test_edit_and_resync(self, temp_directories):
        """Test editing file and resyncing (newer source should copy)."""
        source_dir, dest_dir = temp_directories
        post_file = "edit-test.md"
        
        # Create and sync initial file
        source_post = create_test_post(source_dir, post_file, "Original content")
        run_rsync_update(source_dir.parent, dest_dir.parent)
        
        dest_post = dest_dir / post_file
        initial_dest_info = get_file_info(dest_post)
        
        # Wait to ensure different timestamp
        time.sleep(1)
        
        # Edit the source file
        edited_post = create_test_post(source_dir, post_file, "EDITED content")
        edited_info = get_file_info(edited_post)
        
        # Verify source is newer
        assert edited_info['mtime'] > initial_dest_info['mtime'], "Source should be newer than destination"
        
        # Sync edited file
        result = run_rsync_update(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, f"Edit sync failed: {result.stderr}"
        
        # Verify content was updated
        final_dest_info = get_file_info(dest_post)
        assert final_dest_info['content'] == edited_info['content'], "Destination should have updated content"
        assert "EDITED content" in final_dest_info['content'], "Should contain edited content"
    
    def test_destination_newer_blocks_sync(self, temp_directories):
        """Test that newer destination file blocks sync with --update flag."""
        source_dir, dest_dir = temp_directories
        post_file = "newer-dest.md"
        
        # Create and sync initial file
        source_post = create_test_post(source_dir, post_file, "Original content")
        run_rsync_update(source_dir.parent, dest_dir.parent)
        
        dest_post = dest_dir / post_file
        
        # Make destination file artificially newer
        future_time = time.time() + 3600  # 1 hour in future
        os.utime(dest_post, (future_time, future_time))
        
        dest_before_info = get_file_info(dest_post)
        
        # Edit source file (but it will be older than destination)
        time.sleep(1)
        create_test_post(source_dir, post_file, "This edit should be BLOCKED")
        source_info = get_file_info(source_post)
        
        # Verify source is older than destination
        assert source_info['mtime'] < dest_before_info['mtime'], "Source should be older than destination"
        
        # Attempt sync - should not copy due to --update flag
        result = run_rsync_update(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Rsync should succeed but not copy files"
        
        # Verify destination wasn't changed
        dest_after_info = get_file_info(dest_post)
        assert dest_after_info['content'] == dest_before_info['content'], "Destination should be unchanged"
        assert "BLOCKED" not in dest_after_info['content'], "Blocked content should not appear"
    
    def test_same_timestamp_no_copy(self, temp_directories):
        """Test that files with same timestamp are not unnecessarily copied."""
        source_dir, dest_dir = temp_directories
        post_file = "same-timestamp.md"
        
        # Create and sync initial file
        source_post = create_test_post(source_dir, post_file, "Same content")
        run_rsync_update(source_dir.parent, dest_dir.parent)
        
        dest_post = dest_dir / post_file
        
        # Get initial info
        source_info = get_file_info(source_post)
        dest_info = get_file_info(dest_post)
        
        # Sync again - should be no-op
        result = run_rsync_update(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Second sync should succeed"
        
        # Should show no files transferred
        assert "sent" in result.stdout.lower(), "Should show transfer statistics"
        # With no changes, rsync typically shows minimal transfer
    
    def test_multiple_files_sync(self, temp_directories):
        """Test syncing multiple files with different modification states."""
        source_dir, dest_dir = temp_directories
        
        # Create multiple files
        file1 = create_test_post(source_dir, "file1.md", "Content 1")
        file2 = create_test_post(source_dir, "file2.md", "Content 2") 
        file3 = create_test_post(source_dir, "file3.md", "Content 3")
        
        # Initial sync
        result = run_rsync_update(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Multi-file sync should succeed"
        
        # Verify all files copied
        for filename in ["file1.md", "file2.md", "file3.md"]:
            dest_file = dest_dir / filename
            assert dest_file.exists(), f"{filename} should be copied"
        
        # Edit one file
        time.sleep(1)
        create_test_post(source_dir, "file2.md", "UPDATED Content 2")
        
        # Sync again
        result = run_rsync_update(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Selective sync should succeed"
        
        # Verify only edited file was updated
        dest_file2 = dest_dir / "file2.md"
        updated_content = get_file_info(dest_file2)['content']
        assert "UPDATED Content 2" in updated_content, "File 2 should be updated"


@pytest.mark.deployment
@pytest.mark.skipif(subprocess.run(["which", "rsync"], capture_output=True).returncode != 0, 
                   reason="rsync not available")
class TestRsyncAvailability:
    """Test that rsync is available for deployment scenarios."""
    
    def test_rsync_command_available(self):
        """Test that rsync command is available."""
        result = subprocess.run(["rsync", "--version"], capture_output=True, text=True)
        assert result.returncode == 0, "rsync should be available"
        assert "rsync" in result.stdout.lower(), "Should show rsync version info"
    
    def test_rsync_update_flag_supported(self):
        """Test that rsync supports --update flag."""
        result = subprocess.run(["rsync", "--help"], capture_output=True, text=True)
        assert result.returncode == 0, "rsync help should work"
        # Check for either long form --update or short form -u
        has_update = "--update" in result.stdout or "-u" in result.stdout
        assert has_update, "rsync should support --update flag (or -u short form)"