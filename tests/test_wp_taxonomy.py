#!/usr/bin/env python3
# test_wp_taxonomy — Tests for mapping WordPress terms onto curated tags
# Author: Pito Salas and Claude Code
# Version: 2
# Created: 2026-10-18
# Updated: 2026-10-20

import pytest

from salasblog2.wp_taxonomy import (
    WpPost,
    build_wp_proposals,
    index_local_posts,
    match_key,
    match_posts,
    parse_wxr,
    resolve_terms,
)

WXR = """<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:wp="http://wordpress.org/export/1.2/">
<channel>
{items}
</channel>
</rss>
"""


def wxr_item(slug, post_type="post", status="publish", terms=()):
    categories = "".join(
        f'<category domain="post_tag" nicename="{t}"><![CDATA[{t}]]></category>'
        for t in terms
    )
    return (
        f"<item><title>{slug} title</title><wp:post_name>{slug}</wp:post_name>"
        f"<wp:post_type>{post_type}</wp:post_type><wp:status>{status}</wp:status>"
        f"{categories}</item>"
    )


def test_parse_wxr_keeps_only_published_posts(tmp_path):
    items = "".join(
        [
            wxr_item("real", terms=["robots", "robots", "life"]),
            wxr_item("draft", status="draft"),
            wxr_item("about", post_type="page"),
            wxr_item("pic", post_type="attachment", status="inherit"),
        ]
    )
    path = tmp_path / "export.xml"
    path.write_text(WXR.format(items=items), encoding="utf-8")
    posts = parse_wxr(path)
    assert posts == [WpPost(slug="real", title="real title", terms=["robots", "life"])]


@pytest.mark.parametrize(
    "text, expected",
    [
        ("crn-8220newsgator-20", "crnnewsgator20"),
        ("Google API -&gt; Open Standard", "googleapiopenstandard"),
        ("Curaçao harbor", "curaaoharbor"),
    ],
)
def test_match_key(text, expected):
    assert match_key(text) == expected


def write_post(blog_dir, filename, title, tags):
    tag_lines = "".join(f"- {t}\n" for t in tags)
    tags_block = f"tags:\n{tag_lines}" if tags else "tags: []\n"
    (blog_dir / filename).write_text(
        f"---\ntitle: '{title}'\n{tags_block}---\nBody text.\n", encoding="utf-8"
    )


def test_match_posts_by_slug_then_title(tmp_path):
    write_post(tmp_path, "2005-01-01-gmail-8211-part-3.md", "Gmail part 3", [])
    write_post(tmp_path, "2007-11-29-short-slug.md", "Curaçao harbor", [])
    wp_posts = [
        WpPost(slug="gmail-part-3", title="whatever", terms=[]),
        WpPost(slug="curacao-harbor", title="Curaçao harbor", terms=[]),
        WpPost(slug="missing", title="Not here", terms=[]),
    ]
    matched, unmatched = match_posts(wp_posts, *index_local_posts(tmp_path))
    assert set(matched) == {
        "2005-01-01-gmail-8211-part-3.md",
        "2007-11-29-short-slug.md",
    }
    assert [p.slug for p in unmatched] == ["missing"]


ALIASES = {"robotics": "robotics", "robot": "robotics", "personal": "personal"}


def test_resolve_terms_merges_aliases_and_drops_structural_and_unknown():
    merges = {"robots": "robotics", "links": None}
    terms = [
        "robots",
        "robot",
        "links",
        "uncategorized",
        "post-format-link",
        "119",
        "x",
    ]
    assert resolve_terms(terms, merges, ALIASES) == ["robotics"]


HINTS = (
    "# Rules\n\n* stuff\n\n# Curated Tags\n\n"
    "79       robotics (robot)\n32       personal\n"
)


def test_build_wp_proposals_is_additive_and_curated_only(tmp_path):
    hints = tmp_path / "tag-hints.md"
    hints.write_text(HINTS, encoding="utf-8")
    blog = tmp_path / "blog"
    blog.mkdir()
    write_post(blog, "2004-01-01-a.md", "A", ["oddtag", "123"])
    write_post(blog, "2004-01-02-b.md", "B", ["robotics"])
    matched = {
        "2004-01-01-a.md": WpPost(slug="a", title="A", terms=["robots", "rare"]),
        "2004-01-02-b.md": WpPost(slug="b", title="B", terms=["robot"]),
    }
    proposals = build_wp_proposals(blog, matched, {"robots": "robotics"}, hints)
    assert len(proposals) == 1
    assert proposals[0].filename == "2004-01-01-a.md"
    assert proposals[0].proposed_tags == ["oddtag", "robotics"]


def test_match_posts_unions_terms_of_duplicate_wp_posts(tmp_path):
    write_post(tmp_path, "2008-05-21-creepy.md", "Creepy", [])
    wp_posts = [
        WpPost(slug="20051129creepy-html", title="Creepy", terms=["life"]),
        WpPost(slug="2008521creepy-html", title="Creepy", terms=["life", "robots"]),
    ]
    matched, _ = match_posts(wp_posts, *index_local_posts(tmp_path))
    assert matched["2008-05-21-creepy.md"].terms == ["life", "robots"]
    assert wp_posts[0].terms == ["life"]
