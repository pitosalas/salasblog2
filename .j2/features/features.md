# salasblog2 Feature List

Status values:
- **Status**: `not started` / `in progress` / `done`
- **Tests written**: `no` / `yes`
- **Tests passing**: `n/a` / `no` / `yes`

---

<!-- ===== INCOMPLETE FEATURES (High → Medium → Low) ===== -->

## F26 — Traffic Classification by Visitor Type
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Extend the visit statistics system (F25) to classify each request as one of five visitor types: `human`, `ai_bot`, `search_engine`, `crawler`, `unknown`. Classification is based on the `User-Agent` request header. AI bots (GPTBot, ClaudeBot, etc.) and search engines (Googlebot, Bingbot, etc.) are identified by known UA substrings. Requests with browser signatures (Mozilla/, Chrome/, etc.) are classified as human. Remaining requests containing generic bot/crawler/spider keywords are classified as crawler. Empty or unrecognized UAs are unknown. The `VisitCounter` stores counts per path broken down by visitor type. The admin Stats tab displays counts per type alongside totals. No new external dependencies.

<!-- ===== COMPLETED FEATURES (High → Medium → Low) ===== -->

## F25 — Simple Visit Statistics
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Track and display simple page-visit statistics server-side without any external analytics service. Count visits to: the home page, the link blog listing page (`/raindrops/`), each individual raindrop post page, and each static page (`/pages/*`). Stats are stored in a lightweight persistent store (e.g. a JSON file or SQLite on the Fly.io volume). A stats summary is visible to the admin (e.g. at `/admin/stats`) showing visit counts per URL, sortable by count. No JavaScript tracking — counts are incremented server-side on each GET request. No personally identifiable information is stored (no IPs, no cookies).

---

## F24 — Content Type Visual Indicators
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Each item displayed in listing pages and on the home page should make its content type immediately clear to the reader. Blog posts show a distinct label or icon (e.g. "Post" badge or pencil icon). Link blog (raindrop) items show a distinct label or icon (e.g. "Link" badge or chain icon). The indicator appears consistently on listing pages, the home page, and individual post pages. Implementation uses Bootstrap badges or icons — no custom CSS.

---

## F22 — Scheduler Git Push Uses fly.toml Branch
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: The scheduler's Git sync must push content to the branch specified by `GIT_BRANCH` in `fly.toml`. The current push command (`git push origin <branch>`) fails when the local repo is checked out on a different branch (e.g. `main` built into Docker but `GIT_BRANCH=j2-experiment` at runtime). Fix: use `git push origin HEAD:<branch>` so the current HEAD is always pushed to the configured remote branch regardless of local branch name.

---

## F23 — Tag Selection for Blog Posts (UI and API)
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Blog posts created or edited via the admin web UI or the XML-RPC Blogger API can carry one or more tags. A fixed tag vocabulary is defined in code (a Python list constant). The admin create-post and edit-post forms render the vocabulary as a multi-select control (checkboxes or `<select multiple>`); selected tags are written as a YAML `tags` list in the post's frontmatter. The XML-RPC `newPost`/`editPost` handlers accept a `tags` field and persist it the same way. Tags are displayed as clickable Bootstrap badge links on `blog_post.html` and listing pages, identical to how raindrop tags are shown (F18).

---

## F21 — Raindrop Collection Filtering
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: The `/raindrops/` listing page displays a row of links at the top, one for each collection found across all raindrops. Clicking a collection link filters the displayed raindrops to show only those from that collection. The generator extracts collection names from raindrop frontmatter and generates filtered listing pages per collection.

## F19 — Configurable Front Page Post Count
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: The number of recent posts shown in each section on the home page (blog posts and raindrops) is currently hardcoded to 5. Add a `HOME_POSTS_COUNT` environment variable (default 5) read by the generator when building the home page context so operators can adjust the count without code changes.

---

## F18 — Clickable Tag Pages
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Blog posts can have a `tags` list in their YAML frontmatter. Each tag displayed on a post page or listing page becomes a link to `/tags/<tag>/index.html`, which lists all posts carrying that tag (title, date, excerpt). The generator builds one static tag page per unique tag across all blog posts. Tags are shown as Bootstrap badges on `blog_post.html`, `blog_list.html`, and `home.html` (recent posts section).

---

## F20 — Front Page "See All" Links
**Priority**: Low
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Add a "See all posts →" link below the recent blog posts section on `home.html` and a "See all links →" link below the recent raindrops section. Each links to the corresponding listing page (`/blog/` and `/raindrops/` respectively).

---

## F17 — Bootstrap-First Styling
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Replace custom CSS with the latest Bootstrap (v5.x) loaded from CDN. Remove or minimize `static/css/` overrides so the site uses Bootstrap's default components and utilities throughout all Jinja2 templates (nav, cards, pagination, tables, forms, admin UI). No custom color themes or layout overrides — accept Bootstrap defaults. Verify all pages render correctly with no broken layouts.

---

## F08 — Placeholder Title for Missing Frontmatter
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: When a content file has no `title` field in its YAML frontmatter, the generator substitutes a placeholder title derived from the filename (e.g. `placeholder title: My Post Name`). Fixed by removing stale `theme="test"` kwarg from test instantiation calls (6/6 tests pass).

