"""
Test the placeholder title functionality for frontmatter parsing failures.
"""

import pytest
import tempfile
from pathlib import Path
from salasblog2.generator import SiteGenerator


class TestPlaceholderTitle:
    """Test placeholder title generation when frontmatter is missing or malformed."""
    
    @pytest.fixture
    def temp_setup(self):
        """Set up temporary test environment."""
        test_dir = Path(tempfile.mkdtemp())
        content_dir = test_dir / "content"
        pages_dir = content_dir / "pages"
        pages_dir.mkdir(parents=True, exist_ok=True)
        
        yield test_dir, pages_dir
        
        import shutil
        shutil.rmtree(test_dir)
    
    def test_placeholder_title_for_missing_frontmatter(self, temp_setup):
        """Test that missing frontmatter generates placeholder title."""
        test_dir, pages_dir = temp_setup
        
        # Create a file with no frontmatter
        test_file = pages_dir / "about_me.md"
        test_file.write_text("This is content without frontmatter.")
        
        generator = SiteGenerator(theme="test")
        generator.pages_dir = pages_dir
        
        pages = generator.load_posts('pages')
        
        assert len(pages) == 1
        assert pages[0]['title'] == "placeholder title: About Me"
        assert pages[0]['filename'] == "about_me"
    
    def test_placeholder_title_for_malformed_frontmatter(self, temp_setup):
        """Test that malformed frontmatter generates placeholder title."""
        test_dir, pages_dir = temp_setup
        
        # Create a file with malformed frontmatter (missing title)
        test_file = pages_dir / "contact-info.md"
        test_file.write_text("""---
date: "2024-01-01"
category: "Information"
---
This has frontmatter but no title field.""")
        
        generator = SiteGenerator(theme="test")
        generator.pages_dir = pages_dir
        
        pages = generator.load_posts('pages')
        
        assert len(pages) == 1
        assert pages[0]['title'] == "placeholder title: Contact Info"
        assert pages[0]['filename'] == "contact-info"
        assert pages[0]['category'] == "Information"  # Other frontmatter should work
    
    def test_placeholder_title_formatting(self, temp_setup):
        """Test that placeholder titles are properly formatted."""
        test_dir, pages_dir = temp_setup
        
        test_cases = [
            ("my_project", "placeholder title: My Project"),
            ("about-me", "placeholder title: About Me"),
            ("contact_info", "placeholder title: Contact Info"),
            ("simple", "placeholder title: Simple"),
            ("multi-word_test", "placeholder title: Multi Word Test")
        ]
        
        for filename, expected_title in test_cases:
            test_file = pages_dir / f"{filename}.md"
            test_file.write_text("Content without frontmatter")
        
        generator = SiteGenerator(theme="test")
        generator.pages_dir = pages_dir
        
        pages = generator.load_posts('pages')
        
        # Check each case by finding the matching page
        for filename, expected_title in test_cases:
            page = next(p for p in pages if p['filename'] == filename)
            assert page['title'] == expected_title
            assert page['filename'] == filename
    
    def test_proper_frontmatter_still_works(self, temp_setup):
        """Test that proper frontmatter titles are still used correctly."""
        test_dir, pages_dir = temp_setup
        
        # Create a file with proper frontmatter
        test_file = pages_dir / "about.md"
        test_file.write_text("""---
title: "About Me - The Real Title"
date: "2024-01-01"
category: "Personal"
---
This has proper frontmatter with a title.""")
        
        generator = SiteGenerator(theme="test")
        generator.pages_dir = pages_dir
        
        pages = generator.load_posts('pages')
        
        assert len(pages) == 1
        assert pages[0]['title'] == "About Me - The Real Title"  # Should use real title
        assert pages[0]['filename'] == "about"
        assert pages[0]['category'] == "Personal"
    
    def test_mixed_files_with_and_without_titles(self, temp_setup):
        """Test handling of mixed files - some with titles, some without."""
        test_dir, pages_dir = temp_setup
        
        # File with proper title
        good_file = pages_dir / "good.md"
        good_file.write_text("""---
title: "Proper Title"
category: "Good"
---
Good content.""")
        
        # File without title
        bad_file = pages_dir / "bad-file.md"
        bad_file.write_text("""---
category: "Bad"
---
Bad content without title.""")
        
        # File with no frontmatter at all
        ugly_file = pages_dir / "ugly_file.md"
        ugly_file.write_text("No frontmatter at all.")
        
        generator = SiteGenerator(theme="test")
        generator.pages_dir = pages_dir
        
        pages = generator.load_posts('pages')
        pages.sort(key=lambda p: p['filename'])  # Sort for consistent testing
        
        assert len(pages) == 3
        
        # bad-file.md - has frontmatter but no title
        bad_page = next(p for p in pages if p['filename'] == 'bad-file')
        assert bad_page['title'] == "placeholder title: Bad File"
        assert bad_page['category'] == "Bad"
        
        # good.md - has proper title
        good_page = next(p for p in pages if p['filename'] == 'good')
        assert good_page['title'] == "Proper Title"
        assert good_page['category'] == "Good"
        
        # ugly_file.md - no frontmatter at all
        ugly_page = next(p for p in pages if p['filename'] == 'ugly_file')
        assert ugly_page['title'] == "placeholder title: Ugly File"
        assert ugly_page['category'] == "Uncategorized"  # Default fallback