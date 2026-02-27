#!/usr/bin/env python3
# test_tag_pages.py — Tests for F18 clickable tag pages
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from pathlib import Path
import pytest
from jinja2 import Environment, FileSystemLoader
from salasblog2.utils import format_date, group_posts_by_month, get_markdown_processor, slugify_tag

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def make_env():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    md = get_markdown_processor()
    env.filters["strftime"] = lambda d, fmt: format_date(d, fmt)
    env.filters["dd_mm_yyyy"] = lambda d: format_date(d, "%d-%m-%Y")
    env.filters["group_by_month"] = group_posts_by_month
    env.filters["markdown"] = lambda text: md.convert(text) if text else ""
    env.filters["slugify"] = slugify_tag
    env.filters["truncate"] = lambda s, n, killwords=False, end="...": s[:n] + end if s and len(s) > n else (s or "")
    return env


def fake_post(tags=None):
    return {
        "title": "Tagged Post",
        "url": "/blog/tagged-post.html",
        "date": "2024-01-15",
        "category": "Tech",
        "excerpt": "An excerpt.",
        "is_truncated": False,
        "filename": "tagged-post",
        "content": "<p>Body</p>",
        "tags": tags or [],
    }


# --- slugify_tag tests ---

def test_slugify_lowercase():
    assert slugify_tag("Python") == "python"


def test_slugify_spaces_to_hyphens():
    assert slugify_tag("open source") == "open-source"


def test_slugify_strips_special_chars():
    assert slugify_tag("C++") == "c"


def test_slugify_strips_leading_trailing_hyphens():
    assert slugify_tag("-tag-") == "tag"


def test_slugify_multiple_spaces():
    assert slugify_tag("web  dev") == "web-dev"


# --- Template rendering tests ---

def test_tag_links_in_blog_post_html():
    env = make_env()
    template = env.get_template("blog_post.html")
    post = fake_post(tags=["python", "web"])
    html = template.render(post=post, navigation=[], prev_post=None, next_post=None)
    assert "/tags/python/index.html" in html
    assert "/tags/web/index.html" in html


def test_tag_links_in_blog_list_html():
    env = make_env()
    template = env.get_template("blog_list.html")
    post = fake_post(tags=["open-source"])
    html = template.render(
        posts=[post],
        navigation=[],
        pagination={"current_page": 1, "total_pages": 1, "has_prev": False, "has_next": False, "page_urls": []},
        total_posts=1,
    )
    assert "/tags/open-source/index.html" in html


def test_tag_links_in_home_html():
    env = make_env()
    template = env.get_template("home.html")
    post = fake_post(tags=["science"])
    html = template.render(
        recent_posts=[post],
        recent_raindrops=[],
        navigation=[],
        NOTE_TRUNCATE_LENGTH=200,
    )
    assert "/tags/science/index.html" in html


def test_generate_tag_pages_creates_files(tmp_path):
    from salasblog2.generator import SiteGenerator

    gen = SiteGenerator()
    gen.output_dir = tmp_path
    gen.templates_dir = PROJECT_ROOT / "templates"
    gen.jinja_env = make_env()

    posts = [
        fake_post(tags=["python", "web"]),
        fake_post(tags=["python"]),
    ]
    gen.generate_tag_pages(posts)

    assert (tmp_path / "tags" / "python" / "index.html").exists()
    assert (tmp_path / "tags" / "web" / "index.html").exists()


# --- Bug regression tests ---

def test_numeric_tags_are_not_displayed():
    # Tags that are purely numeric IDs (WordPress import artifacts) must not appear as badges
    env = make_env()
    template = env.get_template("blog_post.html")
    post = fake_post(tags=["615", "1797", "python"])
    html = template.render(post=post, navigation=[], prev_post=None, next_post=None)
    # Numeric-only tags should be filtered out before rendering
    assert '">615<' not in html
    assert '">1797<' not in html
    # Real text tag should still appear
    assert ">python<" in html


def test_tag_link_resolves_to_generated_page(tmp_path):
    # Each tag badge link in rendered HTML must point to an actually-generated tag page
    import re
    from salasblog2.generator import SiteGenerator

    gen = SiteGenerator()
    gen.output_dir = tmp_path
    gen.templates_dir = PROJECT_ROOT / "templates"
    gen.jinja_env = make_env()

    posts = [fake_post(tags=["robotics", "open-source"])]
    gen.generate_tag_pages(posts)

    env = make_env()
    template = env.get_template("blog_post.html")
    html = template.render(post=posts[0], navigation=[], prev_post=None, next_post=None)

    slugs = re.findall(r'href="/tags/([^/]+)/index\.html"', html)
    assert len(slugs) > 0, "Expected tag links in rendered HTML"
    for slug in slugs:
        assert (tmp_path / "tags" / slug / "index.html").exists(), \
            f"Tag page missing for slug '{slug}'"
