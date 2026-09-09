#!/usr/bin/env python3
# apply_tag_batch.py — Apply a reviewed tag-proposal batch to content files
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-09
# Updated: 2026-09-09
# Open Source Under MIT license
"""
CLI adapter for the tag-cleanup pipeline (F46). Reads a proposals JSON file
(as produced by auto_tag_posts.py, optionally hand-edited after review) and
writes the approved tags into each post's frontmatter, verifying body
content is untouched.

Reviewed-file schema: same shape auto_tag_posts.py writes, with two optional
overrides per entry - "approved_tags" (defaults to "proposed_tags") and
"skip": true (defaults to false).

Usage: uv run python3 scripts/apply_tag_batch.py output/tag_cleanup/proposals.json
"""

import argparse
import json
import logging
from pathlib import Path

from salasblog2.tag_cleanup import apply_tag_batch

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def resolve_blog_dir() -> Path:
    volume_content_dir = Path("/data/content")
    if volume_content_dir.exists():
        return volume_content_dir / "blog"
    return Path("content/blog")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Apply a reviewed tag-proposal batch"
    )
    parser.add_argument("proposals", type=Path, help="Path to a proposals JSON file")
    args = parser.parse_args()

    entries = json.loads(args.proposals.read_text(encoding="utf-8"))
    approved = [
        {
            "filename": entry["filename"],
            "tags": entry.get("approved_tags", entry["proposed_tags"]),
            "skip": entry.get("skip", False),
        }
        for entry in entries
    ]

    blog_dir = resolve_blog_dir()
    written = apply_tag_batch(blog_dir, approved)
    logger.info("Applied tags to %d posts", len(written))


if __name__ == "__main__":
    main()
