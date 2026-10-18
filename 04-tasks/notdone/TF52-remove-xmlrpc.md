# TF52 Remove XML-RPC / MarsEdit Support for Feature F52
**Date Created:** 2026-10-18

## TF52.0 — Remove the server routes and helpers

**Status**: not done

**Description**: In `server.py`, delete:

* `/xmlrpc` (GET and POST) and `/rsd.xml`
* `call_xmlrpc_method`, `unwrap_xmlrpc_binary`, `create_xmlrpc_response`
  and `create_xmlrpc_fault_with_code`
* the `BloggerAPI` and `xmlrpc.client` imports

**Test**: a server test asserts that `POST /xmlrpc` and `GET /rsd.xml`
return 404.

## TF52.1 — Delete `blogger_api.py`

**Status**: not done

**Description**: Delete `src/salasblog2/blogger_api.py`. A grep confirms
nothing else imports it.

**Test**: none needed beyond the full suite importing cleanly.

## TF52.2 — Remove discovery links, admin note and config

**Status**: not done

**Description**:

* Delete the RSD `EditURI` `<link>` from `templates/base.html` and
  `templates/admin.html`.
* Delete the "XML-RPC endpoint for blog editors" note in `admin.html`.
* Delete `RSD_API_TYPE` from `fly.toml`.

**Test**: a render test asserts the home page has no `EditURI` link.

## TF52.3 — Remove XML-RPC-only tests

**Status**: not done

**Description**: Delete:

* `tests/test_blogger_api.py`
* `tests/test_xmlrpc_parsing.py`
* `TestXMLRPCHelpers` in `test_server_simple.py`
* `TestBloggerApiTagParsing` in `test_blog_tags.py`
* the `/rsd.xml` tests in `tests/integration/test_server.py` and
  `tests/test_pages_live_server.py`

Tests that merely mention MarsEdit in a docstring but test something else
are kept.

## TF52.4 — Update docs

**Status**: not done

**Description**:

* Update `02-doc/spec.md`, `README.md` (drop "MarsEdit Setup"), the
  project description in `.claude/settings.json`, and `current.md`.
* Fix the docstring in `utils.py` that cites MarsEdit's category picker.
* Reword F41 TF41.10 as not applicable.
* Delete `01-literate/08-blogger_api.md`.

**Test**: none needed; this is documentation only.

## TF52.5 — Tests

**Status**: not done

**Description**: Add the TF52.0 and TF52.2 tests, then run the full suite.

## TF52.6 — Deploy and verify

**Status**: not done

**Description**:

1. Commit, push and `make deploy`.
2. `curl` checks that `POST /xmlrpc` and `GET /rsd.xml` return 404.
3. The home page and admin load.
4. Create, edit and delete a throwaway post through the web editor.

**Test**: manual. Record the curl status codes.
