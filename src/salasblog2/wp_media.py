#!/usr/bin/env python3
# wp_media — self-host WordPress-era images and repair the post links to them
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-18
# Updated: 2026-10-18
# Open Source Under MIT license
"""
Old posts embed images that lived in salas.com's WordPress uploads, usually
through the `i0.wp.com` proxy. Those originals are gone. The WordPress media
export (a tar of `YYYY/MM/<file>` paths) holds copies of many of them.

`extract_media` copies the tar into `static/images/wp/`. `rewrite_wp_media`
then points each salas.com upload URL in a post body at its local copy,
but only when that copy exists. Frontmatter and every other byte of the post
are left alone; unmatched URLs are returned for reporting, never touched.
"""

import re
import tarfile
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

MEDIA_URL_PREFIX = "/static/images/wp"
MEDIA_KEY = re.compile(r"^\d{4}/\d{2}/[^/]+$")
URL_CHARS = r"[^\s\"'()<>\[\]?#]"
WP_MEDIA_URL = re.compile(
    rf"https?://(?:i\d\.wp\.com/)?(?:www\.)?salas\.com/wp-content/uploads/"
    rf"(\d{{4}}/\d{{2}}/{URL_CHARS}+)(?:\?[^\s\"'()<>\[\]#]*)?"
)
FRONTMATTER_END = "\n---\n"


@dataclass
class MediaRewrite:
    """Result of rewriting one post body."""

    text: str
    rewritten_count: int = 0
    unmatched_urls: list[str] = field(default_factory=list)


def media_key(encoded_path: str) -> str:
    """The tar-relative path for a URL path, with percent-encoding undone
    (WordPress URLs sometimes double-encode, e.g. `%2520` for a space)."""
    key = encoded_path
    while "%" in key and urllib.parse.unquote(key) != key:
        key = urllib.parse.unquote(key)
    return key


def split_frontmatter(text: str) -> tuple[str, str]:
    """Split a post into (frontmatter block including its fences, body)."""
    if not text.startswith("---\n"):
        return "", text
    end = text.find(FRONTMATTER_END, 4)
    if end == -1:
        raise ValueError("frontmatter opened with --- but never closed")
    cut = end + len(FRONTMATTER_END)
    return text[:cut], text[cut:]


def rewrite_wp_media(text: str, available_keys: set[str]) -> MediaRewrite:
    """Point salas.com WordPress upload URLs in the body at local copies.

    Only URLs whose `YYYY/MM/<file>` is in `available_keys` are rewritten,
    to `/static/images/wp/<YYYY/MM/file>` with the proxy's query string
    dropped. Others are listed in `unmatched_urls` and left as they are.
    """
    frontmatter, body = split_frontmatter(text)
    result = MediaRewrite(text=text)

    def replace(match: re.Match) -> str:
        key = media_key(match.group(1))
        if key not in available_keys:
            result.unmatched_urls.append(match.group(0))
            return match.group(0)
        result.rewritten_count += 1
        return f"{MEDIA_URL_PREFIX}/{urllib.parse.quote(key)}"

    new_body = WP_MEDIA_URL.sub(replace, body)
    result.text = frontmatter + new_body
    return result


def available_media(media_dir: Path) -> set[str]:
    """Every `YYYY/MM/<file>` present under `media_dir`."""
    return {
        path.relative_to(media_dir).as_posix()
        for path in media_dir.glob("*/*/*")
        if path.is_file()
    }


def extract_media(tar_path: Path, media_dir: Path) -> int:
    """Copy every `YYYY/MM/<file>` member of the tar into `media_dir`.

    Raises on any member that isn't a plain file at that shape, rather than
    writing outside `media_dir`.
    """
    count = 0
    with tarfile.open(tar_path) as archive:
        for member in archive.getmembers():
            if member.isdir():
                continue
            if not member.isfile() or not MEDIA_KEY.match(member.name):
                raise ValueError(f"unexpected tar member {member.name!r}")
            dest = media_dir / member.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            dest.write_bytes(source.read())
            count += 1
    return count


def url_status(url: str) -> str:
    """HTTP status of a HEAD request, or the error's name."""
    request = urllib.request.Request(url, method="HEAD")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return str(response.status)
    except urllib.error.HTTPError as error:
        return str(error.code)
    except urllib.error.URLError as error:
        return f"error: {error.reason}"


def rewrite_media_content(
    content_dirs: list[Path], media_dir: Path, is_dry_run: bool
) -> list[str]:
    """Rewrite matched media URLs in every post; print one line per changed
    file. Returns the unmatched URLs seen, for reporting."""
    keys = available_media(media_dir)
    if not keys:
        raise FileNotFoundError(f"no media found under {media_dir}")
    total = 0
    unmatched = []
    for content_dir in content_dirs:
        for md_file in sorted(content_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            result = rewrite_wp_media(text, keys)
            unmatched.extend(result.unmatched_urls)
            if result.rewritten_count == 0:
                continue
            total += result.rewritten_count
            print(f"{md_file}: {result.rewritten_count}")
            if not is_dry_run:
                md_file.write_text(result.text, encoding="utf-8")
    action = "would rewrite" if is_dry_run else "rewrote"
    print(f"{action} {total} media links; {len(unmatched)} unmatched")
    return unmatched
