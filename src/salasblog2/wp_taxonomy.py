#!/usr/bin/env python3
# wp_taxonomy — WordPress categories/tags as a curated-tag signal for posts
# Author: Pito Salas and Claude Code
# Version: 2
# Created: 2026-10-18
# Updated: 2026-10-20
# Open Source Under MIT license
"""
The WordPress export (WXR) records the categories and tags each old post
had. This module maps those terms onto the curated vocabulary in
`02-doc/tag-hints.md` and turns them into ordinary F46 tag proposals.

A term resolves in two steps. First, `02-doc/wp-term-merges.json` can
redirect it to another name (a near-synonym or misspelling) or to `null` to
ignore it. Second, the result goes through tag-hints.md's alias map, so a
declared synonym lands on its curated primary.

`build_wp_proposals` proposes, for each local post
matched to a WordPress post, its existing tags plus the curated tags its
terms resolve to - additive only, via F46's `build_proposal`.
"""

import html
import json
import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import frontmatter

from salasblog2.tag_cleanup import PostSummary, TagProposal, build_proposal
from salasblog2.tag_vocabulary import canonicalize_tags
from salasblog2.utils import load_curated_tag_aliases

WXR_NAMESPACES = {"wp": "http://wordpress.org/export/1.2/"}
MERGES_FILE = Path(__file__).parents[2] / "02-doc" / "wp-term-merges.json"
STRUCTURAL_TERM = re.compile(r"^(uncategorized|post-format-.*|\d+)$")
ENTITY_LEFTOVER = re.compile(r"&#?\w+;|8[0-9]{3}")


@dataclass
class WpPost:
    slug: str
    title: str
    terms: list[str]


def parse_wxr(wxr_path: Path) -> list[WpPost]:
    """Every published post in a WordPress export, with its category and tag
    nicenames (deduplicated, in file order)."""
    channel = ET.parse(wxr_path).getroot().find("channel")
    posts = []
    for item in channel.findall("item"):
        post_type = item.findtext("wp:post_type", namespaces=WXR_NAMESPACES)
        status = item.findtext("wp:status", namespaces=WXR_NAMESPACES)
        if post_type != "post" or status != "publish":
            continue
        terms = [term.get("nicename") for term in item.findall("category")]
        posts.append(
            WpPost(
                slug=item.findtext("wp:post_name", namespaces=WXR_NAMESPACES) or "",
                title=item.findtext("title") or "",
                terms=list(dict.fromkeys(term for term in terms if term)),
            )
        )
    return posts


def match_key(text: str) -> str:
    """Comparable form of a slug or title: entities and the import's
    `8220`-style numeric-entity leftovers removed, then only [a-z0-9]."""
    text = ENTITY_LEFTOVER.sub("", html.unescape(text).lower())
    return re.sub(r"[^a-z0-9]", "", text)


def index_local_posts(blog_dir: Path) -> tuple[dict[str, str], dict[str, str]]:
    """Map match keys of each post's filename slug, and of its title, to the
    filename. A filename is `YYYY-MM-DD-<slug>.md`."""
    by_slug, by_title = {}, {}
    for path in sorted(blog_dir.glob("*.md")):
        by_slug[match_key(path.stem[11:])] = path.name
        title = str(frontmatter.load(path).metadata.get("title", ""))
        if title:
            by_title[match_key(title)] = path.name
    return by_slug, by_title


def match_posts(
    wp_posts: list[WpPost], by_slug: dict[str, str], by_title: dict[str, str]
) -> tuple[dict[str, WpPost], list[WpPost]]:
    """Match WordPress posts to local filenames by slug, then by title.
    Returns ({filename: wp_post}, unmatched wp_posts).

    The export holds some posts twice (republished under a later date) while
    the local import kept one file, so copies matching the same file have
    their terms unioned.
    """
    matched, unmatched = {}, []
    for wp_post in wp_posts:
        filename = by_slug.get(match_key(wp_post.slug)) or by_title.get(
            match_key(wp_post.title)
        )
        if not filename:
            unmatched.append(wp_post)
        elif filename in matched:
            first = matched[filename]
            first.terms = list(dict.fromkeys(first.terms + wp_post.terms))
        else:
            matched[filename] = WpPost(wp_post.slug, wp_post.title, list(wp_post.terms))
    return matched, unmatched


def load_merges(merges_path: Path) -> dict[str, str | None]:
    merges = json.loads(merges_path.read_text(encoding="utf-8"))
    merges.pop("_comment", None)
    return merges


def resolve_terms(
    terms: list[str], merges: dict[str, str | None], alias_map: dict[str, str]
) -> list[str]:
    """Resolve a post's WordPress terms to curated primaries, deduplicated.

    Structural terms (`uncategorized`, `post-format-*`, numeric IDs) and
    terms merged to `null` are dropped, and so is anything the closed
    curated list doesn't recognize.
    """
    merged = [
        merges.get(term, term) for term in terms if not STRUCTURAL_TERM.match(term)
    ]
    targets = [target for target in merged if target is not None]
    return canonicalize_tags(targets, alias_map).kept


def build_wp_proposals(
    blog_dir: Path,
    matched: dict[str, WpPost],
    merges: dict[str, str | None],
    tag_hints_path: Path,
) -> list[TagProposal]:
    """One proposal per matched post that would gain a curated tag."""
    alias_map = load_curated_tag_aliases(tag_hints_path)
    curated = set(alias_map.values())
    proposals = []
    for filename, wp_post in sorted(matched.items()):
        post = frontmatter.load(blog_dir / filename)
        current_tags = [str(tag) for tag in (post.metadata.get("tags") or [])]
        summary = PostSummary(
            filename=filename,
            title=str(post.metadata.get("title", "")),
            current_tags=current_tags,
            excerpt="",
        )
        tags = resolve_terms(wp_post.terms, merges, alias_map)
        proposal = build_proposal(summary, tags, curated)
        if set(proposal.proposed_tags) - set(current_tags):
            proposals.append(proposal)
    return proposals
