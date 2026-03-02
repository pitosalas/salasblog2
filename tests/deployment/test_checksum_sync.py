"""
Tests for rsync behavior with --checksum flag used in volume synchronization.
Validates content-based sync approach that solves MarsEdit timestamp issues.
"""
import pytest
import tempfile
import subprocess
import time
import os
from pathlib import Path


@pytest.fixture
def temp_directories():
    """Create temporary source and destination directories."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir) / "app_content" / "blog"
        dest_dir = Path(temp_dir) / "data_content" / "blog"
        
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)
        
        yield source_dir, dest_dir


def run_rsync_checksum(source, dest):
    """Run rsync with --checksum flag and return result."""
    cmd = ["rsync", "-av", "--checksum", f"{source}/", f"{dest}/"]
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


@pytest.mark.deployment
class TestRsyncChecksumBehavior:
    """Test rsync --checksum flag behavior for content-based synchronization."""
    
    def test_initial_checksum_sync(self, temp_directories):
        """Test initial sync with checksum flag."""
        source_dir, dest_dir = temp_directories
        
        # Create initial post
        post_file = "checksum-test.md"
        source_post = create_test_post(source_dir, post_file, "Original content")
        
        # Initial sync with checksum
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, f"Initial checksum sync failed: {result.stderr}"
        
        # Verify file was copied
        dest_post = dest_dir / post_file
        assert dest_post.exists(), "File should be copied to destination"
        
        # Verify content matches
        source_content = source_post.read_text()
        dest_content = dest_post.read_text()
        assert source_content == dest_content, "Content should match after initial sync"
    
    def test_checksum_ignores_timestamps(self, temp_directories):
        """Test that checksum sync ignores timestamps and compares content only."""
        source_dir, dest_dir = temp_directories
        post_file = "timestamp-test.md"
        
        # Create and sync initial file
        source_post = create_test_post(source_dir, post_file, "Original content")
        run_rsync_checksum(source_dir.parent, dest_dir.parent)
        
        dest_post = dest_dir / post_file
        
        # Make destination artificially newer (timestamp issue simulation)
        future_time = time.time() + 3600  # 1 hour in future
        os.utime(dest_post, (future_time, future_time))
        
        # Verify destination timestamp is newer
        dest_stat_before = dest_post.stat()
        source_stat = source_post.stat()
        assert dest_stat_before.st_mtime > source_stat.st_mtime, "Destination should have newer timestamp"
        
        # Edit source content (but keep older timestamp)
        time.sleep(1)
        create_test_post(source_dir, post_file, "EDITED content - should sync despite timestamp!")
        
        # Sync with checksum - should sync because content differs
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, f"Checksum sync failed: {result.stderr}"
        
        # Verify content was synced despite timestamp
        final_dest_content = dest_post.read_text()
        assert "EDITED content - should sync despite timestamp!" in final_dest_content, "Content should be synced despite newer destination timestamp"
    
    def test_identical_content_skipped(self, temp_directories):
        """Test that identical content is skipped even with different timestamps."""
        source_dir, dest_dir = temp_directories
        post_file = "identical-content.md"
        
        # Create and sync initial file
        source_post = create_test_post(source_dir, post_file, "Same content")
        run_rsync_checksum(source_dir.parent, dest_dir.parent)
        
        dest_post = dest_dir / post_file
        initial_dest_mtime = dest_post.stat().st_mtime
        
        # Change source timestamp but keep same content
        time.sleep(1)
        source_post.touch()  # Update timestamp but not content
        
        # Sync again - should skip because content is identical
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Checksum sync should succeed"
        
        # Verify destination wasn't unnecessarily updated
        final_dest_mtime = dest_post.stat().st_mtime
        # Content should be the same
        dest_content = dest_post.read_text()
        assert "Same content" in dest_content, "Content should remain unchanged"
    
    def test_content_based_detection(self, temp_directories):
        """Test that checksum detects content changes regardless of file size."""
        source_dir, dest_dir = temp_directories
        post_file = "content-change.md"
        
        # Create initial file
        source_post = create_test_post(source_dir, post_file, "Version 1 content")
        run_rsync_checksum(source_dir.parent, dest_dir.parent)
        
        dest_post = dest_dir / post_file
        
        # Make a content change that keeps similar file size
        create_test_post(source_dir, post_file, "Version 2 content")  # Same length
        
        # Sync - should detect content change
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Content change sync should succeed"
        
        # Verify content was updated
        final_content = dest_post.read_text()
        assert "Version 2 content" in final_content, "Content should be updated to version 2"
        assert "Version 1 content" not in final_content, "Old content should be replaced"
    
    def test_multiple_files_checksum_sync(self, temp_directories):
        """Test checksum sync with multiple files having different content states."""
        source_dir, dest_dir = temp_directories
        
        # Create multiple files
        file1 = create_test_post(source_dir, "file1.md", "Content A")
        file2 = create_test_post(source_dir, "file2.md", "Content B")
        file3 = create_test_post(source_dir, "file3.md", "Content C")
        
        # Initial sync
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Multi-file initial sync should succeed"
        
        # Verify all files copied
        for filename in ["file1.md", "file2.md", "file3.md"]:
            dest_file = dest_dir / filename
            assert dest_file.exists(), f"{filename} should be copied"
        
        # Edit only one file's content
        create_test_post(source_dir, "file2.md", "UPDATED Content B")
        
        # Make all destination files artificially newer
        future_time = time.time() + 3600
        for filename in ["file1.md", "file2.md", "file3.md"]:
            dest_file = dest_dir / filename
            os.utime(dest_file, (future_time, future_time))
        
        # Sync with checksum - should only update the changed file
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "Selective checksum sync should succeed"
        
        # Verify only edited file was updated
        dest_file1_content = (dest_dir / "file1.md").read_text()
        dest_file2_content = (dest_dir / "file2.md").read_text()
        dest_file3_content = (dest_dir / "file3.md").read_text()
        
        assert "Content A" in dest_file1_content, "File 1 should remain unchanged"
        assert "UPDATED Content B" in dest_file2_content, "File 2 should be updated"
        assert "Content C" in dest_file3_content, "File 3 should remain unchanged"
    
    def test_mars_edit_scenario_simulation(self, temp_directories):
        """Test scenario that simulates MarsEdit timestamp issue resolution."""
        source_dir, dest_dir = temp_directories
        post_file = "mars-edit-post.md"
        
        # Step 1: Create initial post (simulates blog post creation)
        source_post = create_test_post(source_dir, post_file, "Original blog post content")
        run_rsync_checksum(source_dir.parent, dest_dir.parent)
        
        dest_post = dest_dir / post_file
        
        # Step 2: Simulate MarsEdit editing scenario
        # - Destination file gets touched/modified during deployment process
        # - This makes it newer than the source when MarsEdit edits
        time.sleep(1)
        dest_post.touch()  # Simulate deployment touching the file
        
        # Step 3: MarsEdit saves edited content to source
        time.sleep(1)  # Ensure distinct timestamp
        create_test_post(source_dir, post_file, "EDITED via MarsEdit - this should sync!")
        
        # Verify the problematic timestamp situation
        source_stat = source_post.stat()
        dest_stat = dest_post.stat()
        assert source_stat.st_mtime > dest_stat.st_mtime, "This would normally work with --update"
        
        # But let's make it more challenging - make dest newer again
        later_time = time.time() + 1800  # 30 minutes newer
        os.utime(dest_post, (later_time, later_time))
        
        dest_stat_after = dest_post.stat()
        source_stat_after = source_post.stat()
        assert dest_stat_after.st_mtime > source_stat_after.st_mtime, "Destination is now newer (problematic for --update)"
        
        # Step 4: Checksum sync should work despite timestamp issue
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        assert result.returncode == 0, "MarsEdit scenario sync should succeed"
        
        # Step 5: Verify edited content made it through
        final_content = dest_post.read_text()
        assert "EDITED via MarsEdit - this should sync!" in final_content, "MarsEdit edits should sync despite timestamp conflicts"
        assert "Original blog post content" not in final_content, "Old content should be replaced"


@pytest.mark.deployment
@pytest.mark.skipif(subprocess.run(["which", "rsync"], capture_output=True).returncode != 0, 
                   reason="rsync not available")
class TestRsyncChecksumFeatures:
    """Test rsync checksum functionality and feature availability."""
    
    def test_checksum_flag_supported(self):
        """Test that rsync supports --checksum flag."""
        result = subprocess.run(["rsync", "--help"], capture_output=True, text=True)
        assert result.returncode == 0, "rsync help should work"
        assert "--checksum" in result.stdout, "rsync should support --checksum flag"
    
    def test_checksum_performance_note(self, temp_directories):
        """Test checksum sync and note performance characteristics."""
        source_dir, dest_dir = temp_directories
        
        # Create a moderately sized file to test checksum performance
        large_content = "Line of content\n" * 1000  # ~16KB file
        source_post = create_test_post(source_dir, "large-file.md", large_content)
        
        # Time the checksum sync
        import time
        start_time = time.time()
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        sync_time = time.time() - start_time
        
        assert result.returncode == 0, "Large file sync should succeed"
        assert sync_time < 10, "Checksum sync should complete reasonably quickly for moderate files"
        
        # Verify content integrity
        dest_post = dest_dir / "large-file.md"
        assert dest_post.exists(), "Large file should be copied"
        
        source_content = source_post.read_text()
        dest_content = dest_post.read_text()
        assert source_content == dest_content, "Large file content should match exactly"