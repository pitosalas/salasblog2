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

**Status**: not done

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
