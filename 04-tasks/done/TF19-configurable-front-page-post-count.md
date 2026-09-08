# TF19 — Configurable Front Page Post Count
**Date Created:** 2026-03-01

## TF19.0 — Read HOME_POSTS_COUNT env var in generator
**Status**: done

**Description**: In `generator.py`, read `int(os.environ.get("HOME_POSTS_COUNT", "5"))` and use it instead of the hardcoded `5` when slicing `recent_posts` and `recent_raindrops` for the home page context.

## TF19.1 — Write test
**Status**: done

**Description**: In `tests/test_home_posts_count.py`: set `HOME_POSTS_COUNT=3` via `monkeypatch.setenv`, generate the home page, confirm only 3 posts appear in each section.
