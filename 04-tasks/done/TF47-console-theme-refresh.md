# TF47 Console Theme Visual Refresh for Feature F47
**Date Created:** 2026-09-11

## TF47.0 — Create the dedicated branch

**Status**: done

**Description**: Work happens on `feature/site-redesign`, not `main`
directly, given the size of the change. Branch created from a clean
`main`. No test — infrastructure step, not behavior.

## TF47.1 — Delete confirmed-dead templates

**Status**: done

**Description**: Deleted `templates/admin_new.html` (no route renders
it) and `templates/includes/navigation.html`, `pagination.html`,
`post-navigation.html` (never referenced by any `{% include %}`).
Test: full suite passes after deletion — nothing referenced these files.

## TF47.2 — Decide disposition of `overview.html`

**Status**: done — decided (a)

**Description**: `templates/overview.html` is still actively rendered
by `generator.py`'s `generate_overview_page()` (called from the main
generation pipeline) to `output/overview.html`, even though it's
orphaned from nav. Decision: **(a)** leave
`generate_overview_page()`/`overview.html` alone — out of scope for
this visual refresh, keeps generating the orphaned page as-is,
unstyled/Bootstrap. No code needed for this task.

## TF47.3 — Add Console theme CSS and theme-toggle script

**Status**: done

**Description**: Added the Console theme as three small, single-concern
CSS files rather than one stylesheet (per the user's modular-files
preference — see `.claude/style_guide.md`'s "one CSS file per module"
rule, applied more literally here):

- `static/css/theme.css` — color tokens (light default, dark via
  `[data-theme="dark"]` or `prefers-color-scheme`), `IBM Plex Mono`
  font, base reset (`body`, `a`, `.d-none`).
- `static/css/header.css` — header/nav/brand/search/theme-toggle button.
- `static/css/layout.css` — main content wrapper, footer, and the
  still-functional (non-Bootstrap) rules `base.html` depended on from
  the old `style.css`: markdown image sizing/border and
  `.excerpt-heading`.

Each future per-template task (TF47.5+) gets its own CSS file the same
way, rather than growing one of these three.

Added `static/js/theme-toggle.js`: sets `data-theme` on `<html>`
synchronously in `<head>` (avoids a flash of the wrong theme on load),
button click toggles and persists the choice to `localStorage`, default
follows OS preference when nothing's stored. Built from the two
reference screenshots directly (light/dark home page), not the external
`des-hand` handoff folder — per the user, that folder should be
disregarded.

Test: no isolated JS test added (DOM/localStorage behavior would need a
browser harness) — covered instead by TF47.15's manual visual QA pass,
per the style guide's "runtime-only... marked manual" rule. Verified by
hand via `make generate`: generated `output/index.html` links all three
CSS files and the toggle script, and the button/markup render correctly
in a standalone template render.

## TF47.4 — Restyle `base.html` shell

**Status**: done

**Description**: Replaced the Bootstrap nav/head/footer in `base.html`
with the Console theme's monospace header (`~/pito salas`, nav links,
dark/light toggle button), hairline-rule footer, and the new CSS/font
links (Bootstrap and Bootstrap Icons CDN links removed, along with
`style.css`). Preserved the `title`/`description`/`content`/`extra_js`
blocks, the admin-status reveal JS (`classList.remove('d-none')`), and
the search box's element IDs.

Test: full suite passes. Updated `tests/test_bootstrap_styling.py`'s
three base-chrome assertions (navbar/bootstrap-cdn/footer-bg) to assert
the new `site-header`/`theme.css`/`site-footer` markup instead — the
old assertions tested exactly what this task intentionally removed. The
file's other tests (Bootstrap card/grid/pagination classes inside
not-yet-migrated child templates) are untouched and still pass; they'll
be updated template-by-template in TF47.5–TF47.13. Also updated
`tests/test_pages_feature.py::test_pages_url_contains_menu_and_header`,
which asserted `"navbar"` against `base.html`'s live-rendered output,
to assert `site-header`/`site-nav` instead.

## TF47.5 — Restyle `home.html`

**Status**: done

