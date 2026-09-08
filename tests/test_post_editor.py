"""
Tests for the unified post/page editor and admin content management (F42):
delete endpoints for posts/pages/raindrops, category persistence, concurrency
conflict detection, and the "All Posts" admin index.

Run with: uv run pytest tests/test_post_editor.py -v
"""

import time
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


class TestCategoryPersistence:
    """F42 point 7: category wasn't editable anywhere in the admin UI."""

    def test_create_post_with_category(self, client, tmp_path):
        response = client.post(
            "/admin/new-post",
            data={
                "title": "Categorized Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Body",
                "category": "Technology",
            },
        )
        assert response.status_code == 200
        filename = response.json()["filename"]
        saved = (tmp_path / "content" / "blog" / filename).read_text()
        assert "category: Technology" in saved or 'category: "Technology"' in saved

    def test_edit_post_updates_category(self, client, tmp_path):
        write_post(tmp_path, "2026-01-01-my-post.md", category="General")
        response = client.post(
            "/admin/edit-post/2026-01-01-my-post.md",
            data={
                "title": "Test Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Body content.",
                "category": "Updated Category",
            },
        )
        assert response.status_code == 200
        saved = (tmp_path / "content" / "blog" / "2026-01-01-my-post.md").read_text()
        assert "Updated Category" in saved


class TestFreeFormTags:
    """F42 point 6: tags were a fixed checkbox vocabulary; now free-form."""

    def test_new_post_accepts_tag_not_in_blog_tags_vocabulary(self, client, tmp_path):
        response = client.post(
            "/admin/new-post",
            data={
                "title": "Novel Tag Post",
                "date": "2026-01-01",
                "type": "blog",
                "content": "Body",
                "tags": ["a-brand-new-tag-nobody-configured"],
            },
        )
        assert response.status_code == 200
        filename = response.json()["filename"]
        saved = (tmp_path / "content" / "blog" / filename).read_text()
        assert "a-brand-new-tag-nobody-configured" in saved


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


class TestUnifiedEditorTemplate:
    """F42 point 4: new_post.html/edit_post.html were hand-duplicated and had
    drifted (e.g. image_size only on edit). Both now render post_editor.html
    with identical fields."""

    def test_new_post_page_has_image_size_field(self, client):
        """Regression: image_size used to be edit-only."""
        response = client.get("/admin/new-post")
        assert response.status_code == 200
        assert 'id="image_size"' in response.text

    def test_new_post_page_has_category_field(self, client):
        response = client.get("/admin/new-post")
        assert 'id="category"' in response.text

    def test_edit_post_page_has_category_field(self, client, tmp_path):
        write_post(tmp_path, "2026-01-01-my-post.md")
        response = client.get("/admin/edit-post/2026-01-01-my-post.md")
        assert response.status_code == 200
        assert 'id="category"' in response.text
