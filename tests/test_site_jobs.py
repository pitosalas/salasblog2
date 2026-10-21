#!/usr/bin/env python3
# test_site_jobs — Tests for running site generation in a child process (F56)
# Author: Pito Salas and Claude Code
# Version: 2
# Created: 2026-10-20
# Updated: 2026-10-20
# Open Source Under MIT license

import sys
import threading
import time
from argparse import Namespace
from unittest.mock import patch

import pytest
import schedule

from salasblog2 import cli, server, site_jobs


def stub_command(code: str):
    """Make run_generation run `python -c code` instead of the bg CLI."""
    return patch.object(
        site_jobs, "generation_command", lambda args: [sys.executable, "-c", code]
    )


class TestRunGeneration:
    def test_command_runs_bg_cli_with_this_interpreter(self):
        assert site_jobs.generation_command(["regen-post", "a.md", "blog"]) == [
            sys.executable,
            "-m",
            "salasblog2.cli",
            "regen-post",
            "a.md",
            "blog",
        ]

    def test_success_returns_quietly(self):
        with stub_command("pass"):
            site_jobs.run_generation(["generate"])

    def test_failure_raises_with_stderr(self):
        with (
            stub_command("import sys; sys.exit('render broke')"),
            pytest.raises(RuntimeError, match="render broke"),
        ):
            site_jobs.run_generation(["generate"])

    def test_concurrent_runs_never_overlap(self, tmp_path):
        """Each child appends start/end marks; with the lock they never interleave."""
        log = tmp_path / "log"
        code = (
            f"import time; f = open(r'{log}', 'a'); f.write('S'); f.flush(); "
            "time.sleep(0.2); f.write('E'); f.close()"
        )
        with stub_command(code):
            threads = [
                threading.Thread(target=site_jobs.run_generation, args=(["generate"],))
                for _ in range(2)
            ]
            for thread in threads:
                thread.start()
                time.sleep(0.05)
            for thread in threads:
                thread.join()
        assert log.read_text() == "SESE"


class TestRegenCommands:
    def test_regen_post_calls_incremental_regeneration(self):
        with patch.object(cli, "SiteGenerator") as generator:
            cli.cmd_regen_post(Namespace(filename="a.md", type="blog"))
        generator.return_value.incremental_regenerate_post.assert_called_once_with(
            "a.md", "blog"
        )

    def test_regen_deleted_calls_deletion_regeneration(self):
        with patch.object(cli, "SiteGenerator") as generator:
            cli.cmd_regen_deleted(Namespace(filename="a.md", type="pages"))
        generator.return_value.incremental_regenerate_after_deletion.assert_called_once_with(
            "a.md", "pages"
        )

    def test_regen_post_parses_from_command_line(self):
        with (
            patch.object(sys, "argv", ["bg", "regen-post", "a.md", "raindrops"]),
            patch.object(cli, "SiteGenerator") as generator,
        ):
            cli.main()
        generator.return_value.incremental_regenerate_post.assert_called_once_with(
            "a.md", "raindrops"
        )


class TestServerUsesChildProcess:
    def test_save_regeneration_runs_regen_post(self):
        with patch.object(server, "run_generation") as generation:
            server._regenerate_in_background("a.md", "blog")
        generation.assert_called_once_with(["regen-post", "a.md", "blog"])

    def test_delete_regeneration_runs_regen_deleted(self):
        with patch.object(server, "run_generation") as generation:
            server.regenerate_after_deletion_in_background("a.md", "raindrops")
        generation.assert_called_once_with(["regen-deleted", "a.md", "raindrops"])

    def test_record_generation_counts_runs(self):
        before = server._generation_count
        with patch.object(server, "run_generation"):
            server.record_generation(["generate"])
        assert server._generation_count == before + 1
        assert server._last_generation_time is not None


@pytest.mark.asyncio
async def test_lifespan_schedules_no_posts_index_rescan():
    """F56: the posts index is refreshed by writes, not every five minutes."""
    schedule.clear()
    with (
        patch.object(server, "setup_logging"),
        patch.object(server, "validate_environment_and_setup"),
        patch.object(server, "_check_single_instance"),
        patch.object(server, "get_scheduler"),
        patch.object(server, "generate_stats_cache"),
        patch.object(server, "generate_posts_index_cache"),
    ):
        async with server.lifespan(server.app):
            job_names = [job.job_func.func.__name__ for job in schedule.jobs]
    schedule.clear()
    assert "posts_index_cache_job" not in job_names
    assert job_names == ["_stats_cache_job"]
