# Feature description for feature F38
## F38 — Fix Slow Post Save: Avoid Loading Unrelated Content on Incremental Regeneration
**Priority**: High
**Date Created:** 2026-04-15
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: `incremental_regenerate_post()` loads all blog posts, all raindrops, and all pages from disk every time any single post is saved, even though only the changed content type is needed. For a blog post edit, raindrops and pages should not be reloaded from disk. Fix by making `incremental_regenerate_post()` only load the content type that changed, and reuse already-loaded data for other types needed by home page and search index (or load them lazily only when the changed type affects them).

## How to Demo
**Setup**: `uv run bg server`, logged in as admin, with a full content directory (thousands of posts) locally or in production.

**Steps**:
1. Edit and save a single blog post via the admin UI.
2. Confirm the save returns quickly (the HTTP response is not blocked on a full regeneration).
3. Confirm the resulting site still reflects the edit (home page, listing page, search index all updated).

**Expected output**: Saving a single post no longer reloads unrelated content types from disk; save latency is significantly reduced with no loss of correctness.
