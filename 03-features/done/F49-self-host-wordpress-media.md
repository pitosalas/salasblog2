# F49 — Self-host WordPress-era Images
**Priority**: Medium
**Date Created:** 2026-10-18
**Done:** yes
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Old posts imported from the WordPress.com blog embed images
through WordPress's `i0.wp.com` proxy. The originals on
`salas.com/wp-content/uploads/` no longer exist, so these images are broken.

The WordPress media export (`~/Desktop/wordpress-export/media-export-*.tar`,
110 files) has local copies of many of them. This feature puts those copies
into the site's own static images and rewrites the post links to point at
them.

## Findings (2026-10-18)

* 107 local posts link to 147 unique WordPress-hosted image URLs (167 links
  in all).
* 142 of those URLs go through the `i0.wp.com` proxy.
* 74 of the 147 have a matching file in the tar, by `YYYY/MM/filename`.
* Spot check: a `salas.com/wp-content/uploads` image comes back **404**.
* A Squarespace-era S3 image comes back **403**.
* A third-party hotlink (`applegazette.com`) still comes back **200**.

## Scope

* **In:** copy the matched tar files into `static/images/wp/YYYY/MM/`.
* **In:** rewrite the matching links in posts to
  `/static/images/wp/YYYY/MM/<file>`, dropping the proxy's `?w=`/`?resize=`
  query string.
* **In:** a report of the URLs that couldn't be matched, each marked
  dead or alive.
* **Out:** recovering the dead Squarespace/S3 images.
  That needs the Wayback Machine, which would be a separate feature.
* **Out:** third-party hotlinks that still work. They stay as they are.

## What changes, and nothing else

* **Media files are added.**
  The matched files from the tar are committed to the repo under
  `static/images/wp/YYYY/MM/`, and pushed.
  `make deploy` then puts them on fly.io.
  The generator's `copy_static_files()` copies them into the served
  `output/static/` like any other static asset.
* **Image references in existing posts are repaired.**
  The only edit to a post is replacing a matched WordPress image URL with
  its `/static/images/wp/...` path.
  Frontmatter and every other byte of the body stay identical, and this
  is checked before each write.
* **No posts are created, deleted, or modified in any other way.**
  Unmatched URLs are reported, not touched.
  Tags, dates, titles and missing posts are all out of scope here.

## Production

* **Post repairs are made on `/data/content` via `fly ssh`, not by editing
  local `content/`.**
  That's the same rule F46 and F48 follow.
* **The images must be deployed before the post links are rewritten**, so
  that no rewritten link points at a file that isn't there yet.

## How to Demo
**Setup**: rewrite applied on production and the site regenerated.

**Steps**:
1. Open a post from 2014-08 that had a broken `i0.wp.com` image.
2. Check that the image now loads from `/static/images/wp/2014/08/...`.
3. Run `bg wp-media --report` and read the list of URLs still unmatched.

**Expected output**: the 74 matched images show up on their posts.
The rest are listed with their status.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
