# TF22 — Scheduler Git Push Uses fly.toml Branch
**Date Created:** 2026-03-01

## TF22.0 — Fix git push command in scheduler
**Status**: done

**Description**: Fix `_commit_and_push` in `scheduler.py` to use `git push origin HEAD:<branch>` instead of `git push origin <branch>`. This ensures the current local HEAD is pushed to the configured remote branch regardless of which local branch is checked out in the Docker image.

## TF22.1 — Add test for correct push command format
**Status**: done

**Description**: Add a test in `tests/test_scheduler.py` that mocks `subprocess.run` and verifies `_commit_and_push` calls `git push origin HEAD:<branch>` where `<branch>` matches `GIT_BRANCH` env var.

## TF22.2 — Verify GIT_BRANCH env var is documented in deployment notes
**Status**: done

**Description**: Confirm that `fly.toml` `[env]` section has `GIT_BRANCH` set and that the spec documents `GIT_BRANCH` as a required env var for Git sync. Update spec if missing.
