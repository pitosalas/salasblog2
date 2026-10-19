# TF54 Blog Index Sidebar for Feature F54
**Date Created:** 2026-10-19

## TF54.0 — Index data: tag counts and year counts

**Status**: not done

**Description**: Pure functions in `utils.py`:

* `blog_tag_counts(posts)` returns `[(tag, count)]`, sorted by count then
  name, with numeric tags excluded.
* `blog_year_counts(posts)` returns `[(year, count)]`, newest first.

Both take the same post list the blog listing uses.

**Test**: fixture posts covering:

* tag counts and their ordering
* numeric tags excluded
* posts with no tags
* year counts and ordering, including a post with a missing date, which is
  reported, not silently bucketed

## TF54.1 — Shared two-column layout and sidebar partial

**Status**: not done

**Description**:

* Move the home page's grid rules out of `home.css` into a new
  `static/css/two-column.css`, and point `home.html` at it.
* Add `templates/blog_sidebar.html`, a partial that renders the "Tags" and
  "Archive" sections in the secondary-column style.

**Test**: render `home.html` and check that it still has the two-column
markup and links `two-column.css`. Render the partial with fixture counts
and check the tag links (`/tags/<slug>/index.html`), the year links
(`/blog/<year>/index.html`) and the counts.

## TF54.2 — Column on blog listing pages

**Status**: not done

**Description**: `generate_listing_pages()` computes the counts once for
`blog` and passes them to `blog_list.html`. The template wraps the list in
the two-column grid and includes the sidebar. The raindrop listing is
unchanged.

**Test**: generate the listing for fixture posts. Every page, `index.html`
and `page-2.html`, contains the sidebar with the correct counts. The
raindrops listing doesn't.

## TF54.3 — Year archive pages

**Status**: not done

**Description**: Add `generate_year_pages(blog_posts, sidebar)` to write
`output/blog/<year>/index.html` for each year, using a `blog_year.html`
template that reuses the listing's entry markup, grouped by month, with
the sidebar. It is called from `generate_site()`.

TF53's pruning already owns `output/blog/`, so a year with no posts left
loses its page.

**Test**:

* one page per year, holding only that year's posts, newest first
* the sidebar is present
* a stale year directory is pruned

## TF54.4 — Tag pages: Posts / Links sections and sidebar

**Status**: not done

**Description**: `generate_tag_pages()` splits each tag's posts into blog
posts and raindrops. `tag_page.html` renders "Posts", then "Links", leaving
out an empty section, and includes the sidebar.

**Test**: a tag used by both a blog post and a raindrop renders both
sections in that order. A raindrop-only tag shows only "Links". The sidebar
is present.

## TF54.5 — Incremental regeneration updates affected tag and year pages

**Status**: not done

**Description**: `incremental_regenerate_post()` for a blog post also
rewrites:

* the tag pages for that post's tags
* its year page
* the listing page it already rewrites, which carries the fresh sidebar

**Test**: regression for the missing-tag-page gap. Add a post with a new tag
via incremental regeneration, then check that `/tags/<new>/index.html`
exists and the year page lists the post.

## TF54.6 — Tests

**Status**: not done

**Description**: Write the tests described in TF54.0–TF54.5 (in
`tests/test_blog_sidebar.py` plus additions to `tests/test_generator.py`),
then run the full suite.

## TF54.7 — Deploy and verify

**Status**: not done

**Description**:

1. Commit, push, `make deploy`.
2. Run a full regeneration on production.
3. Walk the demo steps in F54, including phone width in a narrow browser
   window, and spot-check that the counts match the tag pages for three
   tags.

**Test**: manual. Record the checks.
