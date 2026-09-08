# TF39 — Auto-generate Blog Drafts from Popular Link Posts
**Date Created:** 2026-04-18

## TF39.0 — Add get_proposed_drops() to propose.py
**Status**: done

**Description**: In `propose.py`, add `get_proposed_drops(drops_dir, stats_counter, filt: DropFilter)`. Load all raindrop markdown files, parse frontmatter for `date`. Use `stats_counter.get(path)` to get visit count for each raindrop's URL path. Return those older than `filt.min_age_months` with visits >= `filt.min_visits`, sorted by visit_count descending.

## TF39.1 — Create draft_generator.py with Claude API integration
**Status**: done

**Description**: New file `src/salasblog2/draft_generator.py`. Functions `generate_draft_from_drop(raindrop)` and `save_draft(content, filename, blog_dirs)`. Calls Claude API (`claude-sonnet-4-6`), optionally fetches linked URL content, generates one-paragraph post with source link. Frontmatter includes `draft: true`, `author: Claude.ai`, `source_raindrop`, `source_url`.

## TF39.2 — Server endpoints for draft workflow
**Status**: done

**Description**: Added four endpoints in `server.py`: `GET /api/propose-drops`, `POST /api/generate-draft`, `GET /api/drafts`, `POST /api/publish-draft`. All admin-auth-gated.

## TF39.3 — Generator: exclude drafts from blog listings
**Status**: done

**Description**: In `generator.py` `load_posts()`, skip posts where frontmatter `draft` is truthy. Also applied in `propose.py` `get_proposed_posts()`.

## TF39.4 — Admin UI updates
**Status**: done

**Description**: Propose tab now has a "Popular Link Posts" section with Generate Draft buttons. New Drafts tab lists pending drafts with Post buttons.

## TF39.5 — Tests
**Status**: done

**Description**: Tests in `test_propose.py`, `test_draft_generator.py`, `test_drafts_api.py`, and `test_generator.py`. All passing.
