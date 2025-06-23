"""
Tests for utility functions.
Run with: uv run pytest test_utils.py -v
"""
import pytest
from datetime import datetime
from pathlib import Path
import tempfile
import os

from salasblog2.utils import (
    format_date,
    create_excerpt,
    parse_date_for_sorting,
    process_markdown_to_html,
    parse_frontmatter_file,
    generate_url_from_filename,
    sort_posts_by_date,
    load_markdown_files_from_directory,
    safe_get_filename_stem
)


class TestFormatDate:
    """Test date formatting utility."""
    
    def test_format_date_valid_iso(self):
        """Test formatting valid ISO date."""
        result = format_date("2025-01-15")
        assert result == "January 15, 2025"
    
    def test_format_date_custom_format(self):
        """Test formatting with custom format string."""
        result = format_date("2025-01-15", "%m/%d/%Y")
        assert result == "01/15/2025"
    
    def test_format_date_empty_string(self):
        """Test formatting empty string."""
        result = format_date("")
        assert result == ""
    
    def test_format_date_none(self):
        """Test formatting None value."""
        result = format_date(None)
        assert result == ""
    
    def test_format_date_invalid_format(self):
        """Test formatting invalid date string."""
        result = format_date("invalid-date")
        assert result == "invalid-date"
    
    def test_format_date_partial_date(self):
        """Test formatting partial date string."""
        result = format_date("2025-01")
        assert result == "2025-01"


class TestCreateExcerpt:
    """Test excerpt creation utility."""
    
    def test_create_excerpt_short_text(self):
        """Test excerpt of text shorter than max length."""
        result = create_excerpt("This is short")
        assert result == "This is short"
    
    def test_create_excerpt_long_text(self):
        """Test excerpt of text longer than max length."""
        long_text = "This is a very long text that should be truncated because it exceeds the maximum length limit for excerpts"
        result = create_excerpt(long_text, 50)
        assert result == "This is a very long text that should be truncated ..."
        assert len(result) == 53  # 50 + "..."
    
    def test_create_excerpt_exact_length(self):
        """Test excerpt of text exactly at max length."""
        text = "A" * 150
        result = create_excerpt(text, 150)
        assert result == text
        assert "..." not in result
    
    def test_create_excerpt_with_newlines(self):
        """Test excerpt removes newlines."""
        text = "Line 1\nLine 2\nLine 3"
        result = create_excerpt(text)
        assert "\n" not in result
        assert result == "Line 1 Line 2 Line 3"
    
    def test_create_excerpt_empty_string(self):
        """Test excerpt of empty string."""
        result = create_excerpt("")
        assert result == ""
    
    def test_create_excerpt_whitespace_only(self):
        """Test excerpt of whitespace-only string."""
        result = create_excerpt("   \n  \t  ")
        assert result == ""


class TestParseDateForSorting:
    """Test date parsing for sorting utility."""
    
    def test_parse_date_valid_iso(self):
        """Test parsing valid ISO date."""
        result = parse_date_for_sorting("2025-01-15")
        expected = datetime(2025, 1, 15)
        assert result == expected
    
    def test_parse_date_iso_datetime(self):
        """Test parsing ISO datetime string."""
        result = parse_date_for_sorting("2021-04-06T13:40:22.885000+00:00")
        expected = datetime(2021, 4, 6)
        assert result == expected
    
    def test_parse_date_empty_string(self):
        """Test parsing empty string."""
        result = parse_date_for_sorting("")
        assert result == datetime.min
    
    def test_parse_date_none(self):
        """Test parsing None value."""
        result = parse_date_for_sorting(None)
        assert result == datetime.min
    
    def test_parse_date_invalid_format(self):
        """Test parsing invalid date format."""
        result = parse_date_for_sorting("invalid-date")
        assert result == datetime.min


class TestProcessMarkdownToHtml:
    """Test markdown processing utility."""
    
    def test_process_markdown_heading(self):
        """Test processing markdown heading."""
        result = process_markdown_to_html("# Hello World")
        # Markdown may add id attributes, so check for h1 tag content
        assert "<h1" in result and "Hello World</h1>" in result
    
    def test_process_markdown_bold(self):
        """Test processing markdown bold text."""
        result = process_markdown_to_html("**bold text**")
        assert "<strong>bold text</strong>" in result
    
    def test_process_markdown_paragraph(self):
        """Test processing markdown paragraph."""
        result = process_markdown_to_html("This is a paragraph.")
        assert "<p>This is a paragraph.</p>" in result
    
    def test_process_markdown_empty(self):
        """Test processing empty markdown."""
        result = process_markdown_to_html("")
        assert result == ""
    
    def test_process_markdown_code_block(self):
        """Test processing markdown code block."""
        result = process_markdown_to_html("```python\nprint('hello')\n```")
        assert "<code>" in result or "<pre>" in result


