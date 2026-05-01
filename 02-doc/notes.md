# Project Notes

_Semi-permanent notes: architecture decisions, research findings, calibration data, recurring gotchas._

## Architecture
- FastAPI web app + static site generator
- Content: blog posts, raindrop link blog entries, static pages
- Deployed to Fly.io with persistent volume storage
- GitHub repo used as backup/sync target

## Key Files
- `src/` — main application source
- `content/` — markdown content files
- `templates/` — Jinja2 HTML templates
- `static/` — static assets

## Integrations
- Raindrop.io REST API (bookmark sync)
- XML-RPC Blogger API (MarsEdit compatibility)
- Fly.io deployment (`uv run bg` CLI)
- GitHub sync (scheduled git push)
