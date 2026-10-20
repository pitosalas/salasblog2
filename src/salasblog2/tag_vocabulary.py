#!/usr/bin/env python3
# tag_vocabulary — The closed curated tag list: convert any tag list onto it
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-20
# Updated: 2026-10-20
# Open Source Under MIT license
"""
The one rule for which tags a blog post or raindrop may carry (F55).

`02-doc/tag-hints.md`'s "Curated Tags" section is a closed list of primary
tags, each with its aliases. `canonicalize_tags` maps any tag list onto it:
an alias becomes its primary, anything unknown is dropped, and the result
is de-duplicated in order. Tags are compared after lowercasing and turning
inner whitespace into hyphens, so `Machine Learning` matches
`machine-learning`.

The post editor, raindrop sync, site generator and one-time conversions all
call this, so they can't drift apart.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

TAG_HINTS_FILE = Path(__file__).parents[2] / "02-doc" / "tag-hints.md"


@dataclass
class CanonicalTags:
    kept: list[str] = field(default_factory=list)
    dropped: list[str] = field(default_factory=list)


def tag_key(tag: str) -> str:
    """The comparable spelling of a tag: lowercase, whitespace as hyphens."""
    return re.sub(r"\s+", "-", str(tag).strip().lower())


def canonicalize_tags(tags: list[str], alias_map: dict[str, str]) -> CanonicalTags:
    """Convert `tags` through `alias_map` (from `load_curated_tag_aliases`).

    Returns the curated primaries in first-seen order without repeats, and
    the original spellings of the tags nothing in the list recognizes.
    """
    result = CanonicalTags()
    for tag in tags:
        primary = alias_map.get(tag_key(tag))
        if primary is None:
            result.dropped.append(str(tag))
        elif primary not in result.kept:
            result.kept.append(primary)
    return result
