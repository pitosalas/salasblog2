#!/usr/bin/env python3
"""
Test script to reproduce rsync behavior when editing posts
"""

import tempfile
import subprocess
import time
from pathlib import Path
import os

def run_rsync(source, dest):
    """Run rsync command and return result"""
    cmd = ["rsync", "-av", "--update", f"{source}/", f"{dest}/"]
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Return code: {result.returncode}")
    print(f"STDOUT:\n{result.stdout}")
    if result.stderr:
        print(f"STDERR:\n{result.stderr}")
    return result

def create_test_post(directory, filename, content, title="Test Post"):
    """Create a test blog post with frontmatter"""
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
    """Get file modification time and size"""
    if file_path.exists():
        stat = file_path.stat()
        return {
            'mtime': stat.st_mtime,
            'size': stat.st_size,
            'content': file_path.read_text()
        }
    return None

def main():
    print("=== Testing rsync behavior with edited posts ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create source and destination directories (simulating /app/content and /data/content)
        source_dir = Path(temp_dir) / "app_content" / "blog"
        dest_dir = Path(temp_dir) / "data_content" / "blog"
        
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)
        
        print(f"Source: {source_dir}")
        print(f"Destination: {dest_dir}")
        print()
        
        # Step 1: Create initial post in source
        print("1. Creating initial post...")
        post_file = "test-post.md"
        source_post = create_test_post(source_dir, post_file, "This is the original content.")
        source_info_1 = get_file_info(source_post)
        print(f"   Created: {source_post}")
        print(f"   Size: {source_info_1['size']} bytes")
        print(f"   Mtime: {source_info_1['mtime']}")
        print()
        
        # Step 2: Initial sync to volume (simulates first backup)
        print("2. Initial sync to volume...")
        result = run_rsync(source_dir.parent, dest_dir.parent)
        dest_post = dest_dir / post_file
        dest_info_1 = get_file_info(dest_post)
        print(f"   Destination file exists: {dest_post.exists()}")
        if dest_post.exists():
            print(f"   Dest size: {dest_info_1['size']} bytes")
            print(f"   Dest mtime: {dest_info_1['mtime']}")
        print()
        
        # Step 3: Wait a bit to ensure different timestamp
        print("3. Waiting 2 seconds for timestamp difference...")
        time.sleep(2)
        print()
        
        # Step 4: Edit the post (simulates MarsEdit editing)
        print("4. Editing the post...")
        source_post = create_test_post(source_dir, post_file, "This is the EDITED content with more text!")
        source_info_2 = get_file_info(source_post)
        print(f"   Edited: {source_post}")
        print(f"   New size: {source_info_2['size']} bytes")
        print(f"   New mtime: {source_info_2['mtime']}")
        print(f"   Content changed: {source_info_1['content'] != source_info_2['content']}")
        print(f"   File is newer: {source_info_2['mtime'] > dest_info_1['mtime']}")
        print()
        
        # Step 5: Sync to volume again (this should copy the edited file)
        print("5. Syncing edited post to volume...")
        result = run_rsync(source_dir.parent, dest_dir.parent)
        dest_info_2 = get_file_info(dest_post)
        print(f"   Destination updated: {dest_info_2['mtime'] != dest_info_1['mtime']}")
        print(f"   Content matches: {source_info_2['content'] == dest_info_2['content']}")
        print()
        
        # Step 6: Test case where destination is newer (shouldn't copy)
        print("6. Testing case where destination is artificially newer...")
        # Make destination file newer by touching it
        future_time = time.time() + 3600  # 1 hour in future
        os.utime(dest_post, (future_time, future_time))
        
        # Edit source again
        time.sleep(1)
        source_post = create_test_post(source_dir, post_file, "This is ANOTHER edit that should be blocked.")
        source_info_3 = get_file_info(source_post)
        dest_info_before = get_file_info(dest_post)
        
        print(f"   Source mtime: {source_info_3['mtime']}")
        print(f"   Dest mtime: {dest_info_before['mtime']}")
        print(f"   Source is newer: {source_info_3['mtime'] > dest_info_before['mtime']}")
        
        result = run_rsync(source_dir.parent, dest_dir.parent)
        dest_info_after = get_file_info(dest_post)
        print(f"   File copied (should be False): {dest_info_after['mtime'] != dest_info_before['mtime']}")
        print()
        
        print("=== Test Summary ===")
        print("✓ Initial sync should work")
        print("✓ Editing and resyncing should work if source is newer")
        print("✓ Sync should be blocked if destination is newer (--update flag)")
        print("\nIf your edit didn't sync, check:")
        print("1. File timestamps - source must be newer than destination")
        print("2. Check if the file was actually modified")
        print("3. Verify rsync command and permissions")

if __name__ == "__main__":
    main()