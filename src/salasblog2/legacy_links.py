#!/usr/bin/env python3
# legacy_links — Find, classify, and rewrite links that use pre-salasblog2 URL schemes
# Author: Pito Salas and Claude Code
"""
Older posts link to other posts on this blog using URL schemes from the blog
engines that preceded salasblog2. None of those URLs exist on the current site.

Recognized schemes (`SCHEME_PATTERNS`), matched against a link's path once an
optional salas.com / salascom.wordpress.com host and any `#fragment` are
stripped:

* `mt` - Movable Type, `/weblogs/archives/000522.html` (or `.php`)
* `wp` - WordPress, `/2008/02/18/slug/`, optionally under `/imported-NNN/`
* `squarespace` - `/blog/2012/5/6/slug.html`, or under `/imported-NNN/`
* `radio-day` - Radio UserLand day archive, `/2004/01/24.html`

A link's *normalized path* (host, fragment, and trailing slash removed) is
the key shared by the URL map, the rewrite, and the server redirects, so all
three agree on what counts as the same legacy URL.
"""

import re
from dataclasses import dataclass
from pathlib import Path

SELF_HOST = r"(?:https?://(?:www\.)?(?:salas\.com|salascom\.wordpress\.com))?"

SCHEME_PATTERNS = {
    "mt": re.compile(r"/weblogs/archives/\d+\.(?:html|php)"),
    "wp": re.compile(r"(?:/imported-\d+)?/\d{4}/\d{2}/\d{2}/[^/?#]+"),
    "squarespace": re.compile(
        r"(?:/blog|/imported-\d+)/\d{4}/\d{1,2}/\d{1,2}/[^/?#]+\.html"
    ),
    "radio-day": re.compile(r"/\d{4}/\d{2}/\d{2}\.html"),
}

# Markdown `](url)` targets and HTML href attributes.
LINK_TARGET = re.compile(r"""\]\(\s*<?([^)\s>]+)>?|href=["']([^"']+)["']""")
SELF_URL = re.compile(rf"^{SELF_HOST}(/[^?#]*)(?:[?#].*)?$")


@dataclass(frozen=True)
class LegacyLink:
    source_file: str
    url: str
    normalized_path: str
    scheme: str


def normalize_legacy_url(url: str) -> tuple[str, str] | None:
    """Return (normalized_path, scheme) for a legacy self-link, else None."""
    match = SELF_URL.match(url)
    if match is None:
        return None
    path = match.group(1).rstrip("/")
    for scheme, pattern in SCHEME_PATTERNS.items():
        if pattern.fullmatch(path):
            return path, scheme
    return None


def link_targets(text: str) -> list[str]:
    """All markdown and HTML link targets in text, in document order."""
    return [md or html for md, html in LINK_TARGET.findall(text)]


def extract_legacy_links(text: str, source_file: str) -> list[LegacyLink]:
    links = []
    for url in link_targets(text):
        classified = normalize_legacy_url(url)
        if classified is not None:
            path, scheme = classified
            links.append(LegacyLink(source_file, url, path, scheme))
    return links


def scan_content(content_dirs: list[Path]) -> list[LegacyLink]:
    """Every legacy self-link in the markdown files under content_dirs."""
    links = []
    for content_dir in content_dirs:
        for md_file in sorted(content_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            links.extend(extract_legacy_links(text, md_file.name))
    return links


def rewrite_legacy_links(text: str, url_map: dict[str, str]) -> tuple[str, int]:
    """
    Replace each legacy link target whose normalized path is in url_map with
    its new URL. Only link targets change - link text and the rest of the
    document are untouched. Returns (new_text, replacement_count).
    """
    count = 0

    def replace_target(match: re.Match) -> str:
        nonlocal count
        group = 1 if match.group(1) is not None else 2
        classified = normalize_legacy_url(match.group(group))
        if classified is None or classified[0] not in url_map:
            return match.group(0)
        count += 1
        start, end = match.span(group)
        offset = match.start(0)
        whole = match.group(0)
        new_url = url_map[classified[0]]
        return whole[: start - offset] + new_url + whole[end - offset :]

    return LINK_TARGET.sub(replace_target, text), count
