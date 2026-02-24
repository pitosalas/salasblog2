# salasblog2 Specification

## Overview

salasblog2 is a personal blogging platform implemented as a Python static site generator with an integrated FastAPI web server. It processes Markdown files with YAML frontmatter into HTML pages, supports three content types (blog posts, link-blog raindrops, static pages), syncs bookmarks from Raindrop.io, and exposes an XML-RPC Blogger API for compatibility with desktop editors like MarsEdit. The application is deployed on Fly.io with dual content storage (a persistent volume as the source of truth and a Git repository for backups).

## UI / Styling Principles

- Use Bootstrap 5 (CDN) as the sole CSS framework; accept its default appearance.
- Do **not** add custom CSS to reproduce what Bootstrap already provides.
- All overrides must live exclusively in `static/css/style.css` — never inline in templates.
- Every rule in `style.css` must have a comment explaining why Bootstrap alone is insufficient.
- When in doubt, remove the override and live with the Bootstrap default.

## Goals

- Generate a complete static website from Markdown + YAML frontmatter content files
- Serve the static site and expose admin/API endpoints via FastAPI
- Support three content types: blog posts, Raindrop.io link-blog entries, and static pages
- Sync Raindrop.io bookmarks automatically on a schedule and on demand
- Provide an XML-RPC Blogger API so MarsEdit (and compatible editors) can create/edit posts
- Provide a web admin interface for managing content and triggering operations
- Deploy on Fly.io with persistent volume for content storage and GitHub for backup/sync
- Run scheduled tasks: periodic Git sync, periodic Raindrop sync

## Architecture

### Package Layout

```
src/salasblog2/
  cli.py          — argparse CLI entry point (commands: generate, server, reset, deploy, sync-raindrops)
  generator.py    — SiteGenerator class: loads content, renders Jinja2 templates, writes HTML
  server.py       — FastAPI app: serves static files, admin UI, XML-RPC endpoint, REST API
  raindrop.py     — RaindropDownloader: fetches bookmarks from Raindrop.io API, writes markdown
  scheduler.py    — Scheduler: runs periodic Git sync and Raindrop sync using the schedule library
  blogger_api.py  — BloggerAPI: implements XML-RPC Blogger protocol for MarsEdit compatibility
  utils.py        — Shared helpers: markdown processing, date formatting, frontmatter parsing, URL generation

templates/        — Jinja2 HTML templates (home, blog list/post, raindrop list/post, pages, 404, admin)
static/           — CSS, JS, images served as-is
content/          — Local content fallback (development); production uses /data/content/ volume
```

### Content Storage

Two storage locations are used in parallel:

- `/data/content/` — persistent Fly.io volume, primary source of truth in production
- `/app/content/` (git repo) — secondary copy, synced to GitHub on a schedule

The generator checks for `/data/content/` at startup; if absent it falls back to local `content/`.

### Content Format

All content is Markdown with YAML frontmatter:

```yaml
---
title: "Post Title"
date: "2024-01-15"
type: "blog" | "drop" | "page"
category: "General"
---
Markdown body here...
```

Raindrop entries additionally carry: `url`, `domain`, `cover`, `tags`, `note`, `raindrop_type`, `important`, `broken`.

### Content Types

| Type       | Directory                  | Listing URL        | Individual URL              |
|------------|----------------------------|--------------------|-----------------------------|
| blog       | `content/blog/`            | `/blog/`           | `/blog/<filename>.html`     |
| raindrops  | `content/raindrops/`       | `/raindrops/`      | `/raindrops/<filename>.html`|
| pages      | `content/pages/`           | `/pages/`          | `/<filename>.html`          |

## Key Features

### Static Site Generation

`SiteGenerator.generate_site()` orchestrates full-site generation:
1. Load blog posts, raindrops, and pages from Markdown files
2. Render individual post pages (blog_post.html, raindrop_post.html, page.html)
3. Render paginated listing pages (20 posts/page)
4. Render home page (5 most recent from each content type)
5. Render pages listing
6. Generate `search.json` (title, url, type, excerpt, first 500 chars of content)
7. Generate 404 error page
8. Copy static assets

