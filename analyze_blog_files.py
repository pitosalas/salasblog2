#!/usr/bin/env python3
"""
Analyze all markdown files in content/blog directory for:
1. HTML content detection
2. Frontmatter consistency analysis
"""

import os
import re
import yaml
from pathlib import Path
from collections import defaultdict, Counter
import sys

def extract_frontmatter_and_content(file_path):
    """Extract frontmatter and content from a markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if file starts with frontmatter
        if not content.startswith('---'):
            return None, content
            
        # Find the end of frontmatter
        lines = content.split('\n')
        frontmatter_end = -1
        for i, line in enumerate(lines[1:], 1):
            if line.strip() == '---':
                frontmatter_end = i
                break
        
        if frontmatter_end == -1:
            return None, content
            
        # Extract frontmatter and content
        frontmatter_text = '\n'.join(lines[1:frontmatter_end])
        content_text = '\n'.join(lines[frontmatter_end + 1:])
        
        # Parse frontmatter
        try:
            frontmatter = yaml.safe_load(frontmatter_text)
            return frontmatter, content_text
        except yaml.YAMLError:
            return None, content_text
            
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None, ""

def detect_html_tags(content):
    """Detect HTML tags in content."""
    # Look for HTML tags (excluding markdown link references)
    html_tag_pattern = r'<[^>]+>'
    html_tags = re.findall(html_tag_pattern, content)
    
    # Filter out markdown link references like [text](url)
    actual_html_tags = []
    for tag in html_tags:
        # Skip if it's not a proper HTML tag
        if not re.match(r'</?[a-zA-Z][^>]*>', tag):
            continue
        actual_html_tags.append(tag)
    
    return actual_html_tags

def analyze_frontmatter_fields(frontmatter_data):
    """Analyze frontmatter fields across all files."""
    field_stats = defaultdict(lambda: {'count': 0, 'types': Counter(), 'values': Counter()})
    
    for file_path, frontmatter in frontmatter_data.items():
        if frontmatter is None:
            continue
            
        for field, value in frontmatter.items():
            field_stats[field]['count'] += 1
            field_stats[field]['types'][type(value).__name__] += 1
            
            # Store sample values for analysis
            if isinstance(value, (str, int, float, bool)):
                field_stats[field]['values'][str(value)] += 1
            elif isinstance(value, list):
                field_stats[field]['values'][f"list_len_{len(value)}"] += 1
            elif isinstance(value, dict):
                field_stats[field]['values'][f"dict_keys_{len(value)}"] += 1
    
    return field_stats

def main():
    blog_dir = Path("/Users/pitosalas/mydev/salasblog2/content/blog")
    
    # Get all markdown files
    md_files = list(blog_dir.glob("*.md"))
    total_files = len(md_files)
    
    print(f"Analyzing {total_files} markdown files in {blog_dir}")
    print("=" * 60)
    
    # Data collection
    frontmatter_data = {}
    html_findings = {}
    files_with_no_frontmatter = []
    files_with_invalid_frontmatter = []
    
    # Process each file
    for file_path in md_files:
        frontmatter, content = extract_frontmatter_and_content(file_path)
        
        # Store frontmatter data
        if frontmatter is None:
            if content.startswith('---'):
                files_with_invalid_frontmatter.append(str(file_path))
            else:
                files_with_no_frontmatter.append(str(file_path))
        else:
            frontmatter_data[str(file_path)] = frontmatter
        
        # Check for HTML tags
        html_tags = detect_html_tags(content)
        if html_tags:
            html_findings[str(file_path)] = html_tags
    
    # Generate report
    print("\n1. FRONTMATTER ANALYSIS")
    print("-" * 40)
    print(f"Files with valid frontmatter: {len(frontmatter_data)}")
    print(f"Files with no frontmatter: {len(files_with_no_frontmatter)}")
    print(f"Files with invalid frontmatter: {len(files_with_invalid_frontmatter)}")
    
    if files_with_no_frontmatter:
        print("\nFiles with no frontmatter:")
        for file_path in files_with_no_frontmatter[:10]:  # Show first 10
            print(f"  - {Path(file_path).name}")
        if len(files_with_no_frontmatter) > 10:
            print(f"  ... and {len(files_with_no_frontmatter) - 10} more")
    
    if files_with_invalid_frontmatter:
        print("\nFiles with invalid frontmatter:")
        for file_path in files_with_invalid_frontmatter[:10]:  # Show first 10
            print(f"  - {Path(file_path).name}")
        if len(files_with_invalid_frontmatter) > 10:
            print(f"  ... and {len(files_with_invalid_frontmatter) - 10} more")
    
    # Analyze frontmatter fields
    if frontmatter_data:
        field_stats = analyze_frontmatter_fields(frontmatter_data)
        
        print("\n2. FRONTMATTER FIELD ANALYSIS")
        print("-" * 40)
        print(f"Total files with frontmatter: {len(frontmatter_data)}")
        print("\nField usage statistics:")
        
        for field, stats in sorted(field_stats.items()):
            print(f"\n  {field}:")
            print(f"    Present in: {stats['count']}/{len(frontmatter_data)} files ({stats['count']/len(frontmatter_data)*100:.1f}%)")
            print(f"    Types: {dict(stats['types'])}")
            
            # Show most common values for fields with limited variety
            if len(stats['values']) <= 20:
                print(f"    Values: {dict(stats['values'].most_common(10))}")
            else:
                print(f"    Values: {len(stats['values'])} unique values")
    
    # HTML content analysis
    print("\n3. HTML CONTENT ANALYSIS")
    print("-" * 40)
    print(f"Files containing HTML tags: {len(html_findings)}")
    
    if html_findings:
        print("\nFiles with HTML content:")
        for file_path, html_tags in list(html_findings.items())[:10]:  # Show first 10
            print(f"  - {Path(file_path).name}")
            unique_tags = set(html_tags)
            print(f"    Tags: {', '.join(sorted(unique_tags))}")
        
        if len(html_findings) > 10:
            print(f"  ... and {len(html_findings) - 10} more files with HTML")
        
        # Summary of all HTML tags found
        all_html_tags = []
        for tags in html_findings.values():
            all_html_tags.extend(tags)
        
        tag_counter = Counter(all_html_tags)
        print(f"\nMost common HTML tags found:")
        for tag, count in tag_counter.most_common(10):
            print(f"  {tag}: {count} occurrences")
    
    # Summary
    print("\n4. SUMMARY")
    print("-" * 40)
    print(f"Total files analyzed: {total_files}")
    print(f"Files with valid frontmatter: {len(frontmatter_data)} ({len(frontmatter_data)/total_files*100:.1f}%)")
    print(f"Files with HTML content: {len(html_findings)} ({len(html_findings)/total_files*100:.1f}%)")
    
    if frontmatter_data:
        all_fields = set()
        for fm in frontmatter_data.values():
            all_fields.update(fm.keys())
        print(f"Total unique frontmatter fields: {len(all_fields)}")
        print(f"Common frontmatter fields: {', '.join(sorted(all_fields))}")

if __name__ == "__main__":
    main()