#!/usr/bin/env python3
# test_bootstrap_styling.py — Tests confirming Bootstrap classes in rendered HTML
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-09
# Updated: 2026-09-09
# Open Source Under MIT license

from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from salasblog2.utils import (
    format_date,
    group_posts_by_month,
    get_markdown_processor,
    slugify_tag,
)

PROJECT_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PROJECT_ROOT / "templates"


def make_env():
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    md = get_markdown_processor()
    env.filters["strftime"] = lambda d, fmt: format_date(d, fmt)
    env.filters["dd_mm_yyyy"] = lambda d: format_date(d, "%d-%m-%Y")
    env.filters["group_by_month"] = group_posts_by_month
    env.filters["markdown"] = lambda text: md.convert(text) if text else ""
    env.filters["truncate"] = (
        lambda s, n, killwords=False, end="...": s[:n] + end
        if s and len(s) > n
        else (s or "")
    )
    env.filters["slugify"] = slugify_tag
    return env


def fake_post():
    return {
        "title": "Test Post",
        "url": "/blog/test.html",
        "date": "2024-01-15",
        "category": "General",
        "excerpt": "Short excerpt",
        "is_truncated": False,
        "filename": "test",
        "content": "<p>Body</p>",
        "tags": [],
    }


def fake_raindrop():
    return {
        "title": "Test Link",
        "url": "/raindrops/test.html",
        "date": "2024-01-15",
        "note": "A note",
        "cover": None,
        "domain": "example.com",
        "excerpt": "excerpt",
        "raindrop_url": "https://example.com",
        "tags": ["tag1"],
        "important": False,
        "broken": False,
        "category": "General",
        "content": "<p>Body</p>",
        "filename": "test",
    }


def fake_page():
    return {
        "title": "About",
        "url": "/about.html",
        "excerpt": "About page",
        "category": "General",
        "filename": "about",
        "content": "<p>About</p>",
    }


def fake_pagination():
    return {
        "current_page": 1,
        "total_pages": 1,
        "has_prev": False,
        "has_next": False,
        "prev_url": None,
        "next_url": None,
        "page_urls": ["/blog/"],
    }


def render(template_name, context):
    env = make_env()
    context.setdefault("current_year", 2024)
    context.setdefault("NOTE_TRUNCATE_LENGTH", 200)
    return env.get_template(template_name).render(**context)


def test_base_contains_console_header():
    html = render(
        "home.html",
        {
            "recent_posts": [fake_post()],
            "recent_raindrops": [fake_raindrop()],
        },
    )
    assert "site-header" in html


def test_base_loads_console_css_not_bootstrap():
    html = render(
        "home.html",
        {
            "recent_posts": [],
            "recent_raindrops": [],
        },
    )
    assert "theme.css" in html
    assert "bootstrap" not in html.lower()


def test_home_uses_console_entry_list():
    html = render(
        "home.html",
        {
            "recent_posts": [fake_post()],
            "recent_raindrops": [],
        },
    )
    assert "entry-list" in html
    assert "card" not in html


def test_home_uses_console_grid_not_bootstrap():
    html = render(
        "home.html",
        {
            "recent_posts": [],
            "recent_raindrops": [],
        },
    )
    assert "home-grid" in html
    assert "col-md-" not in html


def test_blog_list_uses_pagination_class():
    post = fake_post()
    pagination = {
        "current_page": 1,
        "total_pages": 3,
        "has_prev": False,
        "has_next": True,
        "prev_url": None,
        "next_url": "/blog/2/",
        "page_urls": ["/blog/", "/blog/2/", "/blog/3/"],
    }
    html = render(
        "blog_list.html",
        {
            "posts": [post],
            "pagination": pagination,
            "total_posts": 60,
        },
    )
    assert "page-item" in html
    assert "page-link" in html


def test_raindrops_list_uses_console_entries():
    html = render(
        "raindrops_list.html",
        {
            "posts": [fake_raindrop()],
            "pagination": fake_pagination(),
            "total_posts": 1,
        },
    )
    assert "entry-post" in html
    assert "card" not in html


def test_pages_list_uses_console_entries():
    html = render(
        "pages_list.html",
        {
            "pages": [fake_page()],
            "site_title": "Salas Blog",
        },
    )
    assert "entry-list" in html
    assert "card" not in html


def test_blog_post_uses_post_body_not_bootstrap_grid():
    html = render(
        "blog_post.html",
        {
            "post": fake_post(),
            "prev_post": None,
            "next_post": None,
        },
    )
    assert "post-body" in html
    assert "col-lg-" not in html


def test_raindrop_post_uses_post_body_not_bootstrap_grid():
    html = render(
        "raindrop_post.html",
        {
            "post": fake_raindrop(),
            "prev_post": None,
            "next_post": None,
        },
    )
    assert "post-body" in html
    assert "col-lg-" not in html


def test_page_template_uses_post_body_not_bootstrap_grid():
    html = render("page.html", {"page": fake_page()})
    assert "post-body" in html
    assert "col-lg-" not in html


def test_404_uses_console_btn():
    html = render("404.html", {})
    assert "btn btn-edit" in html


def test_footer_uses_console_style():
    html = render("home.html", {"recent_posts": [], "recent_raindrops": []})
    assert "site-footer" in html
