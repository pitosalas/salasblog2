#!/usr/bin/env python3
# test_content_type_badges.py — Tests for F24 content type visual indicators
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from salasblog2.utils import format_date, get_markdown_processor, slugify_tag

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def make_env():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    md = get_markdown_processor()
    env.filters["strftime"] = lambda d, fmt: format_date(d, fmt)
    env.filters["markdown"] = lambda text: md.convert(text) if text else ""
    env.filters["slugify"] = slugify_tag
    env.filters["truncate"] = lambda text, length, **kwargs: text[:length] if text else ""
    env.filters["dd_mm_yyyy"] = lambda d: str(d)
    env.filters["group_by_month"] = lambda posts: [{"month_name": "January 2025", "posts": posts}]
    return env


def make_raindrop(title="Test Link", url="/raindrops/test/"):
    return {
        "title": title,
        "url": url,
        "date": "2025-01-15",
        "tags": [],
        "note": None,
        "excerpt": None,
        "cover": None,
        "domain": None,
        "raindrop_url": None,
        "important": False,
        "broken": False,
        "collection": None,
    }


def make_post(title="Test Post", url="/blog/test/"):
    return {
        "title": title,
        "url": url,
        "date": "2025-01-15",
        "tags": [],
        "excerpt": "",
        "category": "General",
        "is_truncated": False,
    }


class TestLinkBadgeInRaindropsList:
    def test_link_badge_present_in_raindrops_list(self):
        env = make_env()
        tpl = env.get_template("raindrops_list.html")
        html = tpl.render(
            posts=[make_raindrop()],
            collections=[],
            collection_counts={},
            total_posts=1,
            pagination=None,
            NOTE_TRUNCATE_LENGTH=200,
        )
        assert "Link" in html
        assert "bg-info" in html

    def test_link_badge_per_item_in_raindrops_list(self):
        env = make_env()
        tpl = env.get_template("raindrops_list.html")
        raindrops = [make_raindrop(f"Link {i}", f"/raindrops/link{i}/") for i in range(3)]
        html = tpl.render(
            posts=raindrops,
            collections=[],
            collection_counts={},
            total_posts=3,
            pagination=None,
            NOTE_TRUNCATE_LENGTH=200,
        )
        assert html.count("bg-info") >= 3


class TestPostBadgeInBlogList:
    def test_post_badge_present_in_blog_list(self):
        env = make_env()
        tpl = env.get_template("blog_list.html")
        html = tpl.render(
            posts=[make_post()],
            pagination=None,
            total_posts=1,
        )
        assert "Post" in html
        assert "bg-success" in html

    def test_post_badge_per_item_in_blog_list(self):
        env = make_env()
        tpl = env.get_template("blog_list.html")
        posts = [make_post(f"Post {i}", f"/blog/post{i}/") for i in range(3)]
        html = tpl.render(
            posts=posts,
            pagination=None,
            total_posts=3,
        )
        assert html.count("bg-success") >= 3


class TestBadgesInDetailTemplates:
    def test_post_badge_in_blog_post_header(self):
        env = make_env()
        tpl = env.get_template("blog_post.html")
        post = {**make_post(), "content": "<p>body</p>", "filename": "test-post"}
        html = tpl.render(
            post=post,
            navigation=[],
            site_title="Test",
            prev_post=None,
            next_post=None,
        )
        assert "Post" in html
        assert "bg-success" in html

    def test_link_badge_in_raindrop_post_header(self):
        env = make_env()
        tpl = env.get_template("raindrop_post.html")
        post = {**make_raindrop(), "filename": "test-raindrop", "note": None}
        html = tpl.render(
            post=post,
            navigation=[],
            site_title="Test",
            prev_post=None,
            next_post=None,
        )
        assert "Link" in html
        assert "bg-info" in html


class TestBadgesOnHomePage:
    def test_post_badge_on_home_recent_posts(self):
        env = make_env()
        tpl = env.get_template("home.html")
        html = tpl.render(
            recent_posts=[make_post()],
            recent_raindrops=[],
            navigation=[],
            site_title="Test",
            NOTE_TRUNCATE_LENGTH=200,
        )
        assert "bg-success" in html

    def test_link_badge_on_home_recent_raindrops(self):
        env = make_env()
        tpl = env.get_template("home.html")
        html = tpl.render(
            recent_posts=[],
            recent_raindrops=[make_raindrop()],
            navigation=[],
            site_title="Test",
            NOTE_TRUNCATE_LENGTH=200,
        )
        assert "bg-info" in html
