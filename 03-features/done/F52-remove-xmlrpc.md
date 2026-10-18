# F52 — Remove XML-RPC / MarsEdit Support
**Priority**: Medium
**Date Created:** 2026-10-18
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Remove the XML-RPC Blogger/MetaWeblog API.

It existed only so MarsEdit could post to the blog. **The user no longer
uses MarsEdit, and on 2026-10-18 chose to remove the API rather than keep
it** (see F44, closed with its last check waived). The web admin editor is
now the only way to author posts.

## Why

* Less code: `blogger_api.py` is 679 lines, and its two dedicated test
  files are another ~700.
* It closes an authenticated way into the server that nobody uses.
* It drops F41 TF41.10, the XML-RPC architecture review.

## Scope

* **In:** delete `src/salasblog2/blogger_api.py`.
* **In:** delete its server wiring in `server.py`:
  * the `/xmlrpc` GET and POST routes
  * `call_xmlrpc_method`, `unwrap_xmlrpc_binary`, `create_xmlrpc_response`
    and `create_xmlrpc_fault_with_code`
  * the `/rsd.xml` route
  * the `BloggerAPI` and `xmlrpc.client` imports
* **In:** delete the RSD `EditURI` discovery link from `base.html` and
  `admin.html`, and the "XML-RPC endpoint" note in the admin panel.
* **In:** delete `RSD_API_TYPE` from `fly.toml`.
* **In:** delete the tests that only test XML-RPC:
  * `tests/test_blogger_api.py`
  * `tests/test_xmlrpc_parsing.py`
  * the XML-RPC helper tests in `test_server_simple.py`
  * `TestBloggerApiTagParsing` in `test_blog_tags.py`
  * the `/rsd.xml` checks in the integration and live-server tests
* **In:** update `02-doc/spec.md`, `README.md`, the project description in
  `.claude/settings.json`, `current.md`, and comments that mention
  MarsEdit as a live feature.
* **In:** reword F41 TF41.10 as no longer applicable, and drop
  `01-literate/08-blogger_api.md`.
* **Out:** images uploaded through MarsEdit stay where they are under
  `static/images/uploads/`, and posts written in MarsEdit are untouched.
  The web editor's own image upload (`/api/upload-image`) is separate and
  stays.
* **Out:** historical feature and task files (F36, F44 and others) are left
  as the record of what was built.

## Behavior after removal

* `GET /rsd.xml` returns 404.
* `POST /xmlrpc` returns 405, from the GET-only catch-all route.
* No other route, page or admin function changes.

## How to Demo
**Setup**: deployed to production.

**Steps**:
1. `curl -i -X POST https://salas.com/xmlrpc` returns 405.
2. `curl -i https://salas.com/rsd.xml` returns 404.
3. Create and edit a post in the web admin editor, including an image
   upload, and check that it works as before.

**Expected output**: the XML-RPC API is gone, and authoring through the web
editor is unaffected.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
