# salasblog2 Feature List

## F01 — Static Site Generator
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: `SiteGenerator` class reads Markdown + YAML frontmatter from three content directories (blog, raindrops, pages), renders Jinja2 HTML templates, and writes a complete static site to `output/`. Includes paginated listing pages (20/page), home page (5 recent from each type), search index JSON, 404 page, and static asset copy.

## F02 — Raindrop.io Bookmark Sync
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: `RaindropDownloader` fetches bookmarks from the Raindrop.io v1 REST API using a bearer token. Uses a timestamp-based cache to fetch only new items. `--reset` clears the cache and refetches everything. Each bookmark is written as a Markdown file with YAML frontmatter.

## F03 — FastAPI Server
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: FastAPI application that serves the generated static site from `output/`, exposes an XML-RPC endpoint for MarsEdit, provides a web admin UI with session authentication, and offers REST endpoints for triggering sync and regeneration. Validates required environment variables at startup.

## F04 — XML-RPC Blogger API (MarsEdit)
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: `BloggerAPI` implements the Blogger API subset needed by MarsEdit: `getUsersBlogs`, `getRecentPosts`, `newPost`, `editPost`, `deletePost`. New and edited posts trigger incremental site regeneration. Authenticated via HTTP Basic (`BLOG_USERNAME`/`BLOG_PASSWORD`).

## F05 — CLI Entry Point
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: `salasblog2.cli:main` argparse CLI with subcommands: `generate`, `server`, `reset`, `deploy`, `sync-raindrops`, `help`. Installed as `salasblog2` and `bg` entry points via pyproject.toml. Server command accepts `--port` and `--reload`.

## F06 — Incremental Site Regeneration
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: After a single post is created, edited, or deleted via the Blogger API, only the affected post's HTML, its listing page, the home page, and the search index are regenerated — avoiding a full site rebuild. `incremental_regenerate_post` and `incremental_regenerate_after_deletion` on `SiteGenerator`.

## F07 — Scheduler Git Sync
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Periodic Git synchronization of `/data/content/` to the GitHub-backed `/app/content/` repository. Runs every N hours (configurable via `SCHED_GITSYNC_HRS`). Commits and pushes changes.

## F08 — Placeholder Title for Missing Frontmatter
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: When a content file has no `title` field in its YAML frontmatter, the generator substitutes a placeholder title derived from the filename (e.g. `placeholder title: My Post Name`).

## F09 — Content Utility Functions
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: `utils.py` provides shared helpers: `format_date`, `create_excerpt`, `create_excerpt_with_info`, `extract_first_paragraph`, `parse_date_for_sorting`, `process_markdown_to_html`, `parse_frontmatter_file`, `generate_url_from_filename`, `sort_posts_by_date`, `group_posts_by_month`, `load_markdown_files_from_directory`, `get_markdown_processor`, `format_raindrop_as_markdown`, `generate_raindrop_filename`.

## F10 — Dual Content Storage
**Priority**: High
**Done:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: The generator detects `/data/content/` at startup and uses it as the primary source of truth (production Fly.io volume). Falls back to local `content/` for development. The Blogger API writes new posts to the active content directory and immediately backs up to `/data/content/`.

## F11 — Web Admin Interface
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Session-authenticated admin UI at `/admin/*`. Provides pages for listing/editing/deleting posts, triggering Raindrop sync, triggering Git sync, and viewing sync status. Login uses `ADMIN_PASSWORD` environment variable.

## F12 — Scheduler Raindrop Sync
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Periodic Raindrop.io sync runs every N hours (configurable via `SCHED_RAINSYNC_HRS`, default 2). Calls `RaindropDownloader.download_raindrops()` on schedule. Tracks last sync time and recent errors for status reporting.

## F13 — Fly.io Deployment
**Priority**: Medium
**Done:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: `Dockerfile`, `fly.toml`, and `deploy_to_fly()` CLI command. Deploys via `fly deploy`. Documents required Fly secrets: `RAINDROP_TOKEN`, `ADMIN_PASSWORD`, `SESSION_SECRET`, `SSH_PRIVATE_KEY`, `GIT_EMAIL`, `GIT_NAME`, `GIT_BRANCH`.

## F14 — File Serving Security
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: The FastAPI server validates file paths to prevent directory traversal attacks when serving static files and content.

## F15 — MIME Type Handling
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Correct MIME types are served for all static asset types (CSS, JS, images, fonts).

## F16 — Pages Feature
**Priority**: Low
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Third content type: static pages (About, Contact, etc.) rendered from `content/pages/` with `page.html` template. Listed at `/pages/`. Individual pages served at `/<filename>.html`. Uses first paragraph as excerpt, no "read more".

## F17 — Bootstrap-First Styling
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Replace custom CSS with Bootstrap v5.x loaded from CDN. Remove or minimize `static/css/` overrides so the site uses Bootstrap's default components and utilities throughout all Jinja2 templates (nav, cards, pagination, tables, forms, admin UI). No custom color themes or layout overrides.

