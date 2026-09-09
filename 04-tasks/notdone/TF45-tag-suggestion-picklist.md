# TF45 Tag Suggestion Picklist for Post Editor

**Date Created:** 2026-09-09

## TF45.0 — Compute and cache the 100 most-used tags

**Status**: done

**Description**: `server.py`'s `generate_posts_index_cache()` already reads every
blog post's frontmatter once, on the same triggers that need to stay fresh
here (create/edit/delete, the periodic cache job, and startup). Extend it —
rather than adding a second independent cache with its own invalidation
wiring — to also tally tag frequency across those posts while it's already
reading them, and write the top 100 (by count, ties broken alphabetically)
to a small cached JSON file (e.g. `output/top-tags.json`), following the
same "pre-generate on write, serve directly on read" pattern already used
for `admin-posts-index.json` and the stats page.

Test: unit test the frequency-counting/top-100 selection logic directly
against a list of posts with known tags (not through the full cache-file
write path).

**Found during implementation**: local content confirmed a real data-quality
issue this task's plan didn't anticipate — many older, WordPress-imported
posts (`type: "wp"`) carry raw numeric WordPress category IDs (e.g. `"1221"`)
as their `tags` frontmatter, a leftover migration artifact. A naive frequency
count let these swamp genuinely useful tags — the local top-100 was almost
entirely numeric IDs. `top_tags_by_frequency()` (`utils.py`) now skips
purely-numeric tags via `tag.isdigit()`, the same check `blog_post.html`/
`blog_list.html`/`home.html` already use when rendering a post's tag badges
— confirmed this was an existing, known convention, not a new one invented
for this feature.

## TF45.1 — Serve the cached tag list to the post editor

**Status**: done

**Description**: Load `top-tags.json` when rendering `post_editor.html`
(same place `blog_tags` is currently passed into the template context from
`BLOG_TAGS`) and pass it in as the picklist's data source, replacing
`BLOG_TAGS` for this purpose. Handle the cache file not existing yet (fresh
install, before the first cache generation) by falling back to an empty
list rather than erroring.

Test: route/render test confirming the top-100 list reaches the template
context, and that a missing cache file doesn't break the page.

`load_top_tags()` (`server.py`) added: reads `output/top-tags.json`, returns
`[]` if the file doesn't exist or fails to parse — matches this task's
"nothing to error on" plan exactly. `BLOG_TAGS` import dropped from
`server.py` entirely (no longer used there — still used by `blogger_api.py`
for MarsEdit's unrelated category picker, F44, untouched by this feature).

## TF45.2 — Replace the datalist with a searchable multi-select picklist

**Status**: done

**Description**: Replace the `<input list="tagSuggestions">` / `<datalist>`
pair with a small custom widget: the existing text input stays (so typing a
free-form tag keeps working), plus a filterable panel of the 100 suggested
tags — type to narrow the list, click a tag to add it to the comma-separated
field, click again (or an "x" on an already-added tag) to remove it. Follows
the style guide's CSS/JS-in-its-own-file rule — no inline `<script>`/`<style>`
blocks added to the Python side; new JS goes in `static/js/`, reusing
`static/js/admin-delete.js`'s pattern of a small shared file loaded via
`base.html`. No new external JS dependency — vanilla JS is enough for
filter/click/toggle against a 100-item in-page list.

Test: manual test notes (command/setup/expected observation/actual result)
per the style guide's "Runtime quality" section, since this is UI interaction
behavior — plus any DOM-logic that can be reasonably unit tested in isolation
(e.g. the filter-matching function, if factored out as a pure function).

**Deviation from plan, found during implementation**: `post_editor.html`
turned out not to use `base.html`/`admin-delete.js` at all — it's a fully
standalone page (own `<head>`, own inline `<script>`/`<style>` blocks for
EasyMDE, preview, autosave, etc.), unlike `admin.html`. Matched that file's
own existing convention instead of forcing an external `static/js/` file
that would have broken from how this template already works: the picklist's
CSS was added to `post_editor.html`'s existing `<style>` block, and its JS
to the existing `<script>` block, both scoped inside
`{% if content_type == 'blog' %}` (pages have no tags field, so no picklist
DOM to wire up). No new external JS library, per the original plan.

**Manual test notes**:
- Command/setup: `uv run python -m salasblog2.cli server --port 8791`,
  then `curl http://localhost:8791/admin/new-post`.
- Expected observation: response HTML contains `id="tagPicklistToggle"`,
  `id="tagPicklistChips"`, and a `TOP_TAGS` JS array populated from
  `output/top-tags.json`.
- Actual result: confirmed present; `TOP_TAGS` correctly reflected the
  cached top-tags list, and correctly excluded the numeric WordPress-ID
  tags found in local content (see TF45.0). Extracted the inline `<script>`
  block and ran `node --check` against it — syntactically valid.
- **Not verified this session**: actually clicking a chip in a live browser
  (add/remove/filter interaction). No browser automation tool was available
  in this session — the user was mid-installation of one, but a fresh
  connection there only gets picked up by a new Claude Code session, not
  this one. The click/filter/toggle logic was verified by full code review
  (`renderTagChips`/`toggleTag`/event wiring — plain DOM APIs, no exotic
  behavior) and by the automated tests confirming the data reaching the
  page is correct, but not by driving a real browser. **You should try this
  live in `/admin` before moving on to the retagging phases**, per the
  original plan.

## TF45.3 — Wire the picklist into the existing tag-submission logic

**Status**: done

**Description**: `post_editor.html` already has `getTags()` / `tags_raw`
handling that turns the comma-separated input into the `tags` form field on
submit (F42). The picklist only needs to add/remove chips from that same
text input's value — no change to how tags are submitted or saved server-side.

Test: covered by TF45.2's manual test notes (add via click, remove via click,
free-form type, submit — all land in the saved post's frontmatter correctly).

`toggleTag()` reads/writes the same `#tags` input `getTags()`/`buildFormData()`
already use — no server-side submission path changed. Live click-through not
verified this session (see TF45.2's manual test notes); this step's actual
correctness rides on that same unverified interaction.

## TF45.4 — Write tests

**Status**: done

**Description**: Cover TF45.0's frequency/top-100 logic and TF45.1's
template-context wiring with automated tests (per-step tests above already
outline what each covers); confirm the full suite still passes.

Added: `TestTopTagsByFrequency` (`tests/test_utils.py`, 6 tests — ranking,
alphabetical tie-break, numeric-tag exclusion, limit, empty input, empty-string
tags) and `TestTopTagsCache` + `TestTagPicklistUI` (`tests/test_post_editor.py`,
5 tests — cache generation and numeric-exclusion through the real write path,
missing-cache fallback, template context wiring, pages correctly excluded).
Also updated one pre-existing F23 test
(`tests/test_blog_tags.py::test_new_post_template_offers_tag_suggestions`)
that asserted the now-removed `<datalist>` markup, to assert the picklist
markup instead — same underlying capability (tag suggestions offered),
different UI. Full suite: 551 passed, only the pre-existing unrelated
`test_raindrop.py::test_load_cache_from_env` failure remains.
