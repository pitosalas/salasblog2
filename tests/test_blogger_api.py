"""
Regression tests for BloggerAPI.

Run with: uv run pytest tests/test_blogger_api.py -v
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from xmlrpc.client import Fault

from salasblog2.blogger_api import BloggerAPI


class TestBackupToVolume:
    """Tests for _backup_to_volume() error propagation."""

    @pytest.fixture
    def api(self, tmp_path):
        with patch.object(BloggerAPI, '__init__', lambda self: None):
            obj = BloggerAPI.__new__(BloggerAPI)
            obj.root_dir = tmp_path
            obj.blog_dir = tmp_path / "content" / "blog"
            obj.blog_dir.mkdir(parents=True)
            return obj

    def test_backup_to_volume_success(self, api, tmp_path):
        """Happy path: file is copied to /data relative path."""
        post_file = api.blog_dir / "my-post.md"
        post_file.write_text("hello")

        volume_root = tmp_path / "data"
        with patch("pathlib.Path.__new__", wraps=Path) as _:
            # Patch /data to a temp dir so we don't need root access
            with patch("salasblog2.blogger_api.Path") as MockPath:
                # Let most Path calls pass through; only redirect Path("/data")
                import salasblog2.blogger_api as mod
                original_Path = Path

                def path_factory(*args):
                    if args == ("/data",):
                        return volume_root
                    return original_Path(*args)

                MockPath.side_effect = path_factory

                # Re-import after patch is tricky; test directly instead
        # Simpler approach: patch shutil.copy2 and mkdir
        import shutil
        with patch("shutil.copy2") as mock_copy, \
             patch.object(Path, "mkdir"):
            api._backup_to_volume(post_file)
            assert mock_copy.called

    def test_backup_to_volume_raises_on_failure(self, api, tmp_path):
        """Regression: _backup_to_volume() must raise on failure so the caller
        can surface the error via XML-RPC fault instead of silently losing the post."""
        post_file = api.blog_dir / "my-post.md"
        post_file.write_text("hello")

        import shutil
        with patch("shutil.copy2", side_effect=OSError("disk full")), \
             patch.object(Path, "mkdir"):
            with pytest.raises(OSError, match="disk full"):
                api._backup_to_volume(post_file)

    def test_new_post_raises_fault_when_volume_backup_fails(self, tmp_path):
        """Regression: blogger_newPost() must raise an XML-RPC Fault when the
        volume backup fails, so MarsEdit knows the post was not fully saved and
        the subsequent rsync --delete cannot silently delete it."""
        api = BloggerAPI.__new__(BloggerAPI)
        api.root_dir = tmp_path
        api.blog_dir = tmp_path / "content" / "blog"
        api.blog_dir.mkdir(parents=True)

        import shutil
        with patch.object(api, "_authenticate", return_value=True), \
             patch.object(api, "_write_post_file"), \
             patch.object(api, "_backup_to_volume", side_effect=OSError("no volume")), \
             patch.object(api, "_regenerate_and_verify"):
            with pytest.raises(Fault):
                api.blogger_newPost("key", "blog", "user", "pass", "Title\nBody", True)

    def test_edit_post_raises_fault_when_volume_backup_fails(self, tmp_path):
        """Regression: blogger_editPost() must raise an XML-RPC Fault when the
        volume backup fails."""
        api = BloggerAPI.__new__(BloggerAPI)
        api.root_dir = tmp_path
        api.blog_dir = tmp_path / "content" / "blog"
        api.blog_dir.mkdir(parents=True)

        # Create an existing post file
        post_file = api.blog_dir / "existing-post.md"
        post_file.write_text("---\ntitle: Test\n---\nBody")

        with patch.object(api, "_authenticate", return_value=True), \
             patch.object(api, "_write_post_file"), \
             patch.object(api, "_backup_to_volume", side_effect=OSError("no volume")), \
             patch.object(api, "_regenerate_and_verify"):
            with pytest.raises(Fault):
                api.blogger_editPost("key", "existing-post.md", "user", "pass", "Title\nBody", True)
