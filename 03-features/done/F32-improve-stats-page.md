# Feature description for feature F32
## F32 — Improving the Stats Page
**Priority**: Medium
**Date Created:** 2026-03-01
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Enhanced the admin Stats tab with time-period sub-tabs (Today, This Week, This Month, This Year, All Time) and grouped row display. `VisitCounter` storage format updated to store per-visit timestamps (with migration for old int and type-count formats). `get_all(period=)` filters by cutoff datetime. `/api/stats` endpoint accepts optional `?period=` query param. Stats table groups rows into Root, Blog, and Raindrops sections with section headers. 9 new period-filtering tests added.

## How to Demo
**Setup**: `uv run bg server`, logged in as admin.

**Steps**:
1. Open `/admin` → Stats tab.
2. Click through the Today / This Week / This Month / This Year / All Time sub-tabs and confirm counts change appropriately.
3. Confirm rows are grouped under Root, Blog, and Raindrops section headers.
4. Run `uv run pytest tests/ -k stats` and confirm all period-filtering tests pass.

**Expected output**: Stats tab shows correctly filtered, grouped visit data for each time period with no errors.
