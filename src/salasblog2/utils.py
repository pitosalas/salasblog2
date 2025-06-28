"""
Pure utility functions for content processing and site generation.
These functions are completely independent and reusable.
"""
import re
import markdown
import frontmatter
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional


def format_date(date_str: Optional[str], format_str: str = '%B %d, %Y') -> str:
    """
    Format a date string using strftime format.
    
    Args:
        date_str: Date string in YYYY-MM-DD format, or None/empty
        format_str: strftime format string
        
    Returns:
        Formatted date string, or empty string if input is invalid
        
    Examples:
        >>> format_date("2025-01-15")
        'January 15, 2025'
        >>> format_date("2025-01-15", "%m/%d/%Y")
        '01/15/2025'
        >>> format_date("")
        ''
        >>> format_date(None)
        ''
    """
    if not date_str:
        return ''
    
    try:
        if isinstance(date_str, str):
            # Try to parse ISO format YYYY-MM-DD
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            return date_obj.strftime(format_str)
        return str(date_str)
    except (ValueError, TypeError):
        return str(date_str) if date_str else ''


def create_excerpt(content: str, max_length: int = 150) -> str:
    """
    Create an excerpt from text content.
    
    Args:
        content: Full text content
        max_length: Maximum length of excerpt
        
    Returns:
        Excerpt with ellipsis if truncated
        
    Examples:
        >>> create_excerpt("This is a short text")
        'This is a short text'
        >>> create_excerpt("This is a very long text that will be truncated", 20)
        'This is a very long...'
    """
    if not content:
        return ''
    
    # Clean up content - remove newlines and extra spaces
    clean_content = content.replace('\n', ' ').strip()
    
    if len(clean_content) <= max_length:
        return clean_content
    
    return clean_content[:max_length] + '...'


def parse_date_for_sorting(date_str: Optional[str]) -> datetime:
    """
    Parse a date string for sorting purposes.
    
    Args:
        date_str: Date string in various formats
        
    Returns:
        datetime object, or datetime.min if parsing fails
        
    Examples:
        >>> parse_date_for_sorting("2025-01-15")
        datetime.datetime(2025, 1, 15, 0, 0)
        >>> parse_date_for_sorting("")
        datetime.datetime(1, 1, 1, 0, 0)
    """
    if not date_str:
        return datetime.min
    
    try:
        # Handle various date formats
        date_str = str(date_str)
        
        # Try ISO format first (YYYY-MM-DD)
        if len(date_str) >= 10 and date_str[4] == '-' and date_str[7] == '-':
            return datetime.strptime(date_str[:10], '%Y-%m-%d')
        
        # Try ISO datetime format
        if 'T' in date_str:
            # Handle ISO datetime like "2021-04-06T13:40:22.885000+00:00"
            date_part = date_str.split('T')[0]
            return datetime.strptime(date_part, '%Y-%m-%d')
            
        # Fallback - return min date for unknown formats
        return datetime.min
        
    except (ValueError, TypeError):
        return datetime.min


# Module-level singleton for markdown processor
_md_processor = None

def get_markdown_processor():
    """Get or create the singleton markdown processor."""
    global _md_processor
    if _md_processor is None:
        _md_processor = markdown.Markdown(extensions=['meta', 'toc'])
    return _md_processor

def process_markdown_to_html(content: str) -> str:
    """Convert markdown content to HTML."""
    if not content:
        return ''
    
    return get_markdown_processor().convert(content)


