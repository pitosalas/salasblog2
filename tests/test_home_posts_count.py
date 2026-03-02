#!/usr/bin/env python3
# test_home_posts_count.py — Test HOME_POSTS_COUNT environment variable
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import pytest


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
    def test_respects_home_posts_count_env_var(self, generator, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME_POSTS_COUNT", "3")
        g = generator
        posts = [make_post(f"Post {i}", f"2025-01-{i+1:02d}") for i in range(8)]
        g.generate_home_page(posts, [])
        html = (g.output_dir / "index.html").read_text()
        # With count=3, only the 3 newest posts (Post 7, 6, 5) appear; older ones do not
        assert "Post 0" not in html
        assert "Post 1" not in html
        assert "Post 2" not in html

    def test_default_is_five(self, generator):
        g = generator
        posts = [make_post(f"Post {i}", f"2025-01-{i+1:02d}") for i in range(8)]
        g.generate_home_page(posts, [])
        html = (g.output_dir / "index.html").read_text()
        # With default of 5, only the 5 newest posts (Post 7-3) appear; older ones do not
        assert "Post 0" not in html
        assert "Post 1" not in html

    def test_respects_count_for_raindrops(self, generator, monkeypatch):
        monkeypatch.setenv("HOME_POSTS_COUNT", "2")
        g = generator
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
