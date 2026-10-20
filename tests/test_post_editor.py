"""
Tests for the unified post/page editor and admin content management (F42):
delete endpoints for posts/pages/raindrops, retired categories (F51), concurrency
conflict detection, and the "All Posts" admin index.

Run with: uv run pytest tests/test_post_editor.py -v
"""

import time
from pathlib import Path

import frontmatter
import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    from pathlib import Path as _Path

    from jinja2 import Environment, FileSystemLoader

    from salasblog2.server import app, config

    config["root_dir"] = tmp_path
    config["output_dir"] = tmp_path / "output"
    (tmp_path / "output").mkdir()
    config["admin_password"] = ""
    templates_dir = _Path.cwd() / "templates"
    config["jinja_env"] = Environment(loader=FileSystemLoader(templates_dir))
    tag_hints_dir = tmp_path / "02-doc"
    tag_hints_dir.mkdir()
    (tag_hints_dir / "tag-hints.md").write_text(
        "# Curated Tags\n\nprogramming (python)\ncomputing (iphone)\nai\n",
        encoding="utf-8",
    )
    return TestClient(app)


def write_post(
    tmp_path, filename, title="Test Post", date="2026-01-01", tags=None, category=None
):
    blog_dir = tmp_path / "content" / "blog"
    blog_dir.mkdir(parents=True, exist_ok=True)
    lines = ["---", f'title: "{title}"', f'date: "{date}"', 'type: "blog"']
    if tags is not None:
        lines.append("tags: [" + ", ".join(f'"{t}"' for t in tags) + "]")
    if category is not None:
        lines.append(f'category: "{category}"')
    lines += ["---", "Body content."]
    path = blog_dir / filename
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


class TestDeletePost:
    def test_delete_removes_file(self, client, tmp_path):
        write_post(tmp_path, "2026-01-01-my-post.md")
        response = client.post("/admin/delete-post/2026-01-01-my-post.md")
        assert response.status_code == 200
        assert response.json()["status"] == "success"
        assert not (tmp_path / "content" / "blog" / "2026-01-01-my-post.md").exists()

    def test_delete_missing_file_returns_404(self, client, tmp_path):
        response = client.post("/admin/delete-post/does-not-exist.md")
        assert response.status_code == 404

    def test_delete_requires_auth(self, tmp_path):
        from salasblog2.server import app, config

        config["root_dir"] = tmp_path
        config["output_dir"] = tmp_path / "output"
        (tmp_path / "output").mkdir()
        config["admin_password"] = "secret"
        write_post(tmp_path, "2026-01-01-my-post.md")

        client = TestClient(app)
        response = client.post("/admin/delete-post/2026-01-01-my-post.md")
        assert response.status_code == 401
        assert (tmp_path / "content" / "blog" / "2026-01-01-my-post.md").exists()


class TestDeletePage:
    def test_delete_page_removes_file(self, client, tmp_path):
        pages_dir = tmp_path / "content" / "pages"
        pages_dir.mkdir(parents=True)
        (pages_dir / "about.md").write_text(
            '---\ntitle: "About"\ndate: "2026-01-01"\n---\nBody', encoding="utf-8"
        )
        response = client.post("/admin/delete-page/about.md")
        assert response.status_code == 200
        assert not (pages_dir / "about.md").exists()

    def test_delete_page_without_md_extension(self, client, tmp_path):
        """The route must accept a bare filename (no .md), matching the edit-page route."""
        pages_dir = tmp_path / "content" / "pages"
        pages_dir.mkdir(parents=True)
        (pages_dir / "about.md").write_text(
            '---\ntitle: "About"\ndate: "2026-01-01"\n---\nBody', encoding="utf-8"
        )
        response = client.post("/admin/delete-page/about")
        assert response.status_code == 200
        assert not (pages_dir / "about.md").exists()


class TestDeleteRaindrop:
    def test_delete_raindrop_uses_raindrops_directory_not_blog(self, client, tmp_path):
        """Regression: raindrop_post.html used to call the blog delete endpoint,
        which 404s because raindrops live in a separate content directory."""
        raindrops_dir = tmp_path / "content" / "raindrops"
        raindrops_dir.mkdir(parents=True)
        (raindrops_dir / "2026-01-01-a-link.md").write_text(
            '---\ntitle: "A Link"\ndate: "2026-01-01"\n---\nBody', encoding="utf-8"
        )
        response = client.post("/admin/delete-raindrop/2026-01-01-a-link.md")
        assert response.status_code == 200
        assert not (raindrops_dir / "2026-01-01-a-link.md").exists()


