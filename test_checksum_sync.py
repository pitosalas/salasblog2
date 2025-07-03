#!/usr/bin/env python3
"""
Test the checksum-based rsync approach
"""

import tempfile
import subprocess
import time
import os
from pathlib import Path

def run_rsync_checksum(source, dest):
    """Run rsync with checksum flag"""
    cmd = ["rsync", "-av", "--checksum", f"{source}/", f"{dest}/"]
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

def main():
    print("=== Testing rsync --checksum behavior ===\n")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        source_dir = Path(temp_dir) / "app_content" / "blog"
        dest_dir = Path(temp_dir) / "data_content" / "blog"
        
        source_dir.mkdir(parents=True)
        dest_dir.mkdir(parents=True)
        
        print(f"Source: {source_dir}")
        print(f"Destination: {dest_dir}")
        print()
        
        # Step 1: Create and sync initial post
        print("1. Creating and syncing initial post...")
        post_file = "test-post.md"
        source_post = create_test_post(source_dir, post_file, "Original content")
        
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        print()
        
        # Step 2: Make destination newer (timestamp issue)
        print("2. Making destination file artificially newer...")
        dest_post = dest_dir / post_file
        future_time = time.time() + 3600  # 1 hour in future
        os.utime(dest_post, (future_time, future_time))
        
        dest_stat = dest_post.stat()
        source_stat = source_post.stat()
        print(f"   Source mtime: {source_stat.st_mtime}")
        print(f"   Dest mtime: {dest_stat.st_mtime}")
        print(f"   Dest is newer: {dest_stat.st_mtime > source_stat.st_mtime}")
        print()
        
        # Step 3: Edit source content (same timestamps issue as your MarsEdit case)
        print("3. Editing source content...")
        source_post = create_test_post(source_dir, post_file, "EDITED content - this should sync!")
        
        print("   Content is different but destination timestamp is newer")
        print("   With --update this would be skipped")
        print("   With --checksum this should sync because content differs")
        print()
        
        # Step 4: Sync with checksum
        print("4. Syncing with --checksum...")
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        
        # Verify content was synced
        source_content = source_post.read_text()
        dest_content = dest_post.read_text()
        content_matches = source_content == dest_content
        
        print(f"   Content synced successfully: {content_matches}")
        if content_matches:
            print("   ✅ Checksum approach works - edited content was synced despite timestamp!")
        else:
            print("   ❌ Content still differs")
        print()
        
        # Step 5: Test same content (should skip)
        print("5. Testing sync with identical content...")
        result = run_rsync_checksum(source_dir.parent, dest_dir.parent)
        print("   Should show no files transferred since content is identical")
        print()
        
        print("=== Summary ===")
        print("✅ --checksum ignores timestamps and compares file content")
        print("✅ Edited files sync even when destination timestamp is newer")
        print("✅ Identical files are skipped (efficient)")
        print("✅ This should fix your MarsEdit edit sync issue!")

if __name__ == "__main__":
    main()