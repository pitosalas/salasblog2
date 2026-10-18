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

## How curated tags interact with other tags

The single source is the **Curated Tags** list in `02-doc/tag-hints.md`.

* Each line is a usage count, a primary tag, and optional aliases in
  parentheses: `79       robotics (robot, ros, ros2, lidar, ...)`.
* As of 2026-10-18 there are 80 primaries and 271 aliases.

Three rules apply at different levels of strictness, **on purpose**.

### 1. Hand-entered tags: free-form

* The post editor's picklist suggests curated tags plus the
  most-used tags (`output/top-tags.json`).
* Any tag can be typed. It is saved exactly as entered, never blocked or
  rewritten.

### 2. Display: every tag is equal

* Every tag on a post gets a badge and a `/tags/<slug>/` page, curated or
  not (`SiteGenerator.generate_tag_pages`).
* Raindrop tags come from Raindrop.io and are displayed the same way.
* The only exception is numeric WordPress-import leftovers (`1221`). They
  are hidden in templates and left out of the top-tags list.

### 3. Automated tagging: curated-only and additive

This covers F46 tag cleanup (`tag_cleanup.py`) and F50's WordPress import
(`wp_taxonomy.py`).

* They add only curated tags, with an alias resolved to its primary
  (`robots` → `robotics`).
* They **never remove** a tag already on a post. The one exception is
  numeric junk.
* A wanted tag outside the list is held back. Once it recurs on **4 or
  more** posts (`MIN_RECURRENCE_FOR_PROPOSED_TAG`), it is appended to the
  curated list and usable from then on.
* `apply_tag_proposal` refuses a post with CR line endings rather than
  flatten it (I04).

### The one strict tool: normalization (TF46.13)

* `scripts/normalize_tag_aliases.py` rewrites an alias to its primary
  (`pivot-table` → `lotus`), and drops any tag that is neither a primary nor
  an alias.
* It runs only by hand and has never been run for real.
* Its 2026-10-18 dry run would change one post and drop no tags.

### Consequences

* **Hand-picked tags win.** They are stored and displayed as typed.
* **The curated list steers automation** and feeds editor suggestions.
* Aliases matter only to the automated tagging and to normalization.
* **Aliases are not merged for display.** A hand-typed alias like `improv`
  gets its own `/tags/improv/` page, separate from `/tags/lotus/`. Folding
  aliases into their primary would mean running normalization, or a small
  feature that resolves aliases in the editor or in tag-page generation.
