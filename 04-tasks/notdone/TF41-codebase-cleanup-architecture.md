# TF41 — Codebase Cleanup and Architectural Consistency
**Date Created:** 2026-04-18

## TF41.0 — Audit and fix underscore prefixes on private names
**Status**: not done

**Description**: Search all `src/salasblog2/*.py` for names starting with `_` (methods, functions, module-level variables). Remove the underscore prefix from each. Update all call sites. Pay attention to `server.py` (`_load_yaml_config`, `_cfg`, `_safe_resolve`, `_regenerate_in_background`, `_build_stats_for_period`, `_STATS_PLACEHOLDER`, `_stats_cache_job`, `_generate_and_save`), `draft_generator.py` (`_load_model`, `_ascii`), `generator.py` (`_yaml_cfg`, `_yaml_count`), and `propose.py`. Exceptions: Python dunder methods (`__init__` etc.) are fine.

## TF41.1 — Add/fix file headers in all Python source files
**Status**: not done

**Description**: Each `src/salasblog2/*.py` file must have: (1) `#!/usr/bin/env python3` shebang, (2) `# <filename> — <one-line description>` comment, (3) `# Author: Pito Salas and Claude Code`, (4) `# Open Source Under MIT license`. Audit every file and add or correct missing lines. Files to check: `server.py`, `generator.py`, `raindrop.py`, `draft_generator.py`, `propose.py`, `stats.py`, `scheduler.py`, `utils.py`, `visitor_type.py`, `blogger_api.py`.

## TF41.2 — Extract inline JavaScript from HTML templates to .js files
**Status**: not done

**Description**: Move all `<script>` block content from `templates/admin.html` and `templates/stats_page.html` into appropriately named files under `static/js/` (e.g. `admin.js`). Replace inline `<script>` blocks with `<script src="/static/js/admin.js">` etc. Jinja2 template variables referenced from JS (e.g. `{{ action_url }}`) must be moved to `data-*` attributes on DOM elements or a small inline `<script>` block that only sets config variables — no logic in inline scripts. **Do not touch `new_post.html`/`edit_post.html`** — F42 (TF42.3) unifies and rewrites these into a shared editor template with its own JS separation as part of that work; extracting their current inline JS here would just be redone or discarded by F42.

## TF41.3 — Remove HTML string literals from Python files
**Status**: not done

**Description**: Audit `server.py` for any multi-line HTML strings or f-strings that produce HTML (e.g. `_STATS_PLACEHOLDER`, any `HTMLResponse(content="<html>...")` calls). Move HTML fragments to template files and render via Jinja2. Note: the XML-RPC response builders (`create_xmlrpc_response()`, `create_xmlrpc_fault_with_code()`) that were previously the main offender here are being replaced by F44 with `xmlrpc.client.dumps()` calls, which are not HTML/string-literal-building code — if F44 has landed by the time this task runs, there should be little or nothing left to do for XML-RPC specifically; verify rather than assume, and only extract what still exists.

## TF41.4 — Audit and reduce JavaScript in admin.js
**Status**: not done

**Description**: After TF41.2, review the extracted `admin.js`. Identify and remove: (a) `loadStats()` / `selectStatsPeriod()` — already deleted but verify no remnants; (b) dead `publishDraft()` function if the direct-publish flow was replaced by "Edit & Post"; (c) duplicate status/progress HTML builders — consolidate into shared helpers; (d) any polling loops that can be eliminated now that stats and propose lists are pre-generated. Target: reduce admin.js by at least 30% in line count.

## TF41.5 — Pre-generate propose lists as static files
**Status**: not done

**Description**: Apply the stats-page pattern to the propose tab. Add `generate_propose_cache()` that writes `output/admin-propose-drops.json` and `output/admin-propose-posts.json` every N minutes (config.yaml: `propose.cache_refresh_minutes`). `GET /api/propose` and `GET /api/propose-drops` serve those files directly — no directory scan on the request path. Background job refreshes the files on a schedule. This makes the Propose tab load instantly instead of scanning 2800 posts per click.

## TF41.6 — Pre-generate draft list as static file
**Status**: not done

**Description**: Apply the same pattern to the Drafts tab. Add `generate_drafts_cache()` that writes `output/admin-drafts.json` (list of draft metadata + body). `GET /api/drafts` serves this file. The cache is invalidated (regenerated immediately) whenever a draft is created, published, or deleted — so freshness is guaranteed for write operations while reads are instant.

## TF41.7 — Review all GET routes for minimal-work compliance
**Status**: not done

**Description**: Audit every `@app.get(...)` route in `server.py`. For each one that does more than read a file: document what work it does, decide if it can serve a pre-generated file instead, and either implement that or add a comment explaining why live computation is necessary. Acceptable live-computation GETs: auth checks, health checks, truly dynamic content. Everything else should be a file read.

## TF41.8 — Architecture review: module decomposition
**Status**: not done

**Description**: `server.py` is ~1850 lines and handles routing, authentication, content loading, draft management, sync orchestration, stats generation, XML-RPC, and file serving. Map out every responsibility it currently owns. Identify which groups of responsibilities belong in separate modules (e.g. `draft_api.py`, `content_api.py`, `file_server.py`, `xmlrpc_handler.py`). Write findings to `process/arch-review.md` — no code changes in this task.

## TF41.9 — Architecture review: scheduler and background work patterns
**Status**: not done

**Description**: The scheduler drives git sync, raindrop sync, and stats cache refresh. The admin UI also triggers all three on demand. Assess: (a) is the `schedule` library the right tool or would `asyncio` periodic tasks be simpler? (b) is there a clear ownership boundary between scheduler-triggered and admin-triggered work, or do they duplicate logic? (c) could the pre-generation pattern (TF41.5, TF41.6) replace the scheduler for some jobs? Write findings to `process/arch-review.md`.

## TF41.10 — Architecture review: XML-RPC / Blogger API implementation
**Status**: not done

**Description**: Whether to keep XML-RPC/`blogger_api.py` has already been decided — F44 fixes it (replacing hand-rolled parsing/response-building with stdlib `xmlrpc` marshalling) specifically to restore MarsEdit support, rather than removing it. Record that decision and its rationale in `process/arch-review.md` instead of re-assessing "should we remove it." What's still worth assessing here: given F44's fix, can the *implementation* be simplified further (e.g. fewer supported MetaWeblog/Blogger methods than currently implemented, if some are unused by MarsEdit in practice)?

## TF41.11 — Architecture review: volume-first content architecture
**Status**: not done

**Description**: Content lives in three places: `/data/content` (persistent volume), `/app/content` (git/Docker image), and `output/` (generated static site). Assess: (a) does the three-way sync add more complexity than it solves? (b) are there race conditions or consistency gaps between the three? (c) would a simpler model (volume only, no `/app/content` copy) work given the current deployment on fly.io? Write findings to `process/arch-review.md`.

## TF41.12 — Architecture review: YAGNI and speculative abstractions
**Status**: not done

**Description**: Scan the codebase for abstractions, config options, or code paths that exist but are not exercised by any current requirement or test. Candidates: `mount_static_files()` (disabled at startup), `_check_single_instance()` (fly CLI dependency), `bidirectional_sync` (vs simpler one-way), multiple `content_type` branches in shared helpers that only ever receive `'blog'`. List each finding with a delete/keep recommendation in `process/arch-review.md`.
