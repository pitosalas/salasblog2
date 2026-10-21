# TF56 Run site generation out of the server process for Feature F56
**Date Created:** 2026-10-20

## TF56.0 — Measure the baseline
**Status**: done

**Description**: Before changing anything, time `/` on production in a loop
while an admin Regenerate runs, and record the numbers in this file's notes.
That shows whether generation is really the cause, and gives the demo a
before/after. No automated test: it is a measurement of the live machine.

## TF56.1 — CLI commands for incremental regeneration
**Status**: done

**Description**: Add `bg regen-post <filename> <type>` and
`bg regen-deleted <filename> <type>`, which call
`SiteGenerator.incremental_regenerate_post` and
`incremental_regenerate_after_deletion`. `bg generate` already covers the
full case. Test: invoking each command's handler on a temp content tree
writes (or removes) the expected output files.

## TF56.2 — One way to run a generation child
**Status**: done

**Description**: A small module (`site_jobs.py`) with `run_generation(args)`
that runs `python -m salasblog2.cli <args>` as a subprocess with the server's
environment, holds a module-level lock so only one generation runs at a time,
logs start and end, and raises with the child's stderr on a non-zero exit.
(Changed from the plan: it does not refresh the posts index. Generation
only writes `output/`, never content, so it can't make the index stale.)
Test: with a stub command, a failing child raises with its stderr, and two
concurrent calls never overlap.

## TF56.3 — Route every generation through the child
**Status**: done

**Description**: Replace the in-process `SiteGenerator().generate_site()`,
`incremental_regenerate_post` and `incremental_regenerate_after_deletion`
calls with `run_generation`:
- `server.py`: save/new/delete background tasks, `/api/regenerate`,
  `/api/sync-raindrops` (both branches), draft publish.
- `scheduler.py`: the raindrop-sync full regeneration.
`render_post_page_now` (one page, before the editor redirect) stays in
process: it is small and the request must wait for it anyway.
The admin's generation count and last-generation time keep updating.
Test: existing server and scheduler tests, updated to assert that
`run_generation` is called with the right arguments instead of `SiteGenerator`.

## TF56.4 — Drop the 5-minute posts-index rescan
**Status**: done

**Description**: Remove the scheduled `posts_index_cache_job` in `lifespan`.
The index stays fresh because every admin write already refreshes it. The
two endpoints that change content outside the editor (emergency restore and
sync-pages-from-repo) now refresh it too. The startup build stays, and the
`posts_index` entry is gone from `config.yaml`.
Test: a test that `lifespan` schedules no posts-index job.

## TF56.5 — Write the tests
**Status**: done

**Description**: Write the tests named in TF56.1–TF56.4 and run the full suite.

## TF56.6 — Deploy and verify
**Status**: done

**Description**: Deploy, repeat the TF56.0 measurement, confirm a separate
`bg` process appears during Regenerate, and walk F56's demo. No automated
test: it is a production check.

## Notes
- Implemented 2026-10-20. Tests in `tests/test_site_jobs.py`, plus updated
  `test_scheduler.py` and `test_drafts_api.py`. Full suite: 712 passed,
  29 skipped.
- Raindrop sync with a few new drops still runs one `regen-post` child per
  drop, as before (each reloads all content). It is rare and off the
  request path now.
- `startup.sh`'s `bg generate &` already ran as its own process and is not
  covered by the server's lock. An admin Regenerate in the first minute
  after boot could overlap it, as it could before F56.
- TF56.0 baseline (2026-10-20, 20:19–20:24, admin Regenerate clicked
  about 20:20): 180 requests to `/`, all 200. Quiet: 0.07–0.10 s. During
  the regeneration: 12 over 1 s, spikes of 19 s, 24 s and 33 s, and
  0.5–2 s for most of the 4 minutes. Average 0.72 s.
- TF56.6 first re-measurement (2026-10-20, 20:33–20:37, Regenerate clicked
  about 20:33:30): 180 requests, all 200, average 0.38 s, 6 over 1 s. The
  regeneration itself now finishes in under a minute (was ~4) and `/` stayed
  at ~0.08 s while it ran. But spikes of 11–20 s came **after** it finished
  (20:35:01, 20:35:21, 20:36:21). Suspected Fly shared-CPU throttling after
  two back-to-back full generations, or memory pressure; to be confirmed in
  Fly metrics. TF56.6 stays open.
- TF56.6 closed 2026-10-20: the user accepted the performance as is. The
  after-regeneration spikes are not investigated; if they matter later,
  check Fly metrics for CPU throttling or memory first.
