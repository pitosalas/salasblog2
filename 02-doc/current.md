# Current State — salasblog2
_Last updated: 2026-09-11_

---

## What this project is

A personal blog platform for Pito Salas deployed on fly.io. It is a FastAPI server that:
- Serves a **pre-generated static site** (Hugo-style markdown → HTML, done by `generator.py`)
- Provides an **admin panel** (`/admin`) for managing posts, pages, drafts, raindrops, and site regeneration
- Syncs bookmarks from **Raindrop.io** (link blog at `/raindrops/`)
- Uses **Claude AI** to auto-generate blog draft posts from popular raindrop link posts
- Backs content up to **GitHub** on a schedule via git push
- Stores persistent content on a **fly.io volume** at `/data/content/`
- Supports **MarsEdit** (XML-RPC/MetaWeblog) as an alternate authoring path (F44)

The server is the product — it IS the blog. There is no separate CMS.

---

## Repository layout

```
salasblog2/
├── src/salasblog2/         # Python package (FastAPI server + site generator)
│   ├── server.py           # 2221 lines — main FastAPI app, ALL routes, too much logic
│   ├── generator.py        # 782 lines — static site generator
│   ├── blogger_api.py      # 714 lines — XML-RPC / MarsEdit / MetaWeblog API
│   ├── utils.py            # 449 lines — markdown processing, shared helpers
│   ├── scheduler.py        # 399 lines — background job scheduler (git sync, raindrop sync)
│   ├── raindrop.py         # 350 lines — Raindrop.io API client
│   ├── stats.py            # 165 lines — visit counter (file-backed)
│   ├── propose.py          # 151 lines — scoring/filtering for propose tab
│   ├── cli.py              # 126 lines — CLI entry point
│   ├── draft_generator.py  # 120 lines — Claude API draft generation
│   └── visitor_type.py     # 117 lines — bot/human/search classifier
├── templates/              # Jinja2 HTML templates
│   ├── admin.html          # Main admin SPA (~940 lines, heavy inline JS)
│   ├── post_editor.html    # Unified create/edit for posts and pages (F42; replaced new_post.html/edit_post.html)
│   ├── stats_page.html     # Pre-generated stats page (served via iframe)
│   └── ...                 # blog_post.html, home.html, raindrop_post.html, page.html, etc.
├── static/js/
│   ├── script.js           # Main blog JS (search)
│   ├── admin-delete.js     # Shared delete handlers for post/page/raindrop (F42), loaded via base.html
│   └── admin-functions.js  # (admin logic is still mostly inline in admin.html)
├── content/                # Source markdown (blog/, raindrops/, pages/) — local dev only; /data/content/ is prod source of truth
├── output/                 # Generated static site (served directly), incl. admin-stats.html and admin-posts-index.json caches
├── config.yaml             # Runtime parameters (see below)
├── 03-features/{notdone,done,deferred}/   # FNN-<slug>.md feature files
├── 04-tasks/{notdone,done,deferred}/      # TFNN-<slug>.md task files
└── tests/                  # 501 passing, 2 skipped, 1 pre-existing unrelated failure (2026-09-08)
```

---

## config.yaml

```yaml
stats:
  cache_refresh_seconds: 60

posts_index:
  cache_refresh_seconds: 300

home:
  posts_count: 5

scheduler:
  git_sync_hours: 6.0
  raindrop_sync_hours: 2.0

propose:
  pool_size: 50
  count: 5
  drops_min_age_months: 0
  drops_min_visits: 5

drafts:
  claude_model: claude-sonnet-4-6
```

---

## Key architectural decisions (current)

### Static pre-generation pattern
The preferred pattern for any data that changes infrequently is:
1. Pre-generate a JSON or HTML file in `output/` on a background schedule
2. Serve that file directly on GET — zero computation
3. Invalidate/regenerate immediately on writes

