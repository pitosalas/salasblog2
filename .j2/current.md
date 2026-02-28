# Current Session State

## What was just completed
Improved visitor classification heuristics in `visitor_type.py`:
- Empty/missing User-Agent now classified as `crawler` (not `unknown`)
- Added `accept_language` parameter to `classify_visitor()` — browser UA without `Accept-Language` header classified as `crawler`
- Expanded `BOT_SIGNALS` with common HTTP libs (httpx, aiohttp, axios, okhttp, ruby, php, perl, etc.)
- Expanded `GENERIC_BOT_PATTERNS` with validator, reader, indexer, downloader, httpclient, request, agent
- All 3 call sites in `server.py` updated to pass `accept-language` header
- 17 tests passing

## What is currently in progress
Nothing actively in progress.

## What is next
- Deploy to see Unknown count drop in production stats
- `/features-update` to plan next milestone or `/deploy` to ship

## Open questions
None

## Feature status summary
F01–F26: all done
