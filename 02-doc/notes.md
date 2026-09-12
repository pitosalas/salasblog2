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

## Backup coverage: raindrops are deliberately excluded from GitHub

`content/raindrops/` is listed in `.gitignore`, and `scheduler.py`'s
`sync_to_github()` does a plain `git add content/`, which silently
respects `.gitignore` — so raindrops have never actually reached the
GitHub backup (confirmed 2026-09-11: 0 raindrop files on `origin/main`
vs. 1547 on production's `/data/content/raindrops`, while all 2832
blog posts are correctly tracked).

**This is intentional, not a bug.** Raindrops are pure downstream
copies of Raindrop.io — never locally edited (no edit UI, only
delete), so there's no local-only state to lose. `raindrop.py`'s
`download_raindrops(reset=True)` does a full reset + re-fetch from the
Raindrop.io API, reconstructing every file (notes, tags, excerpt)
from scratch. Raindrop.io's own service is the durable source of
truth for that content, not GitHub.

The one real dependency this creates: if the Raindrop.io account *and*
the production volume were both lost at the same time, there'd be
nothing to recover raindrops from. Considered an acceptable,
much-lower-probability risk than the routine "forgot to back it up"
case GitHub sync guards against for blog posts/pages.
