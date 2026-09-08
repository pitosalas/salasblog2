# Feature description for feature F30
## F30 — Code Quality Improvements in raindrop.py
**Priority**: Low
**Date Created:** 2026-03-01
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Three low-priority code quality improvements in `raindrop.py`. (1) Move magic numbers (`DEFAULT_PAGE_SIZE = 50`, `DEFAULT_FIRST_SYNC_LIMIT = 100`, `FETCH_MULTIPLIER = 2`) to configuration constants or environment variables for flexibility. (2) Break down `fetch_raindrops()` (51 lines) by extracting pagination helper methods to improve readability and testability. (3) Replace generic `Exception` handling with specific exception types for different error scenarios to enable better error diagnosis.

## How to Demo
**Setup**: Checkout the branch with F30 applied; `uv sync`.

**Steps**:
1. Grep `raindrop.py` for the named constants (`DEFAULT_PAGE_SIZE`, `DEFAULT_FIRST_SYNC_LIMIT`, `FETCH_MULTIPLIER`) and confirm they replace the former inline literals.
2. Read `fetch_raindrops()` and confirm pagination is delegated to a helper method.
3. Grep for `except Exception` in `raindrop.py` and confirm only specific exception types remain.
4. Run `uv run pytest tests/` and confirm no regressions.

**Expected output**: No behavior change — raindrop sync works exactly as before, but the code is more readable and errors are diagnosable by type.
