"""
Pure utility functions for content processing and site generation.
These functions are completely independent and reusable.
"""
import os
import re
import markdown
import frontmatter
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


def _parse_iso_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse ISO date string into datetime object."""
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str):
            # Handle ISO datetime format first
            if 'T' in date_str:
                return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            else:
                # Try to parse ISO format YYYY-MM-DD
                return datetime.strptime(date_str, '%Y-%m-%d')
        return None
    except (ValueError, TypeError):
        return None


def format_date(date_str: Optional[str], format_str: str = '%B %d, %Y') -> str:
    """Format date string using strftime format."""
    date_obj = _parse_iso_date(date_str)
    if date_obj:
        return date_obj.strftime(format_str)
    return str(date_str) if date_str else ''


def create_excerpt_with_info(content: str, max_length: int = None, smart_threshold: int = None) -> tuple[str, bool]:
    """Create excerpt from text content and return truncation status."""
    if not content:
        return '', False
    
    # Get excerpt length from environment variables with defaults
    if max_length is None:
        max_length = int(os.getenv('EXCERPT_LENGTH', '150'))
    if smart_threshold is None:
        smart_threshold = int(os.getenv('EXCERPT_SMART_THRESHOLD', '100'))
    
    # Clean up content - remove newlines and extra spaces
    clean_content = content.replace('\n', ' ').strip()
    
    # If content is short enough, return as-is
    if len(clean_content) <= max_length:
        return clean_content, False
    
    # If content is only slightly longer than max_length, return full content
    if len(clean_content) <= max_length + smart_threshold:
        return clean_content, False
    
    return clean_content[:max_length] + '...', True


def create_excerpt(content: str, max_length: int = None, smart_threshold: int = None) -> str:
    """Create excerpt from text content with ellipsis if truncated."""
    excerpt, _ = create_excerpt_with_info(content, max_length, smart_threshold)
    return excerpt


def parse_date_for_sorting(date_str: Optional[str]) -> datetime:
    """Parse date string for sorting, returns datetime.min if parsing fails."""
    date_obj = _parse_iso_date(date_str)
    return date_obj if date_obj else datetime.min


# Module-level singleton for markdown processor
_md_processor = None

def get_markdown_processor():
    """Get or create the singleton markdown processor."""
    global _md_processor
    if _md_processor is None:
        _md_processor = markdown.Markdown(extensions=['meta', 'toc', 'codehilite'])
    return _md_processor

def process_markdown_to_html(content: str) -> str:
    """Convert markdown content to HTML."""
    if not content:
        return ''
    
    # Reset the processor to avoid state issues between conversions
    processor = get_markdown_processor()
    processor.reset()
    return processor.convert(content)


def parse_frontmatter_file(file_path: Path) -> Dict[str, Any]:
    """Parse markdown file with frontmatter, returns dict with metadata and content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
        # Debug logging to see what content we're actually getting
        import logging
        logger = logging.getLogger(__name__)
        if post.content and len(post.content) > 0:
            content_start = post.content[:100].replace('\n', ' ')
            logger.debug(f"Raw content from {file_path.name}: {content_start}")
            if post.content.startswith('<'):
                logger.warning(f"File {file_path.name} contains HTML, not markdown: {content_start}")
        
        return {
            'metadata': post.metadata,
            'content': post.content,
            'raw_content': post.content,
            'html_content': process_markdown_to_html(post.content)
        }
    except (yaml.YAMLError, Exception) as e:
        # Handle malformed YAML by attempting to fix common issues
        return _parse_malformed_frontmatter(file_path, e)


def _parse_malformed_frontmatter(file_path: Path, original_error: Exception) -> Dict[str, Any]:
    """Attempt to parse frontmatter with common YAML fixes."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to fix common YAML escaping issues
        if content.startswith('---\n'):
            parts = content.split('---\n', 2)
            if len(parts) >= 3:
                yaml_content = parts[1]
                markdown_content = parts[2]
                
                # Fix common escaping issues
                fixed_yaml = yaml_content.replace('\\"', '\\\\"')  # Fix unescaped quotes
                
                try:
                    # Try parsing the fixed YAML
                    import yaml
                    metadata = yaml.safe_load(fixed_yaml) or {}
                    
                    return {
                        'metadata': metadata,
                        'content': markdown_content,
                        'raw_content': markdown_content,
                        'html_content': process_markdown_to_html(markdown_content)
                    }
                except:
                    pass
        
        # Fallback: extract filename as title and use content as-is
        return _create_fallback_metadata(file_path, content)
        
    except Exception:
        # Ultimate fallback
        error_content = f"Error parsing file: {original_error}"
        return _create_fallback_metadata(file_path, error_content)


def _create_fallback_metadata(file_path: Path, content: str) -> Dict[str, Any]:
    """Create fallback metadata when frontmatter parsing fails."""
    filename_stem = file_path.stem
    title = filename_stem.replace('-', ' ').replace('_', ' ').title() if '-' in filename_stem or '_' in filename_stem else filename_stem
    
    return {
        'metadata': {
            'title': title,
            'date': '',
            'type': 'blog',
            'category': 'Uncategorized'
        },
        'content': content,
        'raw_content': content,
        'html_content': process_markdown_to_html(content)
    }


def generate_url_from_filename(filename: str, content_type: str) -> str:
    """Generate URL from filename and content type."""
    if content_type == 'pages':
        return f"/{filename}.html"
    else:
        return f"/{content_type}/{filename}.html"


def sort_posts_by_date(posts: List[Dict[str, Any]], reverse: bool = True) -> List[Dict[str, Any]]:
    """Sort posts by date, newest first by default."""
    return sorted(posts, key=lambda post: parse_date_for_sorting(post.get('date')), reverse=reverse)


def group_posts_by_month(posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group posts by month and year."""
    if not posts:
        return []
    
    groups = []
    current_group = None
    
    for post in posts:
        post_date = parse_date_for_sorting(post.get('date'))
        if post_date == datetime.min:
            continue
            
        month_year = post_date.strftime('%Y-%m')
        month_name = post_date.strftime('%B %Y')
        
        if current_group is None or current_group['month_year'] != month_year:
            current_group = {
                'month_year': month_year,
                'month_name': month_name,
                'posts': []
            }
            groups.append(current_group)
        
        current_group['posts'].append(post)
    
    return groups


