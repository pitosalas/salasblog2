# Feature description for feature F33
## F33 — Fix and Improve Web Search
**Priority**: Medium
**Date Created:** 2026-03-02
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: The search box in the navbar does nothing when typed into. Root cause: `script.js` references `item.category` but `search.json` emits `item.type`, causing a TypeError that silently kills the filter. Fix the field name mismatch and improve search quality (raindrop content indexed, full body text, results page, etc.).

## How to Demo
**Setup**: `uv run bg generate && uv run bg server`.

**Steps**:
1. Open the site in a browser and type a query into the navbar search box.
2. Confirm results appear for both blog posts and raindrops.
3. Type a term that only appears in a raindrop's note/URL and confirm it is found.
4. Type a term that only appears deep in a long blog post body and confirm it is found (not truncated out of the index).

**Expected output**: Search returns relevant results for both content types, including raindrop notes/URLs and full-length blog post content.
