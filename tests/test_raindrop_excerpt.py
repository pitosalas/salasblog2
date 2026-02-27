#!/usr/bin/env python3
# test_raindrop_excerpt.py — Tests for raindrop excerpt generation bug fix
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import tempfile
from pathlib import Path
import shutil

from salasblog2.generator import SiteGenerator


def make_raindrops_dir():
    test_dir = Path(tempfile.mkdtemp())
    rd_dir = test_dir / "content" / "raindrops"
    rd_dir.mkdir(parents=True)
    return test_dir, rd_dir


def teardown(test_dir):
    shutil.rmtree(test_dir)


def load_raindrops(rd_dir):
    g = SiteGenerator()
    g.raindrops_dir = rd_dir
    return g.load_posts("raindrops")


def test_raindrop_with_frontmatter_excerpt_uses_it():
    """Frontmatter excerpt is used as-is, not replaced by body content."""
    test_dir, rd_dir = make_raindrops_dir()
    try:
        (rd_dir / "25-01-01-1-test.md").write_text(
            "---\n"
            "title: Test Link\n"
            "date: '2025-01-01'\n"
            "type: drop\n"
            "url: https://example.com\n"
            "domain: example.com\n"
            "excerpt: Clean blurb from Raindrop.io\n"
            "---\n"
            "# Test Link\n\n"
            "**URL:** https://example.com\n"
            "**Type:** link\n"
            "**Domain:** example.com\n"
            "**Notes:**\nMy personal note.\n"
        )
        posts = load_raindrops(rd_dir)
        assert len(posts) == 1
        assert posts[0]["excerpt"] == "Clean blurb from Raindrop.io"
    finally:
        teardown(test_dir)


def test_raindrop_without_frontmatter_excerpt_has_empty_excerpt():
    """Without a frontmatter excerpt, excerpt is empty — not generated from raw body."""
    test_dir, rd_dir = make_raindrops_dir()
    try:
        (rd_dir / "25-01-01-1-test.md").write_text(
            "---\n"
            "title: Building the Panama Canal\n"
            "date: '2025-01-01'\n"
            "type: drop\n"
            "url: https://example.com\n"
            "domain: example.com\n"
            "---\n"
            "# Building the Panama Canal\n\n"
            "**URL:** https://example.com\n"
            "**Type:** link\n"
            "**Domain:** example.com\n"
            "**Notes:**\nInfo about the Panama Canal.\n"
        )
        posts = load_raindrops(rd_dir)
        assert len(posts) == 1
        assert posts[0]["excerpt"] == ""
    finally:
        teardown(test_dir)


def test_raindrop_excerpt_never_contains_raw_markdown_labels():
    """Excerpt must not contain **URL:**, **Type:**, **Domain:**, or **Notes:** literals."""
    test_dir, rd_dir = make_raindrops_dir()
    try:
        (rd_dir / "25-02-01-1-link.md").write_text(
            "---\n"
            "title: Some Link\n"
            "date: '2025-02-01'\n"
            "type: drop\n"
            "url: https://example.org\n"
            "domain: example.org\n"
            "---\n"
            "# Some Link\n\n"
            "**URL:** https://example.org\n"
            "**Type:** article\n"
            "**Domain:** example.org\n"
            "**Excerpt:** A blurb from the page.\n"
            "**Notes:**\nPersonal annotation here.\n"
        )
        posts = load_raindrops(rd_dir)
        assert len(posts) == 1
        excerpt = posts[0]["excerpt"]
        for label in ("**URL:**", "**Type:**", "**Domain:**", "**Notes:**", "**Excerpt:**"):
            assert label not in excerpt, f"Excerpt must not contain {label!r}"
    finally:
        teardown(test_dir)


def test_raindrop_note_field_is_separate_from_excerpt():
    """Note field is populated from frontmatter independently of excerpt."""
    test_dir, rd_dir = make_raindrops_dir()
    try:
        (rd_dir / "25-03-01-1-link.md").write_text(
            "---\n"
            "title: Noted Link\n"
            "date: '2025-03-01'\n"
            "type: drop\n"
            "url: https://noted.example.com\n"
            "domain: noted.example.com\n"
            "note: This is a hand-written note.\n"
            "---\n"
            "# Noted Link\n\n"
            "**URL:** https://noted.example.com\n"
            "**Type:** link\n"
            "**Domain:** noted.example.com\n"
            "**Notes:**\nThis is a hand-written note.\n"
        )
        posts = load_raindrops(rd_dir)
        assert len(posts) == 1
        assert posts[0]["note"] == "This is a hand-written note."
        assert posts[0]["excerpt"] == ""
    finally:
        teardown(test_dir)


def test_blog_post_still_gets_generated_excerpt():
    """Blog posts (not raindrops) still have excerpts generated from content."""
    test_dir = Path(tempfile.mkdtemp())
    blog_dir = test_dir / "content" / "blog"
    blog_dir.mkdir(parents=True)
    try:
        (blog_dir / "2025-01-01-my-post.md").write_text(
            "---\n"
            "title: My Blog Post\n"
            "date: '2025-01-01'\n"
            "type: blog\n"
            "category: General\n"
            "---\n"
            "This is the beginning of a long blog post with plenty of content "
            "that should be truncated into an excerpt for display on the home page.\n"
        )
        g = SiteGenerator()
        g.blog_dir = blog_dir
        posts = g.load_posts("blog")
        assert len(posts) == 1
        assert posts[0]["excerpt"] != ""
        assert "This is the beginning" in posts[0]["excerpt"]
    finally:
        shutil.rmtree(test_dir)