Incremental regeneration (`incremental_regenerate_post`, `incremental_regenerate_after_deletion`) regenerates only the affected post, its listing page, the home page, and the search index.

### FastAPI Server

The server serves the generated static site and exposes:
- `GET /` and all static HTML — serves from `output/` directory
- `POST /xmlrpc` — XML-RPC Blogger API for MarsEdit
- Admin web UI at `/admin/*` — login, post management, sync triggers, raindrop management
- REST endpoints: `/api/sync-raindrops`, `/api/sync-status`, `/api/regen-status`, etc.

Authentication: session-based for admin UI (via `itsdangerous`), HTTP Basic for XML-RPC.

Required environment variables: `SESSION_SECRET`, `ADMIN_PASSWORD`. Optional: `BLOG_USERNAME`, `BLOG_PASSWORD`, `RAINDROP_TOKEN`.

### Raindrop.io Integration

`RaindropDownloader.download_raindrops()` fetches bookmarks from the Raindrop.io v1 REST API and writes each bookmark as a Markdown file. It uses a timestamp-based cache to fetch only new items since the last sync. `--reset` clears the cache and refetches everything (bounded by `--count`).

### XML-RPC Blogger API

`BloggerAPI` implements the Blogger API subset needed by MarsEdit:
- `blogger.getUsersBlogs` — returns blog info
- `blogger.getRecentPosts` — returns latest N posts
- `blogger.newPost` — creates a new Markdown file in `content/blog/` and triggers incremental regen
- `blogger.editPost` — updates an existing post and triggers incremental regen
- `blogger.deletePost` — removes a post file and triggers incremental regen

### Scheduler

`Scheduler` runs two recurring jobs using the `schedule` library:
- Git sync every N hours (default 6): copies `/data/content/` to `/app/content/`, commits, pushes to GitHub
- Raindrop sync every N hours (default 2): calls `RaindropDownloader.download_raindrops()`

Interval is configurable via `SCHED_GITSYNC_HRS` and `SCHED_RAINSYNC_HRS` environment variables.

## CLI Commands

| Command                            | Action                                         |
|------------------------------------|------------------------------------------------|
| `uv run bg generate`               | Full static site generation                    |
| `uv run bg server [--port N]`      | Start FastAPI server (default port 8000)       |
| `uv run bg reset`                  | Delete `output/` directory                     |
| `uv run bg deploy`                 | `fly deploy` to Fly.io                         |
| `uv run bg sync-raindrops [--reset] [--count N]` | Fetch Raindrop.io bookmarks   |

## Deployment

Fly.io via `Dockerfile` and `fly.toml`. Persistent volume at `/data/content/`. Required Fly secrets:
- `RAINDROP_TOKEN`
- `ADMIN_PASSWORD`
- `SESSION_SECRET`
- `SSH_PRIVATE_KEY` (for Git sync) or `GIT_TOKEN`
- `GIT_EMAIL`, `GIT_NAME`, `GIT_BRANCH`

## Dependencies

- Python 3.12+, uv
- `fastapi`, `uvicorn` — web server
- `jinja2` — HTML templating
- `markdown`, `python-frontmatter` — content processing
- `requests` — Raindrop.io API calls
- `pyyaml` — YAML config/frontmatter
- `python-dotenv` — environment variable loading
- `python-multipart`, `itsdangerous` — form handling and sessions
- `schedule` — recurring task scheduling

## Testing

Tests live in `tests/`. Some require `httpx` (FastAPI test client) and `pytest-asyncio` for async tests. Core unit tests (utils, raindrop, scheduler, placeholder title) run without a live server. Integration and deployment tests are in `tests/integration/` and `tests/deployment/` and require a running server or Fly.io access.

Current test status: 144 passing, 13 failing (scheduler mock issues, utils filename test, placeholder title feature gap).

## Constraints

- No database — all state in files on disk
- Content files are the source of truth; the system is stateless between runs
- Fly.io persistent volume is required in production for content durability
- GitHub repo serves as backup and is synced on a schedule, not in real time
