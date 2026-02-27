# Current Session — 2026-02-26

## What was completed
- F18 Clickable Tag Pages: fixed numeric tag filtering to prevent WordPress import artifact IDs from displaying
  - Added `{% if not tag.isdigit() %}` condition to blog_post.html, blog_list.html, home.html templates
  - All 11 F18 tests passing, moved F18.md to done folder
- F19 Configurable Home Page Post Count: already complete, all tests passing
- F20 Front Page "See All" Links: already complete, all tests passing

## Currently in progress
None — all 20 features done.

## What is next
- /features-update to add new features, or /deploy to ship to Fly.io

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
| F17 Bootstrap-First Styling | Medium | done ✓ |
| F18 Clickable Tag Pages | Medium | done ✓ |
| F19 Configurable Post Count | Medium | done ✓ |
| F20 See All Links | Low | done ✓ |
| F16 Pages Feature | Low | done ✓ |
