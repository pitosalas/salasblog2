# Salasblog2

Python static site generator with FastAPI server, XML-RPC Blogger API, and Raindrop.io integration.

## Features

- Markdown + YAML frontmatter processing
- Multiple content types: blog posts, link blog, pages
- Jinja2 templating with theme system
- FastAPI server with XML-RPC Blogger API (MarsEdit compatible)
- Web admin interface with authentication
- Automated Git sync and Fly.io deployment
- Raindrop.io bookmark integration
- Client-side search, incremental regeneration

## Installation

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv
uv sync                                          # Install dependencies
```

## Quick Start

```bash
# Generate static site
salasblog2 generate

# Run server with API
salasblog2 server

# Preview static files
python -m http.server 8000 -d output
```

## Commands

```bash
salasblog2 generate [--theme THEME]     # Generate site
salasblog2 server [--port PORT]         # FastAPI server
salasblog2 reset                        # Clean output
salasblog2 deploy                       # Deploy to Fly.io
salasblog2 themes                       # List themes
salasblog2 sync-raindrops [--reset]     # Sync Raindrop.io bookmarks
```

## Content Structure

```
content/
├── blog/       # Blog posts
├── raindrops/  # Link blog
└── pages/      # Static pages (auto-nav)
```

Frontmatter: `title`, `date` (YYYY-MM-DD), `type` (blog/drop/page), `category`

## Server & APIs

- Web admin: `/admin` (set `ADMIN_PASSWORD`)
- XML-RPC: `/xmlrpc` (MarsEdit/blog editors)
- Volume sync: `/api/sync-to-volume`, `/api/sync-from-volume`
- Git scheduler: `/api/scheduler/*`

## Environment Variables

**Required:**
- `RAINDROP_TOKEN` - Raindrop.io API token

**Authentication:**
- `ADMIN_PASSWORD` - Web admin password
- `BLOG_USERNAME/BLOG_PASSWORD` - XML-RPC credentials (default: admin/password)

**Git Integration (Fly.io):**
- `GIT_TOKEN` or `SSH_PRIVATE_KEY` - GitHub access
- `GIT_EMAIL/GIT_NAME` - Commit info
- `GIT_BRANCH` - Target branch for pushes (default: main)

## Blog Editor Setup (MarsEdit)

1. Start server: `salasblog2 server`
2. Add blog: XML-RPC URL `http://localhost:8000/xmlrpc`, API type "Blogger"
3. Credentials: Use `BLOG_USERNAME/BLOG_PASSWORD` values

## Fly.io Deployment

```bash
fly secrets set RAINDROP_TOKEN="your_token"
fly secrets set ADMIN_PASSWORD="your_password" 
fly secrets set SSH_PRIVATE_KEY="$(cat ~/.ssh/id_ed25519)"
fly deploy
```

## Themes

Default: `claude`. Available themes in `themes/` directory.
Use `salasblog2 themes` to list, `--theme NAME` to select.

## Development

See [CLAUDE.md](CLAUDE.md) for architecture details, API specs, and development guidelines.