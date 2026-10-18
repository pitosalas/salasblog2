#!/usr/bin/env python3
# test_strip_categories — Tests for removing the retired category frontmatter line
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-18
# Updated: 2026-10-18

from argparse import Namespace

import pytest

from salasblog2.cli import cmd_strip_categories
from salasblog2.utils import remove_frontmatter_key


@pytest.mark.parametrize(
    "line", ["category: '298'", 'category: "General"', "category: 538", "category:"]
)
def test_removes_only_the_category_line(line):
    text = f"---\ntitle: T\n{line}\ntags:\n- a\n---\nBody\n"
    assert remove_frontmatter_key(text, "category") == (
        "---\ntitle: T\ntags:\n- a\n---\nBody\n"
    )


def test_last_frontmatter_line():
    text = "---\ntitle: T\ncategory: '1'\n---\nBody\n"
    assert remove_frontmatter_key(text, "category") == "---\ntitle: T\n---\nBody\n"


def test_no_category_line_is_unchanged():
    text = "---\ntitle: T\n---\nBody\n"
    assert remove_frontmatter_key(text, "category") == text


def test_body_and_similar_keys_are_untouched():
    text = "---\ntitle: T\ncategory_old: x\n---\ncategory: in body\n"
    assert remove_frontmatter_key(text, "category") == text


def test_idempotent():
    text = "---\ncategory: '1'\ntitle: T\n---\nBody\n"
    once = remove_frontmatter_key(text, "category")
    assert remove_frontmatter_key(once, "category") == once


def test_multiline_value_raises():
    text = "---\ncategory:\n- a\n- b\ntitle: T\n---\nBody\n"
    with pytest.raises(ValueError):
        remove_frontmatter_key(text, "category")


def make_content(tmp_path):
    blog = tmp_path / "blog"
    blog.mkdir()
    (blog / "a.md").write_text("---\ntitle: A\ncategory: '298'\n---\nA\n")
    (blog / "b.md").write_text("---\ntitle: B\n---\nB\n")
    (tmp_path / "pages").mkdir()
    return blog


def test_command_dry_run_writes_nothing(tmp_path, capsys):
    blog = make_content(tmp_path)
    cmd_strip_categories(Namespace(content=str(tmp_path), apply=False))
    assert "category" in (blog / "a.md").read_text()
    assert "would strip category from 1 files" in capsys.readouterr().out


def test_command_apply_strips(tmp_path):
    blog = make_content(tmp_path)
    cmd_strip_categories(Namespace(content=str(tmp_path), apply=True))
    assert (blog / "a.md").read_text() == "---\ntitle: A\n---\nA\n"
    assert (blog / "b.md").read_text() == "---\ntitle: B\n---\nB\n"