Applied to: **stats page** (`output/admin-stats.html`, refreshed every 60s) and **admin posts index** (`output/admin-posts-index.json`, refreshed every 5 min + after every create/edit/delete, F42).
**Not yet applied to**: propose lists, draft list (F41 TF41.5/TF41.6).

### Non-blocking I/O
All blocking operations (Claude API, URL fetch, directory scans, site generation, XML-RPC post regeneration as of F44) run via `BackgroundTasks` or `loop.run_in_executor(None, fn)` to avoid blocking the FastAPI event loop.

### Post/page editing (unified, F42)
`templates/post_editor.html` handles both create and edit, for both blog posts and pages, via an `is_edit` context flag — replacing the previously hand-duplicated `new_post.html`/`edit_post.html`. Includes: category field, free-form comma-separated tags (with `<datalist>` suggestions from `BLOG_TAGS`, not a hard vocabulary), EasyMDE autosave + `beforeunload` unsaved-changes guard, inline preview (via `/admin/preview-markdown`, no more round-trip to a new tab), and mtime-based concurrency conflict detection (`409` on stale save). Delete is real (`/admin/delete-post`, `/admin/delete-page`, `/admin/delete-raindrop`), backed by `static/js/admin-delete.js` loaded globally via `base.html`.

### Draft workflow
1. Propose tab → Popular Link Posts → "Generate Draft" button
2. POST `/api/generate-draft` → calls Claude API in executor → saves `draft-<name>.md` to `/data/content/blog/`
3. Drafts tab shows all `draft-*.md` files with full body text
4. "Edit & Post" → `/admin/repost/<filename>` → opens `post_editor.html` pre-filled with draft content
5. User edits and clicks "Create Post" → new published post created, draft file remains (user deletes it)

Generated drafts start with `Originally Posted on: [url](url)` and a 50–75 word Claude paragraph.

### MarsEdit / XML-RPC (F44)
`/xmlrpc` uses Python's stdlib `xmlrpc.client.loads()`/`dumps()` for marshalling (not hand-rolled `ElementTree`), so it correctly handles `dateTime.iso8601`, `<array>`, `<base64>` (as `xmlrpc.client.Binary`, unwrapped to plain `bytes` at the parsing boundary), and properly escapes response content. Response `Content-Type` must be left to `media_type="text/xml"` alone — an explicit `headers={"Content-Type": "text/xml"}` suppresses Starlette's automatic `; charset=utf-8`, which broke MarsEdit on any post with non-ASCII characters. Kept deliberately (not removed) to support MarsEdit alongside the web admin UI — see F44 for the "should we even keep XML-RPC" question, already answered.

### Content storage (volume-first)
- `/data/content/` — persistent fly.io volume, source of truth at runtime
- `/app/content/` — baked into Docker image from git; overwritten by `startup.sh`'s `git checkout -f -B main origin/main` at container boot
- `output/` — generated static site, regenerated from `/data/content/` at startup and on demand

This three-way architecture is identified as a complexity target in F41 TF41.11.

**Sync is one-way**: `/data/content` is seeded from git only once, at first deploy (`startup.sh`, if `/data/content` doesn't exist yet or is empty). After that, nothing ever pushes local/GitHub content back into the volume, except `pages/` (rsync'd on every boot). The scheduled `sync_to_github` job only goes the other direction: volume → `/app/content` → GitHub, as a backup. Confirmed the hard way (2026-09-10/11): every tag-cleanup batch done against local `content/blog/` before that point never reached the live site, and production's real content had itself drifted from git for unrelated reasons (manual admin edits). **Any content change meant for the live site must be made against `/data/content` directly** (via `fly ssh`, or the live admin UI) — editing local `content/` and pushing to GitHub does not affect production.

### Admin panel
Single-page app at `/admin`. Tabs: Stats, Propose, Drafts, **All Posts** (F42), Generate, Scheduler, Data Sync, Pages Sync, Raindrop, Emergency. Most admin JavaScript is still inline in `templates/admin.html` — extracting it is F41 TF41.2 (explicitly excludes `post_editor.html`, which already got its own JS separation as part of F42).

