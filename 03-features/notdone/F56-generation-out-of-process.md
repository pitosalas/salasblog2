# F56 — Run site generation out of the server process
**Priority**: High
**Date Created:** 2026-10-20
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: The public site feels slow at times because every page is served by the
single uvicorn process on one shared CPU, and that same process also runs
CPU-heavy site generation in background threads. Python's GIL lets only one
thread run at a time, so while a generation renders thousands of pages, page
requests wait. Fly's shared-CPU throttling stretches this out further.

This feature moves all site generation (full and incremental) into a child
process (`bg` CLI commands launched with `subprocess`), so it no longer
competes with request handling for the GIL. A lock in the server makes sure
only one generation child runs at a time. It also removes the 5-minute
posts-index rescan, which re-reads every post's frontmatter even though every
write path already refreshes that index.

Out of scope: serving `output/` from a static web server or CDN (option 1),
changing how visits are counted, and the 60-second stats cache.

## How to Demo
**Setup**: Deployed to production (or `bg server` locally with the full content).

**Steps**:
1. In one terminal, time the home page in a loop:
   `while true; do curl -s -o /dev/null -w '%{time_total}\n' https://salas.com/; sleep 1; done`
2. In the admin, click Regenerate (full site generation).
3. While it runs, watch the timings, and run `ps` on the machine (`fly ssh console -C "ps aux"`)
   to see a separate `bg generate` process doing the work.
4. Edit and save a blog post in the admin; the post page opens at once and the
   home page shows the change shortly after.

**Expected output**: home-page times stay roughly flat (no multi-second
spikes) during the regeneration; the generation runs as its own process; the
edited post, its listings and the admin All Posts list are all up to date.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
