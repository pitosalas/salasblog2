#!/usr/bin/env python3
"""
Debug script to check content directory structure and find missing files.
Development/troubleshooting utility for Fly.io deployment issues.

Usage: python scripts/debug_content_dirs.py
"""

import os
from pathlib import Path
import subprocess

def check_directory(path_str, description):
    """Check a directory and report its status"""
    path = Path(path_str)
    print(f"\n=== {description} ===")
    print(f"Path: {path}")
    print(f"Exists: {path.exists()}")
    print(f"Is directory: {path.is_dir()}")
    print(f"Is symlink: {path.is_symlink()}")
    
    if path.is_symlink():
        print(f"Symlink target: {path.readlink()}")
    
    if path.exists() and path.is_dir():
        try:
            files = list(path.rglob("*.md"))
            print(f"Markdown files found: {len(files)}")
            for f in files:
                stat = f.stat()
                print(f"  - {f} (size: {stat.st_size}, mtime: {stat.st_mtime})")
        except Exception as e:
            print(f"Error listing files: {e}")

def run_find_command(pattern, description):
    """Run find command to locate files"""
    print(f"\n=== {description} ===")
    try:
        result = subprocess.run(['find', '/', '-name', pattern, '-type', 'f', '2>/dev/null'], 
                              capture_output=True, text=True, timeout=10)
        if result.stdout:
            print(f"Found files matching '{pattern}':")
            for line in result.stdout.strip().split('\n'):
                if line:
                    print(f"  {line}")
        else:
            print(f"No files found matching '{pattern}'")
    except Exception as e:
        print(f"Error running find: {e}")

def main():
    print("=== Content Directory Debug Analysis ===")
    
    # Check current working directory
    cwd = Path.cwd()
    print(f"Current working directory: {cwd}")
    
    # Check key directories
    check_directory("/app", "App Directory")
    check_directory("/app/content", "App Content Directory")
    check_directory("/app/content/blog", "App Blog Directory")
    check_directory("/data", "Data Volume")
    check_directory("/data/content", "Data Content Directory") 
    check_directory("/data/content/blog", "Data Blog Directory")
    
    # Check for any markdown files anywhere
    run_find_command("*.md", "All Markdown Files on System")
    
    # Check blogger API paths
    print(f"\n=== Blogger API Configuration ===")
    try:
        # Simulate blogger API initialization
        from pathlib import Path
        root_dir = Path.cwd()
        blog_dir = root_dir / "content" / "blog"
        print(f"Blogger API root_dir: {root_dir}")
        print(f"Blogger API blog_dir: {blog_dir}")
        print(f"Blog dir exists: {blog_dir.exists()}")
        print(f"Blog dir is symlink: {blog_dir.is_symlink()}")
    except Exception as e:
        print(f"Error checking blogger API paths: {e}")
    
    # Check recent file modifications
    print(f"\n=== Recently Modified Files ===")
    try:
        result = subprocess.run(['find', '/', '-name', '*.md', '-mtime', '-1', '2>/dev/null'],
                              capture_output=True, text=True, timeout=10)
        if result.stdout:
            print("Markdown files modified in last 24 hours:")
            for line in result.stdout.strip().split('\n'):
                if line:
                    print(f"  {line}")
        else:
            print("No recently modified markdown files found")
    except Exception as e:
        print(f"Error finding recent files: {e}")

if __name__ == "__main__":
    main()