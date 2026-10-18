# F53 — Keep the Generated Site in Sync with Its Sources
**Priority**: High
**Date Created:** 2026-10-18
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Three gaps let the live site drift from its sources, or
glitch while it regenerates. All three were found on 2026-10-18, after the
user deleted bookmarks on Raindrop.io and they stayed on the link blog.

## The three bugs

1. **Raindrop deletions never reach the site.**
   * `RaindropDownloader.download_raindrops()` only fetches bookmarks
     created since the last sync and writes new files. It never checks
     whether a local raindrop still exists on Raindrop.io.
   * Three deleted bookmarks were found and removed by hand on 2026-10-18:
     1,550 local vs 2,608 remote, 3 local IDs missing remotely.
2. **Full regeneration never deletes stale pages.**
   * `generate_site()` writes every page but leaves behind output files
     whose source is gone.
   * After the three raindrops were removed, their HTML was still served
     until it was deleted by hand.
   * Production had 1,639 files in `output/raindrops/` for 1,547 raindrops.
3. **Regeneration briefly removes all CSS, JS and images.**
   * `copy_static_files()` does `rmtree(output/static)` and then
     `copytree`, now including 30 MB of WordPress images.
   * A page loaded during that window renders unstyled, with broken images.

## Intended behavior

* **The raindrop sync also removes deleted bookmarks.**
  * A local raindrop whose `raindrop_id` is not among Raindrop.io's current
    bookmarks (trash excluded) is deleted, along with its output page.
  * **This only runs after a complete fetch of every remote ID.** If any
    page of the fetch fails, the sync raises and deletes nothing.
    A partial list must never be treated as "these were deleted".
  * Today `fetch_raindrops` swallows a page error and returns what it has.
    The deletion path must not use that behavior.
* **Full regeneration prunes stale generated pages.**
  * In the directories it fully owns (`output/blog/`, `output/raindrops/`,
    `output/tags/`), it removes `.html` files it didn't write in this run.
  * Root-level files are not touched: `index.html`, `admin-stats.html`,
    caches, and page HTML.
* **The static-file copy never leaves a gap.**
  * Copy into a temporary sibling directory, then swap it into place with
    renames, so `output/static` is never missing for longer than two
    renames.

## Out of scope

* Raindrops edited on Raindrop.io (title or note changes) are still not
  re-synced. Only deletion is added.
* Root-level page cleanup. Deleting a page through the admin already
  removes its output.

## How to Demo
**Setup**: deployed to production.

**Steps**:
1. Delete a bookmark on Raindrop.io, then run the raindrop sync from the
   admin Raindrop tab.
2. The bookmark's page returns 404, and it's gone from `/raindrops/` and
   the home page.
3. Run a full regeneration. `output/raindrops/` has one HTML file per
   raindrop, plus listing pages.
4. Load the site repeatedly during the regeneration. Styling never
   disappears.

**Expected output**: the live site matches Raindrop.io and the markdown
sources, with no glitch during regeneration.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
