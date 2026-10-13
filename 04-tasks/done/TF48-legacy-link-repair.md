# TF48 Repair Legacy Internal Links

**Date Created:** 2026-10-13

## TF48.0 — Inventory legacy self-links

**Status**: done

**Description**: Write a scanner that finds every legacy self-link in post
and page content. It records the source file, the link text, the legacy
URL, and which scheme it belongs to (Movable Type, WordPress, or import
leftover).

Run it against production content (pulled read-only via `fly ssh`), since
production is the source of truth and may differ from the local repo.

**Progress**: scanner done (`legacy_links.py`, `tests/test_legacy_links.py`).
On local content it finds 140 legacy links in 94 files: 78 `mt`
(64 distinct, including `.php`-era IDs), 54 `wp`, 7 `radio-day`
(Radio UserLand day archives, `/2004/01/24.html`), and 1 `squarespace`
(`/blog/2012/5/6/slug.html`). The last two schemes weren't in the original
plan. Production run (2026-10-13, read-only copy of `/data/content`) found the same 140 links; production and local content were identical.

Test: unit test the scheme classifier and link extraction against sample
markdown that has each scheme, plus links that must *not* match (external
sites, current `/blog/` URLs).

## TF48.1 — Resolve Movable Type IDs via the Wayback Machine

**Status**: done

**Description**: For each distinct `/weblogs/archives/NNNNNN.html` ID, use
the Wayback CDX API to find a 200 snapshot. Fetch the raw page (`id_`
form) and pull out its title and date.

Cache every fetch locally (scratch or a gitignored dir) so reruns don't hit
archive.org again. Rate-limit the requests.

Test: unit test title/date extraction against a saved fixture of a real
archived MT page. The network fetch isn't unit-tested (external service);
it's covered by the cache and the manual review in TF48.3.

**Found during implementation**:

* archive.org throttles (503) and times out under per-path lookups.

* `wayback.py` now makes one CDX prefix query per directory
  (`collapse=urlkey`) instead of one per path.

* It also retries 429/503 and timeouts with bounded backoff.

* Some MT pages pad the day ("February  1, 2005"), so the date patterns
  accept any whitespace.

## TF48.2 — Match legacy URLs to current posts

**Status**: done

**Description**: Match each legacy URL to a current post:

* **Movable Type** — by Wayback title + date, allowing ±1 day (dates
  shifted during migration, e.g. 000522 → Nov 28 vs. `2004-11-29`).

* **WordPress** — by the date and slug in the URL against post date and
  title/filename.

Write the result to `02-doc/legacy-url-map.json`. Each entry records the
old URL, the new URL, the match confidence (`exact`, `fuzzy`, or
`unmatched`), and the evidence (archived title and date).

Test: unit test the matcher against a small fixture post set, covering an
exact match, a ±1-day match, a near-title fuzzy match, and no match.

## TF48.3 — User review of the map

**Status**: done

**Description**: Present the `fuzzy` and `unmatched` entries to the user.
Apply their corrections to `legacy-url-map.json`.

**Nothing after this task runs until the user approves the map.**

**Result (2026-10-13)**: of 117 distinct legacy paths, 97 were exact matches.

The user approved:

* All 8 fuzzy matches as proposed.

* 4 unmatched entries pointed at posts found by title search. These posts
  were re-dated or renamed in a later import.

* The 3 archived 2003 MT posts (the archive has no 2003 posts) pointed at
  their Wayback copies.

The other 5 stay unmatched, with no target: one 2003 WP post, the "AMZN
continued" post, and 3 ambiguous or empty Radio day pages.

All decided entries carry `"reviewed": true`. 112 of 117 paths have a
target, which covers 135 of the 140 links.

**Round 2 (2026-10-13)**: the TF48.6 checker found 7 more legacy links of
the form `/imported-NNN/2012/1/4/slug.html`. These are Squarespace URLs
under the import prefix, with an unpadded month, which no pattern covered.

* The `squarespace` pattern now accepts the `/imported-NNN/` prefix.

