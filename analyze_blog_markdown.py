#!/usr/bin/env python3
"""
Analyze all markdown files in content/blog directory for:
1. HTML content in markdown files (should be none)
2. Frontmatter consistency across all files
"""

import os
import re
import frontmatter
from pathlib import Path
from collections import defaultdict, Counter

def analyze_blog_markdown():
    blog_dir = Path("content/blog")
    
    if not blog_dir.exists():
        print(f"Directory {blog_dir} does not exist")
        return
    
    # Find all markdown files
    md_files = list(blog_dir.glob("*.md"))
    total_files = len(md_files)
    
    print(f"=== BLOG MARKDOWN ANALYSIS REPORT ===")
    print(f"Total files analyzed: {total_files}")
    print()
    
    # Analyze HTML content and frontmatter
    html_files = []
    frontmatter_fields = defaultdict(set)
    frontmatter_inconsistencies = []
    
    # HTML pattern to detect tags
    html_pattern = re.compile(r'<[^>]+>')
    
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Parse frontmatter
            try:
                post = frontmatter.loads(content)
                
                # Collect frontmatter fields
                for key, value in post.metadata.items():
                    frontmatter_fields[key].add(type(value).__name__)
                
                # Check for HTML in content
                if html_pattern.search(post.content):
                    html_matches = html_pattern.findall(post.content)
                    html_files.append({
                        'file': md_file.name,
                        'html_tags': html_matches[:5]  # First 5 examples
                    })
                    
            except Exception as e:
                frontmatter_inconsistencies.append(f"{md_file.name}: Frontmatter parsing error - {e}")
                
        except Exception as e:
            print(f"Error reading {md_file}: {e}")
    
    # Report HTML findings
    print("=== HTML CONTENT ANALYSIS ===")
    if html_files:
        print(f"⚠️  Found HTML content in {len(html_files)} files:")
        for item in html_files[:10]:  # Show first 10
            print(f"  - {item['file']}")
            print(f"    Examples: {item['html_tags']}")
        if len(html_files) > 10:
            print(f"    ... and {len(html_files) - 10} more files")
    else:
        print("✅ No HTML content found in markdown files")
    print()
    
    # Report frontmatter consistency
    print("=== FRONTMATTER CONSISTENCY ANALYSIS ===")
    print("Fields found across all files:")
    for field, types in sorted(frontmatter_fields.items()):
        print(f"  - {field}: {', '.join(types)}")
    
    print()
    print("Field usage frequency:")
    field_counts = Counter()
    
    # Track files missing fields
    missing_fields = defaultdict(list)
    
    # Count field usage and track missing fields
    for md_file in md_files:
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                post = frontmatter.load(f)
                file_fields = set(post.metadata.keys())
                
                # Count present fields
                for field in file_fields:
                    field_counts[field] += 1
                
                # Track missing fields
                all_expected_fields = {'title', 'category', 'date', 'type', 'subtitle', 'tags', 'wordpress_id'}
                for field in all_expected_fields:
                    if field not in file_fields:
                        missing_fields[field].append(md_file.name)
                        
        except:
            continue
    
    for field, count in field_counts.most_common():
        percentage = (count / total_files) * 100
        print(f"  - {field}: {count}/{total_files} files ({percentage:.1f}%)")
    
    # Report missing fields and provide fix instructions
    if missing_fields:
        print()
        print("=== MISSING FIELDS DETAILS ===")
        for field, files in missing_fields.items():
            print(f"\n❌ Field '{field}' missing from {len(files)} files:")
            for filename in files:
                print(f"  - {filename}")
        
        print()
        print("=== HOW TO FIX MISSING FIELDS ===")
        print("To fix the missing frontmatter fields:")
        print()
        print("1. Open each file listed above")
        print("2. Add the missing fields to the frontmatter section (between the --- lines)")
        print("3. Use these templates:")
        print()
        print("   For missing 'subtitle':")
        print("   subtitle: \"Brief description of the post\"")
        print()
        print("   For missing 'tags':")
        print("   tags: []")
        print("   # or with actual tags:")
        print("   tags: [\"tag1\", \"tag2\"]")
        print()
        print("   For missing 'wordpress_id':")
        print("   wordpress_id: 0")
        print("   # or assign a unique integer ID")
        print()
        print("4. Ensure all frontmatter fields are properly indented and formatted")
        print("5. Re-run this script to verify fixes")
    else:
        print()
        print("✅ All files have consistent frontmatter fields!")
    
    # Report inconsistencies
    if frontmatter_inconsistencies:
        print()
        print("=== FRONTMATTER PARSING ERRORS ===")
        for error in frontmatter_inconsistencies:
            print(f"  - {error}")
    
    print()
    print("=== SUMMARY ===")
    print(f"Total files: {total_files}")
    print(f"Files with HTML: {len(html_files)}")
    print(f"Unique frontmatter fields: {len(frontmatter_fields)}")
    print(f"Parsing errors: {len(frontmatter_inconsistencies)}")

if __name__ == "__main__":
    analyze_blog_markdown()