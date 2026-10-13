#!/usr/bin/env python3
# test_wayback — Tests for parsing archived Movable Type pages
# Author: Pito Salas and Claude Code

from pathlib import Path

import pytest
import requests

from salasblog2.wayback import (
    ArchivedPost,
    get_with_retry,
    parse_archived_post,
    resolve_paths,
)

FIXTURES = Path(__file__).parent / "fixtures" / "wayback"


def test_parse_html_era_page_uses_date_header():
    page = (FIXTURES / "mt_000522.html").read_text(encoding="latin-1")
    archived = parse_archived_post(page, "snap")
    assert archived == ArchivedPost("Why Improv didn't succeed", "2004-11-28", "snap")


def test_parse_php_era_page_uses_dc_date():
    page = (FIXTURES / "mt_001350.html").read_text(encoding="latin-1")
    archived = parse_archived_post(page, "snap")
    assert archived.title == "More musings on the not-better-RSS-aggregator"
    assert archived.date == "2006-10-12"


def test_parse_posted_on_footer_with_padded_day():
    page = (FIXTURES / "mt_000571.html").read_text(encoding="latin-1")
    archived = parse_archived_post(page, "snap")
    assert archived == ArchivedPost("A9's Photographic Yellow Pages", "2005-02-01", "snap")


def test_parse_posted_on_footer_when_no_other_date():
    page = (
        "<title>Pito's Blog: A &amp; B</title>"
        "<span>Posted by Pito Salas on March 3, 2005 09:21 PM</span>"
    )
    assert parse_archived_post(page, "s") == ArchivedPost("A & B", "2005-03-03", "s")


def test_parse_raises_without_title():
    with pytest.raises(ValueError, match="No <title>"):
        parse_archived_post("<h2 class=\"date\">May 1, 2004</h2>", "s")


def test_parse_raises_without_date():
    with pytest.raises(ValueError, match="No entry date"):
        parse_archived_post("<title>Pito's Blog: X</title>", "s")


def test_resolve_paths_uses_cache_without_network(tmp_path, monkeypatch):
    cache_file = tmp_path / "wayback.json"
    cache_file.write_text(
        '{"/weblogs/archives/000522.html": '
        '{"title": "T", "date": "2004-11-28", "snapshot_url": "s"},'
        ' "/weblogs/archives/000001.html": null}'
    )

    def fail_lookup(path, session):
        raise AssertionError(f"network lookup for cached path {path}")

    monkeypatch.setattr("salasblog2.wayback.snapshot_index", fail_lookup)
    monkeypatch.setattr("salasblog2.wayback.fetch_archived_post", fail_lookup)
    resolved = resolve_paths(
        ["/weblogs/archives/000522.html", "/weblogs/archives/000001.html"], cache_file
    )
    assert resolved == {
        "/weblogs/archives/000522.html": ArchivedPost("T", "2004-11-28", "s"),
        "/weblogs/archives/000001.html": None,
    }


class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, statuses):
        self.statuses = list(statuses)

    def get(self, url, **kwargs):
        status = self.statuses.pop(0)
        if status == "timeout":
            raise requests.Timeout("slow")
        return FakeResponse(status)


def test_get_with_retry_recovers_from_throttling(monkeypatch):
    monkeypatch.setattr("salasblog2.wayback.time.sleep", lambda seconds: None)
    response = get_with_retry(FakeSession([503, 429, 200]), "u")
    assert response.status_code == 200


def test_get_with_retry_gives_up_after_bounded_attempts(monkeypatch):
    monkeypatch.setattr("salasblog2.wayback.time.sleep", lambda seconds: None)
    with pytest.raises(RuntimeError, match="HTTP 503"):
        get_with_retry(FakeSession([503] * 5), "u")


def test_get_with_retry_does_not_retry_other_errors(monkeypatch):
    monkeypatch.setattr("salasblog2.wayback.time.sleep", lambda seconds: None)
    with pytest.raises(RuntimeError, match="HTTP 404"):
        get_with_retry(FakeSession([404, 200]), "u")


def test_get_with_retry_recovers_from_timeout(monkeypatch):
    monkeypatch.setattr("salasblog2.wayback.time.sleep", lambda seconds: None)
    assert get_with_retry(FakeSession(["timeout", 200]), "u").status_code == 200


def test_resolve_paths_looks_up_only_uncached(tmp_path, monkeypatch):
    monkeypatch.setattr("salasblog2.wayback.time.sleep", lambda seconds: None)
    cache_file = tmp_path / "wayback.json"
    cache_file.write_text('{"/weblogs/archives/000001.html": null}')
    indexed_dirs = []

    def fake_index(directory, session):
        indexed_dirs.append(directory)
        return {"/weblogs/archives/000522.html": "snap522"}

    monkeypatch.setattr("salasblog2.wayback.snapshot_index", fake_index)
    monkeypatch.setattr(
        "salasblog2.wayback.fetch_archived_post",
        lambda url, session: ArchivedPost("T", "2004-11-28", url),
    )
    resolved = resolve_paths(
        ["/weblogs/archives/000001.html", "/weblogs/archives/000522.html",
         "/weblogs/archives/000777.html"],
        cache_file,
    )
    assert indexed_dirs == ["/weblogs/archives/"]
    assert resolved["/weblogs/archives/000522.html"].snapshot_url == "snap522"
    assert resolved["/weblogs/archives/000777.html"] is None
    assert "000777" in cache_file.read_text()
