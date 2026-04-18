#!/usr/bin/env python3
# test_drafts_api.py — Tests for draft generation and publishing endpoints
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from pathlib import Path
from unittest.mock import patch

import frontmatter
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from salasblog2.server import app, config
    config["admin_password"] = ""
    config["root_dir"] = tmp_path
    config["output_dir"] = tmp_path / "output"
    (tmp_path / "output").mkdir()
    return TestClient(app)


def _write_drop(drops_dir: Path, filename: str) -> None:
    drops_dir.mkdir(parents=True, exist_ok=True)
    (drops_dir / filename).write_text(
        "---\ntitle: 'Test Link'\ndate: '2020-01-01'\ntype: drop\n"
        "url: 'https://example.com'\nnote: 'interesting'\ndomain: example.com\n"
        "excerpt: 'summary'\ntags: [ai]\n---\nbody\n"
    )


def _write_draft(blog_dir: Path, filename: str, title: str = "Draft Title") -> None:
    blog_dir.mkdir(parents=True, exist_ok=True)
    (blog_dir / filename).write_text(
        f"---\ntitle: {title!r}\ndate: '2024-01-01'\ntype: blog\ndraft: true\n"
        "author: Claude.ai\nsource_raindrop: 'drop.md'\nsource_url: 'https://x.com'\n"
        "---\nDraft body text.\n"
    )


class TestListDrafts:
    def test_returns_only_drafts(self, client, tmp_path):
        blog_dir = tmp_path / "data" / "content" / "blog"
        blog_dir.mkdir(parents=True)
        _write_draft(blog_dir, "draft-one.md", "Draft One")
        (blog_dir / "real.md").write_text(
            "---\ntitle: 'Real'\ndate: '2024-01-01'\ntype: blog\n---\nbody\n"
        )
        with patch("salasblog2.server.get_content_directory", return_value=blog_dir):
            resp = client.get("/api/drafts")
        assert resp.status_code == 200
        filenames = [d["filename"] for d in resp.json()]
        assert "draft-one.md" in filenames
        assert "real.md" not in filenames

    def test_draft_has_required_fields(self, client, tmp_path):
        blog_dir = tmp_path / "data" / "content" / "blog"
        blog_dir.mkdir(parents=True)
        _write_draft(blog_dir, "draft-one.md")
        with patch("salasblog2.server.get_content_directory", return_value=blog_dir):
            resp = client.get("/api/drafts")
        draft = resp.json()[0]
        for key in ("filename", "title", "date", "source_raindrop", "source_url"):
            assert key in draft


class TestPublishDraft:
    def test_removes_draft_flag(self, client, tmp_path):
        blog_dir = tmp_path / "data" / "content" / "blog"
        blog_dir.mkdir(parents=True)
        _write_draft(blog_dir, "draft-one.md")

        with patch("salasblog2.server.get_content_directory", return_value=blog_dir), \
             patch("salasblog2.server.SiteGenerator") as mock_gen:
            mock_gen.return_value.incremental_regenerate_post.return_value = None
            resp = client.post("/api/publish-draft", json={"filename": "draft-one.md"})

        assert resp.status_code == 200
        post = frontmatter.loads((blog_dir / "draft-one.md").read_text())
        assert "draft" not in post.metadata

    def test_returns_404_for_missing_draft(self, client, tmp_path):
        blog_dir = tmp_path / "data" / "content" / "blog"
        blog_dir.mkdir(parents=True)
        with patch("salasblog2.server.get_content_directory", return_value=blog_dir):
            resp = client.post("/api/publish-draft", json={"filename": "missing.md"})
        assert resp.status_code == 404


class TestGenerateDraftEndpoint:
    def test_returns_draft_filename(self, client, tmp_path):
        drops_dir = tmp_path / "data" / "content" / "raindrops"
        blog_dir = tmp_path / "data" / "content" / "blog"
        _write_drop(drops_dir, "drop.md")
        blog_dir.mkdir(parents=True)

        mock_content = (
            "---\ntitle: 'Draft'\ndate: '2024-01-01'\ntype: blog\ndraft: true\n"
            "author: Claude.ai\nsource_raindrop: drop.md\nsource_url: https://example.com\n"
            "tags: []\n---\nParagraph body.\n"
        )

        def fake_get_dir(content_type):
            return drops_dir if content_type == "raindrops" else blog_dir

        with patch("salasblog2.server.get_content_directory", side_effect=fake_get_dir), \
             patch("salasblog2.server.generate_draft_from_drop", return_value=mock_content), \
             patch("salasblog2.server.save_draft"):
            resp = client.post("/api/generate-draft", json={"filename": "drop.md"})

        assert resp.status_code == 200
        assert "filename" in resp.json()

    def test_returns_404_for_missing_drop(self, client, tmp_path):
        drops_dir = tmp_path / "data" / "content" / "raindrops"
        drops_dir.mkdir(parents=True)
        with patch("salasblog2.server.get_content_directory", return_value=drops_dir):
            resp = client.post("/api/generate-draft", json={"filename": "missing.md"})
        assert resp.status_code == 404
