# Feature description for feature F43
## F43 — Token-Authenticated REST API for Remote Post Creation
**Priority**: High
**Date Created:** 2026-09-08
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Add a small, token-authenticated JSON REST API that lets posts be authored from anywhere without a browser session or git — e.g. a phone with no computer nearby. This is independent of MarsEdit/XML-RPC support, which is being fixed separately in F44 rather than replaced; the two are complementary authoring paths (Mac desktop app vs. anywhere-with-a-phone), not alternatives to each other.

Core points:
- A new `POST /api/posts` endpoint accepts a JSON body (`title`, `content` (markdown), optional `date`, `tags`, `category`, `draft`) guarded by a dedicated bearer token (`POST_API_TOKEN`), separate from `ADMIN_PASSWORD`/the admin session cookie, read from the environment at request time (same rotate-without-redeploy pattern as F35) rather than fixed at startup.
- The endpoint reuses the existing `create_filename_for_content()` / `save_content_item()` / incremental-regeneration machinery already used by the admin web form, so there remains exactly one canonical code path for "create a post" rather than a second parallel implementation.
- New posts default to `draft: true` unless the caller explicitly passes `draft: false` — they land in the existing Drafts tab (built for F39/F40) for a look/edit/publish from the web, rather than instantly publishing unreviewed text typed on a phone.
- A token-authenticated image upload path reuses the existing three-location upload logic so a photo taken on a phone can be attached to a post created via the API.
- A documented reference client (an iOS Shortcut recipe) is written down so the capability is actually usable day one, even though the API itself is plain HTTP/JSON and usable from curl or any other client.

## How to Demo
**Setup**: `uv run bg server` with `POST_API_TOKEN` set; a terminal with `curl` and (optionally) an iPhone.

**Steps**:
1. `curl -X POST /api/posts -H "Authorization: Bearer <token>" -d '{"title": "Test", "content": "Hello from curl"}'` and confirm a `200`/`201` response with a filename and a message indicating it was saved as a draft.
2. Open the admin Drafts tab and confirm the new post appears there, unpublished.
3. Publish it from the Drafts tab and confirm it goes live at the expected URL.
4. Repeat step 1 with a missing/wrong token and confirm a `401` with a clear JSON error body, not an HTML page.
5. Repeat step 1 with `"draft": false` and confirm the post is live immediately, no Drafts-tab step needed.
6. Run the documented iOS Shortcut from a phone, typing a short post, and confirm it lands as a draft the same way as the curl call.

**Expected output**: Posts (with optional images) can be created from any device with just an HTTPS request and a token — no browser admin session, no git — landing safely as a draft by default.
