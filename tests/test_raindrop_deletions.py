#!/usr/bin/env python3
# test_raindrop_deletions — Tests for removing raindrops deleted on Raindrop.io (F53)
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-18
# Updated: 2026-10-18

import json
from unittest.mock import Mock, patch

import pytest

from salasblog2.raindrop import (
    RaindropDownloader,
    local_raindrop_ids,
    select_deleted_raindrops,
)


def page_response(ids, status=200):
    return Mock(
        status_code=status,
        text="err",
        json=lambda: {"items": [{"_id": i} for i in ids]},
    )


@pytest.fixture
def downloader(tmp_path):
    d = RaindropDownloader(access_token="test_token")
    d.drops_dir = tmp_path / "raindrops"
    d.drops_dir.mkdir()
    d.cache_file = tmp_path / ".rd_cache.json"
    return d


def write_drop(drops_dir, name, raindrop_id):
    id_line = f"raindrop_id: '{raindrop_id}'\n" if raindrop_id else ""
    (drops_dir / name).write_text(f"---\ntitle: {name}\n{id_line}---\nBody\n")


class TestFetchAllIds:
    def test_unions_every_page_until_empty(self, downloader):
        pages = [page_response([1, 2]), page_response([3]), page_response([])]
        with patch("salasblog2.raindrop.requests.get", side_effect=pages):
            assert downloader.fetch_all_ids() == {"1", "2", "3"}

    def test_failed_page_raises_instead_of_returning_partial(self, downloader):
        pages = [page_response([1, 2]), page_response([], status=503)]
        with patch("salasblog2.raindrop.requests.get", side_effect=pages):
            with pytest.raises(Exception, match="503"):
                downloader.fetch_all_ids()


class TestSelectDeleted:
    def test_selects_only_ids_missing_remotely(self):
        local = {"keep.md": "1", "gone.md": "2", "no-id.md": None}
        assert select_deleted_raindrops(local, {"1"}) == ["gone.md"]

    def test_local_ids_read_from_frontmatter(self, downloader):
        write_drop(downloader.drops_dir, "a.md", "11")
        write_drop(downloader.drops_dir, "b.md", None)
        assert local_raindrop_ids(downloader.drops_dir) == {"a.md": "11", "b.md": None}


class TestRemoveDeletedRaindrops:
    def test_removes_files_and_forgets_cached_ids(self, downloader):
        write_drop(downloader.drops_dir, "keep.md", "1")
        write_drop(downloader.drops_dir, "gone.md", "2")
        downloader.cache_file.write_text(
            json.dumps({"downloaded": ["1", "2"], "last_sync_timestamp": "t"})
        )
        with patch.object(downloader, "fetch_all_ids", return_value={"1", "9"}):
            assert downloader.remove_deleted_raindrops() == ["gone.md"]
        assert sorted(p.name for p in downloader.drops_dir.iterdir()) == ["keep.md"]
        assert json.loads(downloader.cache_file.read_text())["downloaded"] == ["1"]

    def test_fetch_failure_deletes_nothing(self, downloader):
        write_drop(downloader.drops_dir, "a.md", "1")
        with patch.object(downloader, "fetch_all_ids", side_effect=RuntimeError("503")):
            with pytest.raises(RuntimeError):
                downloader.remove_deleted_raindrops()
        assert (downloader.drops_dir / "a.md").exists()

    def test_empty_remote_refuses_to_delete(self, downloader):
        write_drop(downloader.drops_dir, "a.md", "1")
        with patch.object(downloader, "fetch_all_ids", return_value=set()):
            with pytest.raises(ValueError, match="refusing"):
                downloader.remove_deleted_raindrops()
        assert (downloader.drops_dir / "a.md").exists()
