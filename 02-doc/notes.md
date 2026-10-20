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

* Each line is a usage count, a primary tag, and its aliases in
  parentheses: `0        robotics (robot, ros, ros2, lidar, ...)`.
* As of 2026-10-20 (F55) there are **16 primaries and 429 aliases**.
* **The list is closed.** Only the user adds a primary or an alias, by
  editing the file. Automatic promotion was removed in F55.

### One rule, one function

`tag_vocabulary.canonicalize_tags` converts any tag list onto the list:

* an alias becomes its primary
* an unknown tag is dropped and reported
* tags are compared lowercased, with spaces as hyphens
* the result is de-duplicated, in order

### Where it is enforced

* **Post editor.** The picklist offers exactly the 16 tags. On save an
  alias is converted, and any unknown tag gets a 400 naming it. Nothing is
  saved.
* **Raindrop sync.** Raindrop.io tags are converted as each file is
  written. Unknown ones are dropped, and a raindrop with none left has no
  `tags` key.
* **Site generation.** Only curated tags are shown or get `/tags/` pages.
  Any other tag in a file is skipped and printed once per run.
* **Automated tagging** (`tag_cleanup.py`, `wp_taxonomy.py`) applies only
  curated tags. Others are reported as candidates and never written.

### One-time conversion

* `bg convert-tags --content <root> [--apply]` rewrites existing raindrop
  and blog tags in place. Only the `tags:` lines change, line endings
  included, and each rewrite is re-parsed to check it.
* On blog posts the generic `technology` and `personal` are dropped when
  the post has a real topic, and kept as markers otherwise.
* `bg generic-tags` selects the marked posts for the judgment pass and
  applies reviewed `[{filename, tags}]` decisions.
* **Never `--reset` raindrops** to convert them. Nothing filters what a
  reset downloads, so it would pull every bookmark on Raindrop.io.