def parse_frontmatter_file(file_path: Path) -> Dict[str, Any]:
    """
    Parse a markdown file with frontmatter.
    
    Args:
        file_path: Path to markdown file
        
    Returns:
        Dictionary with 'metadata', 'content', and 'raw_content' keys
        
    Raises:
        FileNotFoundError: If file doesn't exist
        UnicodeDecodeError: If file encoding is invalid
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            post = frontmatter.load(f)
        
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
    """
    Attempt to parse frontmatter with common YAML fixes.
    
    Args:
        file_path: Path to markdown file
        original_error: The original parsing error
        
    Returns:
        Dictionary with parsed data or fallback values
    """
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
        filename_stem = file_path.stem
        return {
            'metadata': {
                'title': filename_stem.replace('-', ' ').replace('_', ' ').title(),
                'date': '',
                'type': 'blog',
                'category': 'Uncategorized'
            },
            'content': content,
            'raw_content': content,
            'html_content': process_markdown_to_html(content)
        }
        
    except Exception:
        # Ultimate fallback
        filename_stem = file_path.stem
        return {
            'metadata': {
                'title': filename_stem,
                'date': '',
                'type': 'blog', 
                'category': 'Uncategorized'
            },
            'content': f"Error parsing file: {original_error}",
            'raw_content': f"Error parsing file: {original_error}",
            'html_content': f"<p>Error parsing file: {original_error}</p>"
        }


def generate_url_from_filename(filename: str, content_type: str) -> str:
    """
    Generate URL from filename and content type.
    
    Args:
        filename: Base filename (without extension)
        content_type: Type of content ('blog', 'raindrops', 'pages')
        
    Returns:
        URL string
        
    Examples:
        >>> generate_url_from_filename("my-post", "blog")
        '/blog/my-post.html'
        >>> generate_url_from_filename("about", "pages")
        '/about.html'
    """
    if content_type == 'pages':
        return f"/{filename}.html"
    else:
        return f"/{content_type}/{filename}.html"


def sort_posts_by_date(posts: List[Dict[str, Any]], reverse: bool = True) -> List[Dict[str, Any]]:
    """
    Sort a list of posts by date.
    
    Args:
        posts: List of post dictionaries with 'date' key
        reverse: If True, sort newest first (default)
        
    Returns:
        Sorted list of posts
        
    Examples:
        >>> posts = [{'date': '2025-01-01'}, {'date': '2025-01-15'}]
        >>> sorted_posts = sort_posts_by_date(posts)
        >>> sorted_posts[0]['date']
        '2025-01-15'
    """
    return sorted(posts, key=lambda post: parse_date_for_sorting(post.get('date')), reverse=reverse)


def load_markdown_files_from_directory(directory_path: Path) -> List[Path]:
    """
    Get all markdown files from a directory.
    
    Args:
        directory_path: Path to directory
        
    Returns:
        List of Path objects for .md files
        
    Examples:
        >>> files = load_markdown_files_from_directory(Path("/content/blog"))
        >>> len(files) >= 0
        True
    """
    if not directory_path.exists():
        return []
    
    return list(directory_path.glob("*.md"))


def safe_get_filename_stem(file_path: Path) -> str:
    """
    Safely get the filename stem (without extension).
    
    Args:
        file_path: Path object
        
    Returns:
        Filename without extension
        
    Examples:
        >>> safe_get_filename_stem(Path("test.md"))
        'test'
        >>> safe_get_filename_stem(Path("complex-name.md"))
        'complex-name'
    """
    return file_path.stem


def create_filename_from_title(title: str) -> str:
    """
    Create a safe filename from post title with current date prefix.
    
    Args:
        title: Post title to convert to filename
        
    Returns:
        Safe filename with date prefix and .md extension
        
    Examples:
        >>> create_filename_from_title("My Test Post!")
        '2025-06-28-my-test-post.md'
    """
    # Remove special characters and convert to lowercase
    safe_title = re.sub(r'[^\w\s-]', '', title.lower())
    safe_title = re.sub(r'[-\s]+', '-', safe_title)
    
    # Add date prefix
    date_str = datetime.now().strftime("%Y-%m-%d")
    return f"{date_str}-{safe_title}.md"


def generate_raindrop_filename(raindrop: Dict[str, Any], counter: int) -> str:
    """
    Create markdown filename from raindrop data and counter.
    
    Args:
        raindrop: Dictionary containing raindrop data with 'created' and 'title'
        counter: Counter for uniqueness
        
    Returns:
        Safe filename for raindrop markdown file
        
    Examples:
        >>> raindrop = {"created": "2025-06-28T10:00:00Z", "title": "Test Bookmark"}
        >>> generate_raindrop_filename(raindrop, 1)
        '25-06-28-1-Test-Bookmark.md'
    """
    created = datetime.fromisoformat(raindrop["created"].replace("Z", "+00:00"))
    date_str = created.strftime("%y-%m-%d")

    # Get title and clean it for filename
    title = raindrop.get("title", "Untitled")[:30]
    # Replace characters that aren't filename-safe
    safe_title = "".join(
        c for c in title if c.isalnum() or c in (" ", "-", "_")
    ).strip()
    safe_title = safe_title.replace(" ", "-")

    return f"{date_str}-{counter}-{safe_title}.md"


def format_raindrop_as_markdown(raindrop: Dict[str, Any]) -> str:
    """
    Convert raindrop data to markdown with YAML frontmatter.
    
    Args:
        raindrop: Dictionary containing raindrop data
        
    Returns:
        Formatted markdown content with frontmatter
        
    Examples:
        >>> raindrop = {"created": "2025-06-28T10:00:00Z", "title": "Test", "link": "https://example.com"}
        >>> markdown = format_raindrop_as_markdown(raindrop)
        >>> "---" in markdown
        True
    """
    created = datetime.fromisoformat(raindrop["created"].replace("Z", "+00:00"))

    # Format tags as space-separated string to match existing raindrop format
    tags = raindrop.get("tags", [])
    tags_str = " ".join(tags) if tags else ""

    frontmatter_data = {
        "date": created.isoformat(),
        "excerpt": raindrop.get("excerpt", ""),
        "tags": [tags_str] if tags_str else [],
        "title": raindrop.get("title", "Untitled"),
        "type": "drop", 
        "url": raindrop.get("link", ""),
    }

    yaml_content = yaml.dump(frontmatter_data, default_flow_style=False)

    content = f"---\n{yaml_content}---\n\n# {raindrop.get('title', 'Untitled')}\n\n**URL:** {raindrop.get('link', '')}\n"

    if raindrop.get("excerpt"):
        content += f"\n**Excerpt:** {raindrop['excerpt']}\n"

    if raindrop.get("note"):
        content += f"\n**Notes:**\n{raindrop['note']}\n"

    return content