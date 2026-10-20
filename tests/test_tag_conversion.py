#!/usr/bin/env python3
# test_tag_conversion — Tests for the in-place conversion onto curated tags (F55)
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-20
# Updated: 2026-10-20
# Open Source Under MIT license

import json

import pytest

from salasblog2.generator import SiteGenerator
from salasblog2.tag_conversion import (
    apply_tag_decisions,
    convert_blog_tags,
    convert_directory,
    replace_frontmatter_tags,
    select_generic_posts,
)
from salasblog2.tag_vocabulary import canonicalize_tags

ALIASES = {
    "ai": "ai",
    "chatgpt": "ai",
    "robotics": "robotics",
    "life": "life",
    "food": "life",
}


def post_text(tag_lines, eol="\n", body="Body line one.\nBody line two.\n"):
    head = ["---", 'title: "A Post"', *tag_lines, "date: 2020-01-01", "---"]
    return eol.join(head) + eol + body.replace("\n", eol)


def write(directory, name, text):
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(text.encode("utf-8"))
    return path


class TestReplaceFrontmatterTags:
    def test_block_list_replaced_rest_untouched(self):
        text = post_text(["tags:", "- chatgpt", "- free"])
        assert replace_frontmatter_tags(text, ["ai"]) == post_text(["tags:", "- ai"])

    def test_flow_list_replaced(self):
        text = post_text(["tags: [chatgpt, free]"])
        assert replace_frontmatter_tags(text, []) == post_text(["tags: []"])

    def test_crlf_line_endings_preserved(self):
        text = post_text(["tags:", "- chatgpt"], eol="\r\n")
        expected = post_text(["tags:", "- ai", "- life"], eol="\r\n")
        assert replace_frontmatter_tags(text, ["ai", "life"]) == expected

    def test_closing_fence_is_not_a_list_item(self):
        text = "---\ntags:\n- ai\n---\n- a body bullet\n"
        assert (
            replace_frontmatter_tags(text, [])
            == "---\ntags: []\n---\n- a body bullet\n"
        )

    def test_missing_tags_key_raises(self):
        with pytest.raises(ValueError, match="no tags"):
            replace_frontmatter_tags(post_text([]), ["ai"])


class TestConvertBlogTags:
    def test_aliases_convert(self):
        assert convert_blog_tags(["chatgpt", "food"], ALIASES).kept == ["ai", "life"]

    def test_generic_dropped_when_post_has_a_real_topic(self):
        result = convert_blog_tags(["personal", "food", "technology"], ALIASES)
        assert result.kept == ["life"]
        assert result.dropped == ["personal", "technology"]

    def test_generic_kept_as_marker_when_nothing_else_fits(self):
        result = convert_blog_tags(["technology", "banana", "personal"], ALIASES)
        assert result.kept == ["technology", "personal"]
        assert result.dropped == ["banana"]


class TestConvertDirectory:
    def make_drops(self, tmp_path):
        drops = tmp_path / "raindrops"
        write(drops, "mixed.md", post_text(["tags:", "- chatgpt", "- free"]))
        write(drops, "unknown.md", post_text(["tags:", "- free"]))
        write(drops, "untagged.md", post_text(["tags: []"]))
        write(drops, "crlf.md", post_text(["tags:", "- robotics", "- x"], eol="\r\n"))
        return drops

    def test_dry_run_reports_and_writes_nothing(self, tmp_path):
        drops = self.make_drops(tmp_path)
        before = {p.name: p.read_bytes() for p in drops.iterdir()}
        report = convert_directory(drops, canonicalize_tags, ALIASES, is_apply=False)
        assert report.files_changed == 3
        assert report.now_untagged == 1
        assert report.tags_kept == 2
        assert report.dropped == {"free": 2, "x": 1}
        assert {p.name: p.read_bytes() for p in drops.iterdir()} == before

    def test_apply_changes_only_tag_lines(self, tmp_path):
        drops = self.make_drops(tmp_path)
        convert_directory(drops, canonicalize_tags, ALIASES, is_apply=True)
        assert (drops / "mixed.md").read_text() == post_text(["tags:", "- ai"])
        assert (drops / "unknown.md").read_text() == post_text(["tags: []"])
        assert (drops / "untagged.md").read_text() == post_text(["tags: []"])
        assert (drops / "crlf.md").read_bytes() == post_text(
            ["tags:", "- robotics"], eol="\r\n"
        ).encode("utf-8")

    def test_second_run_changes_nothing(self, tmp_path):
        drops = self.make_drops(tmp_path)
        convert_directory(drops, canonicalize_tags, ALIASES, is_apply=True)
        report = convert_directory(drops, canonicalize_tags, ALIASES, is_apply=True)
        assert report.files_changed == 0

    def test_error_names_the_file(self, tmp_path):
        drops = tmp_path / "raindrops"
        write(drops, "bad.md", post_text(["tags: chatgpt"]))
        with pytest.raises(ValueError, match="bad.md"):
            convert_directory(drops, canonicalize_tags, ALIASES, is_apply=False)


