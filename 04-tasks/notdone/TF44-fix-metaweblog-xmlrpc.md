# TF44 — Fix the MetaWeblog/XML-RPC Implementation (MarsEdit Support)
**Date Created:** 2026-09-08

## TF44.0 — Replace the hand-rolled request parser with xmlrpc.client.loads()
**Status**: done

**Description**: In `server.py`'s `xmlrpc_endpoint()`, replace the manual `ElementTree` walk over `param/value` nodes (currently handling only `string`/`boolean`/`int`/`i4`/`base64`/one-level `struct`) with `xmlrpc.client.loads(body)`, which returns `(params, method_name)` and correctly handles every standard XML-RPC type, including `dateTime.iso8601` and `<array>`, and nested/mixed struct members — the types MarsEdit sends that the current parser silently drops.

## TF44.1 — Replace the hand-rolled response/fault builders with xmlrpc.client.dumps()
**Status**: done

**Description**: Replace `create_xmlrpc_response()` and `create_xmlrpc_fault_with_code()` with `xmlrpc.client.dumps(...)`. This fixes the unescaped-XML bug (post titles/content containing `&`, `<`, `>` currently produce invalid response XML) and correctly encodes `datetime` values as `dateTime.iso8601` instead of falling back to a plain string.

## TF44.2 — Audit blogger_api.py method signatures against real MarsEdit payloads
**Status**: done

**Description**: With correct parsing in place (TF44.0), verify each `blogger_*`/`metaweblog_*` method in `blogger_api.py` receives the fields it expects — in particular struct fields MarsEdit sends as arrays (e.g. `mt_keywords`/categories) or as `dateTime.iso8601` (e.g. `dateCreated`) that the old parser previously dropped or mis-typed. Adjust method bodies if they were written around the old parser's incorrect types.

Findings: `_parse_content_or_struct()`'s existing tags handling already correctly handled both string and list inputs — once the parser delivers a real list for `mt_keywords` instead of an empty string, no change was needed there. Two real issues were found and fixed: (1) `xmlrpc.client.loads()` decodes `<base64>` values as `xmlrpc.client.Binary` wrappers, not raw `bytes` — normalized at the parsing boundary in `server.py` (`_unwrap_xmlrpc_binary()`) so `blogger_api.py` keeps receiving plain `bytes` as it already expects. (2) `blogger_getRecentPosts`/`blogger_getUsersBlogs` raised a bare `Exception("Authentication failed")` instead of `Fault(401, ...)` like every other method — now use `self._authenticate_or_raise()` for consistency, so the correct 401 fault code reaches the client instead of being squashed to a hardcoded 403 by the old server.py catch block.

## TF44.3 — Make XML-RPC post regeneration non-blocking
**Status**: done

**Description**: `blogger_api.py`'s `_regenerate_and_verify()` runs `SiteGenerator().incremental_regenerate_post()` synchronously, inline in the XML-RPC request handler (`blogger_newPost`/`blogger_editPost`/delete), so MarsEdit's "Post"/"Save" action blocks until the full incremental regeneration finishes. This is the same class of slow-save problem F38 already fixed for the admin web form by deferring regeneration via FastAPI `BackgroundTasks`. Apply the equivalent here: return the XML-RPC response as soon as the post file is written and verified saved, and run `_regenerate_and_verify()` in the background rather than before responding. Since `xmlrpc_endpoint()` is a FastAPI route, this can reuse the same `BackgroundTasks` mechanism F38 established, or an equivalent (e.g. `asyncio.create_task`) if `BloggerAPI`'s methods aren't easily threaded through `BackgroundTasks`.

## TF44.4 — Manual end-to-end verification against real MarsEdit
**Status**: not done — needs you, at your Mac, with MarsEdit

**Description**: Configure MarsEdit against a local server instance and verify: fetch recent posts, create a new post, edit an existing post, upload an image (regression check against F36), and confirm all round-trip correctly — including a post with a title/content containing `&`, `<`, or `>` that broke the old unescaped response builder. Also confirm MarsEdit's "Post" action returns promptly (TF44.3) rather than hanging until regeneration finishes.

**First real-world attempt (production) found a real bug, now fixed**: MarsEdit's "Refresh Blog" failed with `XMLRPC Response Parsing Failed: (null)`. Root cause: every `Response(...)` in `xmlrpc_endpoint()` passed an explicit `headers={"Content-Type": "text/xml"}` alongside `media_type="text/xml"` — the explicit header wins and suppresses Starlette's automatic `; charset=utf-8` suffix, so the wire response was `Content-Type: text/xml` with no charset declared, even though the body is UTF-8. `blogger_getRecentPosts` returns real post content, which routinely contains non-ASCII characters (curly quotes, en/em dashes) — a client defaulting to a non-UTF-8 encoding when no charset is declared can't decode the body at all. This pre-dated F44 (the same header pattern was in the original hand-rolled code) but was never caught because the request-parsing bugs meant XML-RPC calls rarely succeeded far enough to return real content. Fixed: dropped the redundant explicit header on all four XML-RPC response paths, letting `media_type="text/xml"` alone drive the correct `text/xml; charset=utf-8`. Two regression tests added (`test_response_content_type_declares_utf8_charset`, `test_fault_response_content_type_declares_utf8_charset`) since the original TF44.5 pass only checked response *bodies*, not headers. **Needs a redeploy before re-testing MarsEdit** — this fix is not live yet.

## TF44.5 — Write tests
**Status**: done

**Description**: Add/extend `tests/test_xmlrpc_parsing.py` and `tests/test_blogger_api.py` covering: request parsing of `dateTime.iso8601` params and array-typed struct members; existing base64 param parsing still works (regression); response encoding correctly escapes a title/content containing `&`/`<`/`>`; fault responses are correctly escaped too; the XML-RPC response for `newPost`/`editPost` is returned before regeneration completes (TF44.3), mirroring the async-save test pattern from F38.
