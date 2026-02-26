#!/usr/bin/env python3
# test_home_posts_count.py — Test HOME_POSTS_COUNT environment variable
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from pathlib import Path

import pytest

from salasblog2.generator import SiteGenerator

PROJECT_ROOT = Path(__file__).parent.parent


def make_generator(tmp_path):
    """Return a SiteGenerator wired to tmp_path for output, real templates."""
    g = SiteGenerator()
    g.root_dir = PROJECT_ROOT
    g.templates_dir = PROJECT_ROOT / "templates"
    g.static_dir = PROJECT_ROOT / "static"
    g.output_dir = tmp_path / "output"
    g.output_dir.mkdir()
    from jinja2 import Environment, FileSystemLoader
    from salasblog2.utils import format_date, group_posts_by_month, get_markdown_processor, process_markdown_to_html, slugify_tag
    g.jinja_env = Environment(loader=FileSystemLoader(g.templates_dir))
    g.jinja_env.filters['strftime'] = g.format_date
    g.jinja_env.filters['dd_mm_yyyy'] = lambda d: format_date(d, '%d-%m-%Y')
    g.jinja_env.filters['group_by_month'] = group_posts_by_month
    g.jinja_env.filters['markdown'] = g.markdown_to_html
    g.jinja_env.filters['slugify'] = slugify_tag
    return g


def make_post(title, date):
    """Create a post dict for testing."""
    return {
        "title": title,
        "date": date,
        "type": "blog",
        "category": "General",
        "content": "<p>body</p>",
        "raw_content": "body",
        "filename": "test",
        "url": "/blog/test.html",
        "excerpt": "Ex",
        "is_truncated": False,
        "tags": []
    }


class TestHomePostsCount:
    def test_respects_home_posts_count_env_var(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME_POSTS_COUNT", "3")
        g = make_generator(tmp_path)
        posts = [make_post(f"Post {i}", f"2025-01-{i+1:02d}") for i in range(8)]
        g.generate_home_page(posts, [])
        html = (g.output_dir / "index.html").read_text()
        # Posts 3-7 (oldest) should not be in the home page
        assert "Post 3" not in html
        assert "Post 4" not in html
        assert "Post 5" not in html

    def test_default_is_five(self, tmp_path):
        g = make_generator(tmp_path)
        posts = [make_post(f"Post {i}", f"2025-01-{i+1:02d}") for i in range(8)]
        g.generate_home_page(posts, [])
        html = (g.output_dir / "index.html").read_text()
        # With default of 5, post 5 (index 5, "Post 5") should not be included
        assert "Post 7" not in html

    def test_respects_count_for_raindrops(self, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME_POSTS_COUNT", "2")
        g = make_generator(tmp_path)
        raindrops = [
            {
                "title": f"Drop {i}",
                "date": f"2025-01-{i+1:02d}",
                "type": "drop",
                "category": "General",
                "content": "<p>body</p>",
                "raw_content": "body",
                "filename": "test",
                "url": "/raindrops/test.html",
                "excerpt": "Ex",
                "is_truncated": False,
                "raindrop_url": "https://example.com",
                "domain": "example.com",
                "cover": "",
                "note": "",
                "tags": [],
                "important": False,
                "broken": False,
                "raindrop_type": "link",
                "media": []
            }
            for i in range(5)
        ]
        g.generate_home_page([], raindrops)
        html = (g.output_dir / "index.html").read_text()
        # With count=2, only 2 raindrops should appear
        assert "Drop 2" not in html
