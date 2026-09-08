# Feature description for feature F36
## F36 — MarsEdit Image Upload Support
**Priority**: Medium
**Date Created:** 2026-04-15
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Implement `metaWeblog.newMediaObject` in the XML-RPC API so MarsEdit can upload images directly to the server. The method receives binary image data plus a filename and MIME type, saves the file to `static/images/uploads/` (source), copies it to `output/static/images/uploads/` (served immediately), and backs it up to `/data/static/images/uploads/` (volume persistence). Images are also included in the git sync so the full site can be reconstructed from GitHub. Returns a public URL `/static/images/uploads/<filename>`. Filenames are prefixed with the date (e.g. `2026-04-15-original.jpg`) to avoid collisions.

## How to Demo
**Setup**: `uv run bg server`, MarsEdit configured against the local XML-RPC endpoint.

**Steps**:
1. In MarsEdit, insert an image into a post via the image upload control.
2. Confirm the returned URL is reachable immediately (`/static/images/uploads/<date>-<filename>`).
3. Confirm the file exists in `static/images/uploads/`, `output/static/images/uploads/`, and (in production) `/data/static/images/uploads/`.
4. Run `uv run pytest tests/test_xmlrpc_parsing.py tests/test_blogger_api.py -v` and confirm all pass.

**Expected output**: Images uploaded from MarsEdit are immediately servable and persisted in all three required locations, with date-prefixed filenames avoiding collisions.
