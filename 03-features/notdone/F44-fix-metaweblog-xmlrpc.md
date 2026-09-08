# Feature description for feature F44
## F44 — Fix the MetaWeblog/XML-RPC Implementation (MarsEdit Support)
**Priority**: High
**Date Created:** 2026-09-08
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: `/xmlrpc` (`server.py`) and `blogger_api.py` hand-roll XML-RPC parsing and response building with `xml.etree.ElementTree` instead of using a real XML-RPC implementation, and it's broken in two independent ways:

1. **Request parsing** (`xmlrpc_endpoint()`) only understands `<string>`, `<boolean>`, `<int>`/`<i4>`, `<base64>`, and one level of `<struct>` — it has no handling for `<array>` or `<dateTime.iso8601>`. MarsEdit routinely sends `dateCreated` as `dateTime.iso8601` and categories/keywords as arrays; both silently fall through to `value_elem.text or ""` and get dropped or mangled. This is very likely why MarsEdit "doesn't work at all" today.
2. **Response building** (`create_xmlrpc_response()`, `create_xmlrpc_fault_with_code()`) interpolates values directly into XML strings with **no escaping**, so any post title or content containing `&`, `<`, or `>` produces invalid XML sent back to the client. It also has no `dateTime.iso8601` encoding for datetime values — they silently fall back to being stringified as `<string>`.

The fix is to stop hand-rolling XML-RPC marshalling and use Python's standard library `xmlrpc.client.loads()`/`xmlrpc.client.dumps()` for both parsing and building — these correctly and safely handle the full XML-RPC type set (string, boolean, int, double, dateTime.iso8601, base64, array, struct, nil) including proper escaping, which is exactly what's missing today. `blogger_api.py`'s method implementations are kept; only the marshalling layer around them changes.

While in this code: `blogger_api.py`'s post-creation/edit methods already trigger incremental site regeneration (`_regenerate_and_verify()` → `SiteGenerator().incremental_regenerate_post()`) — that already works and is unaffected by the marshalling fix above. But it currently runs *synchronously*, blocking the XML-RPC response until regeneration finishes — the same class of slow-save problem F38 already fixed for the admin web form via `BackgroundTasks`. This feature also makes XML-RPC regeneration non-blocking, so MarsEdit's "Post" action returns promptly instead of hanging.

This restores MarsEdit as a working authoring option on the Mac. It is independent of and complementary to F43 (the new phone-friendly REST API) — MarsEdit is Mac-only and doesn't speak the protocol F43 uses, so both paths are needed to cover "at my Mac" and "away from my Mac."

## How to Demo
**Setup**: `uv run bg server`; MarsEdit configured against the local `/xmlrpc` endpoint per the README's MarsEdit Setup section.

**Steps**:
1. In MarsEdit, fetch recent posts and confirm the list loads with correct titles and dates.
2. Create a new post with a title or body containing an ampersand (e.g. "Cats & Dogs") and publish it; confirm it round-trips correctly with no XML/parsing errors on either side.
3. Edit an existing post from MarsEdit and confirm the change saves and is reflected on the live site.
4. Upload an image from MarsEdit into a post and confirm it appears correctly (regression check against F36).
5. Confirm MarsEdit's "Post"/"Save" action returns promptly rather than hanging until site regeneration finishes.
6. Run `uv run pytest tests/test_xmlrpc_parsing.py tests/test_blogger_api.py -v` and confirm all pass, including new tests for `dateTime.iso8601` and array-typed struct members.

**Expected output**: MarsEdit works end-to-end (fetch, create, edit, image upload) against the local and deployed server, including content containing XML special characters, with no more silent field drops or malformed responses, and posting no longer blocks on regeneration.
