#!/usr/bin/env python3
# test_propose.py — Tests for propose module: blog scoring and popular drop selection
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from datetime import date
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from salasblog2.propose import (
    DropFilter,
    MIN_AGE_DAYS,
    RELEVANCE_KEYWORDS,
    _extract_note_from_body,
    get_proposed_drops,
    get_proposed_posts,
    score_post,
)


class TestExtractNoteFromBody:
    def test_extracts_note(self):
        body = "**URL:** https://example.com\n\n**Notes:**\nThis is my comment about the link."
        assert _extract_note_from_body(body) == "This is my comment about the link."

    def test_returns_empty_when_no_notes(self):
        body = "**URL:** https://example.com\n\n**Excerpt:** Some excerpt."
        assert _extract_note_from_body(body) == ""

    def test_multiline_note(self):
        body = "**Notes:**\nLine one\nLine two"
        assert "Line one" in _extract_note_from_body(body)


class TestScorePost:
    def test_recent_post_excluded(self):
        today = date.today()
        recent = date(today.year, today.month, 1)
        assert score_post("AI and robots", "Some content about ai", recent, today) is None

    def test_old_post_included(self):
        today = date(2024, 6, 1)
        assert score_post("Just a post", "Some content here", date(2022, 1, 1), today) is not None

    def test_keyword_boosts_score(self):
        today = date(2024, 6, 1)
        old = date(2022, 1, 1)
        kw = RELEVANCE_KEYWORDS[0]
        score_with = score_post(" ".join([kw] * 3), " ".join([kw] * 5), old, today)
        score_without = score_post("banana", "banana soup recipe", old, today)
        assert score_with > score_without

    def test_longer_post_scores_higher(self):
        today = date(2024, 6, 1)
        old = date(2022, 1, 1)
        assert score_post("Title", "Short.", old, today) < score_post("Title", "Long. " * 100, old, today)

    def test_newer_old_post_scores_higher(self):
        today = date(2024, 6, 1)
        score_newer = score_post("Title", "content", date(2022, 1, 1), today)
        score_older = score_post("Title", "content", date(2010, 1, 1), today)
        assert score_newer > score_older


class TestGetProposedPosts:
    def _write_post(self, directory, filename, title, date_str, content=""):
        (directory / filename).write_text(
            f"---\ntitle: {title!r}\ndate: '{date_str}'\ntype: blog\n---\n{content}\n"
        )

    def test_returns_top_n(self, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        for i in range(15):
            self._write_post(blog_dir, f"2020-01-{i+1:02d}-post-{i}.md",
                             f"Post {i}", f"2020-01-{i+1:02d}", "Some content here.")
        assert len(get_proposed_posts(blog_dir, 10)) <= 10

    def test_excludes_recent_posts(self, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        recent_date = date.today().replace(day=1).isoformat()
        self._write_post(blog_dir, "2020-01-01-old.md", "Old post", "2020-01-01", "content")
        self._write_post(blog_dir, "recent.md", "Recent post", recent_date, "content")
        filenames = [p.filename for p in get_proposed_posts(blog_dir, 10)]
        assert "recent.md" not in filenames

    def test_empty_dir_returns_empty(self, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        assert get_proposed_posts(blog_dir, 10) == []

    def test_result_has_expected_fields(self, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        content = "artificial intelligence machine learning startup " * 20
        self._write_post(blog_dir, "2020-01-01-test.md", "Test Post", "2020-01-01", content)
        results = get_proposed_posts(blog_dir, 10)
        assert results
        p = results[0]
        assert p.filename == "2020-01-01-test.md"
        assert p.title == "Test Post"
        assert p.date == "2020-01-01"
        assert p.url == "/blog/2020-01-01-test.html"
        assert isinstance(p.score, float)

    def test_excludes_draft_posts(self, tmp_path):
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        (blog_dir / "draft.md").write_text(
            "---\ntitle: 'Draft'\ndate: '2020-01-01'\ndraft: true\n---\ncontent\n"
        )
        self._write_post(blog_dir, "2020-01-01-real.md", "Real", "2020-01-01", "content")
        filenames = [p.filename for p in get_proposed_posts(blog_dir, 10)]
        assert "draft.md" not in filenames


class TestGetProposedDrops:
    def _write_drop(self, directory, filename, date_str, url, note="", visits=0):
        (directory / filename).write_text(
            f"---\ntitle: 'Test Drop'\ndate: '{date_str}'\ntype: drop\n"
            f"url: '{url}'\nnote: '{note}'\ndomain: example.com\nexcerpt: ''\ntags: []\n---\n"
        )

    def _make_counter(self, visit_map: dict):
        counter = MagicMock()
        counter.get.side_effect = lambda path: visit_map.get(path, 0)
        return counter

    def test_filters_by_min_visits(self, tmp_path):
        drops_dir = tmp_path / "raindrops"
        drops_dir.mkdir()
        self._write_drop(drops_dir, "drop-low.md", "2020-01-01", "https://a.com")
        self._write_drop(drops_dir, "drop-high.md", "2020-01-01", "https://b.com")
        counter = self._make_counter({
            "/raindrops/drop-low.html": 2,
            "/raindrops/drop-high.html": 10,
        })
        filt = DropFilter(min_age_months=3, min_visits=5, top_n=10)
        results = get_proposed_drops(drops_dir, counter, filt)
        filenames = [r["filename"] for r in results]
        assert "drop-high.md" in filenames
        assert "drop-low.md" not in filenames

    def test_filters_by_age(self, tmp_path):
        drops_dir = tmp_path / "raindrops"
        drops_dir.mkdir()
        self._write_drop(drops_dir, "old-drop.md", "2020-01-01", "https://old.com")
        self._write_drop(drops_dir, "new-drop.md", date.today().isoformat(), "https://new.com")
        counter = self._make_counter({
            "/raindrops/old-drop.html": 20,
            "/raindrops/new-drop.html": 20,
        })
        filt = DropFilter(min_age_months=3, min_visits=5, top_n=10)
        results = get_proposed_drops(drops_dir, counter, filt)
        filenames = [r["filename"] for r in results]
        assert "old-drop.md" in filenames
        assert "new-drop.md" not in filenames

    def test_sorted_by_visit_count(self, tmp_path):
        drops_dir = tmp_path / "raindrops"
        drops_dir.mkdir()
        self._write_drop(drops_dir, "drop-a.md", "2020-01-01", "https://a.com")
        self._write_drop(drops_dir, "drop-b.md", "2020-01-01", "https://b.com")
        counter = self._make_counter({
            "/raindrops/drop-a.html": 5,
            "/raindrops/drop-b.html": 50,
        })
        filt = DropFilter(min_age_months=3, min_visits=5, top_n=10)
        results = get_proposed_drops(drops_dir, counter, filt)
        assert results[0]["filename"] == "drop-b.md"

    def test_result_includes_required_fields(self, tmp_path):
        drops_dir = tmp_path / "raindrops"
        drops_dir.mkdir()
        self._write_drop(drops_dir, "drop.md", "2020-01-01", "https://x.com", note="my note")
        counter = self._make_counter({"/raindrops/drop.html": 10})
        filt = DropFilter(min_age_months=3, min_visits=5, top_n=10)
        results = get_proposed_drops(drops_dir, counter, filt)
        assert results
        r = results[0]
        for key in ("filename", "title", "url", "note", "domain", "date", "visit_count"):
            assert key in r
