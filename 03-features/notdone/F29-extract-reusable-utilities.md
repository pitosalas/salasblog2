# Feature description for feature F29
## F29 — Extract Reusable Utilities from raindrop.py
**Priority**: Medium
**Date Created:** 2026-03-01
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Extract three generic utility functions from `raindrop.py` into `utils.py` for reuse across modules. (1) `load_json_cache(cache_file, env_var=None)` and `save_json_cache(cache_file, cache)` — extracted from the JSON cache loading/saving logic (lines 45-71). (2) `paginate_api_request(fetch_func, max_items=None, page_size=50)` — extracted from the pagination logic in `fetch_raindrops()` (lines 101-151). (3) `reset_directory_and_cache(directory, cache_file)` — extracted from `reset_data()` (lines 153-163). All extracted functions must be pure utilities with no side effects. Add unit tests for each.

## How to Demo
**Setup**: Checkout the branch with F29 applied; `uv sync`.

**Steps**:
1. Run `uv run pytest tests/test_utils_cache.py -v` and confirm the new utility tests pass.
2. Run `uv run bg sync-raindrops --reset --count 5` and confirm raindrop sync still succeeds using the extracted `load_json_cache`/`save_json_cache`/`paginate_api_request` functions.
3. Grep `raindrop.py` for the extracted logic to confirm it now calls into `utils.py` instead of duplicating it.

**Expected output**: All new unit tests pass; raindrop sync behaves identically to before the refactor; no duplicated cache/pagination/reset logic remains in `raindrop.py`.
