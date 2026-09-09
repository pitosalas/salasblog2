# Current State — salasblog2
_Last updated: 2026-09-08_

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

### Admin panel
Single-page app at `/admin`. Tabs: Stats, Propose, Drafts, **All Posts** (F42), Generate, Scheduler, Data Sync, Pages Sync, Raindrop, Emergency. Most admin JavaScript is still inline in `templates/admin.html` — extracting it is F41 TF41.2 (explicitly excludes `post_editor.html`, which already got its own JS separation as part of F42).

---

## Open

**F44 — Fix the MetaWeblog/XML-RPC Implementation**: 5 of 6 tasks done (see `04-tasks/notdone/TF44-fix-metaweblog-xmlrpc.md`). **TF44.4** (manual MarsEdit verification) is in progress: refresh, edit, and image upload confirmed working against production. Root cause of refresh failing was MarsEdit's endpoint being configured as `http://` — Fly's `force_https` redirect turns a POST into a GET on 301, dropping the XML-RPC body; fixed by pointing MarsEdit at `https://salas.com/xmlrpc` (client-side config, not a server bug). Still to verify: create, delete, and a title/content with `&`/`<`/`>`.

Manual testing also surfaced several real bugs, now fixed and committed (see `04-tasks/chores.md`): `metaweblog_getCategories` hardcoded stub → now returns `BLOG_TAGS`; missing `link`/real-tags-as-`categories` fields on `getPost`/`getRecentPosts`; excerpt truncation breaking markdown formatting (mid-token cuts and collapsed-newline block markers both printed raw markdown/HTML characters instead of rendering); home page missing the "Read more" link on truncated excerpts.

**Fixed**: `BloggerAPI` now resolves its content directory the same volume-first way `get_content_directory()`/`SiteGenerator` already do (`04-tasks/chores.md`), removing the likely cause of a user-reported bug: MarsEdit showing a stale post even after refresh. `_backup_to_volume()`/`_delete_from_volume()` deleted entirely — writes/deletes go straight to the volume-resolved `blog_dir`, so there's no second copy to fall out of sync.

**This session's commits (categories/link/excerpt/Read-more fixes, volume-first BloggerAPI, full style-guide pass, all literate docs regenerated) are pushed to GitHub but not yet deployed** — see Deployment section below.

**Full-repo style-guide pass done this session** (`04-tasks/chores.md`): relative imports fixed to absolute throughout (`generator.py`, `raindrop.py`, `cli.py`, `scheduler.py`), missing file headers added to 6 modules, a real `UnboundLocalError` bug fixed in `scripts/debug_content_dirs.py` (shadowed `Path` import), a genuine test-coverage gap fixed in `tests/deployment/test_checksum_sync.py`, and the whole repo is now `ruff check`/`ruff format --check` clean (was 92 pre-existing violations at session start). All `01-literate/*.md` docs regenerated from scratch in dependency order.

**Other open features** (`03-features/notdone/`, no dependency on each other or on F44):

| Feature | Description | Priority |
|---------|-------------|----------|
| F29 | Extract reusable utilities from raindrop.py | Medium |
| F30 | Code quality improvements in raindrop.py | Low |
| F33 | Fix web search (item.category → item.type bug + raindrop indexing) | Medium |
| F35 | Fix admin sync button after GIT_TOKEN rotation | Medium |
| F41 | Codebase cleanup and architecture review | Medium |

F33 TF33.0 (the category/type field name fix in `script.js`) is already done. F33 TF33.1–TF33.3 (raindrop indexing, content truncation, tests) remain.

F41 was reconciled this session against F42 and F44 (TF41.2, TF41.3, TF41.10 reworded so they don't redo or contradict work those two features already did) — see `04-tasks/notdone/TF41-codebase-cleanup-architecture.md`. Recommended order if picking F41 up: after F44, since TF41.3/TF41.10 assume F44 has landed.

**Deferred**: F43 (token-authenticated REST API for posting from a phone, `03-features/deferred/`) — parked, not abandoned, independent of everything else.

---

## Test status

```
537 passed, 11 skipped, 1 failed, 3 warnings
```

The 1 failure (`test_raindrop.py::TestRaindropDownloader::test_load_cache_from_env`) is pre-existing and unrelated to this session's work (confirmed to fail identically on `main` before any of this session's changes) — raindrop.py cache-loading test isolation issue, F29/F30 territory. Skipped tests require a live server (`https://salasblog2.fly.dev`).

---

## Deployment

```bash
make deploy          # build and deploy to fly.io (uv run bg deploy → fly deploy)
fly logs              # tail live logs
fly ssh console        # shell into running container
```

Deployed app: https://salasblog2.fly.dev

**Startup sequence**: `startup.sh` runs `git checkout -f -B main origin/main` (overwrites `/app` with GitHub HEAD), then starts uvicorn. **Code changes must be committed and pushed to GitHub before `make deploy`**, or they will be silently overwritten at container startup — confirmed the hard way this session: three deploys in a row kept serving pre-session code because nothing had been pushed, verified via `fly ssh console` showing the running container on commit `e909c27` (pre-session HEAD) despite fresh deploy timestamps.

---

## Known rough edges

- `server.py` at 2221 lines is the biggest structural problem — nearly everything lives there. F41 TF41.8 covers decomposition.
- Admin JS is still mostly inline in `admin.html` — hard to maintain, not testable. F41 TF41.2.
- The three-way content sync (`/data` ↔ `/app` ↔ `output/`) adds operational complexity, and is also why deploys silently lose uncommitted work (see Deployment above). F41 TF41.11.
- `mount_static_files()` is defined but intentionally disabled at startup (replaced by custom endpoints) — dead code. F41 TF41.12 candidate.
- `_check_single_instance()` depends on the `fly` CLI being present in the container — fragile.
- `raindrop_post.html` has no admin edit flow (raindrops are Raindrop.io-synced, not manually authored) — only delete was added in F42; this is intentional, not a gap, but worth knowing if someone expects an edit button there.
