#!/usr/bin/env python3
# test_legacy_links — Tests for legacy self-link classification, scanning, and rewrite
# Author: Pito Salas and Claude Code

import pytest

from salasblog2.legacy_links import (
    extract_legacy_links,
    normalize_legacy_url,
    rewrite_legacy_links,
    scan_content,
)


@pytest.mark.parametrize(
    "url, expected",
    [
        ("/weblogs/archives/000522.html", ("/weblogs/archives/000522.html", "mt")),
        ("/weblogs/archives/001350.php", ("/weblogs/archives/001350.php", "mt")),
        (
            "http://www.salas.com/weblogs/archives/000522.html#more",
            ("/weblogs/archives/000522.html", "mt"),
        ),
        ("/2008/02/18/about-amzn/", ("/2008/02/18/about-amzn", "wp")),
        ("/2008/02/18/about-amzn#comment-41711", ("/2008/02/18/about-amzn", "wp")),
        (
            "/imported-20111103233638/2011/07/01/slug/",
            ("/imported-20111103233638/2011/07/01/slug", "wp"),
        ),
        (
            "https://salascom.wordpress.com/2004/11/29/why-improv/",
            ("/2004/11/29/why-improv", "wp"),
        ),
        (
            "http://www.salas.com/blog/2012/5/6/field-of-dreams.html",
            ("/blog/2012/5/6/field-of-dreams.html", "squarespace"),
        ),
        ("/2004/01/24.html#a155", ("/2004/01/24.html", "radio-day")),
    ],
)
def test_normalize_recognizes_legacy_schemes(url, expected):
    assert normalize_legacy_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "/blog/2004-11-29-why-improv-didn8217t-succeed.html",
        "/static/images/foo.png",
        "/",
        "https://en.wikipedia.org/2008/02/18/slug/",
        "https://example.com/weblogs/archives/000522.html",
        "/weblogs/archives/screen.jpg",
        "/wp-admin/post.php?action=edit&post=1901",
    ],
)
def test_normalize_ignores_non_legacy_urls(url):
    assert normalize_legacy_url(url) is None


def test_extract_finds_markdown_and_html_links():
    text = (
        "See [my post](/weblogs/archives/000522.html) and "
        '<a href="/2008/02/18/about-amzn/">this</a> but not '
        "[wiki](https://en.wikipedia.org/wiki/Lotus_Improv)."
    )
    links = extract_legacy_links(text, "post.md")
    assert [(link.normalized_path, link.scheme) for link in links] == [
        ("/weblogs/archives/000522.html", "mt"),
        ("/2008/02/18/about-amzn", "wp"),
    ]
    assert all(link.source_file == "post.md" for link in links)


def test_scan_content_reads_all_dirs(tmp_path):
    blog = tmp_path / "blog"
    pages = tmp_path / "pages"
    blog.mkdir()
    pages.mkdir()
    (blog / "a.md").write_text("[x](/weblogs/archives/000001.html)")
    (pages / "b.md").write_text("[y](/2004/01/24.html)")
    (blog / "notes.txt").write_text("[z](/weblogs/archives/000002.html)")
    links = scan_content([blog, pages])
    assert [link.source_file for link in links] == ["a.md", "b.md"]


def test_rewrite_changes_only_mapped_targets():
    text = (
        "---\ntitle: Part Deux\n---\n\n"
        "My [earlier posting](/weblogs/archives/000522.html), "
        "[another](/weblogs/archives/000999.html), and "
        '<a href="http://www.salas.com/weblogs/archives/000522.html#x">html</a>.\n'
    )
    url_map = {"/weblogs/archives/000522.html": "/blog/2004-11-29-improv.html"}
    new_text, count = rewrite_legacy_links(text, url_map)
    assert count == 2
    assert new_text == (
        "---\ntitle: Part Deux\n---\n\n"
        "My [earlier posting](/blog/2004-11-29-improv.html), "
        "[another](/weblogs/archives/000999.html), and "
        '<a href="/blog/2004-11-29-improv.html">html</a>.\n'
    )


def test_rewrite_with_no_matches_is_identity():
    text = "Nothing [here](https://example.com/) to change.\n"
    assert rewrite_legacy_links(text, {"/2008/02/18/x": "/blog/y.html"}) == (text, 0)
