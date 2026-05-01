#!/usr/bin/env python3
# test_draft_generator.py — Tests for draft blog post generation from raindrops
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from pathlib import Path
from unittest.mock import MagicMock, patch

import frontmatter
import pytest

from salasblog2.draft_generator import build_frontmatter, build_prompt, generate_draft_from_drop, save_draft


SAMPLE_DROP = {
    "filename": "21-04-06-1-some-link.md",
    "title": "A Great Article",
    "url": "https://example.com/article",
    "raindrop_url": "/raindrops/21-04-06-1-some-link.html",
    "note": "Really insightful take on the topic",
    "domain": "example.com",
    "excerpt": "Summary of the article",
    "tags": ["ai", "programming"],
    "date": "2021-04-06",
}


class TestBuildFrontmatter:
    def test_contains_required_fields(self):
        fm = build_frontmatter(SAMPLE_DROP, "A Great Article")
        assert "draft: true" in fm
        assert "author: Claude.ai" in fm
        assert "source_raindrop:" in fm
        assert "source_url:" in fm
        assert "type: blog" in fm

    def test_is_valid_yaml_wrapped(self):
        fm = build_frontmatter(SAMPLE_DROP, "A Great Article")
        assert fm.startswith("---\n")
        assert "---\n" in fm[4:]


class TestBuildPrompt:
    def test_includes_url(self):
        prompt = build_prompt(SAMPLE_DROP, "")
        assert SAMPLE_DROP["url"] in prompt

    def test_includes_note(self):
        prompt = build_prompt(SAMPLE_DROP, "")
        assert SAMPLE_DROP["note"] in prompt

    def test_includes_page_text_when_provided(self):
        prompt = build_prompt(SAMPLE_DROP, "extra page content here")
        assert "extra page content here" in prompt

    def test_omits_page_section_when_empty(self):
        prompt = build_prompt(SAMPLE_DROP, "")
        assert "Page content" not in prompt


class TestGenerateDraftFromDrop:
    def test_draft_has_draft_flag(self):
        mock_body = "A paragraph about the link. [Read more](https://example.com/article)."
        with patch("salasblog2.draft_generator.call_claude", return_value=mock_body), \
             patch("salasblog2.draft_generator.fetch_url_text", return_value=""):
            content = generate_draft_from_drop(SAMPLE_DROP)

        post = frontmatter.loads(content)
        assert post.metadata.get("draft") is True

    def test_draft_author_is_claude(self):
        mock_body = "Paragraph text."
        with patch("salasblog2.draft_generator.call_claude", return_value=mock_body), \
             patch("salasblog2.draft_generator.fetch_url_text", return_value=""):
            content = generate_draft_from_drop(SAMPLE_DROP)

        post = frontmatter.loads(content)
        assert post.metadata.get("author") == "Claude.ai"

    def test_draft_body_contains_source_url(self):
        mock_body = f"Here is a link: [{SAMPLE_DROP['title']}]({SAMPLE_DROP['url']})."
        with patch("salasblog2.draft_generator.call_claude", return_value=mock_body), \
             patch("salasblog2.draft_generator.fetch_url_text", return_value=""):
            content = generate_draft_from_drop(SAMPLE_DROP)

        assert SAMPLE_DROP["url"] in content

    def test_draft_source_raindrop_set(self):
        with patch("salasblog2.draft_generator.call_claude", return_value="body"), \
             patch("salasblog2.draft_generator.fetch_url_text", return_value=""):
            content = generate_draft_from_drop(SAMPLE_DROP)

        post = frontmatter.loads(content)
        assert post.metadata.get("source_raindrop") == SAMPLE_DROP["filename"]


class TestSaveDraft:
    def test_writes_to_all_dirs(self, tmp_path):
        dir_a = tmp_path / "a"
        dir_b = tmp_path / "b"
        save_draft("content here", "draft.md", [dir_a, dir_b])
        assert (dir_a / "draft.md").read_text() == "content here"
        assert (dir_b / "draft.md").read_text() == "content here"

    def test_creates_missing_dirs(self, tmp_path):
        new_dir = tmp_path / "new" / "nested"
        save_draft("hello", "f.md", [new_dir])
        assert (new_dir / "f.md").exists()
