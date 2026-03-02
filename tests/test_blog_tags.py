#!/usr/bin/env python3
# test_blog_tags.py — Tests for F23 tag selection for blog posts
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import frontmatter
import pytest
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from salasblog2.utils import BLOG_TAGS, format_date, get_markdown_processor, slugify_tag

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def make_env():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    md = get_markdown_processor()
    env.filters["strftime"] = lambda d, fmt: format_date(d, fmt)
    env.filters["markdown"] = lambda text: md.convert(text) if text else ""
    env.filters["slugify"] = slugify_tag
    return env


class TestBlogTagsConstant:
    def test_blog_tags_is_a_list(self):
        assert isinstance(BLOG_TAGS, list)

    def test_blog_tags_not_empty(self):
        assert len(BLOG_TAGS) > 0

    def test_blog_tags_are_strings(self):
        assert all(isinstance(t, str) for t in BLOG_TAGS)

    def test_blog_tags_no_duplicates(self):
        assert len(BLOG_TAGS) == len(set(BLOG_TAGS))

    def test_blog_tags_lowercase(self):
        assert all(t == t.lower() for t in BLOG_TAGS)


class TestBloggerApiTagParsing:
    def _make_api(self, tmp_path):
        from salasblog2.blogger_api import BloggerAPI
        api = BloggerAPI.__new__(BloggerAPI)
        api.root_dir = tmp_path
        api.blog_dir = tmp_path / "content" / "blog"
        api.blog_dir.mkdir(parents=True)
        return api

    def test_parse_struct_with_mt_keywords(self, tmp_path):
        api = self._make_api(tmp_path)
        struct = {"title": "My Post", "description": "body", "mt_keywords": "python, coding"}
        title, body, tags = api._parse_content_or_struct(struct)
        assert "python" in tags
        assert "coding" in tags

    def test_parse_struct_with_tags_list(self, tmp_path):
        api = self._make_api(tmp_path)
        struct = {"title": "My Post", "description": "body", "tags": ["ai", "design"]}
        title, body, tags = api._parse_content_or_struct(struct)
        assert tags == ["ai", "design"]

    def test_parse_struct_no_tags_returns_empty(self, tmp_path):
        api = self._make_api(tmp_path)
        struct = {"title": "My Post", "description": "body"}
        title, body, tags = api._parse_content_or_struct(struct)
        assert tags == []

    def test_parse_string_returns_empty_tags(self, tmp_path):
        api = self._make_api(tmp_path)
        title, body, tags = api._parse_content_or_struct("Post Title\nBody content here.")
        assert tags == []

    def test_create_post_frontmatter_includes_tags(self, tmp_path):
        api = self._make_api(tmp_path)
        post = api._create_post_frontmatter("Title", "Body", ["technology", "ai"])
        assert post.metadata["tags"] == ["technology", "ai"]

    def test_create_post_frontmatter_empty_tags(self, tmp_path):
        api = self._make_api(tmp_path)
        post = api._create_post_frontmatter("Title", "Body", [])
        assert post.metadata["tags"] == []


class TestTagsInTemplates:
    def test_new_post_template_has_tag_checkboxes(self):
        env = make_env()
        tpl = env.get_template("new_post.html")
        html = tpl.render(content_type="blog", content_type_title="Post",
                         action_url="/admin/new-post", cancel_url="/blog/",
                         blog_tags=BLOG_TAGS)
        for tag in BLOG_TAGS:
            assert f'value="{tag}"' in html

    def test_edit_post_template_prechecks_existing_tags(self):
        env = make_env()
        tpl = env.get_template("edit_post.html")
        html = tpl.render(content_type="blog", content_type_title="Post",
                         title="My Post", date="2025-01-01", category="General",
                         content="body", filename="foo.md",
                         action_url="/admin/edit-post/foo.md",
                         cancel_url="/blog/", blog_tags=BLOG_TAGS,
                         tags=["technology", "ai"])
        assert 'value="technology"' in html
        assert 'value="ai"' in html
        # technology should be checked
        assert 'value="technology" checked' in html or 'checked' in html

    def test_edit_post_template_no_tags_context(self):
        env = make_env()
        tpl = env.get_template("edit_post.html")
        html = tpl.render(content_type="blog", content_type_title="Post",
                         title="My Post", date="2025-01-01", category="General",
                         content="body", filename="foo.md",
                         action_url="/admin/edit-post/foo.md",
                         cancel_url="/blog/", blog_tags=BLOG_TAGS,
                         tags=[])
        # No checkboxes should be pre-checked
        assert 'checked' not in html

    def test_tag_checkboxes_not_shown_for_pages(self):
        env = make_env()
        tpl = env.get_template("new_post.html")
        html = tpl.render(content_type="page", content_type_title="Page",
                         action_url="/admin/new-page", cancel_url="/pages/",
                         blog_tags=BLOG_TAGS)
        # Tags section should not appear for pages
        assert 'name="tags"' not in html
