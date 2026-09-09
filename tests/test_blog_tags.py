#!/usr/bin/env python3
# test_blog_tags.py — Tests for F23 tag selection for blog posts
# Author: Pito Salas and Claude Code
# Version: 2
# Created: 2026-09-08
# Updated: 2026-09-09
# Open Source Under MIT license

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
        struct = {
            "title": "My Post",
            "description": "body",
            "mt_keywords": "python, coding",
        }
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
        title, body, tags = api._parse_content_or_struct(
            "Post Title\nBody content here."
        )
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
    """post_editor.html (shared by create and edit, per F42) replaced the fixed
    BLOG_TAGS checkbox list with a free-form comma-separated tag input, with
    existing tags offered as suggestions rather than a hard vocabulary — see
    F42 point 6. F45 replaced the original single-match <datalist> suggestion
    UI with a searchable multi-select picklist (a plain <datalist> doesn't
    work well against 100 suggested tags); the `blog_tags` context var — now
    sourced from real tag-frequency data rather than the static BLOG_TAGS
    list, see F45 — still drives the suggestion list, just through different
    markup/JS."""

    def test_new_post_template_offers_tag_suggestions(self):
        env = make_env()
        tpl = env.get_template("post_editor.html")
        html = tpl.render(
            content_type="blog",
            content_type_title="Post",
            action_url="/admin/new-post",
            cancel_url="/blog/",
            blog_tags=BLOG_TAGS,
            is_edit=False,
        )
        assert 'id="tagPicklistToggle"' in html
        assert 'id="tagPicklistChips"' in html
        for tag in BLOG_TAGS:
            assert f'"{tag}"' in html

    def test_edit_post_template_prefills_existing_tags(self):
        env = make_env()
        tpl = env.get_template("post_editor.html")
        html = tpl.render(
            content_type="blog",
            content_type_title="Post",
            title="My Post",
            date="2025-01-01",
            category="General",
            content="body",
            filename="foo.md",
            action_url="/admin/edit-post/foo.md",
            cancel_url="/blog/",
            blog_tags=BLOG_TAGS,
            tags=["technology", "ai"],
            is_edit=True,
        )
        assert 'id="tags"' in html
        assert 'value="technology, ai"' in html

    def test_edit_post_template_no_tags_context(self):
        env = make_env()
        tpl = env.get_template("post_editor.html")
        html = tpl.render(
            content_type="blog",
            content_type_title="Post",
            title="My Post",
            date="2025-01-01",
            category="General",
            content="body",
            filename="foo.md",
            action_url="/admin/edit-post/foo.md",
            cancel_url="/blog/",
            blog_tags=BLOG_TAGS,
            tags=[],
            is_edit=True,
        )
        import re

        tags_input = re.search(r'<input[^>]*id="tags"[^>]*>', html)
        assert tags_input is not None
        assert 'value=""' in tags_input.group(0)

    def test_tag_input_not_shown_for_pages(self):
        env = make_env()
        tpl = env.get_template("post_editor.html")
        html = tpl.render(
            content_type="page",
            content_type_title="Page",
            action_url="/admin/new-page",
            cancel_url="/pages/",
            blog_tags=BLOG_TAGS,
            is_edit=False,
        )
        # Tags section should not appear for pages
        assert 'id="tags"' not in html
        assert 'name="tags_raw"' not in html
