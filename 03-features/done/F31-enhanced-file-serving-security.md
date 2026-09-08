# Feature description for feature F31
## F31 — Enhanced File Serving Security
**Priority**: High
**Date Created:** 2026-03-01
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Hardened all static file serving routes in `server.py` against four attack vectors. (1) Path traversal: added `_safe_resolve()` helper that resolves the full path and verifies it remains within the expected base directory. (2) Symlink escapes: `_safe_resolve()` uses `Path.resolve()` which follows symlinks, then checks `is_relative_to()` on the resolved path, so symlinks pointing outside the base dir are rejected. (3) Hidden file exposure: `_safe_resolve()` blocks any path component starting with `.` (e.g. `.env`, `.htaccess`). (4) Permission error crashes: wrapped `read_bytes()` and `is_dir()` calls in `try/except (PermissionError, OSError)` so permission-denied conditions return 404 instead of crashing the server. Applied to `/static/`, `/raindrops/`, and the catch-all `/{path}` route handlers.

## How to Demo
**Setup**: `uv run bg server`.

**Steps**:
1. Request `/static/../../.env` (or any `../` traversal attempt) and confirm a 404, not file contents.
2. Request a path containing a hidden-file component (e.g. `/static/.env`) and confirm a 404.
3. Run `uv run pytest tests/ -k security` (or the relevant file-serving test module) and confirm all pass.

**Expected output**: All traversal, symlink-escape, and hidden-file requests return 404; no server crash on permission-denied paths.
