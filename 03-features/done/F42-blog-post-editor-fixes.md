# Feature description for feature F42
## F42 — Fix Broken and Missing Blog Post Editing Functionality
**Priority**: High
**Date Created:** 2026-09-08
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: The admin blog post create/edit/delete workflow has nine concrete functional problems, several of them live production bugs rather than mere polish:

1. **Delete buttons are dead.** `blog_post.html` and `pages_list.html` wire "Delete" to `deletePost()`/`deletePage()`, but those functions only exist in `static/js/content-management.js`, which no template actually loads. Clicking Delete throws a JS `ReferenceError` and does nothing — no confirmation, no error shown.
2. **The delete endpoint doesn't work even if called.** `POST /admin/delete-post/{filename}` unconditionally returns `501 Not Implemented`.
3. **No way to browse existing posts from the admin panel.** The only path to `/admin/edit-post/<filename>` is via the "Edit this post" button on that specific live post page — there's no searchable/listable "All Posts" view.
4. **`new_post.html` and `edit_post.html` are hand-duplicated and have drifted.** Edit has an `image_size` field; create does not. Every future editor fix has to be applied twice.
5. **No autosave and no unsaved-changes warning.** A crashed tab or accidental navigation loses the draft. Manual posts also have no "save as draft" option — every save is instantly live, unlike the Claude-generated draft workflow.
6. **Tags are a fixed, hardcoded vocabulary** (`BLOG_TAGS` in `utils.py`) — adding a tag requires a code change and redeploy.
7. **Category isn't editable in the admin UI at all** — neither create nor edit exposes a `category` field, so it's silently whatever was already on disk.
8. **Preview is a full page round-trip**, not live — clicking Preview POSTs the whole form to a new tab instead of rendering inline.
9. **No concurrency protection.** Two admin tabs open on the same post → the later save silently clobbers the earlier one with no warning.

This feature fixes all nine, unifying create/edit into one consistent, safer editing experience.

## How to Demo
**Setup**: `uv run bg server`, logged in as admin, with at least a few existing blog posts and pages.

**Steps**:
1. From the admin panel, find and open an existing post via a new "All Posts" list (not by navigating to the live post first).
2. Edit the post, wait past the autosave interval, then hard-refresh the tab and confirm the draft is recovered (or that a "you have unsaved changes" prompt blocks navigation away).
3. Add a brand-new tag that isn't in the fixed vocabulary and confirm it saves and displays.
4. Change the post's Category and confirm it persists after save.
5. Click Preview and confirm it renders inline/live without a full page round-trip to a new tab.
6. Open the same post in two tabs, save in one, then try to save in the other — confirm a conflict warning appears instead of a silent overwrite.
7. Click Delete on a post and on a page — confirm each is actually removed from disk, from listings, and from the search index, with a real confirmation and success message.
8. Compare the New Post and Edit Post forms and confirm they now share the same fields (including Image Size and Category) and behavior.

**Expected output**: Every one of the nine problems above is fixed; create and edit behave identically; delete actually deletes; nothing is silently lost or clobbered.
