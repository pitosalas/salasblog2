# TF32 — Improving the Stats Page
**Date Created:** 2026-03-01

## TF32.0 — Add time-period filtering to VisitCounter
**Status**: done

**Description**: Extend `stats.py` `VisitCounter` to support time-period filtering. Store a timestamp with each visit entry. Add a `get_all(period=None)` method where `period` can be `today`, `this_week`, `this_month`, `this_year`, or `None` (all-time). This requires changing the storage format to include date information alongside the visitor-type counts.

## TF32.1 — Update /api/stats endpoint to accept period parameter
**Status**: done

**Description**: Update the `/api/stats` endpoint in `server.py` to accept an optional `period` query parameter (`today`, `this_week`, `this_month`, `this_year`). Pass it through to `get_counter().get_all(period=period)`. Default to all-time when not provided. Maintain backwards compatibility.

## TF32.2 — Add sub-tabs to Stats tab in admin.html
**Status**: done

**Description**: Update `templates/admin.html` Stats pane (`#tab-stats`) to show five sub-tabs: Today, This Week, This Month, This Year, All Time. Each sub-tab calls `loadStats(period)` which fetches `/api/stats?period=<value>`. Use Bootstrap btn-group for the sub-tab UI, consistent with existing admin styling. Default to Today on first load.

## TF32.3 — Sort stats rows into root, blog/, and raindrops/ sections
**Status**: done

**Description**: Update the stats table rendering in `admin.html` `loadStats()` JS function to group rows into three sections: (1) root and top-level pages (paths not under `/blog/` or `/raindrops/`), (2) paths under `/blog/`, (3) paths under `/raindrops/`. Add a section header row between groups. Sort within each group by total count descending.

## TF32.4 — Write tests for F32 stats improvements
**Status**: done

**Description**: Add tests covering: (1) `VisitCounter.get_all(period='today')` returns only visits from today, (2) period filtering works for `this_week`, `this_month`, `this_year`, (3) `get_all()` with no period returns all-time data (backwards compat), (4) `/api/stats?period=today` endpoint returns filtered data.
