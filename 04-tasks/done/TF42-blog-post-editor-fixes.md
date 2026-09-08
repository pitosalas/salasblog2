# TF42 — Fix Broken and Missing Blog Post Editing Functionality
**Date Created:** 2026-09-08

## TF42.0 — Fix dead Delete button wiring
**Status**: done

**Description**: `blog_post.html` and `pages_list.html` call `deletePost()`/`deletePage()` on click, but those functions live only in `static/js/content-management.js`, which is never loaded by any template. Either load a corrected version of that script on the relevant pages or replace the dead stub functions with working inline handlers (fetch call, confirm dialog, success/error status) consistent with the rest of the admin JS. Remove the now-redundant `content-management.js` stub functions once real handlers exist elsewhere (see TF42.3 for the broader dead-code cleanup of that file).

## TF42.1 — Implement the delete endpoint
**Status**: done

**Description**: Replace the `501 Not Implemented` stub at `POST /admin/delete-post/{filename}` with a real implementation: admin-auth-gated, removes the file from the active content directory and its volume backup, and triggers incremental regeneration so the post disappears from listings, the home page, and the search index. Add the equivalent for pages (`POST /admin/delete-page/{filename}`) if it doesn't already exist as a working route.

## TF42.2 — Add an "All Posts" admin list view
**Status**: done

**Description**: Add a new admin view (tab or page) listing existing blog posts (and pages) with title, date, and Edit/Delete actions, with basic search/filter. Follow the pre-generated-static-file pattern used elsewhere in the admin panel (e.g. the stats page) rather than scanning thousands of files per request — a background job maintains a small JSON/HTML index that this view reads.

## TF42.3 — Unify new_post.html and edit_post.html into a shared editor
**Status**: done

**Description**: Merge the two hand-duplicated templates (or extract a shared partial/include) so create and edit render identical fields and share one copy of the EasyMDE setup, status-message handling, and preview/save JS. This fixes the missing `image_size` field on the create form as a side effect. Delete `static/js/content-management.js` once its dead `deletePost`/`deletePage`/`deleteRaindrop` stubs and duplicate `createPost`/`savePost`/`previewPost`/`autoSave` functions are no longer needed by anything.

## TF42.4 — Add autosave and an unsaved-changes warning
**Status**: done

**Description**: Enable EasyMDE's built-in `autosave` (localStorage-backed) option on the shared editor so in-progress content survives a crashed tab, and add a `beforeunload` handler that warns before navigating away with unsaved changes. Consider adding an explicit "Save as Draft" option for manually-written posts, mirroring the `draft: true` frontmatter flag already used by the Claude-generated draft workflow.

## TF42.5 — Replace the fixed tag vocabulary with free-form tag entry
**Status**: done

**Description**: Replace the `BLOG_TAGS`-driven checkbox list with a free-form tag input (e.g. a simple comma-separated field or a tag-input widget) that still offers existing tags as autocomplete suggestions, so a new tag doesn't require a code change and redeploy. Update `blogger_api.py`'s XML-RPC tag handling to match if it currently assumes the fixed vocabulary.

## TF42.6 — Add an editable Category field
**Status**: done

**Description**: Add a `category` input to the shared editor (create and edit), pre-filled with the post's existing value when editing, and have `save_content_item()` write it to frontmatter. Currently no admin UI path can set or change a post's category.

## TF42.7 — Replace round-trip Preview with inline/live preview
**Status**: done

**Description**: Replace the current "POST the whole form to a new tab" preview with an inline preview panel on the same page — either EasyMDE's side-by-side/preview mode, or a debounced call to the existing `/admin/preview-markdown` endpoint rendered into a panel without a full navigation.

## TF42.8 — Add concurrency/conflict protection on save
**Status**: done

**Description**: When the edit form loads, capture a version marker for the file (e.g. mtime or content hash). On save, compare against the current on-disk value; if it has changed since the form was loaded, reject the save (409) and show a clear conflict message instead of silently overwriting another admin's concurrent edit.

## TF42.9 — Write tests for all of the above
**Status**: done

**Description**: Add/extend tests covering: delete endpoint removes the file and updates listings/search index; the new admin post-list endpoint returns correct data; the unified editor template renders the same fields for create and edit; a freely-entered tag round-trips through save and display; category persists through create and edit; a concurrent-edit conflict is detected and rejected rather than silently overwritten.

Findings and scope additions made along the way:

- **Two more broken delete buttons found beyond the reported blog_post.html/pages_list.html pair**: `page.html` (individual page view) and `raindrop_post.html` (link blog post view) both had the same "calls a function that's never loaded" bug. `raindrop_post.html`'s delete button also called the *blog* delete endpoint (`/admin/delete-post/...`), which would 404 since raindrops live in a separate content directory — a distinct bug from the missing-JS one. Added `POST /admin/delete-raindrop/{filename}` and fixed the wiring; also removed `raindrop_post.html`'s "Edit Post" link, which pointed at the blog edit route and would also 404 — there is no raindrop-editing admin flow (raindrops are Raindrop.io-synced, not manually authored), so a misleading button was removed rather than a new editing feature built.
- **`base.html` had its own separate, working `deletePost(filename)`** (1-arg, `alert()`-based) that the original bug analysis missed — the real problem for blog posts was only ever the backend's `501` stub, not a missing frontend function. Consolidated all delete handling (post/page/raindrop) into one shared `static/js/admin-delete.js`, loaded globally via `base.html`, instead of four separate per-template copies.
- **Delete endpoints had an auth-check inconsistency**: they gated on `is_admin_authenticated(request)` alone, unlike every other admin route's `config["admin_password"] and not is_admin_authenticated(request)`. This meant delete would wrongly require a session even when no admin password is configured (the app's documented "unrestricted access" mode). Fixed to match the established pattern.
- `content-management.js` deleted (was never loaded by anything, contained only dead stub functions).
- `preview_post.html`/`preview_new_post.html` and their `/admin/preview-post`/`/admin/preview-new-post` routes deleted (superseded by inline preview via `/admin/preview-markdown`).
