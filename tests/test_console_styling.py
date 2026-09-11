#!/usr/bin/env python3
# test_console_styling.py — Repo-wide checks that F47's Console theme
# fully replaced Bootstrap, across all 13 in-scope templates.
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-11
# Updated: 2026-09-11
# Open Source Under MIT license

from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"

# Every template touched by F47: the 9 public ones (via base.html) plus
# the 4 standalone admin/editor pages.
ALL_F47_TEMPLATES = [
    "base.html",
    "home.html",
    "blog_list.html",
    "blog_post.html",
    "raindrops_list.html",
    "raindrop_post.html",
    "pages_list.html",
    "page.html",
    "tag_page.html",
    "404.html",
    "admin_login.html",
    "post_editor.html",
    "admin.html",
    "stats_page.html",
]


def test_no_bootstrap_cdn_links_remain_anywhere():
    for name in ALL_F47_TEMPLATES:
        content = (TEMPLATES_DIR / name).read_text()
        assert "bootstrap@5.3.3" not in content, (
            f"{name} still references the Bootstrap CDN"
        )
        assert "bootstrap-icons" not in content, (
            f"{name} still references Bootstrap Icons"
        )


def test_base_html_links_all_shared_console_css():
    content = (TEMPLATES_DIR / "base.html").read_text()
    for css_file in [
        "theme.css",
        "header.css",
        "layout.css",
        "entries.css",
        "post-detail.css",
    ]:
        assert css_file in content, f"base.html doesn't link {css_file}"
    assert "theme-toggle.js" in content


def test_base_html_has_theme_toggle_button():
    content = (TEMPLATES_DIR / "base.html").read_text()
    assert 'id="theme-toggle"' in content


def test_admin_pages_link_theme_css():
    for name in ["admin_login.html", "post_editor.html", "admin.html", "stats_page.html"]:
        content = (TEMPLATES_DIR / name).read_text()
        assert "theme.css" in content, f"{name} doesn't link theme.css"


def test_admin_and_login_share_site_header_with_public_pages():
    admin_content = (TEMPLATES_DIR / "admin.html").read_text()
    base_content = (TEMPLATES_DIR / "base.html").read_text()
    assert "site-header" in admin_content
    assert "site-header" in base_content


def test_all_css_files_referenced_by_templates_exist():
    static_css_dir = Path(__file__).parent.parent / "static" / "css"
    for name in ALL_F47_TEMPLATES:
        content = (TEMPLATES_DIR / name).read_text()
        for line in content.splitlines():
            if 'href="/static/css/' not in line:
                continue
            start = line.index('href="/static/css/') + len('href="/static/css/')
            end = line.index('"', start)
            css_name = line[start:end]
            assert (static_css_dir / css_name).exists(), (
                f"{name} references missing static/css/{css_name}"
            )
