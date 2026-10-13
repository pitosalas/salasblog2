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
- Legacy link repair: 301 redirects and content rewrites for URLs from the blog's earlier engines

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
uv run bg legacy-map [--content DIR]       # Build/extend the legacy URL map
uv run bg legacy-rewrite [--content DIR] [--apply]  # Rewrite legacy links (dry run by default)
uv run bg check-links [--content DIR] [--output DIR]  # Report dead links to this site
```

The last three are explained under [Legacy Link Repair](#legacy-link-repair).

## Testing

```bash
uv run pytest tests/                       # Run all core tests (674 tests)
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

Blog posts also support a `tags` list (selected from the curated vocabulary in `02-doc/tag-hints.md`).

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

## Legacy Link Repair

The blog ran on Movable Type, WordPress, Squarespace and Radio UserLand
before salasblog2. Old posts still link to each other with those engines'
URLs, which don't exist on this site. For example:

* `/weblogs/archives/000522.html` (Movable Type)
* `/2008/02/18/slug/` (WordPress)
* `/imported-20111103233638/2012/1/4/slug.html` (Squarespace import)
* `/2004/01/24.html` (Radio UserLand day page)

`02-doc/legacy-url-map.json` maps each old path to its current post. It
drives two things:

* **Redirects.** The server returns a 301 for any mapped old URL, so links
  from other sites and search engines keep working. Unmapped old URLs
  return 404.
* **Content rewrites.** `bg legacy-rewrite` replaces old links inside posts
  with the current URLs.

**The map only grows, and human decisions are kept.** An entry stays after
its links are rewritten, because the redirects still need it. A rebuild
never changes an entry marked `"reviewed": true`. Commit the map, since
production reads the copy that's deployed.

### When to use these commands

* `bg check-links` — any time you want to know whether posts contain broken
  links to this site, e.g. after importing old content or a large edit.
  Read-only.
* `bg legacy-map` — when `check-links` reports old-style links that aren't
  in the map yet (new imports, or a URL pattern the scanner didn't
  recognize).
* `bg legacy-rewrite` — after new map entries have been reviewed and
  deployed, to fix the links inside posts.

### `bg check-links`

```bash
uv run bg generate        # it checks against the generated site, so build first
uv run bg check-links     # defaults: --content content --output output
```

Lists every link to this site (root-relative like `/blog/x.html`, or
absolute `salas.com`) that neither serves a generated file nor has a
redirect in the map. Prints `source-file: url` per dead link, then a count.

To check what's actually live, run it on production. Local `content/` can
lag behind the volume, and uploaded images exist only there:

```bash
fly ssh console -C "sh -c 'cd /app && uv run bg check-links --content /data/content --output /app/output'"
```

Some dead links can't be fixed: links accidentally pointed at
`/wp-admin/...`, old comment scripts, and files that no longer exist. About
21 of these remain and are expected (listed in
`04-tasks/done/TF48-legacy-link-repair.md`).

### `bg legacy-map`

```bash
uv run bg legacy-map      # default: --content content
```

1. Scans `content/blog` and `content/pages` for old-style links.
2. Looks up Movable Type IDs on the Wayback Machine to get each archived
   post's title and date. Lookups are cached in `.cache/wayback.json`
   (gitignored), so reruns only look up new IDs. archive.org is slow and
   throttles requests, so a first run over many new IDs can take several
   minutes.
3. Matches every old path to a current post: by title for Movable Type, by
   the date and slug in the URL for the others. Dates may be up to 2 days
   off.
4. Merges the results into `02-doc/legacy-url-map.json` and prints counts
   by scheme and confidence.

Then review the map. Each entry has a `confidence`:

* `exact` — the title or slug is identical. No review needed.
* `fuzzy` — close but not identical, e.g. a truncated slug. Check the
  `new` target against the `evidence`.
* `unmatched` — `new` is `null`. Check `candidates`, or search post titles,
  in case the post was renamed or re-dated in an import.

For every entry you decide on, set `new` (a `/blog/...html` URL, a Wayback
URL, or `null`) and add `"reviewed": true`. Then commit, push and deploy.

### `bg legacy-rewrite`

Production's `/data/content` volume is the source of truth for posts. Run
the rewrite **there**, not on local `content/`. Local content is synced
from production, and committing a local rewrite would diverge from it.

Steps, after the reviewed map has been committed, pushed and deployed:

```bash
# 1. Dry run: prints a diff of every change and "would rewrite N links"
fly ssh console -C "sh -c 'cd /app && uv run bg legacy-rewrite --content /data/content'"

# 2. Apply
fly ssh console -C "sh -c 'cd /app && uv run bg legacy-rewrite --content /data/content --apply'"

# 3. Regenerate the site and sync the changed posts to GitHub
fly ssh console -C "sh -c 'cd /app && uv run bg generate && uv run python -c \"import asyncio; from salasblog2.scheduler import get_scheduler; print(asyncio.run(get_scheduler().sync_to_github()))\"'"

# 4. Pull the synced content locally
git pull
```

Only link targets change. Link text, frontmatter and the rest of each post
are left byte-for-byte unchanged. Links whose map entry has no target are
left alone. Running it again is safe, since rewritten links no longer match
an old pattern.

## Development

See [CLAUDE.md](CLAUDE.md) for coding guidelines and architecture notes.
