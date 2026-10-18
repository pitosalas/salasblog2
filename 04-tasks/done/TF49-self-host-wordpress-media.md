# TF49 Self-host WordPress-era Images for Feature F49
**Date Created:** 2026-10-18

## TF49.0 — URL-to-media matching

**Status**: done

**Description**: Pure function in a new `src/salasblog2/wp_media.py`.

* Input: a post body and the set of paths in the tar.
* It finds WordPress image URLs: `i0.wp.com`, `*.files.wordpress.com`
  and `wp-content/uploads`.
* It pulls each URL's `YYYY/MM/filename` and returns the matched and
  unmatched URLs.
* URL-encoded names (`%2520` and the like) are decoded before matching.

**Test**: fixtures for proxied URLs with `?w=`/`?resize=`, `files.wordpress.com`,
double-encoded names, a Squarespace S3 path (expect unmatched) and a
non-WordPress image (ignored).

## TF49.1 — Link rewrite

**Status**: done

**Description**: Rewrite each matched URL in a post body to
`/static/images/wp/YYYY/MM/<file>`.

* Frontmatter isn't touched.
* Text outside the rewritten URLs stays byte-identical.
* This reuses the verify-then-write approach from F48's `legacy-rewrite`.

**Test**: rewrite of Markdown image links and raw `<img src>`. Check that
the body is unchanged except at the rewritten URLs, and that running it a
second time changes nothing.

## TF49.2 — CLI command `bg wp-media`

**Status**: done

**Description**: `bg wp-media --tar <path> [--content <dir>] [--apply] [--report]`.

* By default it's a dry run that lists each post and how many URLs it
  would rewrite.
* `--extract` copies the matched files from the tar into the repo's
  `static/images/wp/`. It touches no posts.
* `--apply` rewrites the matched image URLs in posts. It touches nothing
  else in them.
  It refuses to rewrite a URL whose target file isn't present under
  `static/images/wp/`.
* `--report` HEAD-checks the unmatched URLs and prints each one's status.

**Test**: CLI wiring is thin, like F48's commands. The logic underneath is
covered by TF49.0/TF49.1. The HEAD checks get mocked in a test of the
report formatter.

## TF49.3 — Tests

**Status**: done

**Description**: Dedicated `tests/test_wp_media.py` covering TF49.0-TF49.2,
then a full-suite run.

## TF49.4 — Production run

**Status**: done

**Description**:

1. Locally, run `bg wp-media --extract`. Commit and push
   `static/images/wp/`, then run `make deploy`.
2. Confirm that one image is served from
   `https://salasblog2.fly.dev/static/images/wp/...`.
3. On production, run
   `bg wp-media --content /data/content --apply` via `fly ssh`.
   No tar is needed there, because the rewrite checks the deployed
   `static/images/wp/`.
4. Regenerate the site, run `sync_to_github()` and pull locally.
5. Run `git diff --stat` on the pull. It should show only the repaired
   posts, with only URL lines changed.
6. Spot-check three posts in the browser.

**Test**: manual. Record the command, the counts, and which posts were
checked.

**Result (2026-10-18)**:

* `bg wp-media --extract` copied all 110 tar files (30 MB) into
  `static/images/wp/`. They were committed in `51e68a0b` and deployed.
* `https://salasblog2.fly.dev/static/images/wp/2014/08/f41d7-1407946425174.jpg`
  returned 200 after the deploy.
* On production:
  `bg wp-media --content /data/content --media-dir /app/static/images/wp --apply`
  rewrote **72 links**. The dry run beforehand gave the same count.
* 4 links were left unmatched. They are 2023-07 screenshots that aren't in
  the tar, and their old URLs return 404.
* The site was regenerated with `bg generate`, and `sync_to_github()`
  returned True.
* Sync commit `ac9c3d93` changed 57 posts, 67 lines each way. Every
  changed line is an image-URL line; nothing else changed.
* Spot-checked three live posts (`2018-04-05-useful`, `2014-08-23-haven…`,
  `2014-08-12-…rotisserie-chickens…`). Each repaired image returns 200.
