# TF55 Closed Curated Tag List for Feature F55
**Date Created:** 2026-10-19

## TF55.0 — One shared tag-normalization function

**Status**: done (2026-10-20)

**Description**: A single pure function converts a tag list through the
curated alias map:

* an alias becomes its primary
* unknown tags are dropped
* the result is de-duplicated, in order

It also returns what it dropped. It replaces the separate logic in
`normalize_post_tags` and `wp_taxonomy.resolve_terms`, so that the editor,
raindrop sync, generator and one-time conversions all use the same rule.

**Test**:

* a primary is kept
* an alias is converted
* an unknown tag is dropped and reported
* duplicates collapse
* case is normalized
* empty input

## TF55.1 — Install the 16-tag list; retire automatic promotion

**Status**: done (2026-10-20)

**Description**:

* Replace the Curated Tags section of `02-doc/tag-hints.md` with
  `02-doc/tag-hints-proposed.md`, then delete the proposed file.
* Rewrite the rules header: the list is closed, aliases convert, nothing
  is auto-added.
* Remove `promote_recurring_candidates`, `MIN_RECURRENCE_FOR_PROPOSED_TAG`,
  its use in `scripts/build_proposals.py`, and `wp_taxonomy.promote_terms`
  with its `bg wp-tags --promote` flag.
* Update the "curated tags" section in `02-doc/notes.md`.

**Test**:

* parse the installed file: exactly 16 primaries, no alias claimed by two
  primaries
* removed functions are gone, and the tests that only covered promotion are
  deleted

## TF55.2 — Editor: picker limited to curated tags, server-side validation

**Status**: done (2026-10-20)

**Description**:

* The tag picklist offers only the 16 tags, not the top-100 frequency
  list.
* On create or edit, the server converts aliases. If any tag is unknown,
  it returns 400 naming the bad tags, and the post isn't saved.

**Test**: through the routes:

* saving `iphone` is stored as `computing`
* `banana` gets 400 and the file is unchanged
* the editor page lists exactly the 16 tags

## TF55.3 — Raindrop sync converts tags on write

**Status**: done (2026-10-20)

**Description**: Before a raindrop's file is written
(`_write_raindrops_to_files`), its Raindrop.io tags go through TF55.0.
Unknown tags are dropped, and nothing extra is stored.

**Test**: write a fixture raindrop tagged `chatgpt`, `free`, `opencv`. The
file has `ai` and `robotics`. A raindrop with only unknown tags is written
with an empty tag list.

## TF55.4 — Generator shows only curated tags

**Status**: done (2026-10-20)

**Description**:

* Listing, post and home templates, and `generate_tag_pages`, use only
  tags in the curated list.
* Any other tag found is skipped, and each distinct one is logged once per
  run.
* TF53's pruning removes the old non-curated tag pages.

**Test**: a fixture post with `programming` and `stray` renders only
`#programming`, has no `/tags/stray/` page, and logs `stray`.

## TF55.5 — One-time in-place raindrop conversion

**Status**: done (2026-10-20)

**Description**: A dry-run-by-default command converts every existing
raindrop file's `tags` frontmatter through TF55.0.

* Only the tag lines change. Everything else is byte-identical, with line
  endings preserved, using the TF51 approach.
* It reports kept, dropped and now-untagged counts.
* **It never re-fetches from Raindrop.io and never uses `--reset`.**

**Test**:

* fixtures: a mixed raindrop, an all-unknown raindrop, an untagged
  raindrop, a CRLF raindrop
* only the tag lines change
* a dry run writes nothing

## TF55.6 — Blog mechanical conversion

**Status**: done (2026-10-20)

**Description**: The same command, for blog posts:

* convert aliases
* remove the generic `personal` tag where the post already has another
  curated tag (about 471 posts)

The generic `technology`, and `personal` on posts with no other topic, are
left in place, marked for TF55.7.

**Added 2026-10-20 at the user's request:** each changed file also gets
an `original_tags:` entry, written right after `tags:`, holding its tags
before conversion. A file that already has `original_tags` is refused, not
overwritten. Editing a post in the admin keeps the field.

**Implemented as `bg convert-tags`, which handles raindrops and blog
together.** `technology` is treated like `personal`: it is dropped when the
post has a real topic. Otherwise pass A could never reach those posts,
since it selects posts tagged only `technology`.

**Test**: fixtures for each rule, plus a byte-identical check outside the
tag lines.

## TF55.7 — Judgment passes for generic `technology` and `personal`

**Status**: tooling done (2026-10-20); judgment passes run on production in TF55.9

**Description**: Select the posts still carrying a generic tag: about 753
`technology` and 350 `personal`.

* Tags are decided from each post's title and excerpt in an assisted
  session, using the F46 select, decide and apply flow.
* The choice is among the 16 tags: `internet` or `computing` for
  technology, `life` or `places` for personal, or the post's real topic.
* **A sample batch of about 50 from each group goes to the user for review
  before the rest is applied.**
* Posts with no fit stay untagged.

**Implemented as `bg generic-tags`.** `--tag technology|personal` writes
title and excerpt summaries for a batch. `--decisions FILE [--apply]` then
replaces each post's tags. F46's apply step can't be reused: it only adds
tags and refuses CRLF files.

**Test**: the selection predicate and the apply step are unit-tested. The tag decisions themselves are a judgment
call that the user reviews; they have no automated test.

## TF55.8 — Tests

**Status**: done (2026-10-20)

**Description**: Write the tests for TF55.0–TF55.6 as described in each
step, update or remove the tests made obsolete by TF55.1, then run the full
suite.

## TF55.9 — Deploy, convert, verify

**Status**: not done

**Description**:

1. Commit, push and deploy.
2. On production, dry-run, then apply TF55.5 and TF55.6, then run TF55.7
   with its review gates.
3. Regenerate, run `sync_to_github()` and pull.
4. Walk F55's demo.
5. Run a final tally across `/data/content`, which must show only the 16
   tags.

**Test**: manual. Record every count.
