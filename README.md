# Salasblog2

Static site generator with FastAPI server, XML-RPC Blogger API, and Raindrop.io integration.

## Features

- Markdown + YAML frontmatter processing
- Multi-content types: blog posts, raindrops (link blog), static pages
- Jinja2 templating
- XML-RPC Blogger API (MarsEdit compatible)
- Web admin interface
- Raindrop.io bookmark sync
- Dual content storage (persistent volume + git)

## Installation

```bash
uv sync
```

## Commands

```bash
uv run bg generate                             # Generate static site
uv run bg server [--port PORT]                # Start FastAPI server
uv run bg sync-raindrops [--reset]            # Sync Raindrop.io bookmarks
uv run bg reset                               # Clean output directory
uv run bg deploy                              # Deploy to Fly.io
```

## Content Structure

### Key Directories
- **`/data/content/`** - Persistent volume storage (production source of truth)
- **`/app/content/`** - Git repository content (development/local)
- Generator prioritizes `/data/content/` if it exists, falls back to local `content/`

### Content Subdirectories
```
content/
├── blog/       # Blog posts with YAML frontmatter + markdown
├── raindrops/  # Link blog posts from Raindrop.io bookmarks  
└── pages/      # Static pages (About, Contact, etc.)
```

### Content File Format
All content files use YAML frontmatter + markdown:
```yaml
---
title: "Post Title"
date: "2024-01-15"
type: "blog" | "drop" | "page"
category: "General"
---
Markdown content here...
```

### Content Lifecycle
- **Creation**: Blog API (MarsEdit) → `/app/content/blog/` → immediate backup to `/data/content/`
- **Raindrops**: API fetch → `/data/content/raindrops/` directly
- **Sync**: Scheduler syncs `/data/content/` ↔ GitHub via `/app/content/`
- **Generation**: Reads from `/data/content/` (or `/app/content/` fallback)

## Environment Variables

**Required for Raindrops:**
- `RAINDROP_TOKEN`

**Authentication:**
- `SESSION_SECRET` - Required for web admin sessions (random string)
- `ADMIN_PASSWORD` - Web admin login password
- `BLOG_USERNAME`/`BLOG_PASSWORD` - XML-RPC (default: admin/password)

**Git Integration:**
- `GIT_TOKEN` or `SSH_PRIVATE_KEY`
- `GIT_EMAIL`/`GIT_NAME`
- `GIT_BRANCH` (default: main)

## XML-RPC Setup (MarsEdit)

1. `uv run bg server`
2. Add blog: `http://localhost:8000/xmlrpc`, API type "Blogger"
3. Use `BLOG_USERNAME`/`BLOG_PASSWORD` credentials

## Fly.io Deployment

```bash
fly secrets set RAINDROP_TOKEN="token"
fly secrets set ADMIN_PASSWORD="password" 
fly secrets set SSH_PRIVATE_KEY="$(cat ~/.ssh/id_ed25519)"
fly deploy
```

## Testing

- Run `uv run bg generate` to test static generation  
- Run `uv run bg server` to test API functionality

## Development

See [CLAUDE.md](CLAUDE.md) for development guidelines.