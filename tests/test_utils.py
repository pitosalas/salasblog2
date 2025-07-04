"""
Comprehensive tests for utility functions.
Includes all doctest examples migrated to pytest format.
Run with: uv run pytest tests/test_utils.py -v
"""
import pytest
from datetime import datetime, timezone
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
    group_posts_by_month,
    load_markdown_files_from_directory,
    create_filename_from_title,
    generate_raindrop_filename,
    format_raindrop_as_markdown
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
        # Use smaller smart_threshold to force truncation
        result = create_excerpt(long_text, 50, 20)
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
        expected = datetime(2021, 4, 6, 13, 40, 22, 885000, tzinfo=timezone.utc)
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
        """Test parsing non-existent file returns fallback data."""
        result = parse_frontmatter_file(Path("/nonexistent/file.md"))
        
        # Should return fallback data structure
        assert 'metadata' in result
        assert 'content' in result
        assert 'raw_content' in result
        assert 'html_content' in result
        
        # Should have default metadata based on filename
        assert result['metadata']['title'] == 'file'  # filename stem
        assert result['metadata']['type'] == 'blog'
        assert result['metadata']['category'] == 'Uncategorized'




class TestGroupPostsByMonth:
    """Test post grouping by month utility."""
    
    def test_group_posts_by_month_basic(self):
        """Test basic month grouping."""
        posts = [
            {'date': '2025-01-15', 'title': 'Post 1'}, 
            {'date': '2025-01-10', 'title': 'Post 2'}
        ]
        grouped = group_posts_by_month(posts)
        assert grouped[0]['month_name'] == 'January 2025'
        assert len(grouped[0]['posts']) == 2
    
    def test_group_posts_by_month_multiple_months(self):
        """Test grouping across multiple months."""
        posts = [
            {'date': '2025-02-15', 'title': 'Feb Post'},
            {'date': '2025-01-15', 'title': 'Jan Post 1'}, 
            {'date': '2025-01-10', 'title': 'Jan Post 2'}
        ]
        grouped = group_posts_by_month(posts)
        assert len(grouped) == 2
        assert grouped[0]['month_name'] == 'February 2025'
        assert grouped[1]['month_name'] == 'January 2025'
        assert len(grouped[1]['posts']) == 2
    
    def test_group_posts_by_month_empty_list(self):
        """Test grouping empty list."""
        result = group_posts_by_month([])
        assert result == []


class TestCreateFilenameFromTitle:
    """Test filename creation from title utility."""
    
    def test_create_filename_from_title_basic(self):
        """Test basic filename creation."""
        # Note: This test will have a dynamic date, so we test the pattern
        result = create_filename_from_title("My Test Post!")
        assert result.endswith("-my-test-post.md")
        assert result.startswith("2025-")  # Assumes current year
        assert len(result.split("-")) >= 4  # YYYY-MM-DD-title format
    
    def test_create_filename_from_title_special_chars(self):
        """Test filename creation with special characters."""
        result = create_filename_from_title("Title with @#$% chars!")
        assert "title-with-chars" in result
        assert result.endswith(".md")
        # Should remove special characters
        assert "@" not in result
        assert "#" not in result
        assert "$" not in result
        assert "%" not in result
    
    def test_create_filename_from_title_spaces(self):
        """Test filename creation with multiple spaces."""
        result = create_filename_from_title("Multiple   Spaces   Here")
        assert "multiple-spaces-here" in result
        assert result.endswith(".md")


class TestGenerateRaindropFilename:
    """Test raindrop filename generation utility."""
    
    def test_generate_raindrop_filename_basic(self):
        """Test basic raindrop filename generation."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Test Bookmark"
        }
        result = generate_raindrop_filename(raindrop, 1)
        assert result == "25-06-28-1-Test-Bookmark.md"
    
    def test_generate_raindrop_filename_long_title(self):
        """Test raindrop filename with long title (truncated)."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "This is a very long title that should be truncated at thirty characters"
        }
        result = generate_raindrop_filename(raindrop, 5)
        assert result.startswith("25-06-28-5-")
        assert result.endswith(".md")
        # Title should be truncated and cleaned
        assert len(result) < len("25-06-28-5-This is a very long title that should be truncated at thirty characters.md")
    
    def test_generate_raindrop_filename_special_chars_in_title(self):
        """Test raindrop filename with special characters in title."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Title with @#$% & * chars!"
        }
        result = generate_raindrop_filename(raindrop, 2)
        assert result.startswith("25-06-28-2-")
        assert result.endswith(".md")
        # Should clean special characters
        assert "@" not in result
        assert "#" not in result
        assert "&" not in result
        assert "*" not in result


class TestFormatRaindropAsMarkdown:
    """Test raindrop markdown formatting utility."""
    
    def test_format_raindrop_as_markdown_basic(self):
        """Test basic raindrop markdown formatting."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Test", 
            "link": "https://example.com"
        }
        markdown = format_raindrop_as_markdown(raindrop)
        assert "---" in markdown  # Has frontmatter
        assert "Test" in markdown  # Has title
        assert "https://example.com" in markdown  # Has URL
    
    def test_format_raindrop_as_markdown_with_excerpt(self):
        """Test raindrop markdown with excerpt."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Test Article", 
            "link": "https://example.com",
            "excerpt": "This is a test excerpt"
        }
        markdown = format_raindrop_as_markdown(raindrop)
        assert "This is a test excerpt" in markdown
        assert "**Excerpt:**" in markdown
    
    def test_format_raindrop_as_markdown_with_tags(self):
        """Test raindrop markdown with tags."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Tagged Article", 
            "link": "https://example.com",
            "tags": ["python", "coding", "tutorial"]
        }
        markdown = format_raindrop_as_markdown(raindrop)
        assert "python coding tutorial" in markdown  # Tags as space-separated string
    
    def test_format_raindrop_as_markdown_with_notes(self):
        """Test raindrop markdown with notes."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Article with Notes", 
            "link": "https://example.com",
            "note": "These are my personal notes about this article"
        }
        markdown = format_raindrop_as_markdown(raindrop)
        assert "**Notes:**" in markdown
        assert "These are my personal notes about this article" in markdown
    
    def test_format_raindrop_as_markdown_important_flag(self):
        """Test raindrop markdown with important flag."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Important Article", 
            "link": "https://example.com",
            "important": True
        }
        markdown = format_raindrop_as_markdown(raindrop)
        assert "⭐ **Marked as Important**" in markdown
    
    def test_format_raindrop_as_markdown_broken_flag(self):
        """Test raindrop markdown with broken link flag."""
        raindrop = {
            "created": "2025-06-28T10:00:00Z", 
            "title": "Broken Link", 
            "link": "https://broken-example.com",
            "broken": True
        }
        markdown = format_raindrop_as_markdown(raindrop)
        assert "⚠️ **Warning: Link may be broken**" in markdown