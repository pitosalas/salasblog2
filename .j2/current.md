# Current Session — 2026-02-22

## What was completed
- Deleted dead code: `scheduler_old.py` (188 stmts, 0% coverage)
- Fixed raindrop excerpt bug: raindrops with no frontmatter excerpt no longer generate excerpts from raw markdown body (which contained **URL:**, **Type:**, **Domain:** labels)
- Fixed long note display: truncated raindrop notes at 300 chars in `raindrops_list.html` using Jinja2 `truncate` filter
- Made truncation length configurable via `NOTE_TRUNCATE_LENGTH` global in `generator.py` (line 57)
- Added `tests/test_raindrop_excerpt.py` (5 tests) covering the excerpt bug fix
- Added `tests/test_generator.py` (34 tests) covering generator.py: load_posts, search index, individual post rendering, listing pages, home page, pages listing, reset, incremental regen
- Improved generator.py coverage from 32% → 73%; overall coverage from 37% → 46%
- All 202 core tests passing

## Currently in progress
Nothing — all 16 features done.

## What is next
- `/features-update` to add new features, or `/deploy` to ship to Fly.io
- Consider adding httpx to dev deps to enable server/blogger_api tests without separate install

## Open questions
- None

## Feature status summary

| Feature | Priority | Status |
|---------|----------|--------|
| F01 Static Site Generator | High | done ✓ |
| F02 Raindrop.io Bookmark Sync | High | done ✓ |
| F03 FastAPI Server | High | done ✓ |
| F04 XML-RPC Blogger API | High | done ✓ |
| F05 CLI Entry Point | High | done ✓ |
| F06 Incremental Site Regen | High | done ✓ |
| F07 Scheduler Git Sync | High | done ✓ |
| F09 Content Utility Functions | High | done ✓ |
| F10 Dual Content Storage | High | done ✓ |
| F08 Placeholder Title | Medium | done ✓ |
| F11 Web Admin Interface | Medium | done ✓ |
| F12 Scheduler Raindrop Sync | Medium | done ✓ |
| F13 Fly.io Deployment | Medium | done ✓ |
| F14 File Serving Security | Medium | done ✓ |
| F15 MIME Type Handling | Medium | done ✓ |
| F16 Pages Feature | Low | done ✓ |
