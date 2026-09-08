# Feature description for feature F37
## F37 — EasyMDE Markdown Editor in Admin Post Editor
**Priority**: Medium
**Date Created:** 2026-04-15
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Replace the plain textarea in `edit_post.html` and `new_post.html` with EasyMDE (via CDN), configured for editing-only (no preview pane). Toolbar shows bold, italic, heading, image, link. Image uploads call `POST /api/upload-image` which saves to `static/images/uploads/`, `output/static/images/uploads/`, and `/data/static/images/uploads/`, returning a JSON `{url}`. EasyMDE inserts the URL as `![filename](url)` at the cursor.

## How to Demo
**Setup**: `uv run bg server`, logged in as admin.

**Steps**:
1. Open `/admin` → New Post and confirm the EasyMDE toolbar (bold, italic, heading, image, link) appears in place of a plain textarea.
2. Click the image toolbar button, upload an image, and confirm a `![filename](url)` markdown link is inserted at the cursor.
3. Save the post and confirm the image renders correctly on the published page.
4. Run `uv run pytest tests/test_upload_image.py -v` and confirm all pass.

**Expected output**: Admin post editing uses EasyMDE with working image upload; no preview pane; uploaded images are reachable immediately.
