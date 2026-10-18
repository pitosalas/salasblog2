# TF53 Keep the Generated Site in Sync for Feature F53
**Date Created:** 2026-10-18

## TF53.0 — Complete, failing-loudly fetch of remote raindrop IDs

**Status**: done

**Description**: Add a method to `RaindropDownloader` that pages through
`/raindrops/0` and returns the set of every current bookmark ID.

* Any non-200 page raises with context.
* It returns only after reaching an empty page.
* It shares the request code with `_fetch_page` rather than duplicating it.

**Test**: with the HTTP calls mocked, a multi-page fetch returns the union
of IDs, and a failure on page 2 raises instead of returning page 1's IDs.

## TF53.1 — Remove local raindrops deleted on Raindrop.io

**Status**: done

**Description**: A pure function selects the local files whose
`raindrop_id` is missing from the remote set. A wrapper deletes those files
and their `output/raindrops/<name>.html`, and drops their IDs from the
cache's `downloaded` list.

* It runs at the end of `download_raindrops()`, which covers both the
  scheduled sync and the admin "sync raindrops" button.
* Deleted filenames are logged and returned, so callers regenerate.

**Test**:

* selection with fixture files: kept, deleted, and a file with no
  `raindrop_id`, which is never deleted and gets a warning
* a fetch error means nothing is deleted
* the cache update
* the output HTML is removed

## TF53.2 — Prune stale pages on full regeneration

**Status**: done

**Description**: `generate_site()` records each `.html` path it writes.
Afterwards, in `output/blog/`, `output/raindrops/` and `output/tags/`, it
deletes any `.html` not written in this run, and any tag directory left
empty.

**Test**: pre-seed the output with a stale post page, a stale raindrop page
and a stale tag directory, then run `generate_site()`. The stale files are
gone, and current pages and root-level files remain.

## TF53.3 — Gap-free static copy

**Status**: done

**Description**: `copy_static_files()` copies into `output/static.new`
(including the volume-upload merge), then:

1. renames `output/static` to `output/static.old`
2. renames `static.new` to `static`
3. removes `static.old`

Leftover `.new`/`.old` directories from an interrupted run are cleared
first.

**Test**: after a copy, `output/static` holds the new files and no
`.new`/`.old` remains. A pre-existing leftover `static.old` doesn't break
the copy.

## TF53.4 — Tests

**Status**: done

**Description**: Cover TF53.0-TF53.3 as described in each step, then run
the full suite.

## TF53.5 — Deploy and verify

**Status**: not done

**Description**:

1. Commit, push, `make deploy`.
2. On production, run the raindrop sync. The expected deletions are 0,
   since the three known orphans were removed by hand.
3. Run a full regeneration. The file count in `output/raindrops/` should
   equal the raindrop count plus the listing and collection pages.
4. Spot-check that pages stay styled during a regeneration.

**Test**: manual. Record the counts.
