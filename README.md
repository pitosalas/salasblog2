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

**Production**: `/data/content/` (persistent volume)  
**Development**: `content/` (local files)

```
content/
├── blog/       # Blog posts (.md files)
├── raindrops/  # Link blog from Raindrop.io
└── pages/      # Static pages
```

**Frontmatter**: `title`, `date`, `type` (blog/drop/page), `category`

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

## Development

See [CLAUDE.md](CLAUDE.md) for architecture and development guidelines.