class TestCategoryRetired:
    """F51: categories were retired; tags carry what they used to."""

    def test_create_post_does_not_write_category(self, client, tmp_path):
        response = client.post(
            "/admin/new-post",
            data={
                "title": "Uncategorized Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Body",
                "category": "Technology",
            },
        )
        assert response.status_code == 200
        filename = response.json()["filename"]
        saved = (tmp_path / "content" / "blog" / filename).read_text()
        assert "category" not in saved

    def test_edit_post_drops_old_category(self, client, tmp_path):
        write_post(tmp_path, "2026-01-01-my-post.md", category="298")
        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Body content.",
            },
        )
        assert response.status_code == 200
        saved = (tmp_path / "content" / "blog" / "2026-01-01-my-post.md").read_text()
        assert "category" not in saved

    def test_editor_has_no_category_field(self, client, tmp_path):
        write_post(tmp_path, "2026-01-01-my-post.md", category="298")
        for url in ["/admin/new-post", "/admin/edit-post/2026-01-01-my-post.md"]:
            response = client.get(url)
            assert response.status_code == 200
            assert 'name="category"' not in response.text


class TestPageRenderedBeforeResponse:
    """The editor redirects to the new page 1.5s after saving; if the page is
    only built by the slow background regeneration, that redirect 404s."""

    @pytest.fixture
    def no_background_regen(self, tmp_path, monkeypatch):
        from salasblog2 import server

        monkeypatch.chdir(tmp_path)
        (tmp_path / "templates").symlink_to(Path(__file__).parent.parent / "templates")
        monkeypatch.setattr(server, "_regenerate_in_background", lambda *args: None)

    def test_new_post_html_exists_when_response_returns(
        self, client, tmp_path, no_background_regen
    ):
        response = client.post(
            "/admin/new-post",
            data={
                "title": "Fresh Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Body",
            },
        )
        assert response.status_code == 200
        html_name = response.json()["filename"].replace(".md", ".html")
        assert (tmp_path / "output" / "blog" / html_name).exists()

    def test_edited_post_html_reflects_edit_when_response_returns(
        self, client, tmp_path, no_background_regen
    ):
        write_post(tmp_path, "2026-01-01-my-post.md")
        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Freshly edited body.",
            },
        )
        assert response.status_code == 200
        html = (tmp_path / "output" / "blog" / "2026-01-01-my-post.html").read_text()
        assert "Freshly edited body." in html

    def test_new_page_html_exists_when_response_returns(
        self, client, tmp_path, no_background_regen
    ):
        response = client.post(
            "/admin/new-page",
            data={
                "title": "Fresh Page",
                "date": "2026-01-01",
                "type": "page",
                "content": "Body",
            },
        )
        assert response.status_code == 200
        html_name = response.json()["filename"].replace(".md", ".html")
        assert (tmp_path / "output" / html_name).exists()


class TestCuratedTagsOnSave:
    """F55: the curated list is closed. Aliases convert on save; anything
    else is refused rather than silently dropped."""

    def post_new(self, client, tags):
        return client.post(
            "/admin/new-post",
            data={
                "title": "Tag Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Body",
                "tags": tags,
            },
        )

    def test_alias_is_saved_as_its_curated_tag(self, client, tmp_path):
        response = self.post_new(client, ["iPhone", "ai", "computing"])
        assert response.status_code == 200
        saved = tmp_path / "content" / "blog" / response.json()["filename"]
        assert frontmatter.load(saved).metadata["tags"] == ["computing", "ai"]

    def test_unknown_tag_is_refused_and_nothing_saved(self, client, tmp_path):
        response = self.post_new(client, ["ai", "banana"])
        assert response.status_code == 400
        assert "banana" in response.json()["detail"]
        assert not (tmp_path / "content" / "blog").exists()

    def test_edit_with_unknown_tag_leaves_file_unchanged(self, client, tmp_path):
        post_file = write_post(tmp_path, "2026-01-01-my-post.md", tags=["ai"])
        before = post_file.read_text()
        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "My edit",
                "tags": ["banana"],
            },
        )
        assert response.status_code == 400
        assert post_file.read_text() == before

    def test_edit_keeps_original_tags(self, client, tmp_path):
        post_file = write_post(tmp_path, "2026-01-01-my-post.md", tags=["ai"])
        text = post_file.read_text().replace(
            'tags: ["ai"]', 'tags: ["ai"]\noriginal_tags: ["chatgpt", "free"]'
        )
        post_file.write_text(text)
        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "My edit",
                "tags": ["ai"],
            },
        )
        assert response.status_code == 200
        metadata = frontmatter.load(post_file).metadata
        assert metadata["original_tags"] == ["chatgpt", "free"]


