#!/usr/bin/env python3
# build_proposals.py — Sanitize tag decisions, build the review file
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-09-09
# Updated: 2026-09-09
# Open Source Under MIT license
"""
CLI adapter for the tag-cleanup pipeline (F46). Combines a candidates file
(from select_tag_candidates.py) with a decisions file - tag choices made by
Claude acting directly in an assisted session, or by a human - into the
reviewable proposals JSON. Per 02-doc/tag-hints.md's rules: a newly proposed
tag is only applied if it's in that file's curated vocabulary; anything else
that recurs across more than one post in the batch gets appended to
tag-hints.md's "Proposed Tags" section for the user to approve, not applied
directly. Sanitization also drops numeric junk, empty strings, and
duplicates before anything is written.

Decisions file schema: a JSON list of {"filename": ..., "tags": [...]}.

Usage:
  uv run python3 scripts/build_proposals.py CANDIDATES.json DECISIONS.json [--output PATH]
"""

import argparse
import json
import logging
from pathlib import Path

from salasblog2.tag_cleanup import (
    PostSummary,
    build_proposal,
    load_curated_tags,
    proposals_to_json,
    record_recurring_candidates,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)

DEFAULT_TAG_HINTS_PATH = Path("02-doc/tag-hints.md")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build validated tag proposals from decisions"
    )
    parser.add_argument("candidates", type=Path)
    parser.add_argument("decisions", type=Path)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/tag_cleanup/proposals.json"),
    )
    parser.add_argument("--tag-hints", type=Path, default=DEFAULT_TAG_HINTS_PATH)
    args = parser.parse_args()

    summaries = {
        entry["filename"]: PostSummary(**entry)
        for entry in json.loads(args.candidates.read_text(encoding="utf-8"))
    }
    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))
    curated_tags = load_curated_tags(args.tag_hints)

    proposals = [
        build_proposal(summaries[decision["filename"]], decision["tags"], curated_tags)
        for decision in decisions
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(proposals_to_json(proposals), encoding="utf-8")
    logger.info("Wrote %d proposals to %s", len(proposals), args.output)

    new_candidates = record_recurring_candidates(proposals, args.tag_hints)
    if new_candidates:
        logger.info(
            "Added %d recurring candidate tag(s) to %s for approval: %s",
            len(new_candidates),
            args.tag_hints,
            ", ".join(new_candidates),
        )


if __name__ == "__main__":
    main()