def load_markdown_files_from_directory(directory_path: Path) -> List[Path]:
    """Get all markdown files from directory."""
    if not directory_path.exists():
        return []
    
    return list(directory_path.glob("*.md"))


def _sanitize_filename(text: str, max_length: int = 30) -> str:
    """Convert text to filename-safe format."""
    # Replace characters that aren't filename-safe
    safe_text = "".join(
        c for c in text if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    safe_text = safe_text.replace(" ", "-")
    
    # Truncate if too long
    if len(safe_text) > max_length:
        safe_text = safe_text[:max_length]
    
    return safe_text


def create_filename_from_title(title: str) -> str:
    """Create safe filename from post title with current date prefix."""
    # Remove special characters and convert to lowercase
    safe_title = re.sub(r'[^\w\s-]', '', title.lower())
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    
    # Add date prefix
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{date_str}-{safe_title}.md"


def generate_raindrop_filename(raindrop: Dict[str, Any], counter: int) -> str:
    """Create markdown filename from raindrop data and counter."""
    created = datetime.fromisoformat(raindrop["created"].replace("Z", "+00:00"))
    date_str = created.strftime("%y-%m-%d")

    # Get title and clean it for filename
    title = raindrop.get("title", "Untitled")
    safe_title = _sanitize_filename(title)

    return f"{date_str}-{counter}-{safe_title}.md"


def format_raindrop_as_markdown(raindrop: Dict[str, Any]) -> str:
    """Convert raindrop data to markdown with YAML frontmatter."""
    created = datetime.fromisoformat(raindrop["created"].replace("Z", "+00:00"))
    
    # Parse lastUpdate if available
    last_update = None
    if raindrop.get("lastUpdate"):
        try:
            last_update = datetime.fromisoformat(raindrop["lastUpdate"].replace("Z", "+00:00")).isoformat()
        except:
            last_update = raindrop.get("lastUpdate")

    # Format tags as space-separated string to match existing raindrop format
    tags = raindrop.get("tags", [])
    tags_str = " ".join(tags) if tags else ""

    # Build comprehensive frontmatter with all available fields
    frontmatter_data = {
        # Core fields (existing)
        "date": created.isoformat(),
        "excerpt": raindrop.get("excerpt", ""),
        "tags": [tags_str] if tags_str else [],
        "title": raindrop.get("title", "Untitled"),
        "type": "drop", 
        "url": raindrop.get("link", ""),
        
        # Additional API fields
        "raindrop_id": raindrop.get("_id"),
        "raindrop_type": raindrop.get("type", ""),
        "domain": raindrop.get("domain", ""),
        "cover": raindrop.get("cover", ""),
        "important": raindrop.get("important", False),
        "broken": raindrop.get("broken", False),
        "last_update": last_update,
        
        # Collection info
        "collection_id": raindrop.get("collection", {}).get("$id") if raindrop.get("collection") else None,
        
        # User info
        "user_id": raindrop.get("user", {}).get("$id") if raindrop.get("user") else None,
        
        # Media/covers
        "media": raindrop.get("media", []),
        
        # Advanced features
        "highlights": raindrop.get("highlights", []),
        "creator_ref": raindrop.get("creatorRef"),
        "file": raindrop.get("file"),
        "cache": raindrop.get("cache"),
        "reminder": raindrop.get("reminder"),
    }
    
    # Remove None values to keep frontmatter clean
    frontmatter_data = {k: v for k, v in frontmatter_data.items() if v is not None and v != "" and v != []}

    yaml_content = yaml.dump(frontmatter_data, default_flow_style=False)

    content = f"---\n{yaml_content}---\n\n# {raindrop.get('title', 'Untitled')}\n\n**URL:** {raindrop.get('link', '')}\n"

    # Add type and domain info if available
    if raindrop.get("type"):
        content += f"**Type:** {raindrop['type']}\n"
    if raindrop.get("domain"):
        content += f"**Domain:** {raindrop['domain']}\n"

    if raindrop.get("excerpt"):
        content += f"\n**Excerpt:** {raindrop['excerpt']}\n"

    if raindrop.get("note"):
        content += f"\n**Notes:**\n{raindrop['note']}\n"
        
    # Add highlights if available
    if raindrop.get("highlights"):
        content += f"\n**Highlights:**\n"
        for highlight in raindrop["highlights"]:
            content += f"- {highlight}\n"
            
    # Add important marker
    if raindrop.get("important"):
        content += f"\n⭐ **Marked as Important**\n"
        
    # Add broken link warning
    if raindrop.get("broken"):
        content += f"\n⚠️ **Warning: Link may be broken**\n"

    return content