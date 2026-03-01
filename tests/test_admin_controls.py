#!/usr/bin/env python3
# test_admin_controls.py — Tests for admin controls visibility behavior
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from pathlib import Path


TEMPLATES_DIR = Path(__file__).parent.parent / "templates"


def test_base_uses_classlist_remove_not_style_display():
    """base.html JS must use classList.remove('d-none') to reveal admin controls."""
    content = (TEMPLATES_DIR / "base.html").read_text()
    assert "classList.remove('d-none')" in content
    # Old broken pattern must not be present for admin-controls reveal
    assert "adminControls.style.display" not in content


def test_blog_post_admin_controls_hidden_by_default():
    """blog_post.html admin-controls div must carry d-none so it starts hidden."""
    content = (TEMPLATES_DIR / "blog_post.html").read_text()
    assert 'admin-controls d-none' in content


def test_blog_post_edit_button_uses_warning_style():
    """Edit button uses btn-warning to distinguish it from outline-secondary nav buttons."""
    content = (TEMPLATES_DIR / "blog_post.html").read_text()
    assert "btn-warning" in content
    assert "Edit this post" in content


def test_blog_post_derive_button_uses_info_style():
    """Derive button uses btn-info to distinguish it from nav and edit buttons."""
    content = (TEMPLATES_DIR / "blog_post.html").read_text()
    assert "btn-info" in content
    assert "New post based on this one" in content


def test_blog_post_nav_buttons_use_outline_secondary():
    """Prev/next nav buttons use btn-outline-secondary, visually distinct from action buttons."""
    content = (TEMPLATES_DIR / "blog_post.html").read_text()
    assert "btn-outline-secondary" in content


def test_new_post_button_hidden_via_d_none_not_inline_style():
    """admin-new-post nav item must use d-none class, not inline style, so JS classList.remove works."""
    content = (TEMPLATES_DIR / "base.html").read_text()
    assert 'admin-new-post d-none' in content
    # Inline style on this element would make classList.remove('d-none') ineffective
    assert 'admin-new-post" style="display: none;"' not in content


def test_admin_raindrop_tab_hidden_by_default():
    """tab-raindrop pane must carry d-none so Sync Raindrops button is hidden on page load."""
    content = (TEMPLATES_DIR / "admin.html").read_text()
    assert 'id="tab-raindrop"' in content
    # The pane must have d-none so it doesn't bleed into other tabs (e.g. Stats)
    assert 'admin-pane d-none" id="tab-raindrop"' in content
