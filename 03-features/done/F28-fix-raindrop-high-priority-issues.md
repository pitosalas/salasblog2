# Feature description for feature F28
## F28 — Fix raindrop.py High-Priority Issues
**Priority**: High
**Date Created:** 2026-03-01
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Two high-priority fixes in `raindrop.py`. (1) Replace the four duplicate instances of `datetime.fromisoformat(date_str.replace("Z", "+00:00"))` (lines 83, 291, 303, 309) with calls to the existing `utils._parse_iso_date()` function for consistent date handling. (2) Fix hardcoded `/data/content/` paths (lines 31-32) by adding the same fallback logic used in `generator.py`: check `/data/content/` first, fall back to local `content/` for development.

## How to Demo
**Setup**: `uv sync`.

**Steps**:
1. Grep `raindrop.py` for `datetime.fromisoformat` and confirm no duplicated inline date parsing remains — all calls go through `utils._parse_iso_date()`.
2. Run `uv run bg sync-raindrops --count 5` locally (no `/data/content/` present) and confirm it falls back to local `content/` without error.

**Expected output**: Date parsing is centralized in `utils.py`; raindrop sync works in both production (`/data/content/`) and local dev (`content/`) layouts.