---

## F07 — Scheduler Git Sync
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Periodic Git synchronization of `/data/content/` to the GitHub-backed `/app/content/` repository. Runs every N hours (configurable via `SCHED_GITSYNC_HRS`). Commits and pushes changes. Fixed by installing pytest-asyncio as a dev dependency (44/44 tests pass).

---

## F01 — Static Site Generator
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: `SiteGenerator` class reads Markdown + YAML frontmatter from three content directories (blog, raindrops, pages), renders Jinja2 HTML templates, and writes a complete static site to `output/`. Includes paginated listing pages (20/page), home page (5 recent from each type), search index JSON, 404 page, and static asset copy.

---

## F02 — Raindrop.io Bookmark Sync
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: `RaindropDownloader` fetches bookmarks from the Raindrop.io v1 REST API using a bearer token. Uses a timestamp-based cache to fetch only new items. `--reset` clears the cache and refetches everything. Each bookmark is written as a Markdown file with YAML frontmatter.

---

## F03 — FastAPI Server
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: FastAPI application that serves the generated static site from `output/`, exposes an XML-RPC endpoint for MarsEdit, provides a web admin UI with session authentication, and offers REST endpoints for triggering sync and regeneration. Validates required environment variables at startup.

---

## F04 — XML-RPC Blogger API (MarsEdit)
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: `BloggerAPI` implements the Blogger API subset needed by MarsEdit: `getUsersBlogs`, `getRecentPosts`, `newPost`, `editPost`, `deletePost`. New and edited posts trigger incremental site regeneration. Authenticated via HTTP Basic (`BLOG_USERNAME`/`BLOG_PASSWORD`).

---

## F05 — CLI Entry Point
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: `salasblog2.cli:main` argparse CLI with subcommands: `generate`, `server`, `reset`, `deploy`, `sync-raindrops`, `help`. Installed as `salasblog2` and `bg` entry points via pyproject.toml. Server command accepts `--port` and `--reload`.

---

## F06 — Incremental Site Regeneration
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: After a single post is created, edited, or deleted via the Blogger API, only the affected post's HTML, its listing page, the home page, and the search index are regenerated — avoiding a full site rebuild. `incremental_regenerate_post` and `incremental_regenerate_after_deletion` on `SiteGenerator`.

---

## F09 — Content Utility Functions
**Priority**: High
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: `utils.py` provides shared helpers: `format_date`, `create_excerpt`, `create_excerpt_with_info`, `extract_first_paragraph`, `parse_date_for_sorting`, `process_markdown_to_html`, `parse_frontmatter_file`, `generate_url_from_filename`, `sort_posts_by_date`, `group_posts_by_month`, `load_markdown_files_from_directory`, `get_markdown_processor`, `format_raindrop_as_markdown`, `generate_raindrop_filename`. Tested in `test_utils.py`.

---

## F10 — Dual Content Storage
**Priority**: High
**Status**: done | Tests written: no | Tests passing: n/a
**Description**: The generator detects `/data/content/` at startup and uses it as the primary source of truth (production Fly.io volume). Falls back to local `content/` for development. The Blogger API writes new posts to the active content directory and immediately backs up to `/data/content/`.

---

## F11 — Web Admin Interface
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Session-authenticated admin UI at `/admin/*`. Provides pages for listing/editing/deleting posts, triggering Raindrop sync, triggering Git sync, and viewing sync status. Login uses `ADMIN_PASSWORD` environment variable.

---

## F12 — Scheduler Raindrop Sync
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Periodic Raindrop.io sync runs every N hours (configurable via `SCHED_RAINSYNC_HRS`, default 2). Calls `RaindropDownloader.download_raindrops()` on schedule. Tracks last sync time and recent errors for status reporting.

---

## F13 — Fly.io Deployment
**Priority**: Medium
**Status**: done | Tests written: no | Tests passing: n/a
**Description**: `Dockerfile`, `fly.toml`, and `deploy_to_fly()` CLI command. Deploys via `fly deploy`. Documents required Fly secrets: `RAINDROP_TOKEN`, `ADMIN_PASSWORD`, `SESSION_SECRET`, `SSH_PRIVATE_KEY`, `GIT_EMAIL`, `GIT_NAME`, `GIT_BRANCH`.

---

## F14 — File Serving Security
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: The FastAPI server validates file paths to prevent directory traversal attacks when serving static files and content. Tests in `test_file_serving_security.py` (require httpx).

---

## F15 — MIME Type Handling
**Priority**: Medium
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Correct MIME types are served for all static asset types (CSS, JS, images, fonts). Tests in `test_mime_types.py` (require httpx).

---

## F16 — Pages Feature
**Priority**: Low
**Status**: done | Tests written: yes | Tests passing: yes
**Description**: Third content type: static pages (About, Contact, etc.) rendered from `content/pages/` with `page.html` template. Listed at `/pages/`. Individual pages served at `/<filename>.html`. Uses first paragraph as excerpt, no "read more". Tests in `test_pages_feature.py`.

---
