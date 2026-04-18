# Current State — salasblog2
_Last updated: 2026-04-18_

---

## What this project is

A personal blog platform for Pito Salas deployed on fly.io. It is a FastAPI server that:
- Serves a **pre-generated static site** (Hugo-style markdown → HTML, done by `generator.py`)
- Provides an **admin panel** (`/admin`) for managing posts, drafts, raindrops, and site regeneration
- Syncs bookmarks from **Raindrop.io** (link blog at `/raindrops/`)
- Uses **Claude AI** to auto-generate blog draft posts from popular raindrop link posts
- Backs content up to **GitHub** on a schedule via git push
- Stores persistent content on a **fly.io volume** at `/data/content/`

The server is the product — it IS the blog. There is no separate CMS.

---

## Repository layout

```
salasblog2/
├── src/salasblog2/         # Python package (FastAPI server + site generator)
│   ├── server.py           # 1859 lines — main FastAPI app, ALL routes, too much logic
│   ├── generator.py        # 782 lines — static site generator
│   ├── blogger_api.py      # 552 lines — XML-RPC / MarsEdit / MetaWeblog API
│   ├── utils.py            # 449 lines — markdown processing, shared helpers
│   ├── scheduler.py        # 399 lines — background job scheduler (git sync, raindrop sync)
│   ├── raindrop.py         # 350 lines — Raindrop.io API client
│   ├── stats.py            # 165 lines — visit counter (file-backed)
│   ├── propose.py          # 151 lines — scoring/filtering for propose tab
│   ├── cli.py              # 126 lines — CLI entry point
│   ├── draft_generator.py  # 120 lines — Claude API draft generation
│   └── visitor_type.py     # 117 lines — bot/human/search classifier
├── templates/              # Jinja2 HTML templates
│   ├── admin.html          # Main admin SPA (~870 lines, heavy inline JS)
│   ├── stats_page.html     # Pre-generated stats page (served via iframe)
│   ├── new_post.html       # New post editor (EasyMDE)
│   ├── edit_post.html      # Edit post editor (EasyMDE)
│   └── ...                 # blog_post.html, home.html, raindrop_post.html, etc.
├── static/js/
│   ├── script.js           # Main blog JS (search, admin controls on post pages)
│   ├── admin-functions.js  # (exists but admin logic is still mostly in admin.html)
│   └── ...
├── content/                # Source markdown (blog/, raindrops/, pages/)
├── output/                 # Generated static site (served directly)
├── config.yaml             # Runtime parameters (see below)
├── process/
│   ├── features/notdone/   # F29, F30, F33, F35, F41
│   ├── features/done/      # F28–F40
│   ├── tasks/notdone/      # F29, F30, F33, F35, F41
│   └── tasks/done/         # F07–F08, F17–F27, F32, F34, F36–F40
└── tests/                  # 494 passing, 11 skipped (2026-04-18)
```

---

## config.yaml