class TestGenericPass:
    def test_select_finds_only_posts_with_the_generic_tag(self, tmp_path):
        blog = tmp_path / "blog"
        write(blog, "a.md", post_text(["tags:", "- technology"]))
        write(blog, "b.md", post_text(["tags:", "- ai"]))
        write(blog, "c.md", post_text(["tags:", "- technology", "- personal"]))
        selected = select_generic_posts(blog, "technology", limit=1)
        assert [p.name for p in selected] == ["a.md"]
        selected = select_generic_posts(blog, "technology", limit=10)
        assert [p.name for p in selected] == ["a.md", "c.md"]

    def test_apply_replaces_tags_through_aliases(self, tmp_path):
        blog = tmp_path / "blog"
        path = write(blog, "a.md", post_text(["tags:", "- technology"], eol="\r\n"))
        decisions = [{"filename": "a.md", "tags": ["chatgpt"]}]
        assert apply_tag_decisions(blog, decisions, ALIASES, is_apply=True) == ["a.md"]
        assert path.read_bytes() == post_text(["tags:", "- ai"], eol="\r\n").encode()

    def test_unknown_decision_tag_refused_before_any_write(self, tmp_path):
        blog = tmp_path / "blog"
        first = write(blog, "a.md", post_text(["tags:", "- technology"]))
        write(blog, "b.md", post_text(["tags:", "- technology"]))
        before = first.read_text()
        decisions = [
            {"filename": "a.md", "tags": ["ai"]},
            {"filename": "b.md", "tags": ["banana"]},
        ]
        with pytest.raises(ValueError, match="banana"):
            apply_tag_decisions(blog, decisions, ALIASES, is_apply=True)
        assert first.read_text() == before

    def test_dry_run_writes_nothing(self, tmp_path):
        blog = tmp_path / "blog"
        path = write(blog, "a.md", post_text(["tags:", "- technology"]))
        decisions = json.loads('[{"filename": "a.md", "tags": ["ai"]}]')
        assert apply_tag_decisions(blog, decisions, ALIASES, is_apply=False) == ["a.md"]
        assert "technology" in path.read_text()


class TestGeneratorShowsOnlyCuratedTags:
    def test_stray_tag_skipped_logged_once_and_gets_no_page(self, tmp_path, capsys):
        generator = SiteGenerator()
        generator.output_dir = tmp_path / "output"
        blog = tmp_path / "blog"
        tags = ["tags:", "- programming", "- stray"]
        first = write(blog, "2020-01-01-a.md", post_text(tags))
        second = write(blog, "2020-01-02-b.md", post_text(tags))

        posts = [generator.load_post(path, "blog") for path in (first, second)]
        generator.generate_tag_pages(posts)

        assert posts[0]["tags"] == ["programming"]
        assert capsys.readouterr().out.count("'stray'") == 1
        assert (generator.output_dir / "tags" / "programming").exists()
        assert not (generator.output_dir / "tags" / "stray").exists()