**Description**: Two-column CSS grid (`home-grid`, 1.7fr/1fr, collapses
to one column under 700px) matching the two reference screenshots:
Recent Posts left, Link Blog right, each a vertical `entry-list` of
hairline-separated entries (date on its own line, bold title, muted
excerpt, amber `#tag` links for posts). Dropped the hero/welcome banner
and all Bootstrap card/grid/icon classes — no icon library, per the
design brief. Post dates switched from `%B %d, %Y` to plain `%Y-%m-%d`
to match the screenshots (raindrop dates already used `dd_mm_yyyy`,
matching). Added `static/css/home.css`, wired in via a new `extra_css`
block added to `base.html`'s `<head>` (same pattern every later
per-template task will reuse).

Also lightened the light-mode background (`--bg` in `theme.css`,
`#faf8f3` → `#f1ede3`, border darkened to match) per user feedback that
the first pass looked too bright/white.

Test: full suite passes. Updated `tests/test_home_see_all.py`'s
read-more assertion (`class="small"` → `class="read-more"`);
`tests/test_bootstrap_styling.py`'s two home-page tests
(`test_home_uses_card_class` → `test_home_uses_console_entry_list`,
`test_home_uses_bootstrap_grid` → `test_home_uses_console_grid_not_bootstrap`)
to assert Console markup and absence of Bootstrap classes;
`tests/test_content_type_badges.py`'s two home-page icon tests
(`TestIconsOnHomePage`) replaced with
`TestContentTypeDistinguishedByColumnOnHome`, asserting no Bootstrap
Icons classes remain and that content type is conveyed by column
instead.

## Desired Hierarchy

* correct the hiearchy of the page.

head area
center area
  left col
    col title ("recent posts")
    line
    list of posts - each post is:
      left subsecton 
        containing date
      righth subsection 
        title
        body
        tags
  right col  (shaded a little)
    col title ("link blog")
    line
    list of link entries - each one is:
      date
      title
      body
footer area

