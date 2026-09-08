# TF43 — Token-Authenticated REST API for Remote Post Creation
**Date Created:** 2026-09-08

## TF43.0 — Add a dedicated API token and auth check
**Status**: not done

**Description**: Add a `POST_API_TOKEN` environment variable, read from `os.environ` at request time (not cached at startup) so it can be rotated live via `fly secrets set` without a redeploy, mirroring the fix in F35. Compare the incoming `Authorization: Bearer <token>` header using a constant-time comparison (`hmac.compare_digest`). If `POST_API_TOKEN` is unset, the endpoint must refuse all requests (fail closed) rather than allow unauthenticated access — the opposite of the current `ADMIN_PASSWORD`-unset behavior, which is a known gap.

## TF43.1 — Implement POST /api/posts
**Status**: not done

**Description**: Add `POST /api/posts` accepting a JSON body: `title` (required), `content` (required, markdown), `date` (optional, defaults to today), `tags` (optional list), `category` (optional), `draft` (optional bool, defaults `true`). Validate required fields and return `400` with a clear message if missing. Generate the filename via the existing `create_filename_for_content()`, check for collisions (`409` if the filename already exists), and save via the existing `save_content_item()` plus the existing background incremental-regeneration path — the same functions the admin web form's `/admin/new-post` route already calls, so there is one canonical "create a post" implementation, not two.

## TF43.2 — Token-authenticated image upload for the API
**Status**: not done

**Description**: Add a token-authenticated image upload path (reusing the existing three-location save logic behind `/api/upload-image`: `static/images/uploads/`, `output/static/images/uploads/`, `/data/static/images/uploads/`) so a photo can be uploaded via the same `POST_API_TOKEN` and referenced by URL in a post's markdown `content`.

## TF43.3 — Error handling and response contract
**Status**: not done

**Description**: Ensure every response from the new endpoints is JSON (never an HTML error page) with a consistent shape (`{"status": ..., "detail"/"message": ..., "filename": ..., "url": ...}`) and correct HTTP status codes: `401` for missing/invalid token, `400` for validation failures, `409` for filename collision, `200`/`201` for success. This is what lets a Shortcut or `curl` caller react programmatically instead of guessing from HTML.

## TF43.4 — Document a reference iOS Shortcut
**Status**: not done

**Description**: Write a working iOS Shortcut recipe (in `README.md` or `02-doc/notes.md`): "Ask for Text" for the post body, a "Get Contents of URL" step POSTing JSON to `/api/posts` with the token stored in the Shortcut, and a result notification. Not code, but required for this feature to be genuinely usable rather than API-only.

## TF43.5 — Write tests
**Status**: not done

**Description**: Add tests covering: valid token succeeds, missing/invalid token returns `401`; a valid `POST /api/posts` call produces a file with correct frontmatter and defaults to `draft: true`; `draft: false` publishes immediately (post appears in listings/search index after regeneration); filename collision returns `409`; image upload via the API saves to all three locations and returns a usable URL.
