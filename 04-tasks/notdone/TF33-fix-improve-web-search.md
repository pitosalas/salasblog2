# TF33 — Fix and Improve Web Search
**Date Created:** 2026-03-02

## TF33.0 — Fix item.category → item.type in script.js
**Status**: done

**Description**: In `static/js/script.js` `performSearch()`, change `item.category` to `item.type` to match the field name actually emitted by `generate_search_index()`. This is the root cause of the search box doing nothing.

## TF33.1 — Improve raindrop content in search index
**Status**: not done

**Description**: In `generator.py` `generate_search_index()`, raindrops currently set `content` to `raw_content[:500]` but raindrop raw content is mostly metadata labels. Index the raindrop's `note` field and `url` field instead so raindrop entries are actually searchable.

## TF33.2 — Remove/raise the 500-char content truncation
**Status**: not done

**Description**: In `generator.py` `generate_search_index()`, blog post content is truncated to 500 chars. Increase or remove this limit so full-body search works across longer posts.

## TF33.3 — Write tests for search index generation
**Status**: not done

**Description**: Add tests in `tests/test_search.py` covering: search index contains entries for all content types, all required fields present (`title`, `url`, `type`, `excerpt`, `content`), raindrop entries have non-empty content, blog post content is not cut short.

## TF33.4 — Stop matching search queries against content type
**Status**: done

**Description**: TF33.0 swapped `item.category` for `item.type` in
`performSearch()`, so every query was also matched against the content
type. Short or common queries then returned whole content types unrelated
to the query:

* "blog" or "log" returned every `blog`-type post.
* "page" returned the pages.
* "drop" or "op" returned every raindrop.
* "wp" returned the 2,801 WordPress-imported posts, which carry
  `type: wp`.

Search now matches only title and content (2026-10-18).

**Test**: `tests/test_search_js.py` runs the real `static/js/script.js`
under Node with a stubbed `document`, and checks that a type-only query
finds nothing while title and content matches still work. It is skipped
when `node` isn't installed.
