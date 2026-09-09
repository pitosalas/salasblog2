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