```yaml
stats:
  cache_refresh_seconds: 60

home:
  posts_count: 5

scheduler:
  git_sync_hours: 6.0
  raindrop_sync_hours: 2.0

propose:
  pool_size: 50
  count: 5
  drops_min_age_months: 3
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

Currently applied to: **stats page** (`output/admin-stats.html`, refreshed every 60s).
**Not yet applied to**: propose lists, draft list. (That is F41 T06/T07.)

### Non-blocking I/O
All blocking operations (Claude API, URL fetch, directory scans, site generation) run in `loop.run_in_executor(None, fn)` to avoid blocking the FastAPI event loop.

### Draft workflow
1. Propose tab → Popular Link Posts → "Generate Draft" button
2. POST `/api/generate-draft` → calls Claude API in executor → saves `draft-<name>.md` to `/data/content/blog/`
3. Drafts tab shows all `draft-*.md` files with full body text
4. "Edit & Post" → `/admin/repost/<filename>` → opens `new_post.html` pre-filled with draft content
5. User edits and clicks "Create Post" → new published post created, draft file remains (user deletes it)

Generated drafts start with `Originally Posted on: [url](url)` and a 50–75 word Claude paragraph.

### Content storage (volume-first)
- `/data/content/` — persistent fly.io volume, source of truth at runtime
- `/app/content/` — baked into Docker image from git; overwritten by startup.sh at deploy
- `output/` — generated static site, regenerated from `/data/content/` at startup and on demand

This three-way architecture is identified as a complexity target in F41 T12.

### Admin panel
Single-page app at `/admin`. Tabs: Stats, Propose, Drafts, Generate, Scheduler, Data Sync, Pages Sync, Raindrop, Emergency. All admin JavaScript is currently inline in `templates/admin.html` (~870 lines). Moving it to `.js` files is F41 T03.

---

## What was done this session (F40)

All complete and deployed to fly.io.

1. **Drafts body not displaying** — `d.body` in template literal broke on backticks/`${` in Claude output. Fixed: added `escapeHtml()`, set body via `textContent` not innerHTML.
2. **"Edit & Post" button not rendering** — same root cause as above. Now works.
3. **Stats page redesign** — pre-generated static HTML via `generate_stats_cache()`, served via iframe, refreshed every 60s. Zero computation on GET.
4. **Non-blocking draft generation** — Claude API + URL fetch in `run_in_executor`.
5. **Draft list fast glob** — `draft-*.md` glob instead of scanning all 2800 posts.
6. **Delete draft endpoint** — `POST /api/delete-draft`.
7. **Publish sets today's date** — so published drafts appear as newest post.
8. **"Originally Posted on:" prefix** — added to all generated drafts.
9. **Claude prompt shortened** — 50–75 words, `max_tokens=150`.
10. **config.yaml** — centralised runtime parameters, read by server.py, generator.py, draft_generator.py.
11. **Test fix** — `'display: none'` → `'d-none'` in live server test assertion.

---

## Next session: F41 — Codebase Cleanup and Architecture Review

**Feature file**: `process/features/notdone/F41.md`
**Task file**: `process/tasks/notdone/F41.md`

### Tasks summary

| # | Task | Focus |
|---|------|-------|
| T01 | Remove `_` prefix from private names | Coding standards |
| T02 | Fix file headers (shebang, author, license) | Coding standards |
| T03 | Extract inline JS from HTML templates to `.js` files | Separation of concerns |
| T04 | Remove HTML literals from Python files | Separation of concerns |
| T05 | Reduce/simplify admin JavaScript | JS reduction |
| T06 | Pre-generate propose lists as static JSON | Responsiveness |
| T07 | Pre-generate draft list as static JSON | Responsiveness |
| T08 | Audit all GET routes for minimal-work compliance | Responsiveness |
| T09 | Arch review: module decomposition (`server.py` is 1859 lines) | Architecture |
| T10 | Arch review: scheduler vs asyncio, background work ownership | Architecture |
| T11 | Arch review: XML-RPC / Blogger API necessity | Architecture |
| T12 | Arch review: volume-first three-way content sync | Architecture |
| T13 | Arch review: YAGNI and speculative abstractions | Architecture |

Architecture review tasks (T09–T13) write findings to `process/arch-review.md` only — no code changes. Code changes follow in subsequent features.

### Suggested starting point
T09 (architecture review of `server.py`) is the highest-value first step — it will shape which subsequent cleanup tasks make sense and in what order.

---

## Open features (not F41)

| Feature | Description | Priority |
|---------|-------------|----------|
| F29 | Extract reusable utilities from raindrop.py | Medium |
| F30 | Code quality improvements in raindrop.py | Low |
| F33 | Fix web search (item.category → item.type bug + raindrop indexing) | Medium |
| F35 | Fix admin sync button after GIT_TOKEN rotation | Medium |

F33 T01 (the category/type field name fix in `script.js`) is already done. F33 T02–T04 (raindrop indexing, content truncation, tests) remain.

---

## Test status

```
494 passed, 11 skipped, 3 warnings
```

All tests pass locally. Skipped tests require a live server (`https://salas.com`).

---

## Deployment

```bash
fly deploy          # build and deploy to fly.io
fly logs            # tail live logs
fly ssh console     # shell into running container
```

Deployed app: https://salasblog2.fly.dev

Startup sequence: `startup.sh` runs `git checkout -f -B main origin/main` (overwrites `/app` with GitHub HEAD), then starts uvicorn. This means **code changes must be committed and pushed to GitHub before `fly deploy`**, or they will be overwritten at startup.

---

## Known rough edges

- `server.py` at 1859 lines is the biggest structural problem — nearly everything lives there.
- Admin JS is ~600 lines inline in `admin.html` — hard to maintain, not testable.
- The three-way content sync (`/data` ↔ `/app` ↔ `output/`) adds operational complexity.
- XML-RPC endpoint (`/xmlrpc`, `blogger_api.py`) may be dead weight if MarsEdit is no longer the primary authoring tool.
- `mount_static_files()` is defined but intentionally disabled at startup (replaced by custom endpoints) — dead code.
- `_check_single_instance()` depends on the `fly` CLI being present in the container — fragile.