* Result: 5 exact matches and 2 fuzzy (truncated slugs). The user approved
  both fuzzy ones.

* The map now has 124 entries, 119 of them with targets.

**Bug found**: rebuilding the map after the round-1 rewrite dropped 92
entries, because the scan no longer saw links that had already been
rewritten.

* `build_map` now keeps every previous entry the scan doesn't find, so the
  map only grows.

* Regression test: `test_build_map_keeps_entries_no_longer_linked`.

* Production was never affected, since it reads only the committed map.

Test: not feasible — this is a human review step.

## TF48.4 — Rewrite links in post content

**Status**: done

**Description**: A rewrite command that replaces every mapped legacy URL in
content with its new URL. It leaves unmatched links untouched.

It has a dry-run mode that prints the per-file diff. It edits only link
targets, never link text, frontmatter, or other body text.

Run it dry first, then for real against production's `/data/content/blog`
via `fly ssh`. Then regenerate the site and sync to GitHub.

Test: unit test the rewrite against fixture markdown. Check that mapped
links change, unmatched ones stay, and the rest of the file is
byte-identical.

## TF48.5 — Server redirects for legacy URLs

**Status**: done

**Description**: Add routes in `server.py` for the legacy URL patterns. A
mapped URL returns a 301 to its new URL. An unmapped one keeps returning
404.

The map loads once at startup from `legacy-url-map.json`. Handle the
trailing-slash and no-trailing-slash forms of WordPress URLs. Make sure the
new routes don't shadow any existing route.

Test: FastAPI test-client tests for a mapped MT URL, a mapped WP URL (with
and without trailing slash), and an unmapped legacy URL (404). Also check
that existing routes still resolve.

## TF48.6 — Dead self-link checker

**Status**: done

**Description**: A CLI command (e.g. `uv run bg check-links`) that reports
every self-link in content that doesn't resolve to a generated page or a
mapped redirect. That covers legacy schemes and broken `/blog/` links alike.

Test: unit test against a fixture content dir with one good link, one
mapped legacy link, and one dead link. Only the dead one should be
reported.

## TF48.7 — Write and run the full test suite

**Status**: done

**Description**: Make sure the tests from TF48.0–TF48.6 exist in
`tests/`. Run the full suite and confirm it's green.

**Result**: 672 passed, 11 skipped. New test files:

* `test_legacy_links.py`
* `test_wayback.py`
* `test_legacy_match.py`
* `test_legacy_commands.py`
* `test_legacy_redirects.py`
* `test_link_check.py`

Test: this task is the test task.

## TF48.8 — Production verification

**Status**: done

**Description**: Deploy. Walk through the F48 demo steps against
https://salas.com and run the checker against production content. Record
the remaining unmatched count in the feature file.

Test: manual — this verifies the live deployment.

**Result (2026-10-13)**: deployed `c3ffa71` and then `8cacea8`. The rewrite
was dry-run and then applied on `/data/content`: 135 links in round 1 and
7 in round 2. The site was regenerated and `sync_to_github()` returned
True both times. Local `main` was pulled.

Live checks:

* The Part Deux "my earlier posting" link points to
  `/blog/2004-11-29-why-improv-didn8217t-succeed.html`, which returns 200.

* `/weblogs/archives/000522.html`, `/2009/02/14/saving-the-newspapers/`, and
  `/imported-20111103233638/2012/1/4/teaching-group-projects.html` all 301
  to their posts.

* `/weblogs/archives/000264.html` 301s to its Wayback copy.

* `/2004/02/24.html` (unmapped) returns 404.

`bg check-links` on production reports **21 remaining dead self-links**,
none of them fixable:

* the 5 reviewed-unmatched entries

* 6 accidental `/wp-admin/...` links

* `/mt/mt-comments-pitofake.cgi`, `/weblogs/archives/screen.jpg`, and
  `/weblogs/archives/2003_05.php` (an MT month archive)

* `/stories/rssprez.pdf` ×2 and the Brandeis slides frame

* one malformed WP link with a duplicated segment

* 3 `/robots/...` links on the robots page
