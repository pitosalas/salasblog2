#!/usr/bin/env python3
# normalize_tag_aliases.py — Remap secondary tag spellings to their primary
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-11
# Updated: 2026-09-11
# Open Source Under MIT license
"""
CLI adapter for a full-corpus tag normalization pass (F46 follow-on) -
distinct from the rest of the tag-cleanup pipeline, which only touches
posts with empty or numeric-junk tags. This scans *every* post that has
any tags at all, since it's correcting tags a post already has, not
filling in missing ones.

For each post, every existing tag is looked up in 02-doc/tag-hints.md's
alias map (a curated tag's "(aka: ...)" secondaries - see
`utils.load_curated_tag_aliases`): a tag that's already a curated primary
is kept, a known secondary is rewritten to its primary, and a tag matching
neither is dropped. This pass is deliberately NOT additive-only - unlike
the rest of the pipeline, dropping an unrecognized tag is the point. A
post that loses every tag this way naturally gets `tag_review: no_fit`
(via `apply_tag_proposal`) and re-enters the normal needs-cleanup pipeline
for a real look, rather than keeping stale tags forever.

Usage:
  uv run python3 scripts/normalize_tag_aliases.py [--dry-run] [--tag-hints PATH]
"""

import argparse
import logging
from pathlib import Path

import frontmatter

from salasblog2.tag_cleanup import apply_tag_proposal, normalize_post_tags
from salasblog2.utils import load_curated_tag_aliases

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DEFAULT_TAG_HINTS_PATH = Path("02-doc/tag-hints.md")


def resolve_blog_dir() -> Path:
    volume_content_dir = Path("/data/content")
    if volume_content_dir.exists():
        return volume_content_dir / "blog"
    return Path("content/blog")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Normalize existing post tags to their curated primaries"
    )
    parser.add_argument("--tag-hints", type=Path, default=DEFAULT_TAG_HINTS_PATH)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would change without writing any file",
    )
    args = parser.parse_args()

    alias_map = load_curated_tag_aliases(args.tag_hints)
    blog_dir = resolve_blog_dir()

    changed = 0
    removed_total = 0
    for path in sorted(blog_dir.glob("*.md")):
        post = frontmatter.load(path)
        current_tags = [str(t) for t in (post.metadata.get("tags") or [])]
        if not current_tags:
            continue

        result = normalize_post_tags(path.name, current_tags, alias_map)
        if not result.changed:
            continue

        changed += 1
        removed_total += len(result.removed_tags)
        dropped_note = (
            f" (dropped: {result.removed_tags})" if result.removed_tags else ""
        )
        logger.info(
            "%s: %s -> %s%s",
            result.filename,
            result.original_tags,
            result.normalized_tags,
            dropped_note,
        )
        if not args.dry_run:
            apply_tag_proposal(blog_dir, path.name, result.normalized_tags)

    mode_note = " (dry run, nothing written)" if args.dry_run else ""
    logger.info(
        "%d posts changed, %d tag(s) dropped total%s", changed, removed_total, mode_note
    )


if __name__ == "__main__":
    main()
