#!/usr/bin/env python3
# test_generator.py — Tests for SiteGenerator
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import json
from pathlib import Path

import pytest

from salasblog2.generator import SiteGenerator


def make_blog_post(directory, filename, title, date, content="Post body."):
    (directory / filename).write_text(
        f"---\ntitle: {title!r}\ndate: '{date}'\ncategory: General\ntype: blog\n---\n{content}\n"
    )


def make_raindrop(directory, filename, title, date, url="https://example.com", note=""):
    note_line = f"note: {note!r}\n" if note else ""
    (directory / filename).write_text(
        f"---\ntitle: {title!r}\ndate: '{date}'\ntype: drop\nurl: {url!r}\ndomain: example.com\n{note_line}---\n"
        f"# {title}\n\n**URL:** {url}\n**Type:** link\n**Domain:** example.com\n"
    )


def make_page(directory, filename, title, date):
    (directory / filename).write_text(
        f"---\ntitle: {title!r}\ndate: '{date}'\ntype: page\n---\nPage content here.\n"
    )


# ---------------------------------------------------------------------------
# load_posts
# ---------------------------------------------------------------------------

class TestLoadPosts:
    def test_unknown_content_type_returns_empty(self, generator):
        g = generator
        assert g.load_posts("unknown") == []

    def test_nonexistent_dir_returns_empty(self, generator, tmp_path):
        g = generator
        g.blog_dir = tmp_path / "nonexistent"
        assert g.load_posts("blog") == []

    def test_sorted_newest_first(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        make_blog_post(blog_dir, "2024-01-01-old.md", "Old", "2024-01-01")
        make_blog_post(blog_dir, "2025-06-01-new.md", "New", "2025-06-01")
        posts = g.load_posts("blog")
        assert posts[0]["title"] == "New"
        assert posts[1]["title"] == "Old"

    def test_blog_post_has_expected_fields(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        make_blog_post(blog_dir, "2025-01-15-hello.md", "Hello World", "2025-01-15")
        posts = g.load_posts("blog")
        assert len(posts) == 1
        p = posts[0]
        assert p["title"] == "Hello World"
        assert p["date"] == "2025-01-15"
        assert p["filename"] == "2025-01-15-hello"
        assert "excerpt" in p
        assert "url" in p

    def test_raindrop_has_raindrop_url_field(self, generator, tmp_path):
        g = generator
        rd_dir = tmp_path / "raindrops"
        rd_dir.mkdir()
        g.raindrops_dir = rd_dir
        make_raindrop(rd_dir, "25-01-01-1-link.md", "Some Link", "2025-01-01",
                      url="https://target.example.com")
        posts = g.load_posts("raindrops")
        assert posts[0]["raindrop_url"] == "https://target.example.com"

    def test_raindrop_note_extracted_from_content_body(self, generator, tmp_path):
        g = generator
        rd_dir = tmp_path / "raindrops"
        rd_dir.mkdir()
        g.raindrops_dir = rd_dir
        (rd_dir / "25-02-01-1-link.md").write_text(
            "---\ntitle: 'Link'\ndate: '2025-02-01'\ntype: drop\nurl: 'https://x.com'\ndomain: x.com\n---\n"
            "# Link\n\n**URL:** https://x.com\n**Type:** link\n**Notes:**\nExtracted note text.\n"
        )
        posts = g.load_posts("raindrops")
        assert posts[0]["note"] == "Extracted note text."

    def test_page_excerpt_uses_first_paragraph(self, generator, tmp_path):
        g = generator
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        g.pages_dir = pages_dir
        (pages_dir / "about.md").write_text(
            "---\ntitle: 'About'\ndate: '2025-01-01'\ntype: page\n---\n"
            "First paragraph content.\n\nSecond paragraph.\n"
        )
        posts = g.load_posts("pages")
        assert "First paragraph" in posts[0]["excerpt"]
        assert "Second paragraph" not in posts[0]["excerpt"]


    def test_draft_posts_excluded_from_load(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        make_blog_post(blog_dir, "2020-01-01-real.md", "Real Post", "2020-01-01")
        (blog_dir / "draft-post.md").write_text(
            "---\ntitle: 'Draft'\ndate: '2020-01-01'\ntype: blog\ndraft: true\n---\nbody\n"
        )
        posts = g.load_posts("blog")
        titles = [p["title"] for p in posts]
        assert "Real Post" in titles
        assert "Draft" not in titles


# ---------------------------------------------------------------------------
# get_navigation_items / _get_page_url
# ---------------------------------------------------------------------------

class TestNavAndPagination:
    def test_navigation_contains_four_items(self, generator):
        g = generator
        nav = g.get_navigation_items()
        assert len(nav) == 4
        urls = [item["url"] for item in nav]
        assert "/" in urls
        assert "/blog/" in urls
        assert "/raindrops/" in urls
        assert "/pages/" in urls

    def test_page_url_first_page(self, generator):
        g = generator
        assert g._get_page_url("blog", 1) == "/blog/"

    def test_page_url_subsequent_page(self, generator):
        g = generator
        assert g._get_page_url("blog", 3) == "/blog/page-3.html"
        assert g._get_page_url("raindrops", 2) == "/raindrops/page-2.html"


# ---------------------------------------------------------------------------
# generate_search_index
# ---------------------------------------------------------------------------

class TestGenerateSearchIndex:
    def test_creates_search_json(self, generator):
        g = generator
        g.generate_search_index([
            {"title": "T", "url": "/blog/t.html", "type": "blog",
             "excerpt": "Ex", "raw_content": "Body"},
        ])
        assert (g.output_dir / "search.json").exists()

    def test_search_json_contains_expected_fields(self, generator):
        g = generator
        g.generate_search_index([
            {"title": "My Post", "url": "/blog/my-post.html", "type": "blog",
             "excerpt": "Short blurb", "raw_content": "Full body text"},
        ])
        data = json.loads((g.output_dir / "search.json").read_text())
        assert len(data) == 1
        assert data[0]["title"] == "My Post"
        assert data[0]["url"] == "/blog/my-post.html"
        assert data[0]["excerpt"] == "Short blurb"
        assert data[0]["content"] == "Full body text"

    def test_search_json_truncates_long_content(self, generator):
        g = generator
        long_body = "x" * 1000
        g.generate_search_index([
            {"title": "T", "url": "/u", "type": "blog", "excerpt": "",
             "raw_content": long_body},
        ])
        data = json.loads((g.output_dir / "search.json").read_text())
        assert data[0]["content"].endswith("...")
        assert len(data[0]["content"]) == 503  # 500 + "..."

    def test_search_json_multiple_posts(self, generator):
        g = generator
        posts = [
            {"title": f"Post {i}", "url": f"/blog/p{i}.html", "type": "blog",
             "excerpt": "", "raw_content": "body"}
            for i in range(5)
        ]
        g.generate_search_index(posts)
        data = json.loads((g.output_dir / "search.json").read_text())
        assert len(data) == 5


# ---------------------------------------------------------------------------
# generate_individual_posts
# ---------------------------------------------------------------------------

class TestGenerateIndividualPosts:
    def _one_post(self, title="Test Post", date="2025-01-01"):
        return [{
            "title": title, "date": date, "type": "blog", "category": "General",
            "content": "<p>Hello</p>", "raw_content": "Hello",
            "filename": "2025-01-01-test", "url": "/blog/2025-01-01-test.html",
            "excerpt": "Hello", "is_truncated": False, "tags": [],
        }]

    def test_blog_post_goes_to_blog_subdir(self, generator):
        g = generator
        g.generate_individual_posts(self._one_post(), "blog")
        assert (g.output_dir / "blog" / "2025-01-01-test.html").exists()

    def test_page_goes_to_root_output(self, generator):
        g = generator
        post = self._one_post()
        post[0].update({"type": "page", "filename": "about",
                         "url": "/about.html"})
        g.generate_individual_posts(post, "pages")
        assert (g.output_dir / "about.html").exists()

    def test_raindrop_goes_to_raindrops_subdir(self, generator):
        g = generator
        post = self._one_post()
        post[0].update({
            "type": "drop", "filename": "25-01-01-1-link",
            "url": "/raindrops/25-01-01-1-link.html",
            "raindrop_url": "https://x.com", "domain": "x.com",
            "cover": "", "note": "", "tags": [], "important": False,
            "broken": False, "raindrop_type": "link", "media": [],
        })
        g.generate_individual_posts(post, "raindrops")
        assert (g.output_dir / "raindrops" / "25-01-01-1-link.html").exists()

    def test_output_contains_post_title(self, generator):
        g = generator
        g.generate_individual_posts(self._one_post("Unique Title Here"), "blog")
        html = (g.output_dir / "blog" / "2025-01-01-test.html").read_text()
        assert "Unique Title Here" in html


# ---------------------------------------------------------------------------
# generate_listing_pages
# ---------------------------------------------------------------------------

class TestGenerateListingPages:
    def _posts(self, n, content_type="blog"):
        return [
            {"title": f"Post {i}", "date": f"2025-01-{i+1:02d}", "type": content_type,
             "category": "General", "content": "<p>body</p>", "raw_content": "body",
             "filename": f"2025-01-{i+1:02d}-post-{i}", "url": f"/blog/p{i}.html",
             "excerpt": "Ex", "is_truncated": False}
            for i in range(n)
        ]

    def test_pages_type_skipped(self, generator):
        g = generator
        g.generate_listing_pages([], "pages")
        assert not (g.output_dir / "pages").exists()

    def test_creates_index_html_for_first_page(self, generator):
        g = generator
        g.generate_listing_pages(self._posts(3), "blog")
        assert (g.output_dir / "blog" / "index.html").exists()

    def test_creates_paginated_files_for_overflow(self, generator):
        g = generator
        # 21 posts → 2 pages (20 per page)
        g.generate_listing_pages(self._posts(21), "blog")
        assert (g.output_dir / "blog" / "index.html").exists()
        assert (g.output_dir / "blog" / "page-2.html").exists()

    def test_empty_posts_still_creates_index(self, generator):
        g = generator
        g.generate_listing_pages([], "blog")
        assert (g.output_dir / "blog" / "index.html").exists()


# ---------------------------------------------------------------------------
# generate_home_page
# ---------------------------------------------------------------------------

class TestGenerateHomePage:
    def _post(self, title, date):
        return {"title": title, "date": date, "type": "blog", "category": "General",
                "content": "<p>x</p>", "raw_content": "x",
                "filename": "f", "url": "/blog/f.html",
                "excerpt": "Ex", "is_truncated": False, "tags": []}

    def test_creates_index_html(self, generator):
        g = generator
        g.generate_home_page([], [])
        assert (g.output_dir / "index.html").exists()

    def test_uses_at_most_5_recent_posts(self, generator):
        g = generator
        posts = [self._post(f"Post {i}", f"2025-01-{i+1:02d}") for i in range(8)]
        g.generate_home_page(posts, [])
        html = (g.output_dir / "index.html").read_text()
        # With 8 posts and default count=5, only the 5 newest appear; oldest do not
        assert "Post 0" not in html
        assert "Post 1" not in html
        assert "Post 2" not in html

    def test_home_page_shows_newest_post_first(self, generator, tmp_path, monkeypatch):
        monkeypatch.setenv("HOME_POSTS_COUNT", "2")
        g = generator
        posts = [
            self._post("Old Post", "2024-01-01"),
            self._post("New Post", "2025-12-31"),
            self._post("Middle Post", "2025-06-15"),
        ]
        g.generate_home_page(posts, [])
        html = (g.output_dir / "index.html").read_text()
        # Only the 2 newest (New Post, Middle Post) should appear
        assert "New Post" in html
        assert "Middle Post" in html
        assert "Old Post" not in html

    def test_home_page_contains_recent_post_title(self, generator):
        g = generator
        g.generate_home_page([self._post("Featured Post", "2025-06-01")], [])
        html = (g.output_dir / "index.html").read_text()
        assert "Featured Post" in html


# ---------------------------------------------------------------------------
# generate_pages_listing
# ---------------------------------------------------------------------------

class TestGeneratePagesListing:
    def test_creates_pages_index(self, generator):
        g = generator
        g.generate_pages_listing([])
        assert (g.output_dir / "pages" / "index.html").exists()

    def test_pages_sorted_alphabetically(self, generator):
        g = generator
        pages = [
            {"title": "Zebra", "date": "2025-01-01", "url": "/zebra.html",
             "filename": "zebra", "excerpt": "", "type": "page",
             "content": "", "raw_content": "", "category": "x", "is_truncated": False},
            {"title": "Apple", "date": "2025-01-01", "url": "/apple.html",
             "filename": "apple", "excerpt": "", "type": "page",
             "content": "", "raw_content": "", "category": "x", "is_truncated": False},
        ]
        g.generate_pages_listing(pages)
        html = (g.output_dir / "pages" / "index.html").read_text()
        assert html.index("Apple") < html.index("Zebra")


# ---------------------------------------------------------------------------
# reset_output
# ---------------------------------------------------------------------------

class TestResetOutput:
    def test_removes_existing_output(self, generator):
        g = generator
        (g.output_dir / "file.html").write_text("hello")
        g.reset_output()
        assert not g.output_dir.exists()

    def test_safe_when_output_missing(self, generator, tmp_path):
        g = generator
        g.output_dir = tmp_path / "no_such_dir"
        g.reset_output()  # should not raise


# ---------------------------------------------------------------------------
# incremental_regenerate_post
# ---------------------------------------------------------------------------

class TestIncrementalRegenerate:
    def test_regenerates_individual_post_file(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        g.raindrops_dir = tmp_path / "raindrops"
        g.pages_dir = tmp_path / "pages"
        make_blog_post(blog_dir, "2025-03-01-hello.md", "Hello Post", "2025-03-01")
        g.incremental_regenerate_post("2025-03-01-hello.md", "blog")
        assert (g.output_dir / "blog" / "2025-03-01-hello.html").exists()

    def test_regenerates_search_index(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        g.raindrops_dir = tmp_path / "raindrops"
        g.pages_dir = tmp_path / "pages"
        make_blog_post(blog_dir, "2025-03-01-hello.md", "Hello Post", "2025-03-01")
        g.incremental_regenerate_post("2025-03-01-hello.md", "blog")
        assert (g.output_dir / "search.json").exists()

    def test_regenerates_home_page(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        g.raindrops_dir = tmp_path / "raindrops"
        g.pages_dir = tmp_path / "pages"
        make_blog_post(blog_dir, "2025-03-01-hello.md", "Hello Post", "2025-03-01")
        g.incremental_regenerate_post("2025-03-01-hello.md", "blog")
        assert (g.output_dir / "index.html").exists()


# ---------------------------------------------------------------------------
# incremental_regenerate_after_deletion
# ---------------------------------------------------------------------------

class TestIncrementalDeletion:
    def test_removes_deleted_post_output(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        g.raindrops_dir = tmp_path / "raindrops"
        g.pages_dir = tmp_path / "pages"
        # Pre-create the post output file (simulating a prior generation)
        (g.output_dir / "blog").mkdir()
        stale = g.output_dir / "blog" / "2025-01-01-gone.html"
        stale.write_text("<html>old</html>")
        g.incremental_regenerate_after_deletion("2025-01-01-gone.md", "blog")
        assert not stale.exists()

    def test_regenerates_listing_after_deletion(self, generator, tmp_path):
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        g.raindrops_dir = tmp_path / "raindrops"
        g.pages_dir = tmp_path / "pages"
        make_blog_post(blog_dir, "2025-01-02-remaining.md", "Remaining", "2025-01-02")
        g.incremental_regenerate_after_deletion("2025-01-01-gone.md", "blog")
        assert (g.output_dir / "blog" / "index.html").exists()


class TestNewPostAppearsOnHomePage:
    """Regression tests for bug: new post not showing on front page after creation."""

    def test_new_post_appears_in_home_page_after_incremental_regen(self, generator, tmp_path):
        """After incremental regen for a new post, its title must appear in index.html."""
        g = generator
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        g.blog_dir = blog_dir
        g.raindrops_dir = tmp_path / "raindrops"
        g.pages_dir = tmp_path / "pages"

        # Create pre-existing posts so home page was already generated
        make_blog_post(blog_dir, "2026-01-01-old.md", "Old Post", "2026-01-01")

        # Write the initial home page
        g.generate_home_page(g.load_posts("blog"), [])

        # Simulate creating a new post (yesterday)
        make_blog_post(blog_dir, "2026-02-28-new.md", "Brand New Post", "2026-02-28")

        # Incremental regen should update index.html
        g.incremental_regenerate_post("2026-02-28-new.md", "blog")

        html = (g.output_dir / "index.html").read_text()
        assert "Brand New Post" in html

