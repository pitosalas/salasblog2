# Feature description for feature F41
## F41 — Codebase Cleanup and Architectural Consistency
**Priority**: Medium
**Date Created:** 2026-04-18
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: A systematic cleanup pass across all source files to enforce coding standards, separate concerns, and improve responsiveness. Four focus areas:

### 1. Coding standards compliance (style_guide.md)
Review all Python source files in `src/salasblog2/` against `.claude/style_guide.md`. Key violations to fix:
- Remove leading underscores from private methods, functions, and instance variables (e.g. `_load_cache`, `_fetch_page`, `_build_stats_for_period`) — the standard says no underscore prefix for privates
- Ensure all files have the correct three-line header (shebang, module name/description, author, license)
- Replace any `Optional[X]` with `X | None`
- No bare `except Exception:` — use specific types
- Functions/methods over 50 lines should be broken down
- Files over ~300 lines should be split

### 2. JavaScript separation
All JavaScript currently embedded in HTML templates (`admin.html`, `stats_page.html`, etc.) should move to `.js` files under `static/js/`. HTML templates should only contain `<script src="...">` tags. No inline `<script>` blocks. Python files (`server.py`) should not contain HTML string literals. **Excluded from this task**: `new_post.html`/`edit_post.html` — F42 unifies and rewrites these into a shared editor template with its own proper JS separation as part of that work, so extracting their current inline JS here would just be redone (or thrown away) by F42.

### 3. JavaScript reduction
Audit all JavaScript in `static/js/script.js` and the admin templates. Identify and remove:
- Dead code (functions no longer called)
- Duplicate logic across admin tab handlers
- Overly defensive polling/retry patterns that add complexity without value
- Functions that can be replaced with simpler HTML form submissions

### 4. GET endpoints return static files
All `GET` routes should do minimal work — ideally just read and return a pre-generated file. Any route that currently computes data on the fly (parses markdown, scans directories, calls external APIs) should instead: (a) return a cached/pre-generated file, and (b) trigger background regeneration of that file if stale. Pattern already established by the stats page (`admin-stats.html`) — apply it consistently to other expensive GETs (propose lists, draft lists, etc.). Responsiveness is preferred over guaranteed freshness.

### 5. Architecture review against current requirements
Step back and review the overall architecture of the application against what it actually needs to do today. Look for patterns that were reasonable when first written but are now wrong, over-engineered, or mismatched with how the system is actually used. Questions to answer:
- Does the module decomposition still make sense? (`server.py` at ~1850 lines is almost certainly doing too much.)
- Is the scheduler the right primitive for background work, or would a simpler approach (e.g. time-based cache invalidation on first request) be cleaner?
- XML-RPC/Blogger API support is being kept and fixed under F44 (to restore MarsEdit) rather than removed — record that decision here rather than re-litigating it; instead assess whether the *implementation*, once on stdlib `xmlrpc` marshalling per F44, can be simplified further (e.g. fewer supported methods).
- Is the volume-first content architecture (`/data/content` → `/app/content` → output) still the right model, or does it introduce unnecessary duplication and sync complexity?
- Are there abstractions that were added speculatively (YAGNI violations) that can be deleted?
- Are there places where two systems do the same thing (e.g. both the scheduler and the admin UI trigger site regeneration) with no clear ownership?
The output of this review is a written findings document (`process/arch-review.md`) with specific recommendations — not code changes. Code changes follow in subsequent features.

## How to Demo
**Setup**: Checkout the branch with F41 applied; `uv sync`.

**Steps**:
1. Grep `src/salasblog2/*.py` for leading-underscore private names and confirm none remain (dunders excepted).
2. Grep the same files for the required file-header lines and confirm all are present.
3. Grep `templates/*.html` for inline `<script>` blocks and confirm none remain (other than a minimal config-variable block, if any).
4. Read `process/arch-review.md` and confirm it contains findings for module decomposition, scheduler/background work, XML-RPC implementation simplification (given F44 already settled whether to keep it), volume-first architecture, and YAGNI abstractions.
5. Run `uv run pytest` and confirm the full suite still passes.

**Expected output**: Source files conform to the style guide, no inline JS/HTML string literals remain in templates/Python, GET routes read pre-generated files, and `process/arch-review.md` documents the architecture findings with concrete recommendations.
