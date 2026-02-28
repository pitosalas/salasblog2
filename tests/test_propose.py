"""
Tests for the propose module — post relevance scoring.
"""
from datetime import date
from pathlib import Path
import pytest
import tempfile

from salasblog2.propose import score_post, get_proposed_posts, MIN_AGE_DAYS, RELEVANCE_KEYWORDS


class TestScorePost:
    def _today(self):
        return date.today()

    def test_recent_post_excluded(self):
        """Posts from the past two months return None."""
        today = self._today()
        recent = date(today.year, today.month, 1)  # start of this month
        score = score_post("AI and robots", "Some content about ai", recent, today)
        assert score is None

    def test_old_post_included(self):
        """Posts older than MIN_AGE_DAYS get a score (not None)."""
        today = date(2024, 6, 1)
        old_date = date(2022, 1, 1)
        score = score_post("Just a post", "Some content here", old_date, today)
        assert score is not None

    def test_keyword_boosts_score(self):
        """A post with matching keywords scores higher than one without."""
        today = date(2024, 6, 1)
        old_date = date(2022, 1, 1)
        keyword = RELEVANCE_KEYWORDS[0]
        score_with = score_post(keyword, keyword * 3, old_date, today)
        score_without = score_post("banana", "banana soup recipe", old_date, today)
        assert score_with > score_without

    def test_longer_post_scores_higher(self):
        """Longer posts should score higher than shorter ones (all else equal)."""
        today = date(2024, 6, 1)
        old_date = date(2022, 1, 1)
        short_score = score_post("Title", "Short.", old_date, today)
        long_score = score_post("Title", "Long content. " * 100, old_date, today)
        assert long_score > short_score

    def test_newer_old_post_scores_higher(self):
        """Among old posts, a more recent one should score higher (less age penalty)."""
        today = date(2024, 6, 1)
        newer_old = date(2022, 1, 1)   # ~2.4 years ago
        older_old = date(2010, 1, 1)   # ~14 years ago
        score_newer = score_post("Title", "content", newer_old, today)
        score_older = score_post("Title", "content", older_old, today)
        assert score_newer > score_older


class TestGetProposedPosts:
    def _write_post(self, directory, filename, title, date_str, content=""):
        (directory / filename).write_text(
            f"---\ntitle: {title!r}\ndate: '{date_str}'\ntype: blog\n---\n{content}\n"
        )

    def test_returns_top_n(self, tmp_path):
        """Returns at most top_n posts."""
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        for i in range(15):
            self._write_post(blog_dir, f"2020-01-{i+1:02d}-post-{i}.md",
                             f"Post {i}", f"2020-01-{i+1:02d}", "Some content here.")
        results = get_proposed_posts(blog_dir, top_n=10)
        assert len(results) <= 10

    def test_excludes_recent_posts(self, tmp_path):
        """Posts from within the past two months are excluded."""
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        today = date.today()
        recent_date = today.replace(day=1).isoformat()
        self._write_post(blog_dir, "2024-01-01-old.md", "Old post", "2020-01-01", "content")
        self._write_post(blog_dir, "recent.md", "Recent post", recent_date, "content")
        results = get_proposed_posts(blog_dir)
        filenames = [p.filename for p in results]
        assert "recent.md" not in filenames

    def test_empty_dir_returns_empty(self, tmp_path):
        """Empty directory returns an empty list."""
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        assert get_proposed_posts(blog_dir) == []

    def test_result_has_expected_fields(self, tmp_path):
        """Each result has filename, title, date, url, score."""
        blog_dir = tmp_path / "blog"
        blog_dir.mkdir()
        # Use a long content with multiple keywords so score > 0 even with age penalty
        content = "artificial intelligence machine learning startup " * 20
        self._write_post(blog_dir, "2020-01-01-test.md", "Test Post", "2020-01-01", content)
        results = get_proposed_posts(blog_dir)
        assert results
        p = results[0]
        assert p.filename == "2020-01-01-test.md"
        assert p.title == "Test Post"
        assert p.date == "2020-01-01"
        assert p.url == "/blog/2020-01-01-test.html"
        assert isinstance(p.score, float)