class TestConcurrencyProtection:
    """F42 point 9: two admin tabs editing the same post used to silently clobber."""

    def test_save_with_stale_mtime_returns_409(self, client, tmp_path):
        post_file = write_post(tmp_path, "2026-01-01-my-post.md")
        stale_mtime = post_file.stat().st_mtime

        # Simulate someone else's edit landing after the form was loaded.
        time.sleep(0.05)
        post_file.write_text(post_file.read_text() + "\nchanged elsewhere")

        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "My edit",
                "loaded_mtime": str(stale_mtime),
            },
        )
        assert response.status_code == 409

    def test_save_with_current_mtime_succeeds(self, client, tmp_path):
        post_file = write_post(tmp_path, "2026-01-01-my-post.md")
        current_mtime = post_file.stat().st_mtime

        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "My edit",
                "loaded_mtime": str(current_mtime),
            },
        )
        assert response.status_code == 200

    def test_save_with_no_mtime_sent_does_not_block(self, client, tmp_path):
        """A client that doesn't send loaded_mtime (e.g. an old cached page)
        should not be hard-blocked — this is a best-effort warning, not a lock."""
        write_post(tmp_path, "2026-01-01-my-post.md")
        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "My edit",
            },
        )
        assert response.status_code == 200


class TestAdminPostsIndex:
    """F42 point 3: no way to browse existing posts from the admin panel."""

    def test_admin_posts_endpoint_lists_posts_and_pages(self, client, tmp_path):
        write_post(tmp_path, "2026-01-01-my-post.md", title="My Post")
        pages_dir = tmp_path / "content" / "pages"
        pages_dir.mkdir(parents=True)
        (pages_dir / "about.md").write_text(
            '---\ntitle: "About"\ndate: "2026-01-01"\n---\nBody', encoding="utf-8"
        )

        response = client.get("/api/admin-posts")
        assert response.status_code == 200
        entries = response.json()
        titles = {e["title"] for e in entries}
        assert "My Post" in titles
        assert "About" in titles
        content_types = {e["filename"]: e["content_type"] for e in entries}
        assert content_types["2026-01-01-my-post.md"] == "blog"
        assert content_types["about.md"] == "pages"

    def test_admin_posts_excludes_drafts(self, client, tmp_path):
        blog_dir = tmp_path / "content" / "blog"
        blog_dir.mkdir(parents=True)
        (blog_dir / "draft-123.md").write_text(
            '---\ntitle: "Draft"\ndate: "2026-01-01"\ndraft: true\n---\nBody',
            encoding="utf-8",
        )
        response = client.get("/api/admin-posts")
        titles = {e["title"] for e in response.json()}
        assert "Draft" not in titles

    def test_admin_posts_requires_auth_when_password_set(self, tmp_path):
        from salasblog2.server import app, config

        config["root_dir"] = tmp_path
        config["output_dir"] = tmp_path / "output"
        (tmp_path / "output").mkdir()
        config["admin_password"] = "secret"
        client = TestClient(app)
        response = client.get("/api/admin-posts")
        assert response.status_code == 401


class TestTagPicklistUI:
    """The blog post editor's picklist offers exactly the curated tags (F55);
    the page editor (no tags field at all) has no picklist."""

    def test_new_post_page_offers_exactly_the_curated_tags(self, client):
        response = client.get("/admin/new-post")
        assert response.status_code == 200
        assert 'const CURATED_TAGS = ["programming", "computing", "ai"];' in (
            response.text
        )
        assert 'id="tagPicklistToggle"' in response.text
        assert 'id="tagPicklistChips"' in response.text

    def test_new_page_form_has_no_tag_picklist(self, client):
        """Pages have no tags field at all — the picklist markup/JS must not
        appear (it references elements that wouldn't exist on this form)."""
        response = client.get("/admin/new-page")
        assert response.status_code == 200
        assert 'id="tagPicklistToggle"' not in response.text
        assert "CURATED_TAGS" not in response.text


class TestUnifiedEditorTemplate:
    """F42 point 4: new_post.html/edit_post.html were hand-duplicated and had
    drifted (e.g. image_size only on edit). Both now render post_editor.html
    with identical fields."""

    def test_new_post_page_has_image_size_field(self, client):
        """Regression: image_size used to be edit-only."""
        response = client.get("/admin/new-post")
        assert response.status_code == 200
        assert 'id="image_size"' in response.text