---

## Open

**F44 — Fix the MetaWeblog/XML-RPC Implementation**: 5 of 6 tasks done (see `04-tasks/notdone/TF44-fix-metaweblog-xmlrpc.md`). **TF44.4** (manual MarsEdit verification) still in progress: refresh, edit, and image upload confirmed working against production; create, delete, and a title/content with `&`/`<`/`>` still need verification. Full history of what was found/fixed getting here is in `02-doc/history.md`.

**F45 — Tag Suggestion Picklist for Post Editor**: done, confirmed working live by the user (`03-features/done/F45-tag-suggestion-picklist.md`). The post editor's Tags field offers a searchable picklist backed by real tag-frequency data (`output/top-tags.json`) merged with the curated vocabulary — now sourced from `02-doc/tag-hints.md` (the standalone `BLOG_TAGS` constant was consolidated away this session; see F46 below).

**F46 — Automated Tag Cleanup for Full Blog Corpus**: `04-tasks/notdone/TF46-automated-tag-cleanup.md`, TF46.0-TF46.5 done, TF46.6 (autonomous batch run) in progress, TF46.7-TF46.10 (curated-vocabulary restriction, one unified curated list, 3+ recurrence threshold for Proposed Tags, no-fit posts no longer re-selected every batch) done. Batches 7-12 (3,000 posts, 2004-2023 archive era) run for real against **production's `/data/content/blog` volume** via `fly ssh` — earlier batches (1-6, before this session) only ever touched the local repo and never reached the live site (see the architecture note above). ~545 posts remained after batch 12 (the self-tracking selection order still has 2013-2023 and then 2023-2026 ahead of it). Full batch-by-batch numbers and the three design corrections that got here are in `02-doc/history.md`.

`02-doc/tag-hints.md`'s **Proposed Tags** queue currently holds candidates awaiting the user's approval to promote into the Curated Tags list (or reject): `blogbridge`, `blogging`, `etech`, `folksonomy`, `gmail`, `java`, `microsoft`, `orkut`, `podcasting`, `red-sox`, `security`, `spam`, `tivo`, `web2.0`, `agile`, `geek-dinner`, `gnomedex`, `howard-stern`, `opml`, `social-networking`, `games`, `theatre`, `css`, `flask`, `git`, `kubernetes`, `raspberry-pi`, `startup`, `woodworking`, `excel`, `graphql`, `portfolio`, `postgres`, `sqlite`. None of these are applied to any post until promoted.

**F47 — Console Theme Visual Refresh**: new, `03-features/notdone/F47-console-theme-refresh.md` / `04-tasks/notdone/TF47-*.md` (13 tasks). Plan written and stopped for approval per the process gate — no code written yet. Visual-only refresh of the 9 live public-facing templates (home/blog/link-blog/pages/tag/404) to an externally-designed "Console" theme (monospace chrome, hairline rules, one amber accent, dark/light toggle); `admin.html`/`admin_login.html`/`post_editor.html`/`stats_page.html` explicitly out of scope (standalone, Bootstrap, no design reference given). To be done on a dedicated branch (`feature/f47-console-theme`), not this repo's usual direct-to-`main` workflow, per the user's request — merge-back is its own final task, gated on a full visual QA pass.

