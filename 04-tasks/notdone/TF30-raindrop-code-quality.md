# TF30 — Code Quality Improvements in raindrop.py
**Date Created:** 2026-04-18

## TF30.0 — Move magic numbers to named constants
**Status**: not done

**Description**: At the top of `src/salasblog2/raindrop.py`, replace inline literals with named constants: `DEFAULT_PAGE_SIZE = 50`, `DEFAULT_FIRST_SYNC_LIMIT = 100`, `FETCH_MULTIPLIER = 2`. Update all call sites in `fetch_raindrops()` and related methods to reference the constants. No behaviour change — purely a readability improvement.

## TF30.1 — Break down fetch_raindrops() into smaller helpers
**Status**: not done

**Description**: `fetch_raindrops()` is ~51 lines. Extract a `_fetch_page(page: int, page_size: int) -> list` helper that makes a single API call and returns the raw items list. The main `fetch_raindrops()` becomes a loop that calls `_fetch_page` until done. This makes the pagination logic independently testable.

## TF30.2 — Replace bare Exception catches with specific types
**Status**: not done

**Description**: Audit `raindrop.py` for `except Exception` blocks and replace with the most specific exception type available: `requests.exceptions.HTTPError` for HTTP failures, `requests.exceptions.Timeout` for timeouts, `requests.exceptions.ConnectionError` for network errors, `json.JSONDecodeError` for cache parse failures, `KeyError`/`ValueError` for malformed API responses. Add a log message at WARNING level for each catch that includes the exception type and message.