class TestGenerateUrlFromFilename:
    """Test URL generation utility."""
    
    def test_generate_url_blog_post(self):
        """Test URL generation for blog post."""
        result = generate_url_from_filename("my-post", "blog")
        assert result == "/blog/my-post.html"
    
    def test_generate_url_raindrop(self):
        """Test URL generation for raindrop."""
        result = generate_url_from_filename("quick-note", "raindrops")
        assert result == "/raindrops/quick-note.html"
    
    def test_generate_url_page(self):
        """Test URL generation for page."""
        result = generate_url_from_filename("about", "pages")
        assert result == "/about.html"
    
    def test_generate_url_special_characters(self):
        """Test URL generation with special characters in filename."""
        result = generate_url_from_filename("post-with-dashes", "blog")
        assert result == "/blog/post-with-dashes.html"


class TestSortPostsByDate:
    """Test post sorting utility."""
    
    def test_sort_posts_newest_first(self):
        """Test sorting posts with newest first (default)."""
        posts = [
            {'date': '2025-01-01', 'title': 'Old Post'},
            {'date': '2025-01-15', 'title': 'New Post'},
            {'date': '2025-01-10', 'title': 'Middle Post'}
        ]
        result = sort_posts_by_date(posts)
        
        assert result[0]['title'] == 'New Post'
        assert result[1]['title'] == 'Middle Post'
        assert result[2]['title'] == 'Old Post'
    
    def test_sort_posts_oldest_first(self):
        """Test sorting posts with oldest first."""
        posts = [
            {'date': '2025-01-15', 'title': 'New Post'},
            {'date': '2025-01-01', 'title': 'Old Post'}
        ]
        result = sort_posts_by_date(posts, reverse=False)
        
        assert result[0]['title'] == 'Old Post'
        assert result[1]['title'] == 'New Post'
    
    def test_sort_posts_missing_dates(self):
        """Test sorting posts with missing dates."""
        posts = [
            {'date': '2025-01-15', 'title': 'With Date'},
            {'title': 'No Date'},
            {'date': '', 'title': 'Empty Date'}
        ]
        result = sort_posts_by_date(posts)
        
        # Post with valid date should be first
        assert result[0]['title'] == 'With Date'
    
    def test_sort_posts_empty_list(self):
        """Test sorting empty list."""
        result = sort_posts_by_date([])
        assert result == []


class TestLoadMarkdownFilesFromDirectory:
    """Test markdown file loading utility."""
    
    def test_load_markdown_files_existing_directory(self):
        """Test loading markdown files from existing directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test files
            (temp_path / "test1.md").write_text("# Test 1")
            (temp_path / "test2.md").write_text("# Test 2")
            (temp_path / "not_markdown.txt").write_text("Not markdown")
            
            result = load_markdown_files_from_directory(temp_path)
            
            assert len(result) == 2
            md_files = [f.name for f in result]
            assert "test1.md" in md_files
            assert "test2.md" in md_files
            assert "not_markdown.txt" not in md_files
    
    def test_load_markdown_files_nonexistent_directory(self):
        """Test loading markdown files from non-existent directory."""
        result = load_markdown_files_from_directory(Path("/nonexistent/path"))
        assert result == []
    
    def test_load_markdown_files_empty_directory(self):
        """Test loading markdown files from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            result = load_markdown_files_from_directory(Path(temp_dir))
            assert result == []


class TestSafeGetFilenameStem:
    """Test filename stem utility."""
    
    def test_safe_get_filename_stem_simple(self):
        """Test getting stem from simple filename."""
        result = safe_get_filename_stem(Path("test.md"))
        assert result == "test"
    
    def test_safe_get_filename_stem_complex(self):
        """Test getting stem from complex filename."""
        result = safe_get_filename_stem(Path("my-blog-post.md"))
        assert result == "my-blog-post"
    
    def test_safe_get_filename_stem_no_extension(self):
        """Test getting stem from filename without extension."""
        result = safe_get_filename_stem(Path("filename"))
        assert result == "filename"
    
    def test_safe_get_filename_stem_multiple_dots(self):
        """Test getting stem from filename with multiple dots."""
        result = safe_get_filename_stem(Path("file.name.with.dots.md"))
        assert result == "file.name.with.dots"


class TestParseFrontmatterFile:
    """Test frontmatter file parsing utility."""
    
    def test_parse_frontmatter_file_with_metadata(self):
        """Test parsing file with frontmatter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""---
title: Test Post
date: 2025-01-15
category: Test
---

# This is a test post

Some content here.
""")
            f.flush()
            
            try:
                result = parse_frontmatter_file(Path(f.name))
                
                assert result['metadata']['title'] == 'Test Post'
                # frontmatter may parse dates as date objects
                date_value = result['metadata']['date']
                assert str(date_value) == '2025-01-15'
                assert result['metadata']['category'] == 'Test'
                assert '# This is a test post' in result['content']
                assert '<h1' in result['html_content'] and 'This is a test post</h1>' in result['html_content']
                
            finally:
                os.unlink(f.name)
    
    def test_parse_frontmatter_file_no_metadata(self):
        """Test parsing file without frontmatter."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("# Just a simple post\n\nNo frontmatter here.")
            f.flush()
            
            try:
                result = parse_frontmatter_file(Path(f.name))
                
                assert result['metadata'] == {}
                assert 'Just a simple post' in result['content']
                
            finally:
                os.unlink(f.name)
    
    def test_parse_frontmatter_file_nonexistent(self):
        """Test parsing non-existent file."""
        with pytest.raises(FileNotFoundError):
            parse_frontmatter_file(Path("/nonexistent/file.md"))