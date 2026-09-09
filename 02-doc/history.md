# History

## Session: F40 — Drafts UI Polish and Admin Performance Improvements
_Completed and deployed to fly.io (as of the last update to this file's predecessor, 2026-04-18)._

1. **Drafts body not displaying** — `d.body` in template literal broke on backticks/`${` in Claude output. Fixed: added `escapeHtml()`, set body via `textContent` not innerHTML.
2. **"Edit & Post" button not rendering** — same root cause as above. Now works.
3. **Stats page redesign** — pre-generated static HTML via `generate_stats_cache()`, served via iframe, refreshed every 60s. Zero computation on GET.
4. **Non-blocking draft generation** — Claude API + URL fetch in `run_in_executor`.
5. **Draft list fast glob** — `draft-*.md` glob instead of scanning all 2800 posts.
6. **Delete draft endpoint** — `POST /api/delete-draft`.
7. **Publish sets today's date** — so published drafts appear as newest post.
8. **"Originally Posted on:" prefix** — added to all generated drafts.
9. **Claude prompt shortened** — 50–75 words, `max_tokens=150`.
10. **config.yaml** — centralised runtime parameters, read by server.py, generator.py, draft_generator.py.
11. **Test fix** — `'display: none'` → `'d-none'` in live server test assertion.

---

## Session: 2026-09-08 — scaffold rename, F42, F44, deploy-pipeline gotcha

### Process/scaffold cleanup
- Renamed all feature/task files from `FNN.md` to `FNN-<slug>.md` / `TFNN-<slug>.md`, retroactively, including `done/`-archived ones, per the repo-wide-convention-change rule. Renumbered task steps from bare `T0N` to `TFNN.N`.
- Reformatted `.claude/process.md`: one statement per bullet (was mixing several rules per bullet via semicolons), bolded key gating rules.
- Bootstrapped support files: `Makefile`, `.githooks/pre-commit`, `02-doc/history.md` (this file), `settings.json` env block.
- Made the project `Makefile` self-contained (`run`/`local`/`deploy` targets inline their commands) and deleted `run.bash`. Also updated the canonical scaffold kit (`.claude/bootstrap.md`, `.claude/templates/Makefile.template`, copied to `~/mydev/j3/.claude`) to the same self-contained pattern for future bootstraps.
- Added `make deploy` (`uv run bg deploy`) and `make local` (`uv run bg server --reload`).

### F42 — Fix Broken and Missing Blog Post Editing Functionality (done)
Fixed all 9 originally-reported problems (dead Delete buttons, 501 delete stub, no admin post browser, duplicated new/edit templates, no autosave, fixed tag vocabulary, no category field, round-trip preview, no concurrency protection), plus 3 more found while implementing:
- `page.html` and `raindrop_post.html` had the same dead-delete-button bug, not in the original report.
- `raindrop_post.html`'s delete button called the *blog* delete endpoint (wrong content directory) — added `POST /admin/delete-raindrop/{filename}`; removed its broken "Edit Post" link (no raindrop-editing flow exists — raindrops are Raindrop.io-synced, not authored).
- Delete endpoints had an auth-check inconsistency (`is_admin_authenticated()` alone, unlike every other route's `config["admin_password"] and not is_admin_authenticated()`) — fixed to match.

`new_post.html`, `edit_post.html`, `preview_post.html`, `preview_new_post.html`, `static/js/content-management.js` deleted. Replaced by `templates/post_editor.html` (unified create/edit) and `static/js/admin-delete.js` (shared delete handlers, loaded globally via `base.html`). New admin "All Posts" tab backed by a pre-generated `output/admin-posts-index.json` (refreshed after every create/edit/delete + every 5 minutes).

### F44 — Fix the MetaWeblog/XML-RPC Implementation (MarsEdit Support) — 5 of 6 tasks done
Replaced the hand-rolled `ElementTree` request parser and string-built response/fault builders in `xmlrpc_endpoint()` with `xmlrpc.client.loads()`/`dumps()`. Fixed: missing `dateTime.iso8601`/`<array>` parsing (silently dropped fields — likely why MarsEdit "didn't work at all"), unescaped response XML (`&`/`<`/`>` in content broke responses), `<base64>` now correctly unwrapped from `xmlrpc.client.Binary`, auth-fault code fidelity (401 was being squashed to a hardcoded 403), and made XML-RPC post regeneration non-blocking (`BackgroundTasks`, mirroring F38's pattern). **Found during first production test**: every XML-RPC response was missing its charset (`Content-Type: text/xml` instead of `text/xml; charset=utf-8`) because an explicit `headers={...}` override was suppressing Starlette's automatic charset suffix — likely contributor to "Response Parsing Failed" on any post with non-ASCII characters. Fixed; regression tests added for response headers, not just bodies.

**TF44.4 (manual MarsEdit verification) still open** — blocked on getting this session's code actually deployed (see below), not yet retested end-to-end against real MarsEdit.

### Deploy-pipeline gotcha (rediscovered, already documented at `02-doc/current.md`'s Deployment section)
`startup.sh` runs `git checkout -f -B main origin/main` on every boot (since `GIT_TOKEN` is set in production), overwriting whatever `COPY . .` baked into the Docker image with the last-pushed GitHub `main` HEAD. Three deploys this session silently kept serving pre-session code because nothing had been committed/pushed yet — confirmed via `fly ssh console` that the running container was on commit `e909c27` (the pre-session HEAD) despite fresh-looking deploys. **Commit and push are a hard requirement before `make deploy` actually ships anything**, not just good practice.

---

## Session: 2026-09-08 (continued) — TF44.4 manual MarsEdit verification, diagnostic logging, real bugs found

### Diagnosed and fixed: MarsEdit "Refresh Blog" → "XMLRPC Response Parsing Failed: (null)"
Added diagnostic logging to `xmlrpc_endpoint()` in `server.py` (request user-agent, result repr before marshalling, `logger.exception` instead of `logger.error` for full tracebacks, and — genuinely load-bearing, kept permanently — wrapped `create_xmlrpc_response()` in its own try/except so a marshalling failure can't crash uncaught into an HTML 500 page). The logging showed every refresh attempt landing as `GET /xmlrpc`, never `POST`. Root cause: MarsEdit's endpoint was configured as `http://salas.com/xmlrpc`; `fly.toml`'s `force_https = true` makes Fly's edge return a 301 to the `https://` URL, and MarsEdit's HTTP client replays a 301 on a POST as a GET, silently dropping the XML-RPC body — confirmed with `curl -X POST http://salas.com/xmlrpc`. Not a server bug; fixed by pointing MarsEdit at `https://salas.com/xmlrpc`. Refresh, edit, and image upload all confirmed working against production afterward.

### Real bugs found during manual verification, fixed
- `metaweblog_getCategories` was a hardcoded `["General", "Technology"]` stub, unrelated to this blog's actual tags (F42 built it around free-form tags, not a fixed taxonomy) — now returns `BLOG_TAGS`.
- `blogger_getPost`/`blogger_getRecentPosts` never returned a `link` (permalink) field, so MarsEdit's Link field was always empty; their MetaWeblog wrappers also hardcoded `categories: ["General"]` instead of each post's real tags. Both fixed.
- `create_excerpt_with_info()` (`utils.py`) truncated by raw character count, which could cut mid-`**bold**`, mid-`[link](url)`, or mid-`<tag>`, leaving a dangling marker that printed literally instead of being dropped — added `_trim_dangling_markup()`.
- Same function also collapsed all newlines into spaces *before* truncating, so a `## Heading`/`> quote`/`* bullet` written correctly on its own line in MarsEdit ended up mid-sentence, where markdown no longer recognizes the marker as a block construct and prints it literally (confirmed with the user: the source markdown was correctly formatted; the bug was entirely server-side). Added `_strip_block_markdown_markers()`, applied per-line before collapsing.
- `home.html` had no "Read more" link for a truncated excerpt — `blog_list.html` already had one (conditional on `post.is_truncated`), `home.html` didn't. Added, matching the existing pattern.
- All logged in `04-tasks/chores.md` (retroactively, since they weren't logged as chores at fix time) along with one still-pending: `BloggerAPI` doesn't follow the volume-first content-directory pattern `get_content_directory()`/`SiteGenerator` already use, which is the likely cause of a separate user-reported bug (MarsEdit showing a stale post even after refresh). Proposed, not yet approved/implemented.

### Two commits pushed this session (not yet deployed)
`9e08d2b` (categories/link/excerpt-truncation fixes) and `2275fc6` (block-markdown-marker stripping + home page Read more link). `fly.toml`'s `EXCERPT_LENGTH`/`EXCERPT_SMART_THRESHOLD` were also manually retuned from 300/400 to 700/300 during this session (by the user, not via a commit I authored, but included in `9e08d2b`).

### BloggerAPI made volume-first (chore, approved and implemented)
User reported MarsEdit showing a stale post even after refresh. Root cause: `BloggerAPI.__init__` hardcoded `blog_dir` to `root_dir/content/blog` (the ephemeral container filesystem), never checking `/data/content` like `get_content_directory()` (`server.py`) and `SiteGenerator` (`generator.py`) already do. Writes went to `content/blog` first, then an explicit `_backup_to_volume()` copied to `/data/content/blog` — but reads only ever looked at `content/blog`. Two ways that showed a stale post: a web-admin edit (writes straight to `/data/content` only) was invisible to MarsEdit until the next scheduled GitHub sync; and a container restart between a MarsEdit edit and the next MarsEdit read reverted `content/blog` to the last-pushed git commit via `startup.sh`'s `git checkout -f`, while `/data/content` (and the live site) kept the newer version.

Fixed: `__init__` now resolves `blog_dir` under `/data/content` when it exists, same as the rest of the codebase. `_backup_to_volume()`/`_delete_from_volume()` deleted entirely — writes/deletes go straight to the volume-resolved location, so there's nothing left to reconcile after the fact. `metaweblog_newMediaObject`'s separate media-upload volume backup was left untouched (different concern — media intentionally lives in three copies for different reasons: source for git sync, output for immediate serving, volume for persistence). Tests: `TestBackupToVolume` replaced with `TestVolumeFirstContentDir` (verifies the `__init__` resolution against both a present and absent `/data/content`) and `TestNewEditDeletePost` (verifies writes/deletes land directly). `01-literate/06-blogger_api.md` updated to match (this doc's own "Observations for future improvement" section had already flagged this exact bug in an earlier session, before it was known to be live).

### All literate docs regenerated from scratch; full-repo style-guide pass
User asked for two large follow-on tasks, done without stopping for further confirmation per explicit instruction: (1) recreate every `01-literate/*.md` doc from scratch, and (2) run the whole repo against `.claude/style_guide.md` and fix what needed fixing.

**Literate docs**: dispatched 9 parallel general-purpose agents (one per module, two small modules doubled up per agent) to read each source file fresh and write an independent narrative doc, in dependency order: `01-utils`, `02-stats`, `03-visitor_type`, `04-propose`, `05-draft_generator`, `06-raindrop`, `07-generator`, `08-blogger_api` (replacing the old `06-blogger_api.md`, deleted), `09-scheduler`, `10-server`, and `X01-cli` (appendix — small, self-evident glue). The `blogger_api.py` agent was given the historical/design context (F34 volume-backup incident, F42 free-form-tags-not-categories, the volume-first fix from earlier this session) explicitly, since none of that is derivable from reading the code alone. Several agents independently surfaced real findings worth a future look (not fixed this session, out of scope for a docs/style pass): `generator.py`'s incremental regeneration writes `search.json` with `pages=[]`, silently dropping Pages from search until the next full rebuild; `stats.py` has a latent dict-mutated-during-iteration race between `increment()`/`flush()` and `get()`/`get_all()`, plus no cross-process file lock; `visitor_type.py`'s docstring promises an `"unknown"` classification the code never actually returns; `scheduler.py` has dead "run once at startup" job machinery (`_handle_sync_result`, `_cleanup_startup_job`) that's never wired up, and its `schedule.clear()` wipes jobs process-wide since `schedule` uses one global registry that `server.py`'s `lifespan()` also registers directly against.

**Style-guide pass**: repo-wide `ruff check`/`ruff format` was 92 violations at session start, 0 at the end. Fixed relative imports to absolute (`generator.py`, `raindrop.py`, `cli.py` — including a `from .server import app` inside `cmd_server` that was missed on the first pass; `scheduler.py`'s lazy in-function imports moved to top-level, confirmed no circular-import risk via a dependency grep first). Added the missing required file header (shebang/module-line/Author/license) to `generator.py`, `raindrop.py`, `cli.py`, `scheduler.py`, `utils.py`, `__init__.py` — the pre-commit hook auto-stamps Version/Created/Updated on next commit, so these were written without hand-writing those three fields, per the style guide's own instruction. Mechanical fixes (`ruff check --fix`, unused imports/f-strings) applied everywhere; judgment-required fixes (unused variables, bare excepts) handled file by file, preserving each function's actual side effects.

Two fixes went beyond linting into real bugs/gaps: `scripts/debug_content_dirs.py`'s `main()` had a redundant `from pathlib import Path` inside a `try` block that shadowed the module-level import for the whole function scope, so the earlier `Path.cwd()` call would have raised `UnboundLocalError` if the script were ever run — found via ruff's F823 (variable referenced before assignment). And `tests/deployment/test_checksum_sync.py::test_identical_content_skipped` computed `initial_dest_mtime`/`final_dest_mtime` but never compared them despite the comment claiming to verify exactly that — a genuine test-coverage gap. First fix attempt (assert the two mtimes equal) was itself wrong and failed in CI-style testing: `rsync -a --checksum` still syncs destination mtime via `-a`'s `-t` regardless of whether `--checksum` decided to skip the data transfer, so mtime equality doesn't prove anything about whether a transfer was skipped — reverted to removing the dead variables with a comment explaining why, rather than shipping an incorrect assertion.

All 40+ touched test files: `ruff format .` also reformatted ~26 files project-wide that weren't otherwise touched (pure whitespace/formatting, confirmed via `git diff --stat`). Full test suite: 536 passed, 12 skipped, 1 pre-existing unrelated failure throughout — no regressions introduced by any of this pass.

---

## Session: 2026-09-09 — home page markdown formatting, F45 tag picklist, bulk retagging

### Excerpt formatting continued: headers as bold inline text
User reported the front page "better but headers are not styled a little larger and bold. they are just plain text" — a follow-on to the earlier excerpt paragraph-break fix. Headers crossed by an excerpt were fully flattened (block marker stripped, no visual treatment). Fixed by wrapping header text in `<strong class="excerpt-heading">` (not a real `<h1>`-`<h6>`, which would inherit Bootstrap's much larger size and can't validly nest inside `blog_list.html`'s `<p>` wrapper) with matching CSS in `style.css`. `_trim_dangling_markup()` extended to also drop a truncation cut landing mid-heading-span.

### F45 — Tag Suggestion Picklist for Post Editor (done)
User asked for a real feature this time: the post editor's Tags field only suggested from the static 15-tag `BLOG_TAGS` via a single-match `<datalist>`. Per process, wrote `03-features/notdone/F45-tag-suggestion-picklist.md` + `04-tasks/notdone/TF45-*.md` and stopped for approval before coding, per the process gate.

Once approved: `generate_posts_index_cache()` (`server.py`) extended to also tally tag frequency (piggybacking on frontmatter it already reads for `admin-posts-index.json`) and write the top 100 to `output/top-tags.json`; `top_tags_by_frequency()` (`utils.py`) does the ranking, excluding purely-numeric tags — real content confirmed old WordPress-imported posts carry raw category IDs as tags, which would otherwise swamp genuine ones (same `tag.isdigit()` convention the templates already use for tag badges). `post_editor.html` got a searchable click-to-add/remove picklist replacing the datalist, implemented inline in that template's own existing `<script>`/`<style>` blocks rather than a new `static/js/` file — discovered mid-implementation that `post_editor.html` doesn't use `base.html`/`admin-delete.js`'s pattern at all, unlike originally assumed in the plan.

Confirmed working live by the user ("it does work but it is a little ugly. Ok for now" — visual polish explicitly deferred, not blocking). Feature closed, moved to `03-features/done/`.

Follow-up fix: `top_tags_by_frequency()` got an `always_include` parameter (`BLOG_TAGS` passed at the real call site) — a curated tag with zero real usage yet would otherwise never surface in the ranking, and could never start being used since it's never offered.

No live browser tool was available this session to click-test the picklist directly (user was mid-installing one; a fresh connection there only gets picked up by a new Claude Code session). Verified instead via: HTML/JS structure served correctly with real cached data, `node --check` on the extracted inline script, and full-coverage automated tests (cache generation/numeric-exclusion through the real write path, template-context wiring, pages correctly excluded).

### Bulk retagging — two batches, real production data
Once F45 shipped, user asked to retag content in stages: first the 100 most recent posts (for review), then scale up once approved. Two distinct selection criteria ended up in play:

1. **Most recent 100** — straightforward, sorted by `admin-posts-index.json`'s date field.
2. **Most-visited 100** — user asked to use real traffic data instead. The *local* `stats.json` turned out to be seeded test/fixture data (`test-raindrop.html`, `example-article.html` — not real visits), so the actual production file was pulled via `fly ssh sftp get /data/stats.json` (77MB). Raw total-visit counts were dominated by draft posts (`draft-*.html`, not linked anywhere on the site) and bot/crawler/search-engine traffic — `visitor_type.py`'s "human" classification was used instead, and drafts excluded entirely, to get a ranking that actually reflects real readers of real posts.

Cross-referencing the two lists surfaced a real gap: **3 of the top-visited posts (including #1 and #3) exist only on the production volume, never synced to GitHub** — confirmed via `fly ssh sftp find` showing both an old duplicate-named post and the actual current one only on `/data/content/blog`, not in this repo's git history. Fetched directly via SFTP and included in the review rather than silently skipped; the sync gap itself wasn't diagnosed further or filed as an issue this session.

For each batch: read every post's actual title/excerpt, assigned tags from the curated vocabulary based on real content analysis (not keyword matching), removed any numeric-junk or non-vocabulary tags. Verified rigorously before ever committing: every file's body content diffed byte-for-byte against `git show HEAD` (zero corruption across 177 unique posts total), every file re-parsed with the real `frontmatter` library to confirm valid YAML and exact expected tags, full test suite green throughout.

Built a searchable/filterable review artifact (batch toggles, numeric-junk/no-fit filters) rather than dumping 177 rows of text, republished in place as the second batch was added.

User then said: "you can commit the 77 pages" (the traffic-only posts not already in the recent-100 batch) and separately asked to hardwire `curacao`/`boston`/`brandeis`/`jewish`/`arlington` as new curated tags — found via content review (a Curaçao family-reunion post, a Boston Globe press mention, a Brandeis-teaching reference, a Curaçao Jews history page). Added to `BLOG_TAGS`, applied where a clear match existed in the 77 being committed (2 of the 5 new tags had matches in that batch), and applied to 2 more posts that exist in the still-pending recent-100 batch (updated on disk, deliberately left unstaged since only "the 77" was approved for commit). Verified the staged diff contained exactly the 77 traffic-only files (0 recent-only files) before committing.

The recent-100 batch (100 posts, 23 of which are also in the now-committed traffic batch) remains uncommitted, awaiting the user's review of the same artifact.
