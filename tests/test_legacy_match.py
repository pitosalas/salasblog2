#!/usr/bin/env python3
# test_legacy_match — Tests for matching legacy URLs to current posts
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-17
# Updated: 2026-10-17

from datetime import date

from salasblog2.legacy_match import (
    CurrentPost,
    build_url_map,
    comparable,
    load_current_posts,
)
from salasblog2.wayback import ArchivedPost

POSTS = [
    CurrentPost(
        "2004-11-29-why-improv-didn8217t-succeed",
        "Why Improv didn’t succeed",
        date(2004, 11, 29),
    ),
    CurrentPost(
        "2004-12-02-why-improv-didn8217t-succeed-part-deux",
        "Why Improv didn’t succeed, Part Deux",
        date(2004, 12, 2),
    ),
    CurrentPost(
        "2008-02-18-about-amzn-and-cloud-computing",
        "About AMZN and Cloud Computing",
        date(2008, 2, 18),
    ),
    CurrentPost("2004-01-24-radio-post", "Radio post", date(2004, 1, 24)),
    CurrentPost("2004-01-29-first", "First", date(2004, 1, 29)),
    CurrentPost("2004-01-29-second", "Second", date(2004, 1, 29)),
]


def map_one(scheme, path, archived=None):
    return build_url_map({scheme: [path]}, {path: archived}, POSTS)[path]


def test_comparable_flattens_entities_and_punctuation():
    assert comparable("Why Improv didn’t succeed") == comparable(
        "why-improv-didn8217t-succeed"
    )


def test_mt_exact_match_within_one_day():
    archived = ArchivedPost("Why Improv didn't succeed", "2004-11-28", "snap")
    entry = map_one("mt", "/weblogs/archives/000522.html", archived)
    assert entry["new"] == "/blog/2004-11-29-why-improv-didn8217t-succeed.html"
    assert entry["confidence"] == "exact"
    assert entry["evidence"]["snapshot"] == "snap"


def test_mt_near_title_is_fuzzy():
    archived = ArchivedPost("Why Improv did not succeed", "2004-11-28", "snap")
    entry = map_one("mt", "/weblogs/archives/000522.html", archived)
    assert entry["confidence"] == "fuzzy"
    assert entry["new"] == "/blog/2004-11-29-why-improv-didn8217t-succeed.html"


def test_mt_no_close_title_is_unmatched():
    archived = ArchivedPost("Something else entirely", "2004-11-28", "snap")
    entry = map_one("mt", "/weblogs/archives/000522.html", archived)
    assert entry["confidence"] == "unmatched"
    assert entry["new"] is None


def test_mt_not_archived_is_unmatched():
    entry = map_one("mt", "/weblogs/archives/000001.html", None)
    assert entry == {
        "scheme": "mt",
        "new": None,
        "confidence": "unmatched",
        "evidence": "not archived",
    }


def test_wp_slug_exact_match():
    entry = map_one("wp", "/2008/02/18/about-amzn-and-cloud-computing")
    assert entry["new"] == "/blog/2008-02-18-about-amzn-and-cloud-computing.html"
    assert entry["confidence"] == "exact"


def test_wp_truncated_slug_is_fuzzy():
    entry = map_one("wp", "/2008/02/19/about-amzn-and-cloud-computin")
    assert entry["confidence"] == "fuzzy"
    assert entry["new"] == "/blog/2008-02-18-about-amzn-and-cloud-computing.html"


def test_squarespace_unpadded_date():
    entry = map_one(
        "squarespace", "/blog/2008/2/18/about-amzn-and-cloud-computing.html"
    )
    assert entry["confidence"] == "exact"


def test_radio_day_single_post_is_fuzzy():
    entry = map_one("radio-day", "/2004/01/24.html")
    assert entry["new"] == "/blog/2004-01-24-radio-post.html"
    assert entry["confidence"] == "fuzzy"


def test_radio_day_multiple_posts_is_unmatched():
    entry = map_one("radio-day", "/2004/01/29.html")
    assert entry["new"] is None
    assert len(entry["candidates"]) == 2


def test_load_current_posts_skips_drafts(tmp_path):
    (tmp_path / "2004-11-29-a.md").write_text(
        "---\ntitle: A\ndate: '2004-11-29'\n---\nx"
    )
    (tmp_path / "draft-24-01-01-b.md").write_text("---\ntitle: B\n---\nx")
    (tmp_path / "2005-01-01-c.md").write_text("---\ntitle: C\n---\nx")
    posts = load_current_posts(tmp_path)
    assert [(p.stem, p.post_date) for p in posts] == [
        ("2004-11-29-a", date(2004, 11, 29)),
        ("2005-01-01-c", date(2005, 1, 1)),
    ]