## F18 — Clickable Tag Pages
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Blog posts can have a `tags` list in their YAML frontmatter. Each tag displayed on a post page or listing page becomes a link to `/tags/<tag>/index.html`, which lists all posts carrying that tag. The generator builds one static tag page per unique tag across all blog posts. Tags are shown as Bootstrap badges on `blog_post.html`, `blog_list.html`, and `home.html`.

## F19 — Configurable Front Page Post Count
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: The number of recent posts shown in each section on the home page (blog posts and raindrops) is controlled by a `HOME_POSTS_COUNT` environment variable (default 5).

## F20 — Front Page "See All" Links
**Priority**: Low
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Add a "See all posts →" link below the recent blog posts section on `home.html` and a "See all links →" link below the recent raindrops section, linking to `/blog/` and `/raindrops/` respectively.

## F21 — Raindrop Collection Filtering
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: The `/raindrops/` listing page displays a row of links at the top, one for each collection found across all raindrops. Clicking a collection link filters the displayed raindrops to show only those from that collection. The generator extracts collection names from raindrop frontmatter and generates filtered listing pages per collection.

## F22 — Scheduler Git Push Uses fly.toml Branch
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: The scheduler's Git sync pushes content to the branch specified by `GIT_BRANCH` in `fly.toml` using `git push origin HEAD:<branch>` so the current HEAD is always pushed to the configured remote branch regardless of local branch name.

## F23 — Tag Selection for Blog Posts (UI and API)
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Blog posts created or edited via the admin web UI or the XML-RPC Blogger API can carry one or more tags drawn from a fixed vocabulary defined in code. The admin create/edit forms render the vocabulary as a multi-select control; selected tags are written as a YAML `tags` list in frontmatter. Tags are displayed as clickable Bootstrap badge links on post and listing pages.

## F24 — Content Type Visual Indicators
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Each item on listing pages and the home page displays its content type via a Bootstrap badge or icon (e.g. "Post" or "Link"). The indicator appears consistently on listing pages, the home page, and individual post pages. No custom CSS.

## F25 — Simple Visit Statistics
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Track and display simple page-visit statistics server-side without any external analytics service. Counts are stored in a lightweight persistent store (JSON file or SQLite on the Fly.io volume). A stats summary is visible to the admin at `/admin/stats` showing visit counts per URL. No JavaScript tracking, no PII stored.

## F26 — Traffic Classification by Visitor Type
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Each request is classified as one of five visitor types: `human`, `ai_bot`, `search_engine`, `crawler`, `unknown`, based on the `User-Agent` header. The `VisitCounter` stores counts per path broken down by visitor type. The admin Stats tab displays counts per type alongside totals.

## F27 — Per-Post Action Buttons (Edit & Derive)
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Two action buttons on each blog post page (`blog_post.html`), visible only to logged-in admins. "Edit this post" links to the existing admin edit page. "Start a new post based on this one" pre-fills the new-post form with the current post's title (prefixed "Re: ") and body. Both use Bootstrap `btn-warning` or `btn-info`, grouped separately from navigation. No custom CSS, no JavaScript.

## F28 — Fix raindrop.py High-Priority Issues
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Two high-priority fixes in `raindrop.py`. (1) Replaced `datetime.fromisoformat()` calls with `_parse_iso_date()` from `utils.py` for consistent date handling across `utils.py` and `raindrop.py`. (2) The `/data/content/` path fallback was already implemented correctly in `raindrop.py` (lines 31–36), matching the pattern in `generator.py`.

## F31 — Enhanced File Serving Security
**Priority**: High
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Hardened all static file serving routes in `server.py` against four attack vectors. (1) Path traversal: added `_safe_resolve()` helper that resolves the full path and verifies it remains within the expected base directory. (2) Symlink escapes: `_safe_resolve()` uses `Path.resolve()` which follows symlinks, then checks `is_relative_to()` on the resolved path, so symlinks pointing outside the base dir are rejected. (3) Hidden file exposure: `_safe_resolve()` blocks any path component starting with `.` (e.g. `.env`, `.htaccess`). (4) Permission error crashes: wrapped `read_bytes()` and `is_dir()` calls in `try/except (PermissionError, OSError)` so permission-denied conditions return 404 instead of crashing the server. Applied to `/static/`, `/raindrops/`, and the catch-all `/{path}` route handlers.

## F32 — Improving the Stats Page
**Priority**: Medium
**Done:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Enhanced the admin Stats tab with time-period sub-tabs (Today, This Week, This Month, This Year, All Time) and grouped row display. `VisitCounter` storage format updated to store per-visit timestamps (with migration for old int and type-count formats). `get_all(period=)` filters by cutoff datetime. `/api/stats` endpoint accepts optional `?period=` query param. Stats table groups rows into Root, Blog, and Raindrops sections with section headers. 9 new period-filtering tests added.
