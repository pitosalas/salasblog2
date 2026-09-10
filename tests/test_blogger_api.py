"""
Regression tests for BloggerAPI.

Run with: uv run pytest tests/test_blogger_api.py -v
"""

import pytest
import base64
from pathlib import Path
from unittest.mock import patch
from xmlrpc.client import Fault

from salasblog2.blogger_api import BloggerAPI


def _make_api(tmp_path):
    api = BloggerAPI.__new__(BloggerAPI)
    api.root_dir = tmp_path
    api.blog_dir = tmp_path / "content" / "blog"
    api.blog_dir.mkdir(parents=True)
    return api


class TestVolumeFirstContentDir:
    """Regression: BloggerAPI.blog_dir was hardcoded to root_dir/content/blog,
    never checking /data/content like get_content_directory() (server.py) and
    SiteGenerator (generator.py) already do. That let a post edited via the web
    admin (which writes straight to /data/content) go invisible to MarsEdit, and
    let a container restart between a MarsEdit edit and the next MarsEdit read
    revert /app/content to the last-pushed git commit while /data/content (and
    the live site) kept the newer version — reported by the user as MarsEdit
    showing a stale post even after refreshing."""

    @staticmethod
    def redirect_data_content_path(volume_content_dir: Path):
        """Build a Path(...) side_effect that redirects Path("/data/content")
        to an existing tmp directory, passing every other call through."""
        original_Path = Path

        def path_factory(*args):
            if args == ("/data/content",):
                return volume_content_dir
            return original_Path(*args)

        return path_factory

    def test_prefers_volume_when_present(self, tmp_path):
        """When /data/content exists (production-like), blog_dir resolves under it."""
        volume_content_dir = tmp_path / "data" / "content"
        volume_content_dir.mkdir(parents=True)

        with (
            patch(
                "salasblog2.blogger_api.Path",
                side_effect=self.redirect_data_content_path(volume_content_dir),
            ),
            patch("salasblog2.blogger_api.Path.cwd", return_value=tmp_path),
        ):
            api = BloggerAPI()

        assert api.blog_dir == volume_content_dir / "blog"

    def test_falls_back_to_local_content_without_volume(self, tmp_path, monkeypatch):
        """When /data/content doesn't exist (local dev), blog_dir falls back to
        root_dir/content/blog, same as get_content_directory()/SiteGenerator."""
        monkeypatch.chdir(tmp_path)
        api = BloggerAPI()

        assert api.blog_dir == tmp_path / "content" / "blog"


class TestNewEditDeletePost:
    """Writes/deletes go straight to blog_dir now — no separate volume backup
    or delete step to fail independently of the write/delete itself."""

    def test_new_post_written_directly_no_backup_step(self, tmp_path):
        api = _make_api(tmp_path)

        with (
            patch.object(api, "_authenticate", return_value=True),
            patch.object(api, "_regenerate_and_verify"),
        ):
            filename = api.blogger_newPost(
                "key", "blog", "user", "pass", "Title\nBody", True
            )

        assert (api.blog_dir / filename).exists()

    def test_edit_post_written_directly_no_backup_step(self, tmp_path):
        api = _make_api(tmp_path)
        post_file = api.blog_dir / "existing-post.md"
        post_file.write_text("---\ntitle: Test\n---\nBody")

        with (
            patch.object(api, "_authenticate", return_value=True),
            patch.object(api, "_regenerate_and_verify"),
        ):
            api.blogger_editPost(
                "key", "existing-post.md", "user", "pass", "New Title\nNew Body", True
            )

        assert "New Body" in post_file.read_text()

    def test_delete_post_removed_directly_no_volume_step(self, tmp_path):
        api = _make_api(tmp_path)
        post_file = api.blog_dir / "existing-post.md"
        post_file.write_text("---\ntitle: Test\n---\nBody")

        with (
            patch.object(api, "_authenticate", return_value=True),
            patch.object(api, "_regenerate_and_verify"),
        ):
            api.blogger_deletePost("key", "existing-post.md", "user", "pass", True)

        assert not post_file.exists()


