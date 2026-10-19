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

**Description**: `select_deleted_raindrops()` is a pure function that picks
the local files whose `raindrop_id` is missing from the remote set.
`RaindropDownloader.remove_deleted_raindrops()` deletes those files and drops
their IDs from the cache's `downloaded` list. It refuses to delete anything
if Raindrop.io returns no bookmarks at all.

* Both sync paths call it **before** `download_raindrops()`:
  `Scheduler.sync_raindrops()` (scheduled, and the scheduler's "sync now")
  and the admin `/api/sync-raindrops` route. A failed ID fetch therefore
  stops the sync before anything changes.
* When anything was removed, the caller runs a full `generate_site()`, and
  TF53.2's pruning removes the deleted raindrops' pages. The output HTML is
  not deleted here directly.
* The admin route now always resets `sync_status["running"]` and reports
  errors. Before, an exception left it stuck at "running".

**Test**: `tests/test_raindrop_deletions.py` covers:

* selection
* reading IDs from frontmatter
* a file with no ID is never deleted
* the cache update
* a fetch error deletes nothing
* an empty remote list refuses to delete

`tests/test_scheduler.py` covers regeneration after deletions alone, and a
failed check stopping the download.

## TF53.2 — Prune stale pages on full regeneration

**Status**: done

**Description**: Full regeneration rewrites every page unconditionally, so
the generator uses modification time rather than tracking every write path.
`generate_site()` notes its start time, less `MTIME_SLACK_SECONDS`. At the
end, `prune_stale_pages()` deletes any `.html` older than that in
`output/blog/`, `output/raindrops/` and `output/tags/`
(`PRUNED_OUTPUT_DIRS`), then removes empty directories.

**Test**: pre-seed the output with a stale post page, a stale raindrop page
and a stale tag directory, then run `generate_site()`. The stale files are
gone, and current pages and root-level files remain.

## TF53.3 — Gap-free static copy

**Status**: done

**Description**: `copy_static_files()` no longer deletes `output/static`.
It updates the tree in place:

* copies the source over the live tree (`copytree(..., dirs_exist_ok=True)`)
* merges the volume uploads
* deletes files that are no longer in either source, then any empty
  directories

The planned build-and-rename swap was **tried on production and failed**,
with `OSError: [Errno 18] Invalid cross-device link`. In the Docker overlay
filesystem, a directory that comes from the image layer can't be renamed.
That run aborted before pruning, but no harm was done, because the rename
failed before anything moved. Leftover `static.new`/`static.old` from that
attempt are cleared at the start of each copy.

**Test**: `TestGapFreeStaticCopy` in `tests/test_generator.py`:

* the copy replaces content
* leftover staging directories are cleared
* a regression test with `Path.rename` patched to raise EXDEV, which fails
  on the rename-swap version

## TF53.4 — Tests

**Status**: done

**Description**: Cover TF53.0-TF53.3 as described in each step, then run
the full suite.

## TF53.5 — Deploy and verify

**Status**: done

**Description**:

1. Commit, push, `make deploy`.
2. On production, run the raindrop sync. The expected deletions are 0,
   since the three known orphans were removed by hand.
3. Run a full regeneration. The file count in `output/raindrops/` should
   equal the raindrop count plus the listing and collection pages.
4. Spot-check that pages stay styled during a regeneration.

**Test**: manual. Record the counts.

**Result (2026-10-18)**: deployed `9395ec1f`, then the fix `ced7f91c`.

* `Scheduler().sync_raindrops()` on production returned True. It found 0
  deletions and no new raindrops, as expected, since the three orphans
  were removed by hand earlier.
* The first full regeneration aborted on EXDEV (see TF53.3). After the
  fix, `bg generate` completed and removed 0 stale pages.
  `static.new` was gone, and CSS and WordPress images return 200.
* Counts:
  * `output/raindrops/*.html` is 1,625: 1,547 raindrops plus their
    listing pages.
  * `output/blog/*.html` is 2,972, for 2,834 blog sources plus their
    listing pages.
* The earlier claim of "~90 stale raindrop pages" was wrong. It counted
  directories and listing pages, not stale pages.
* Step 4 (watching pages stay styled during a regeneration) was not
  observed directly. It is covered by the in-place copy design and its
  tests.
