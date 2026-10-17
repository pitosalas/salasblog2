#!/usr/bin/env python3
# test_legacy_commands — Tests for building the legacy URL map and rewriting content
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-17
# Updated: 2026-10-17

import json

import pytest

from salasblog2.legacy_commands import build_map, redirect_targets, rewrite_content
from salasblog2.wayback import ArchivedPost


@pytest.fixture
def content_root(tmp_path, monkeypatch):
    blog = tmp_path / "content" / "blog"
    blog.mkdir(parents=True)
    (tmp_path / "content" / "pages").mkdir()
    (blog / "2004-11-29-why-improv.md").write_text(
        "---\ntitle: Why Improv didn't succeed\ndate: '2004-11-29'\n---\nbody\n"
    )
    (blog / "2004-12-02-part-deux.md").write_text(
        "---\ntitle: Part Deux\ndate: '2004-12-02'\n---\n"
        "My [earlier posting](/weblogs/archives/000522.html) and "
        "[gone](/weblogs/archives/000999.html).\n"
    )
    archived = {
        "/weblogs/archives/000522.html": ArchivedPost(
            "Why Improv didn't succeed", "2004-11-28", "snap"
        ),
        "/weblogs/archives/000999.html": None,
    }
    monkeypatch.setattr(
        "salasblog2.legacy_commands.resolve_paths",
        lambda paths, cache_file: {path: archived[path] for path in paths},
    )
    return tmp_path / "content"


def test_build_map_records_matches_and_sources(content_root, tmp_path):
    map_file = tmp_path / "map.json"
    url_map = build_map(content_root, map_file, tmp_path / "cache.json")
    assert (
        url_map["/weblogs/archives/000522.html"]["new"]
        == "/blog/2004-11-29-why-improv.html"
    )
    assert url_map["/weblogs/archives/000522.html"]["linked_from"] == [
        "2004-12-02-part-deux.md"
    ]
    assert url_map["/weblogs/archives/000999.html"]["confidence"] == "unmatched"
    assert json.loads(map_file.read_text()) == url_map


def test_build_map_keeps_reviewed_entries(content_root, tmp_path):
    map_file = tmp_path / "map.json"
    reviewed = {
        "scheme": "mt",
        "new": "/blog/manual.html",
        "confidence": "fuzzy",
        "reviewed": True,
    }
    map_file.write_text(json.dumps({"/weblogs/archives/000999.html": reviewed}))
    url_map = build_map(content_root, map_file, tmp_path / "cache.json")
    assert url_map["/weblogs/archives/000999.html"] == reviewed


def test_build_map_keeps_entries_no_longer_linked(content_root, tmp_path):
    map_file = tmp_path / "map.json"
    rewritten = {"scheme": "wp", "new": "/blog/old.html", "confidence": "exact"}
    map_file.write_text(json.dumps({"/2008/02/18/already-rewritten": rewritten}))
    url_map = build_map(content_root, map_file, tmp_path / "cache.json")
    assert url_map["/2008/02/18/already-rewritten"] == rewritten
    assert "/weblogs/archives/000522.html" in url_map


def test_rewrite_dry_run_leaves_files_alone(content_root, tmp_path, capsys):
    map_file = tmp_path / "map.json"
    build_map(content_root, map_file, tmp_path / "cache.json")
    post = content_root / "blog" / "2004-12-02-part-deux.md"
    before = post.read_text()
    assert rewrite_content(content_root, map_file, is_dry_run=True) == 1
    assert post.read_text() == before
    assert "would rewrite 1 links" in capsys.readouterr().out


def test_rewrite_apply_changes_only_mapped_links(content_root, tmp_path):
    map_file = tmp_path / "map.json"
    build_map(content_root, map_file, tmp_path / "cache.json")
    rewrite_content(content_root, map_file, is_dry_run=False)
    post = (content_root / "blog" / "2004-12-02-part-deux.md").read_text()
    assert "[earlier posting](/blog/2004-11-29-why-improv.html)" in post
    assert "[gone](/weblogs/archives/000999.html)" in post


def test_redirect_targets_skips_null_entries():
    url_map = {"/a": {"new": "/blog/a.html"}, "/b": {"new": None}}
    assert redirect_targets(url_map) == {"/a": "/blog/a.html"}
