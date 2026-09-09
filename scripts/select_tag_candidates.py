#!/usr/bin/env python3
# select_tag_candidates.py — Select posts needing tag cleanup, extract summaries
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-09
# Updated: 2026-09-09
# Open Source Under MIT license
"""
CLI adapter for the tag-cleanup pipeline (F46). Selects the next batch of
posts needing tag cleanup and writes a title/excerpt/current-tags summary
for each to a JSON file - for Claude, acting directly in an assisted session
(or a human), to read and propose tags from. See build_proposals.py for the
next step. Never calls an external API and never writes to content files.

Selection is self-tracking: a post "needs cleanup" if it has empty tags or
any numeric leftover, computed fresh each run - once a batch is applied and
committed, those posts stop matching and the next run naturally picks up
where the last one left off. No offset or progress file to manage.

Usage: uv run python3 scripts/select_tag_candidates.py [--limit N] [--output PATH]
"""

import argparse
import logging
from pathlib import Path

import yaml

from salasblog2.tag_cleanup import (
    select_posts_needing_cleanup,
    summaries_to_json,
    summarize_post,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DEFAULT_BATCH_SIZE = 50


def load_batch_size(config_path: Path = Path("config.yaml")) -> int:
    if not config_path.exists():
        return DEFAULT_BATCH_SIZE
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("tag_cleanup", {}).get("batch_size", DEFAULT_BATCH_SIZE)


def resolve_blog_dir() -> Path:
    volume_content_dir = Path("/data/content")
    if volume_content_dir.exists():
        return volume_content_dir / "blog"
    return Path("content/blog")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Select posts needing tag cleanup and extract summaries"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Batch size (default: config.yaml tag_cleanup.batch_size)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/tag_cleanup/candidates.json"),
    )
    args = parser.parse_args()

    limit = args.limit or load_batch_size()
    blog_dir = resolve_blog_dir()

    posts = select_posts_needing_cleanup(blog_dir, limit)
    logger.info("Selected %d posts needing tag cleanup", len(posts))

    summaries = [summarize_post(path) for path in posts]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summaries_to_json(summaries), encoding="utf-8")
    logger.info("Wrote %d summaries to %s", len(summaries), args.output)


if __name__ == "__main__":
    main()
