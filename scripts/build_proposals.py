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
reviewable proposals JSON. Tags are free-form (F42/F45); sanitization only
drops numeric junk, empty strings, and duplicates before anything is written.

Decisions file schema: a JSON list of {"filename": ..., "tags": [...]}.

Usage:
  uv run python3 scripts/build_proposals.py CANDIDATES.json DECISIONS.json [--output PATH]
"""

import argparse
import json
import logging
from pathlib import Path

from salasblog2.tag_cleanup import PostSummary, build_proposal, proposals_to_json

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


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
    args = parser.parse_args()

    summaries = {
        entry["filename"]: PostSummary(**entry)
        for entry in json.loads(args.candidates.read_text(encoding="utf-8"))
    }
    decisions = json.loads(args.decisions.read_text(encoding="utf-8"))

    proposals = [
        build_proposal(summaries[decision["filename"]], decision["tags"])
        for decision in decisions
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(proposals_to_json(proposals), encoding="utf-8")
    logger.info("Wrote %d proposals to %s", len(proposals), args.output)


if __name__ == "__main__":
    main()
