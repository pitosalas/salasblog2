#!/usr/bin/env python3
# test_image_size.py — Tests for image_size frontmatter feature
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import pytest
from pathlib import Path
from salasblog2.generator import SiteGenerator


def make_blog_post(directory, filename, title, date, content="Post body.", image_size=None):
    image_size_line = f"image_size: {image_size!r}\n" if image_size else ""
    (directory / filename).write_text(
        f"---\ntitle: {title!r}\ndate: '{date}'\ntype: blog\n{image_size_line}---\n{content}\n"
    )


class TestImageSizeGenerator:
    def test_image_size_included_in_post_data(self, generator, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        generator.blog_dir = blog_dir
        make_blog_post(blog_dir, "2025-01-01-test.md", "Test", "2025-01-01", image_size="medium")
        posts = generator.load_posts("blog")
        assert posts[0]["image_size"] == "medium"

    def test_image_size_missing_defaults_to_empty_string(self, generator, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        generator.blog_dir = blog_dir
        make_blog_post(blog_dir, "2025-01-01-test.md", "Test", "2025-01-01")
        posts = generator.load_posts("blog")
        assert posts[0]["image_size"] == ""

    def test_all_valid_sizes_are_read(self, generator, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        generator.blog_dir = blog_dir
        for i, size in enumerate(["small", "medium", "large", "full"]):
            make_blog_post(blog_dir, f"2025-01-0{i+1}-test.md", f"Test {size}", f"2025-01-0{i+1}", image_size=size)
        posts = generator.load_posts("blog")
        sizes = {p["image_size"] for p in posts}
        assert sizes == {"small", "medium", "large", "full"}


class TestImageSizeServerLoadSave:
    def test_load_content_item_returns_image_size(self, tmp_path):
        from salasblog2 import server
        content_file = tmp_path / "test-post.md"
        content_file.write_text(
            "---\ntitle: Test\ndate: '2025-01-01'\ntype: blog\nimage_size: large\n---\nContent here.\n"
        )
        original_func = server.get_content_directory
        server.get_content_directory = lambda ct: tmp_path
        try:
            result = server.load_content_item("test-post.md", "blog")
            assert result["image_size"] == "large"
        finally:
            server.get_content_directory = original_func

    def test_load_content_item_no_image_size_defaults_empty(self, tmp_path):
        from salasblog2 import server
        content_file = tmp_path / "test-post.md"
        content_file.write_text(
            "---\ntitle: Test\ndate: '2025-01-01'\ntype: blog\n---\nContent here.\n"
        )
        original_func = server.get_content_directory
        server.get_content_directory = lambda ct: tmp_path
        try:
            result = server.load_content_item("test-post.md", "blog")
            assert result["image_size"] == ""
        finally:
            server.get_content_directory = original_func

    def test_save_content_item_writes_image_size(self, tmp_path):
        from salasblog2 import server
        import frontmatter
        content_file = tmp_path / "test-post.md"
        content_file.write_text("---\ntitle: Old\ndate: '2025-01-01'\ntype: blog\n---\nOld content.\n")
        original_func = server.get_content_directory
        server.get_content_directory = lambda ct: tmp_path
        try:
            server.save_content_item("test-post.md", "blog", "New Title", "2025-01-01", "blog", "New content.", [], image_size="small")
            with open(content_file) as f:
                saved = frontmatter.load(f)
            assert saved.metadata.get("image_size") == "small"
        finally:
            server.get_content_directory = original_func

    def test_save_content_item_omits_image_size_when_empty(self, tmp_path):
        from salasblog2 import server
        import frontmatter
        content_file = tmp_path / "test-post.md"
        content_file.write_text("---\ntitle: Old\ndate: '2025-01-01'\ntype: blog\n---\nOld content.\n")
        original_func = server.get_content_directory
        server.get_content_directory = lambda ct: tmp_path
        try:
            server.save_content_item("test-post.md", "blog", "New Title", "2025-01-01", "blog", "New content.", [], image_size="")
            with open(content_file) as f:
                saved = frontmatter.load(f)
            assert "image_size" not in saved.metadata
        finally:
            server.get_content_directory = original_func
