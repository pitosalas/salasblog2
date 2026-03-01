# Salasblog2

Personal blogging platform: Python static site generator + FastAPI server, with Raindrop.io link blog and XML-RPC Blogger API for MarsEdit.

## Features

- Markdown + YAML frontmatter content processing
- Three content types: blog posts, raindrops (link blog), static pages
- Jinja2 HTML templating with Bootstrap 5
- XML-RPC Blogger API (MarsEdit compatible)
- Web admin interface with create/edit/delete, tag selection, and per-post edit/derive buttons
- Tag pages: clickable tag badges link to `/tags/<tag>/` listing pages
- Raindrop.io bookmark sync (scheduled + on-demand) with collection filtering
- Dual content storage: Fly.io persistent volume + GitHub backup
- Scheduled Git sync and Raindrop sync
- Visitor statistics with per-period filtering (today/week/month/year) and type breakdown (human, bot, crawler)
- Hardened static file serving: path traversal, symlink, and hidden file protection

## Quick Start

```bash
uv sync
uv run bg generate    # build static site
uv run bg server      # serve at http://localhost:8000
```

## CLI Commands

```bash
uv run bg generate                          # Generate full static site
uv run bg server [--port PORT]             # Start FastAPI server (default: 8000)
uv run bg sync-raindrops [--reset] [--count N]  # Sync Raindrop.io bookmarks
uv run bg reset                            # Delete output/ directory
uv run bg deploy                           # Deploy to Fly.io (runs fly deploy)
```

## Testing

```bash
uv run pytest tests/                       # Run all core tests (434 tests)
```

CI runs automatically on every push via GitHub Actions.

## Content Structure

```
content/
├── blog/         # Blog posts
├── raindrops/    # Raindrop.io link blog entries
└── pages/        # Static pages (About, Contact, etc.)
```

In production, `/data/content/` (Fly.io persistent volume) takes precedence over local `content/`.

### Content File Format

```yaml
---
title: "Post Title"
date: "2024-01-15"
type: "blog"        # blog | drop | page
category: "General"
---
Markdown content here...
```

Blog posts also support a `tags` list (selected from the built-in vocabulary in `BLOG_TAGS`).

Raindrop entries also include: `url`, `domain`, `cover`, `tags`, `note`, `raindrop_type`, `collection`.

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `SESSION_SECRET` | Yes | Random string for admin session signing |
| `ADMIN_PASSWORD` | Yes | Web admin login password |
| `RAINDROP_TOKEN` | For sync | Raindrop.io API token |
| `BLOG_USERNAME` | Optional | XML-RPC auth (default: admin) |
| `BLOG_PASSWORD` | Optional | XML-RPC auth (default: password) |
| `GIT_TOKEN` or `SSH_PRIVATE_KEY` | For git sync | GitHub credentials |
| `GIT_EMAIL` / `GIT_NAME` | For git sync | Git commit identity |
| `GIT_BRANCH` | For git sync | Branch to push to (default: main) |
| `SCHED_GITSYNC_HRS` | Optional | Git sync interval in hours (default: 6) |
| `SCHED_RAINSYNC_HRS` | Optional | Raindrop sync interval in hours (default: 2) |

## MarsEdit Setup

1. Start the server: `uv run bg server`
2. In MarsEdit: add blog → URL `http://localhost:8000/xmlrpc`, API type **Blogger**
3. Credentials: `BLOG_USERNAME` / `BLOG_PASSWORD`

## Fly.io Deployment

```bash
fly secrets set SESSION_SECRET="$(openssl rand -hex 32)"
fly secrets set ADMIN_PASSWORD="yourpassword"
fly secrets set RAINDROP_TOKEN="yourtoken"
fly secrets set GIT_TOKEN="yourghtoken"   # or SSH_PRIVATE_KEY
fly secrets set GIT_EMAIL="you@example.com"
fly secrets set GIT_NAME="Your Name"
fly deploy
```

## Development

See [CLAUDE.md](CLAUDE.md) for coding guidelines and architecture notes.
