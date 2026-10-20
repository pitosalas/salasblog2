#!/usr/bin/env python3
# test_tag_vocabulary — Tests for the closed curated tag list (F55)
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-20
# Updated: 2026-10-20
# Open Source Under MIT license

import re

import frontmatter

from salasblog2.raindrop import RaindropDownloader
from salasblog2.tag_vocabulary import TAG_HINTS_FILE, canonicalize_tags, tag_key
from salasblog2.utils import load_curated_tag_aliases, load_curated_tags

ALIASES = {
    "robotics": "robotics",
    "robot": "robotics",
    "opencv": "robotics",
    "ai": "ai",
    "chatgpt": "ai",
    "machine-learning": "ai",
}


class TestCanonicalizeTags:
    def test_primary_is_kept(self):
        assert canonicalize_tags(["robotics"], ALIASES).kept == ["robotics"]

    def test_alias_becomes_its_primary(self):
        assert canonicalize_tags(["robot"], ALIASES).kept == ["robotics"]

    def test_unknown_tag_is_dropped_and_reported(self):
        result = canonicalize_tags(["ai", "banana"], ALIASES)
        assert result.kept == ["ai"]
        assert result.dropped == ["banana"]

    def test_duplicates_collapse_in_first_seen_order(self):
        result = canonicalize_tags(["chatgpt", "robot", "ai", "robotics"], ALIASES)
        assert result.kept == ["ai", "robotics"]

    def test_case_and_spaces_are_normalized(self):
        result = canonicalize_tags(["ChatGPT", " Machine Learning "], ALIASES)
        assert result.kept == ["ai"]
        assert result.dropped == []

    def test_dropped_keeps_original_spelling(self):
        assert canonicalize_tags(["Banana Split"], ALIASES).dropped == ["Banana Split"]

    def test_numeric_leftover_is_dropped(self):
        assert canonicalize_tags([1221], ALIASES).dropped == ["1221"]

    def test_empty_input(self):
        result = canonicalize_tags([], ALIASES)
        assert result.kept == []
        assert result.dropped == []


def test_tag_key_lowercases_and_hyphenates():
    assert tag_key("  Open   Source ") == "open-source"


class TestInstalledList:
    """The project's tag-hints.md is the 16-tag closed list."""

    def test_exactly_sixteen_primaries(self):
        assert len(load_curated_tags(TAG_HINTS_FILE)) == 16

    def test_no_alias_claimed_twice_or_shadowing_a_primary(self):
        primaries = set(load_curated_tags(TAG_HINTS_FILE))
        aliases = []
        for line in TAG_HINTS_FILE.read_text(encoding="utf-8").splitlines():
            match = re.match(r"^\d+\s+\S+\s*\((.*)\)\s*$", line)
            if match:
                aliases += [a.strip() for a in match.group(1).split(",")]
        assert len(aliases) == len(set(aliases))
        assert not primaries & set(aliases)

    def test_every_alias_maps_to_a_primary(self):
        alias_map = load_curated_tag_aliases(TAG_HINTS_FILE)
        assert set(alias_map.values()) == set(load_curated_tags(TAG_HINTS_FILE))


class TestRaindropSyncConvertsTags:
    def write(self, tmp_path, tags):
        downloader = RaindropDownloader(access_token="test_token")
        downloader.drops_dir = tmp_path
        raindrop = {
            "_id": 1,
            "title": "A bookmark",
            "link": "https://example.com",
            "created": "2026-01-01T00:00:00Z",
            "tags": tags,
        }
        [filename] = downloader._write_raindrops_to_files([raindrop], {})
        return (tmp_path / filename).read_text(encoding="utf-8")

    def test_tags_converted_and_unknown_dropped(self, tmp_path):
        text = self.write(tmp_path, ["chatgpt", "free", "opencv"])
        assert "tags:\n- ai\n- robotics\n" in text
        assert "free" not in text

    def test_only_unknown_tags_leaves_raindrop_untagged(self, tmp_path):
        text = self.write(tmp_path, ["free", "data"])
        assert "tags" not in frontmatter.loads(text).metadata
