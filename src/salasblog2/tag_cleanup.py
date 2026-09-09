#!/usr/bin/env python3
# tag_cleanup — Selection and Claude-based tag proposals for the tag-cleanup pipeline
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-09
# Updated: 2026-09-09
# Open Source Under MIT license
"""
Pure logic for the automated tag-cleanup pipeline (F46): selecting posts that
still carry a numeric WordPress-import tag or no tags at all, extracting each
post's title/excerpt for a human (or Claude, acting directly in an assisted
session - no separate paid API call) to propose tags from, and sanitizing
those proposals before they're written.

Tags on this blog are free-form (F42/F45) - BLOG_TAGS is a curated set of
*suggestions*, not an enforced vocabulary, so a proposal is free to include
a specific entity/topic tag (e.g. "blogbridge", "mars", "tivo") alongside or
instead of a general category. Sanitization only drops what's actually junk:
numeric leftovers, empty strings, and duplicates.

This pipeline is additive-only: a post's existing tags are never removed,
only added to (`build_proposal` unions current tags with newly proposed
ones before sanitizing) - numeric junk is the one exception, dropped like
any other junk regardless of whether it was already on the post.

Frontmatter writes (`apply_tag_proposal`) verify the post's body is
byte-identical before and after, so a bug in this pipeline can't corrupt
post content even if it writes wrong tags.
"""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path

import frontmatter

from salasblog2.utils import create_excerpt

logger = logging.getLogger(__name__)

EXCERPT_LENGTH_FOR_TAGGING = 800


def has_numeric_tag(tags: list[str]) -> bool:
    """True if any tag is a leftover raw WordPress category ID."""
    return any(str(tag).isdigit() for tag in tags)


def needs_tag_cleanup(tags: list[str]) -> bool:
    """A post needs work if it has no tags, or carries a numeric leftover tag."""
    return not tags or has_numeric_tag(tags)


def select_posts_needing_cleanup(blog_dir: Path, limit: int) -> list[Path]:
    """Return up to `limit` post paths (sorted by filename, for stable
    batching across runs) whose current tags need cleanup."""
    selected = []
    for path in sorted(blog_dir.glob("*.md")):
        post = frontmatter.load(path)
        if needs_tag_cleanup(post.metadata.get("tags") or []):
            selected.append(path)
        if len(selected) >= limit:
            break
    return selected


@dataclass
class TagProposal:
    filename: str
    title: str
    current_tags: list[str]
    proposed_tags: list[str] = field(default_factory=list)

    @property
    def no_fit(self) -> bool:
        return not self.proposed_tags


@dataclass
class PostSummary:
    """Everything needed to propose tags for one post, without its full body."""

    filename: str
    title: str
    current_tags: list[str]
    excerpt: str


def summarize_post(path: Path) -> PostSummary:
    """Read a post and extract its title/current tags/excerpt.

    Read-only - never writes to `path`.
    """
    post = frontmatter.load(path)
    title = post.metadata.get("title", "")
    current_tags = [str(tag) for tag in (post.metadata.get("tags") or [])]
    excerpt = create_excerpt(post.content, max_length=EXCERPT_LENGTH_FOR_TAGGING)
    return PostSummary(
        filename=path.name, title=title, current_tags=current_tags, excerpt=excerpt
    )


def summaries_to_json(summaries: list[PostSummary]) -> str:
    return json.dumps([asdict(summary) for summary in summaries], indent=2)


def validate_proposed_tags(tags: list[str]) -> list[str]:
    """Sanitize a proposed tag list: drop numeric junk, empty strings, and
    duplicates (order-preserving). Tags are free-form on this blog (F42/F45)
    - anything else proposed is kept as-is, including specific entity/topic
    tags outside the curated BLOG_TAGS suggestions.
    """
    seen = set()
    cleaned = []
    for tag in tags:
        tag = str(tag).strip()
        if not tag or tag.isdigit() or tag in seen:
            continue
        seen.add(tag)
        cleaned.append(tag)
    return cleaned


def build_proposal(summary: PostSummary, tags: list[str]) -> TagProposal:
    """Combine a post summary with newly proposed tags into a TagProposal.

    Additive-only: the post's existing tags are unioned with the new ones
    before sanitizing, so nothing already on the post is ever dropped -
    except numeric junk, which is sanitized away regardless of source.
    """
    merged = validate_proposed_tags(summary.current_tags + tags)
    return TagProposal(
        filename=summary.filename,
        title=summary.title,
        current_tags=summary.current_tags,
        proposed_tags=merged,
    )


def proposals_to_json(proposals: list[TagProposal]) -> str:
    return json.dumps(
        [
            {
                "filename": p.filename,
                "title": p.title,
                "current_tags": p.current_tags,
                "proposed_tags": p.proposed_tags,
                "no_fit": p.no_fit,
            }
            for p in proposals
        ],
        indent=2,
    )


def apply_tag_proposal(blog_dir: Path, filename: str, tags: list[str]) -> None:
    """Write `tags` into one post's frontmatter, verifying its body is
    byte-identical before and after.

    Raises with context rather than silently skipping or coercing a post
    whose body changed unexpectedly or whose tags didn't persist.
    """
    path = blog_dir / filename
    with open(path, "r", encoding="utf-8") as f:
        post = frontmatter.load(f)
    original_body = post.content

    post.metadata["tags"] = tags
    path.write_text(frontmatter.dumps(post), encoding="utf-8")

    with open(path, "r", encoding="utf-8") as f:
        rewritten = frontmatter.load(f)
    if rewritten.content != original_body:
        raise ValueError(f"{filename}: body content changed after tag write")
    if rewritten.metadata.get("tags") != tags:
        raise ValueError(f"{filename}: tags did not persist correctly")


def apply_tag_batch(blog_dir: Path, approved: list[dict]) -> list[str]:
    """Apply a reviewed batch of `{"filename": ..., "tags": [...]}` entries.

    Entries with `"skip": true` are left untouched. Returns the list of
    filenames actually written.
    """
    written = []
    for entry in approved:
        if entry.get("skip"):
            continue
        apply_tag_proposal(blog_dir, entry["filename"], entry["tags"])
        written.append(entry["filename"])
    return written
