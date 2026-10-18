# TF51 Retire Post Categories for Feature F51
**Date Created:** 2026-10-18

## TF51.0 — Remove the Category field from the post editor

**Status**: done

**Description**: Delete the `field-category` block from
`templates/post_editor.html`, along with any CSS that styles only that
field.

**Test**: a post-editor render test asserts there's no `name="category"`
input, for both create and edit.

## TF51.1 — Stop loading and saving `category` in the server

**Status**: done

**Description**: In `server.py`:

* Drop `category` from `ContentFields`.
* Drop the `category` form parameter from the create and edit routes.
* Drop `category` from the dict the editor loads a post into.

Saving a post no longer writes `category`. `save_content_item` rebuilds the
frontmatter from the form fields, so editing an old post drops its
`category:` line as well.

**Test**: `TestCategoryRetired` in `tests/test_post_editor.py`:

* creating a post doesn't write `category`, even if the form sends one
* editing an old post drops its `category`
* neither editor page renders a category input

## TF51.2 — Remove the category from `overview.html`

**Status**: done

**Description**: Delete the `item-category` span from the orphaned
`templates/overview.html`, so no template refers to the field.

**Test**: none needed. This removes markup from a page nothing links to,
and the existing generator tests still render it.

## TF51.3 — Delete the unused `static/js/search.js`

**Status**: done

**Description**: No template or script loads `search.js`; the live search
is in `script.js`. Its `item.category` match is the field's last reader.

**Test**: none needed. A grep confirms no template or script references the
file.

## TF51.4 — `bg strip-categories` command

**Status**: done

**Description**: A pure function that removes the top-level `category:`
line from a post's frontmatter.

* Only that one line goes. Every other byte of the frontmatter and body
  stays identical, and this is checked before the write.
* No frontmatter re-serialization, so key order and quoting are kept.
* A post without the line is left untouched.
* The CLI wrapper is a dry run by default and writes with `--apply`, the
  same shape as `wp-media`.

**Test**:

* quoted, unquoted and numeric values
* no category line
* `category` inside the body, which must be left alone
* a frontmatter key that merely starts with `category`, which must be left
  alone
* running twice changes nothing
* the byte-identical check

## TF51.5 — Tests

**Status**: done

**Description**: Cover TF51.0, TF51.1 and TF51.4 in the tests, update
fixtures that rely on the editor's category behavior, then run the full
suite.

## TF51.6 — Production run

**Status**: done

**Description**:

1. Commit, push and deploy.
2. On production, run `bg strip-categories --content /data/content`,
   check the dry run, then `--apply`.
3. Regenerate the site, run `sync_to_github()` and pull.
4. Check that the sync diff contains only removed `category:` lines.

**Test**: manual. Record the counts, and run a `grep` for any remaining
`^category:` lines.

**Result (2026-10-18)**:

* Deployed `8b647d1f`.
* The production dry run reported 2,815 files.
* `--apply` stripped 2,815 files, and a grep found **0** remaining
  `^category:` lines. The site was regenerated and `sync_to_github()`
  returned True.
* **Problem found in the sync diff (`a726fafc`):** 3 files with CRLF line
  endings were converted to LF:
  * `2026-10-17-lotus-improv-pre-history.md`
  * `pages/Recommendations.md`
  * `pages/recommendations.md`, an identical duplicate that differs only
    in case
* The cause was `read_text`/`write_text` normalizing newlines. The
  verification compared `splitlines()`, which ignores endings, so it didn't
  catch the change.
* **Fix:**
  * `remove_frontmatter_key` now works on lines with their endings kept.
  * The command reads and writes bytes.
  * Regression tests cover CRLF and mixed endings.
* **Restore:** each file was rebuilt from its pre-run git version, keeping
  its original endings, with only the intended change applied.
  The rebuilt files were copied to `/data/content`.
  The same restore fixed one file that the F46 tag-apply step flattened
  during the F50 run (see I04).
* Ignoring line endings, the strip changed nothing except `category:`
  lines.