class TestNewMediaObject:
    """Tests for metaweblog_newMediaObject."""

    def test_saves_to_source_output_and_returns_url(self, tmp_path):
        """File is written to source and output dirs; correct URL is returned."""
        api = _make_api(tmp_path)
        image_data = b"\x89PNG\r\n\x1a\nfakeimage"
        struct = {"name": "photo.png", "type": "image/png", "bits": image_data}

        with (
            patch.object(api, "_authenticate"),
            patch("salasblog2.blogger_api.Path") as MockPath,
        ):
            # Redirect /data to tmp so we don't need root
            original_Path = Path

            def path_factory(*args):
                if args == ("/data",):
                    return tmp_path / "data"
                return original_Path(*args)

            MockPath.side_effect = path_factory

            result = api.metaweblog_newMediaObject("1", "user", "pass", struct)

        assert "url" in result
        assert result["url"].startswith("/static/images/uploads/")
        assert result["url"].endswith("photo.png")

        # Source file written
        source_files = list((tmp_path / "static" / "images" / "uploads").glob("*.png"))
        assert len(source_files) == 1
        assert source_files[0].read_bytes() == image_data

        # Output file written
        output_files = list(
            (tmp_path / "output" / "static" / "images" / "uploads").glob("*.png")
        )
        assert len(output_files) == 1
        assert output_files[0].read_bytes() == image_data

    def test_filename_is_date_prefixed(self, tmp_path):
        """Uploaded filename gets a YYYY-MM-DD prefix."""
        api = _make_api(tmp_path)
        struct = {"name": "myimage.jpg", "type": "image/jpeg", "bits": b"fakedata"}

        with (
            patch.object(api, "_authenticate"),
            patch("salasblog2.blogger_api.Path") as MockPath,
        ):
            original_Path = Path

            def path_factory(*args):
                if args == ("/data",):
                    return tmp_path / "data"
                return original_Path(*args)

            MockPath.side_effect = path_factory

            result = api.metaweblog_newMediaObject("1", "user", "pass", struct)

        filename = result["url"].split("/")[-1]
        import re

        assert re.match(r"^\d{4}-\d{2}-\d{2}-myimage\.jpg$", filename), (
            f"Expected date-prefixed filename, got: {filename}"
        )

    def test_base64_string_bits_are_decoded(self, tmp_path):
        """If bits arrives as a base64 string it is decoded to bytes before saving."""
        api = _make_api(tmp_path)
        image_data = b"rawbytes"
        struct = {
            "name": "img.png",
            "type": "image/png",
            "bits": base64.b64encode(image_data).decode("ascii"),
        }

        with (
            patch.object(api, "_authenticate"),
            patch("salasblog2.blogger_api.Path") as MockPath,
        ):
            original_Path = Path

            def path_factory(*args):
                if args == ("/data",):
                    return tmp_path / "data"
                return original_Path(*args)

            MockPath.side_effect = path_factory

            api.metaweblog_newMediaObject("1", "user", "pass", struct)

        source_files = list((tmp_path / "static" / "images" / "uploads").glob("*.png"))
        assert source_files[0].read_bytes() == image_data

    def test_volume_backup_failure_raises_fault(self, tmp_path):
        """Volume backup failure raises an XML-RPC Fault when the volume
        (production-like) is present."""
        api = _make_api(tmp_path)
        struct = {"name": "img.png", "type": "image/png", "bits": b"data"}

        volume_root = tmp_path / "data"
        volume_root.mkdir()
        original_Path = Path

        def path_factory(*args):
            if args == ("/data",):
                return volume_root
            return original_Path(*args)

        with (
            patch.object(api, "_authenticate"),
            patch("salasblog2.blogger_api.Path", side_effect=path_factory),
            patch(
                "salasblog2.blogger_api.shutil.copy2",
                side_effect=[None, OSError("no volume")],
            ),
        ):
            with pytest.raises(Fault):
                api.metaweblog_newMediaObject("1", "user", "pass", struct)

    def test_media_backup_skipped_without_volume(self, tmp_path):
        """Regression: when /data doesn't exist (local dev), media backup is a
        silent no-op and the upload still succeeds, same as generator.py/
        raindrop.py's own /data/content volume-detection guards."""
        api = _make_api(tmp_path)
        struct = {"name": "img.png", "type": "image/png", "bits": b"data"}

        with patch.object(api, "_authenticate"):
            result = api.metaweblog_newMediaObject("1", "user", "pass", struct)

        assert "url" in result


class TestGetCategories:
    """Regression: metaweblog_getCategories was a hardcoded ["General", "Technology"]
    stub, unrelated to this blog's actual tags (F42 built it around free-form tags,
    not a fixed taxonomy) — MarsEdit's category picker always showed the same two
    values no matter what tags the blog actually used."""

    def test_returns_blog_tags(self, tmp_path):
        from salasblog2.utils import load_curated_tags

        tag_hints_dir = tmp_path / "02-doc"
        tag_hints_dir.mkdir()
        tag_hints_path = tag_hints_dir / "tag-hints.md"
        tag_hints_path.write_text(
            "# Curated Tags\n\ntechnology\nai\npersonal\n", encoding="utf-8"
        )

        api = _make_api(tmp_path)
        with patch.object(api, "_authenticate"):
            categories = api.metaweblog_getCategories("1", "user", "pass")

        assert [c["description"] for c in categories] == load_curated_tags(
            tag_hints_path
        )
        assert all(c["htmlUrl"].startswith("/tags/") for c in categories)


class TestGetPostLinkAndTags:
    """Regression: blogger_getPost/getRecentPosts never returned a `link` field
    (MarsEdit's post permalink) and the MetaWeblog wrappers hardcoded
    `categories: ["General"]` instead of the post's real tags."""

    def test_get_post_includes_link_and_tags(self, tmp_path):
        api = _make_api(tmp_path)
        post_file = api.blog_dir / "my-post.md"
        post_file.write_text(
            "---\ntitle: My Post\ndate: '2026-09-09'\ntags: [ai, robotics]\n---\n\nBody"
        )

        with patch.object(api, "_authenticate"):
            post = api.blogger_getPost("1", "my-post.md", "user", "pass")

        assert post["link"] == "/blog/my-post.html"
        assert post["tags"] == ["ai", "robotics"]

    def test_metaweblog_get_post_uses_real_tags_as_categories(self, tmp_path):
        api = _make_api(tmp_path)
        post_file = api.blog_dir / "my-post.md"
        post_file.write_text(
            "---\ntitle: My Post\ndate: '2026-09-09'\ntags: [ai, robotics]\n---\n\nBody"
        )

        with patch.object(api, "_authenticate"):
            post = api.metaweblog_getPost("my-post.md", "user", "pass")

        assert post["categories"] == ["ai", "robotics"]
        assert post["link"] == "/blog/my-post.html"

    def test_get_recent_posts_includes_link_and_tags(self, tmp_path):
        api = _make_api(tmp_path)
        post_file = api.blog_dir / "my-post.md"
        post_file.write_text(
            "---\ntitle: My Post\ndate: '2026-09-09'\ntags: [ai]\n---\n\nBody"
        )

        with patch.object(api, "_authenticate"):
            posts = api.blogger_getRecentPosts("1", "1", "user", "pass", 10)

        assert posts[0]["link"] == "/blog/my-post.html"
        assert posts[0]["tags"] == ["ai"]
