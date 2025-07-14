#!/usr/bin/env python3
"""
Script to remove duplicate raindrop files based on their IDs.
Reads the cache file to identify which raindrop IDs have been downloaded,
then looks for duplicate files in the raindrops directory.
"""

import os
import json
import re
from pathlib import Path

def load_cache():
    """Load the raindrop cache file."""
    cache_files = [
        "/data/content/.rd_cache.json",
        "/Users/pitosalas/mydev/salasblog2/content/.rd_cache.json"
    ]
    
    for cache_file in cache_files:
        if os.path.exists(cache_file):
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    print("No cache file found!")
    return None

def find_raindrop_files():
    """Find all raindrop markdown files."""
    raindrop_dirs = [
        "/data/content/raindrops",
        "/Users/pitosalas/mydev/salasblog2/content/raindrops"
    ]
    
    files = []
    for directory in raindrop_dirs:
        if os.path.exists(directory):
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith('.md'):
                        files.append(os.path.join(root, filename))
    
    return files

def extract_raindrop_id_from_file(filepath):
    """Extract raindrop ID from a markdown file's frontmatter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Look for raindrop_id in frontmatter
        match = re.search(r'raindrop_id:\s*["\']*(\d+)["\']*', content)
        if match:
            return match.group(1)
            
        # Alternative: look for raindrop_id in filename
        filename = os.path.basename(filepath)
        match = re.search(r'raindrop_(\d+)', filename)
        if match:
            return match.group(1)
            
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        
    return None

def remove_duplicates():
    """Remove duplicate raindrop files."""
    cache = load_cache()
    if not cache:
        return
        
    downloaded_ids = set(cache.get('downloaded', []))
    print(f"Found {len(downloaded_ids)} downloaded raindrop IDs in cache")
    
    files = find_raindrop_files()
    print(f"Found {len(files)} raindrop files")
    
    if not files:
        print("No raindrop files found to process")
        return
    
    # Group files by raindrop ID
    files_by_id = {}
    files_without_id = []
    
    for filepath in files:
        raindrop_id = extract_raindrop_id_from_file(filepath)
        if raindrop_id:
            if raindrop_id not in files_by_id:
                files_by_id[raindrop_id] = []
            files_by_id[raindrop_id].append(filepath)
        else:
            files_without_id.append(filepath)
    
    print(f"Files without raindrop ID: {len(files_without_id)}")
    
    # Find and remove duplicates
    duplicates_removed = 0
    for raindrop_id, file_list in files_by_id.items():
        if len(file_list) > 1:
            print(f"Raindrop ID {raindrop_id} has {len(file_list)} duplicate files:")
            
            # Keep the first file, remove the rest
            for i, filepath in enumerate(file_list):
                if i == 0:
                    print(f"  KEEPING: {filepath}")
                else:
                    print(f"  REMOVING: {filepath}")
                    try:
                        os.remove(filepath)
                        duplicates_removed += 1
                    except Exception as e:
                        print(f"    Error removing {filepath}: {e}")
    
    print(f"\nRemoved {duplicates_removed} duplicate raindrop files")
    
    # Report on files without IDs
    if files_without_id:
        print(f"\nFiles without raindrop IDs (manual review needed):")
        for filepath in files_without_id:
            print(f"  {filepath}")

if __name__ == "__main__":
    remove_duplicates()