#!/usr/bin/env python3
# test_wp_media — Tests for self-hosting WordPress images and repairing post links
# Author: Pito Salas and Claude Code
# Version: 3
# Created: 2026-10-18
# Updated: 2026-10-19

import io
import tarfile
import urllib.error
from unittest.mock import patch

import pytest

from salasblog2.utils import split_frontmatter
from salasblog2.wp_media import (
    available_media,
    extract_media,
    media_key,
    rewrite_media_content,
    rewrite_wp_media,
    url_status,
)

KEYS = {"2014/08/img.jpg", "2011/03/screen shot.png"}


@pytest.mark.parametrize(
    "url, expected",
    [
        (
            "![](https://i0.wp.com/salas.com/wp-content/uploads/2014/08/img.jpg?w=584&ssl=1)",
            "![](/static/images/wp/2014/08/img.jpg)",
        ),
        (
            "![](https://i0.wp.com/salas.com/wp-content/uploads/2014/08/img.jpg?resize=462%2C278&ssl=1)",
            "![](/static/images/wp/2014/08/img.jpg)",
        ),
        (
            '<img src="http://www.salas.com/wp-content/uploads/2014/08/img.jpg">',
            '<img src="/static/images/wp/2014/08/img.jpg">',
        ),
        (
            "![](https://salas.com/wp-content/uploads/2011/03/screen%2520shot.png)",
            "![](/static/images/wp/2011/03/screen%20shot.png)",
        ),
    ],
)
def test_rewrites_matched_salas_upload_urls(url, expected):
    result = rewrite_wp_media(url, KEYS)
    assert result.text == expected
    assert result.rewritten_count == 1
    assert result.unmatched_urls == []


def test_rewrites_image_and_its_full_size_link():
    text = (
        "[![](https://i0.wp.com/salas.com/wp-content/uploads/2014/08/img.jpg?w=584)]"
        "(https://salas.com/wp-content/uploads/2014/08/img.jpg)"
    )
    result = rewrite_wp_media(text, KEYS)
    assert result.text == (
        "[![](/static/images/wp/2014/08/img.jpg)](/static/images/wp/2014/08/img.jpg)"
    )
    assert result.rewritten_count == 2


def test_unmatched_salas_url_is_reported_and_untouched():
    text = "![](https://i0.wp.com/salas.com/wp-content/uploads/2023/07/gone.png)"
    result = rewrite_wp_media(text, KEYS)
    assert result.text == text
    assert result.unmatched_urls == [text[4:-1]]


@pytest.mark.parametrize(
    "text",
    [
        "![](https://i0.wp.com/s3.media.squarespace.com/production/1/2/wp-content/uploads/2014/08/img.jpg)",
        "![](https://i0.wp.com/www.applegazette.com/wp-content/uploads/2014/08/img.jpg)",
        "![](https://example.com/2014/08/img.jpg)",
    ],
)
def test_other_hosts_are_ignored(text):
    result = rewrite_wp_media(text, KEYS)
    assert result.text == text
    assert result.rewritten_count == 0
    assert result.unmatched_urls == []


def test_frontmatter_is_never_touched_and_rest_of_body_is_identical():
    url = "https://i0.wp.com/salas.com/wp-content/uploads/2014/08/img.jpg?w=584"
    text = f"---\ntitle: T\nsubtitle: '![]({url})'\n---\nBefore ![]({url}) after.\n"
    result = rewrite_wp_media(text, KEYS)
    assert result.text == (
        f"---\ntitle: T\nsubtitle: '![]({url})'\n---\n"
        "Before ![](/static/images/wp/2014/08/img.jpg) after.\n"
    )


def test_rewrite_is_idempotent():
    text = "![](https://salas.com/wp-content/uploads/2014/08/img.jpg)"
    once = rewrite_wp_media(text, KEYS).text
    again = rewrite_wp_media(once, KEYS)
    assert again.text == once
    assert again.rewritten_count == 0


def test_media_key_undoes_double_encoding():
    assert media_key("2011/03/screen%2520shot.png") == "2011/03/screen shot.png"
    assert media_key("2014/08/img.jpg") == "2014/08/img.jpg"


def test_split_frontmatter_without_frontmatter():
    assert split_frontmatter("just body") == ("", "just body")


def test_split_frontmatter_unclosed_raises():
    with pytest.raises(ValueError):
        split_frontmatter("---\ntitle: T\nbody")


def make_tar(tmp_path, names):
    tar_path = tmp_path / "media.tar"
    with tarfile.open(tar_path, "w") as archive:
        for name in names:
            payload = name.encode()
            info = tarfile.TarInfo(name)
            info.size = len(payload)
            archive.addfile(info, io.BytesIO(payload))
    return tar_path


def test_extract_media_copies_every_file(tmp_path):
    tar_path = make_tar(tmp_path, ["2014/08/img.jpg", "2011/03/a.png"])
    media_dir = tmp_path / "wp"
    assert extract_media(tar_path, media_dir) == 2
    assert (media_dir / "2014/08/img.jpg").read_bytes() == b"2014/08/img.jpg"
    assert available_media(media_dir) == {"2014/08/img.jpg", "2011/03/a.png"}


@pytest.mark.parametrize("bad_name", ["../evil.jpg", "2014/08/../../x.jpg", "a.jpg"])
def test_extract_media_rejects_unexpected_members(tmp_path, bad_name):
    tar_path = make_tar(tmp_path, [bad_name])
    with pytest.raises(ValueError):
        extract_media(tar_path, tmp_path / "wp")


def make_site(tmp_path):
    media_dir = tmp_path / "wp" / "2014" / "08"
    media_dir.mkdir(parents=True)
    (media_dir / "img.jpg").write_bytes(b"x")
    blog = tmp_path / "content" / "blog"
    blog.mkdir(parents=True)
    post = blog / "post.md"
    post.write_text(
        "---\ntitle: T\n---\n"
        "![](https://salas.com/wp-content/uploads/2014/08/img.jpg)\n"
        "![](https://salas.com/wp-content/uploads/2023/07/gone.png)\n",
        encoding="utf-8",
    )
    return tmp_path / "wp", blog, post


def test_rewrite_media_content_dry_run_writes_nothing(tmp_path):
    media_dir, blog, post = make_site(tmp_path)
    before = post.read_text(encoding="utf-8")
    unmatched = rewrite_media_content([blog], media_dir, is_dry_run=True)
    assert post.read_text(encoding="utf-8") == before
    assert unmatched == ["https://salas.com/wp-content/uploads/2023/07/gone.png"]


def test_rewrite_media_content_apply_writes(tmp_path):
    media_dir, blog, post = make_site(tmp_path)
    rewrite_media_content([blog], media_dir, is_dry_run=False)
    assert "/static/images/wp/2014/08/img.jpg" in post.read_text(encoding="utf-8")


def test_rewrite_media_content_refuses_without_media(tmp_path):
    with pytest.raises(FileNotFoundError):
        rewrite_media_content([tmp_path], tmp_path / "missing", is_dry_run=True)


def test_url_status_reports_http_error():
    error = urllib.error.HTTPError("u", 404, "Not Found", None, None)
    with patch("salasblog2.wp_media.urllib.request.urlopen", side_effect=error):
        assert url_status("https://example.com/x") == "404"