**F35 — Fix admin sync button after GIT_TOKEN rotation**: the immediate symptom is fixed — the production `GIT_TOKEN` secret was found to be genuinely invalid (not just stale-in-container as originally hypothesized), the user rotated it via `fly secrets set`, and `sync_to_github()` is now confirmed working end-to-end. The actual code fix this feature describes (reconstruct the git remote URL from the env var at sync time, so a *future* rotation doesn't require a restart) is still not implemented — feature stays open.

**Other open features** (`03-features/notdone/`, no dependency on each other or on F44):

| Feature | Description | Priority |
|---------|-------------|----------|
| F29 | Extract reusable utilities from raindrop.py | Medium |
| F30 | Code quality improvements in raindrop.py | Low |
| F33 | Fix web search (item.category → item.type bug + raindrop indexing) | Medium |
| F41 | Codebase cleanup and architecture review | Medium |

F33 TF33.0 (the category/type field name fix in `script.js`) is already done. F33 TF33.1–TF33.3 (raindrop indexing, content truncation, tests) remain.

F41 was reconciled against F42 and F44 (TF41.2, TF41.3, TF41.10 reworded so they don't redo or contradict work those two features already did) — see `04-tasks/notdone/TF41-codebase-cleanup-architecture.md`. Recommended order if picking F41 up: after F44, since TF41.3/TF41.10 assume F44 has landed.

**Open issues** (`05-issues/open/`, found during literate-doc regeneration, not yet fixed): I01 (incremental regeneration drops content types from search/home), I02 (VisitCounter read/write race, no cross-process lock), I03 (scheduler.py's dead startup-job code).

**Deferred**: F43 (token-authenticated REST API for posting from a phone, `03-features/deferred/`) — parked, not abandoned, independent of everything else.

---

## Test status

```
596 passed, 11 skipped, 3 warnings
```

No failures as of 2026-09-11 (the previously-noted `test_raindrop.py::TestRaindropDownloader::test_load_cache_from_env` failure is not currently reproducing). Skipped tests require a live server (`https://salasblog2.fly.dev`).

---

## Deployment

```bash
make deploy          # build and deploy to fly.io (uv run bg deploy → fly deploy)
fly logs              # tail live logs
fly ssh console        # shell into running container
```

Deployed app: https://salasblog2.fly.dev

**Startup sequence**: `startup.sh` runs `git checkout -f -B main origin/main` (overwrites `/app` with GitHub HEAD), then starts uvicorn. **Code changes must be committed and pushed to GitHub before `make deploy`**, or they will be silently overwritten at container startup — confirmed the hard way in an earlier session: three deploys in a row kept serving pre-session code because nothing had been pushed, verified via `fly ssh console` showing the running container on commit `e909c27` (pre-session HEAD) despite fresh deploy timestamps.

**`GIT_TOKEN` rotated and confirmed working (2026-09-11)** — see F35 above. `sync_to_github()` (production `/data/content` → GitHub backup) verified working end-to-end across six batch runs this session. To sync `/app`'s git checkout on a *running* container without a full redeploy (e.g. to pick up a doc/content-adjacent change without restarting the app): `fly ssh console -C "sh -c 'cd /app && git fetch --depth 1 origin main && git checkout -f -B main origin/main'"`.

---

## Known rough edges

- `server.py` at 2221 lines is the biggest structural problem — nearly everything lives there. F41 TF41.8 covers decomposition.
- Admin JS is still mostly inline in `admin.html` — hard to maintain, not testable. F41 TF41.2.
- The three-way content sync (`/data` ↔ `/app` ↔ `output/`) adds operational complexity, and is also why deploys silently lose uncommitted work (see Deployment above). F41 TF41.11.
- `mount_static_files()` is defined but intentionally disabled at startup (replaced by custom endpoints) — dead code. F41 TF41.12 candidate.
- `_check_single_instance()` depends on the `fly` CLI being present in the container — fragile.
- `raindrop_post.html` has no admin edit flow (raindrops are Raindrop.io-synced, not manually authored) — only delete was added in F42; this is intentional, not a gap, but worth knowing if someone expects an edit button there.
- `templates/admin_new.html` is dead code — extends `base.html`, but no route in `server.py` renders it (found while scoping F47). Its own body has a stub comment admitting it's incomplete. Deletion candidate for a future chore.
- `templates/overview.html` is orphaned — rendered to a real file (`output/overview.html`) but not linked from the site's nav, and `generate_overview_as_home()` (the function that would make it the homepage) is never called. Found while scoping F47; not touched.
