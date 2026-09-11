#!/usr/bin/env python3
# test_home_see_all.py — Tests that "see all" links appear on home page
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-08
# Updated: 2026-09-08
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


def fake_post(is_truncated=False):
    return {
        "title": "Post",
        "url": "/blog/p.html",
        "date": "2024-01-15",
        "category": "tech",
        "excerpt": "Excerpt.",
        "tags": [],
        "is_truncated": is_truncated,
    }


def fake_raindrop():
    return {
        "title": "Link",
        "url": "https://example.com",
        "date": "2024-01-15",
        "note": "A note.",
    }


def render_home(is_truncated=False):
    env = make_env()
    template = env.get_template("home.html")
    return template.render(
        recent_posts=[fake_post(is_truncated=is_truncated)],
        recent_raindrops=[fake_raindrop()],
        NOTE_TRUNCATE_LENGTH=200,
    )


def test_see_all_posts_link_present():
    html = render_home()
    assert "/blog/index.html" in html
    assert "See all posts" in html


def test_see_all_links_link_present():
    html = render_home()
    assert "/raindrops/index.html" in html
    assert "See all links" in html


def test_read_more_link_shown_when_truncated():
    """Regression: the home page had no way to reach the full post for a
    truncated excerpt — blog_list.html already had this, home.html didn't."""
    html = render_home(is_truncated=True)
    assert 'href="/blog/p.html" class="read-more">Read more' in html


def test_read_more_link_absent_when_not_truncated():
    html = render_home(is_truncated=False)
    assert "Read more" not in html