**Implemented**: post entries (`home.html`'s left column) now use a
`.entry-post` flex row — `.entry-date` as a fixed 90px left subsection,
`.entry-content` (title/excerpt/read-more/tags) as the right subsection
(`static/css/home.css`). Link blog entries (right column) unchanged —
already a plain vertical stack of date/title/body. Stacks back to a
single column below 480px width.

## TF47.6 — Restyle `blog_list.html`

**Status**: done

**Description**: Reused the same `.entry-post` pattern from `home.html`
(date rail + title/excerpt/tags), grouped by month under a
`.section-heading` (the first one flush via a `.flush` modifier, since
`.page-header` above it already supplies its own bottom border/spacing).
Pagination kept the same `page-item`/`page-link` class names, restyled.

Factored out everything reused across list-style templates (this one,
and `raindrops_list.html`/`tag_page.html` still to come) into a new
shared `static/css/entries.css`, now linked globally from `base.html`
alongside `theme.css`/`header.css`/`layout.css`: `.entry-list`/`.entry`/
`.entry-post` (moved out of `home.css`, which was raindrops_list -->
tag_page.html-only home-page use before this), plus new
`.page-header`/`.page-title`/`.page-subtitle`/`.page-meta`,
`.section-heading` (also moved out of `home.css`, now shared by home's
column titles and blog's month headings), `.pagination`/`.page-link`,
and `.empty-state`. No `blog-list.css` needed — nothing in this
template turned out to be template-specific.

Test: full suite passes. Updated
`tests/test_content_type_badges.py`'s `TestPostIconInBlogList` (was 2
tests asserting `bi-file-text` present) to one test asserting it's
absent and `entry-post` markup is present instead.

## TF47.7 — Restyle `blog_post.html`

**Status**: done (test run deferred — see note)

**Description**: New `post-header`/`post-title`/`post-meta`/`post-body`
structure, tags as the shared `.tag` class. Admin-actions footer
restyled into an `.admin-panel` with three distinct button treatments
(`.btn-edit` amber, `.btn-derive` neutral, `.btn-delete` red — the one
deliberate exception to the single-amber-accent rule, since these are
admin-only controls never shown in the public design reference, and
"delete" specifically benefits from a universally-understood danger
color). Prev/next post nav restyled as plain `.post-nav-link`s (no
button chrome), still exactly the same conditional structure. Added
shared `static/css/post-detail.css` (header/admin-panel/nav — will also
serve `raindrop_post.html` in TF47.9), linked globally from
`base.html`. `.entry-tags .tag` generalized to a standalone `.tag`
class in `entries.css` so this template can reuse it too.

Found but not touched: `blog_post.html` imports the `admin_controls`
macro from `macros.html` but never calls it (builds the same markup
inline instead) — and none of `macros.html`'s four macros
(`render_navigation`, `render_pagination`, `render_post_navigation`,
`render_status_message`, `admin_controls`) are actually invoked by any
template in the repo. Likely fully dead code, but that's a separate
finding from this visual-only task — flagged for the user, not deleted.

Test: not run this pass, per the user's explicit request to stop
running the suite between per-template restyles during this feature —
`make generate` + visual check only. Full-suite verification deferred
to a batch run before the relevant tasks are marked truly complete
(end-of-feature checkpoint / TF47.15), at which point the known
casualties to fix are: `tests/test_admin_controls.py` (`btn-warning`→
`btn-edit`, `btn-info`→`btn-derive`, `btn-outline-secondary`→
`post-nav-link`), `tests/test_content_type_badges.py` (`bi-file-text`
in blog_post header), and `tests/test_bootstrap_styling.py`
(`col-lg-` grid assertion).

## TF47.8 — Restyle `raindrops_list.html`

**Status**: done (test run deferred)

**Description**: Reused the `entry-post`/`section-heading`/pagination
pattern from `blog_list.html`. Page header shows collection count;
collections rendered as `.collection-chip` filter pills. Each entry
gained raindrop-specific extras: importance/broken-link glyphs (plain
Unicode `★`/`⚠`, no icon library) in the date rail, a floated
`.entry-cover` thumbnail, `.entry-source` (domain), `.entry-note`
(the user's comment, italic hairline-bordered), and `.entry-source-url`
(the raindrop permalink). Added `static/css/raindrops-list.css` for all
of this (collection chips + entry extras) since none of it is reused by
`blog_list.html`.

Test: deferred (per the user's "don't run tests" instruction for this
batch) — `make generate` + visual check only.

## TF47.9 — Restyle `raindrop_post.html`

**Status**: done (test run deferred)

**Description**: Mirrors `blog_post.html`'s structure via the shared
`post-detail.css` (`post-header`/`post-title`/`post-meta`/`post-body`/
`admin-panel`/`post-nav`) plus two new shared rules added to that file:
`.post-excerpt` (a hairline-bordered quote block for the raindrop's
excerpt) and `.post-note` (the "My Comment" section). Renamed
`.admin-panel-title` → `.label-heading` in `post-detail.css` (used for
both "Admin Actions" and "My Comment" headings; `blog_post.html`
updated to match). Delete-only admin action (raindrops have no
edit/derive), styled with `.btn-delete`.

Test: deferred, same as TF47.8.

## TF47.10 — Restyle `pages_list.html`

**Status**: done (test run deferred)

**Description**: Converted the Bootstrap card grid to the plain
`entry-list` pattern (no card grid, per the design brief). Edit/Delete
buttons **kept their literal Bootstrap-era class names**
(`btn btn-primary btn-sm` / `btn btn-danger btn-sm`) rather than
switching to `.btn-edit`/`.btn-delete` like `blog_post.html` —
`tests/test_pages_feature.py` hardcodes those exact strings in ~15
places across both `pages_list.html` and `page.html`, so `.btn-primary`/
`.btn-danger`/`.btn-sm` were added to `post-detail.css` as Console-styled
equivalents of the same names instead of touching every assertion.
New templates (`blog_post.html`, `raindrop_post.html`) still use the
`.btn-edit`/`.btn-derive`/`.btn-delete` naming; this is a deliberate,
noted inconsistency traded for not touching ~15 test assertions.

Test: deferred, same as TF47.8.

## TF47.11 — Restyle `page.html`

**Status**: done (test run deferred)

**Description**: Same `post-header`/`post-body` structure as
`blog_post.html`; admin edit/delete controls kept the same
`btn btn-primary btn-sm`/`btn btn-danger btn-sm` classes as
`pages_list.html`, for the same test-compatibility reason (TF47.10).

Test: deferred, same as TF47.8.

## TF47.12 — Restyle `tag_page.html`

**Status**: done (test run deferred)

**Description**: Reused `entry-post`/`entry-list`, ISO dates
(`%Y-%m-%d`), and `raindrops-list.css`'s `.entry-source` for the
raindrop-only collection line. Handles both post types (blog + raindrop)
in one loop, same as before. No icon distinguishing the two types
(icon library dropped) — same "column/context tells you the type"
reasoning as `home.html`, though here both types share one list, so the
distinction is weaker than on the homepage; not addressed further since
no test or design reference calls for it.

Test: deferred, same as TF47.8.

## TF47.13 — Restyle `404.html`

**Status**: done (test run deferred)

**Description**: New `static/css/not-found.css`: large amber `404`,
message, two action buttons (`.btn-edit` for the primary "Go Home",
plain `.btn` for the others), and a hairline-bordered "you might be
looking for" box replacing the Bootstrap card.

Test: deferred, same as TF47.8.

## TF47.14 — Restyle `admin_login.html`

**Status**: done

**Description**: Centered `.login-card` form using `theme.css` tokens
directly (no shared shell needed for something this small). New
`static/css/admin-login.css`. No functional change — same `action`,
same field `name`/`id` attributes.

## TF47.15 — Restyle `post_editor.html`

**Status**: done

**Description**: Full rewrite of the markup/classes (this file has no
test coverage on CSS classes — `tests/test_post_editor.py` exercises
the backend API only, not rendered HTML — so there was no
test-compatibility constraint here, unlike `pages_list.html`/`page.html`
in TF47.10/11). New `editor-header`/`editor-container`/`field`/
`field-row`/`tags-row`/`tag-picklist`/`inline-preview`/`editor-actions`
structure in new `static/css/post-editor.css`, including EasyMDE
toolbar/CodeMirror overrides onto the Console tokens. Dropped the
Bootstrap JS bundle (nothing here used it — no `data-bs-*` attributes).

All element `id`s the JS depends on are unchanged (`title`, `date`,
`category`, `image_size`, `type`, `loaded_mtime`, `tags`,
`tagPicklistToggle`, `tagPicklist`, `tagPicklistFilter`,
`tagPicklistChips`, `content`, `inlinePreview`, `previewBtn`,
`statusMessage`, `editorForm`), as are all JS function/variable names.
One JS line did change: `showStatus()`'s `el.className` construction
switched from Bootstrap's `'alert mb-3 alert-' + ...` to this file's own
`'status-message ' + ('status-error'|'status-success')` — functionally
identical (still fully replaces the class list to reveal/style the
message), just pointed at the new class names.

Verified via standalone Jinja renders (create-blog-post and
edit-existing-page paths) — both render without template errors.

## TF47.16 — Restyle `admin.html`

**Status**: done

**Description**: The admin SPA (~940 lines, ~700 lines of inline JS
building HTML strings for 10 tabs: Stats, Propose, Drafts, All Posts,
Generate, Scheduler, Data Sync, Pages Sync, Raindrop, Emergency).
Highest-risk template in this feature. Two different strategies used,
by risk level:

- **Top nav, topbar, tab buttons, footer** (static markup, nothing
  JS-dependent beyond `.admin-tab`/`.active`/`.admin-pane`/`.d-none`,
  all preserved): rebuilt directly — header/footer now reuse the
  public site's `site-header`/`site-nav`/`site-footer` classes
  (`theme.css`/`header.css`/`layout.css`, plus the light/dark toggle)
  for visual consistency; tab buttons dropped their
  `btn btn-primary btn-sm` classes (kept only `admin-tab`, `active`,
  and a new `admin-tab-danger` for Emergency).
- **Everything inside the 11 tab panes, and all ~20 JS functions that
  build HTML via template literals** (`statusHtml()`, `progressHtml()`,
  `loadDrafts()`, `renderAdminPosts()`, etc.): left completely
  untouched, both the static markup and every literal Bootstrap class
  string baked into the JS (`btn btn-sm btn-outline-primary`,
  `alert-success`, `badge bg-secondary`, `table table-sm table-hover`,
  `spinner-border`, `text-muted`, `d-flex gap-2`, ...). Hand-editing
  every occurrence across that much interleaved template+JS was judged
  too high-risk for a visual-only pass with zero test coverage on this
  file's rendered HTML to catch a mistake. Instead, new
  `static/css/admin.css` includes a "Bootstrap-class-compatible utility
  shim" — the same technique already used for `pages_list.html`/
  `page.html`'s `btn-primary`/`btn-danger` (TF47.10) — redefining
  `btn`/`btn-sm`/`btn-outline-*`/`alert`/`alert-*`/`badge`/`bg-*`/
  `table`/`table-*`/`spinner-border`/`text-muted`/`text-danger`/
  `fw-bold`/`small`/`d-flex`/`d-none`/`gap-*`/`m*-*`/`border*`/
  `font-monospace` etc. against the Console tokens, rather than
  removing Bootstrap and leaving those elements unstyled.

Verified via standalone Jinja render (no context needed) — renders
without template errors; all 10 `showTab()` targets and all 11
`admin-pane d-none` blocks present and unchanged.

## TF47.17 — Restyle `stats_page.html`

**Status**: done

**Description**: Pre-generated stats page (served via iframe from
`admin.html`'s Stats tab). Tables restyled to hairline rows, period
tabs to bordered pill buttons (`.active` uses the accent color — same
class the existing `showPeriod()` JS already toggled, untouched). New
`static/css/stats-page.css`; background stays `transparent` as before
(inherits whatever the parent iframe/tab shows). Verified via a
standalone Jinja render with sample stats data.

## TF47.18 — Write the dedicated test suite for this feature

**Status**: done

**Description**: Ran the full suite (deferred since TF47.7 per the
user's "don't run tests" instruction during the per-template restyle
pass) and fixed every casualty in one batch — 18 failures, all
expected consequences of the redesign, none a real regression:

- `test_admin_controls.py`: `btn-warning`/`btn-info`/
  `btn-outline-secondary` assertions → `btn-edit`/`btn-derive`/
  `post-nav-link`.
- `test_bootstrap_styling.py`: `card`/`col-lg-`/`btn btn-primary`
  assertions on `raindrops_list.html`, `pages_list.html`,
  `blog_post.html`, `raindrop_post.html`, `page.html`, `404.html` →
  Console equivalents (`entry-post`/`entry-list`/`post-body`/
  `btn-edit`), each now also asserting the old class is *absent*.
- `test_content_type_badges.py`: 4 more icon-presence tests (link icon
  in `raindrops_list.html` x2, post/link icon in `blog_post.html`/
  `raindrop_post.html` headers) → icon-absence, same pattern as the
  home/blog_list ones fixed earlier.
- `test_pages_feature.py`: 4 tests hardcoding
  `<div class="card h-100">` counts or `"row row-cols-1"`/
  `"card h-100"` presence → `<li class="entry">` counts and
  `entry-list` presence / `card h-100` absence.
- `test_tag_pages.py`: one test expecting bare `>python<` → `>#python<`
  (tags now render with a literal `#` prefix, per the design).

Added `tests/test_console_styling.py` (6 tests, new): no Bootstrap
CDN reference survives in any of the 13 in-scope templates; `base.html`
links all 5 shared CSS files and `theme-toggle.js`; the toggle button
element is present; all 4 admin/editor pages link `theme.css`; `admin.
html` shares the public `site-header` class with `base.html`; every
`/static/css/*.html` reference across all 13 templates resolves to a
file that actually exists on disk.

Full suite: **613 passed, 11 skipped, 0 failed.**

## TF47.19 — Visual QA pass and merge back

**Status**: done

**Manual test note**:
- **Command/setup**: `make local` (regenerate + `uv run bg server
  --reload`) on `feature/site-redesign`, viewed live in a browser
  throughout the session, both light and dark mode, including sample
  raindrop content copied down from production for the Link Blog
  columns/pages.
- **Expected**: all 9 public templates plus the 4 admin/editor pages
  render in the Console visual style in both modes; no Bootstrap chrome
  anywhere; toggle persists across navigation and reload; admin
  functionality (login, create/edit, delete, stats, tabs) unaffected.
- **Actual**: confirmed by the user through the session, with several
  rounds of live feedback acted on along the way (background shade,
  column divider/shading, section-heading hairlines, header/body
  contrast, date-rail entry layout, spacing) — user confirmed "visual
  pass is OK" on 2026-09-11.

Merging `feature/site-redesign` back into `main` and moving this
feature/task pair to `done/` next.
