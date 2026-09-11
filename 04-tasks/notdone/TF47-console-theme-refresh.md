# TF47 Console Theme Visual Refresh for Feature F47

**Date Created:** 2026-09-11

**Branching**: unlike this repo's usual single-branch workflow (per
`.claude/process.md`: no review branches, commit straight to `main`), all
of TF47.0-TF47.11 happen on a dedicated branch (e.g. `feature/f47-console-
theme`) — a visual overhaul across every public template is too risky to
land directly on `main`, which deploys. Create the branch before TF47.0.
Merging back to `main` is its own explicit step (TF47.12) after TF47.10's
visual QA pass is clean, not automatic.

## TF47.0 — Shell, fonts, theme init, base.html header/nav/footer

**Status**: not done

**Description**: Copy `salas-console.css` into `static/css/` (as the new
stylesheet, alongside or replacing `style.css` — the search-dropdown rules
in `style.css` move into the new file per TF47.1's gap-filling, everything
else in `style.css` becomes redundant once Bootstrap is removed). Copy
`theme-toggle.js` into `static/js/`. In `base.html`: add the Google Fonts
`<link>`s (IBM Plex Mono + IBM Plex Sans), the no-flash inline theme-init
script in `<head>` before the stylesheet, remove the Bootstrap CSS/icons/JS
`<link>`/`<script>` tags, wrap the page in `.shell`, rebuild
`.site-header`/`.site-nav` to the handoff's markup (keeping every existing
nav link, the `admin-new-post`/admin-gating classes and JS, and the search
box), add the theme-toggle button as the last nav item, and restyle
`.site-footer`. Keep `script.js` and `admin-delete.js` loaded exactly as
now.

**Test**: template-render test asserting `base.html`'s output contains
`.shell`, `.site-header`, `.site-nav`, `#theme-toggle`, and the no-flash
script, and does NOT contain any `bootstrap` CDN URL.

## TF47.1 — Search dropdown styling (gap-fill)

**Status**: not done

**Description**: Restyle `.search-container`/`.search-results`/
`.search-result` (moved from `style.css` into the new stylesheet) using
`--bg`/`--panel`/`--line`/`--ink`/`--mute` tokens instead of hardcoded
white/gray hex values, so the dropdown is legible in dark mode. No JS
changes — `script.js`'s search behavior is untouched.

**Test**: manual (visual) — no automated test for pure CSS token
substitution with no markup change; covered by TF47.9's visual pass.

## TF47.2 — Home page

**Status**: not done

**Description**: Rebuild `home.html`'s content block into the handoff's
`.columns`/`.col-posts`/`.col-links` two-column layout: `.post` rows (ISO
date, sans-serif title, excerpt, `#tag` pills, dropping the numeric-tag
filter's Bootstrap badge markup for the handoff's plain `<span>#tag</span>`
style) on the left, `.linkitem` rows (existing `dd-mm-yyyy` date format,
title, note) on the right. Drop the Bootstrap file/link icons. Keep
`recent_posts`/`recent_raindrops` context and counts unchanged.

**Test**: extend `tests/test_blog_tags.py`-style template tests (a real
Jinja env against the actual templates dir) asserting `home.html` renders
`.columns`, `.col-posts`, `.col-links`, `.post`, `.linkitem`, and that a
tag renders as `#tagname` without a `badge` class.

## TF47.3 — Blog index (list + pagination)

**Status**: not done

**Description**: Rebuild `blog_list.html` as a full-width `.post-list`
(reusing TF47.2's `.post` row), keeping the month-group headers (restyled
to the `.col-title` convention: small, uppercase, muted). Design a Console
pagination component (hairline rules, `--accent` for the current page,
`--mute` for others, styled like `.col-more`) to replace Bootstrap's
`.pagination`, preserving all of `pagination`'s existing prev/next/ellipsis
logic untouched.

**Test**: template test asserting the pagination block renders with the
new classes (no `page-link`/`pagination` Bootstrap classes) when a
multi-page `pagination` context is passed, and that post rows use `.post`.

## TF47.4 — Single blog post

**Status**: not done

**Description**: Rebuild `blog_post.html`'s content block as the handoff's
`.article` block (meta line, `h1`, `.article-body`). Restyle admin-controls
(`Edit`/`New post based on this`/`Delete`) as `.btn`/`.btn-ghost`. Restyle
prev/next post nav as plain `.btn-ghost`-style links inside a bordered
footer row (no Bootstrap `.btn-outline-secondary`). Keep the
`images-{size}` wrapper class and the existing image-lightbox `extra_js`
script; change the inline-image treatment in the stylesheet from
border+shadow to a 1px `--line` border only (no shadow). Drop the
Bootstrap file icon next to the title.

**Test**: template test asserting `.article`, `.article-meta`,
`.article-body` render, that admin-controls use `.btn`/`.btn-ghost` (not
`btn-warning`/`btn-danger`), and that an `image_size` post still gets its
`images-{size}` wrapper class.

## TF47.5 — Link blog index (list + collections + pagination)

**Status**: not done

**Description**: Rebuild `raindrops_list.html` as a full-width `.link-list`
(reusing `.linkitem`), keeping month-group headers styled like TF47.3.
Restyle the collection-filter row (currently Bootstrap `.btn`/`.badge`
pills) as plain bordered/monospace pills using Console tokens. Keep cover-
image thumbnails (restyled: 1px `--line` border, no rounded corners per
"square unless it's a button/input" rule) and the important (★)/broken (⚠)
indicators as plain glyphs. Reuse TF47.3's pagination component.

**Test**: template test asserting `.link-list`/`.linkitem` render and that
collection pills no longer carry Bootstrap `.badge`/`.btn` classes.

## TF47.6 — Single raindrop post

**Status**: not done

**Description**: Rebuild `raindrop_post.html` using an `.article`-like
block: meta line (date, collection pill, restyled per TF47.5), the raw
raindrop source URL as an `--accent` link, the excerpt in a `--panel`
block (replacing the Bootstrap `card`), the "My Comment" note (if present)
in `.article-body` styling, tags as `#tag` pills. Restyle admin-controls
(`Delete`) as `.btn`. Restyle prev/next nav like TF47.4. Drop the Bootstrap
link icon.

**Test**: template test asserting the excerpt block no longer uses a
`card`/`card-body` class and that admin-controls use `.btn`.

## TF47.7 — Pages index + single page

**Status**: not done

**Description**: Rebuild `pages_list.html`: replace the Bootstrap 3-column
card grid (explicitly against the handoff's "no card grid" non-goal) with
a single-column `.post-list`-style row list (title, excerpt, no date since
pages don't have one) reusing the row-hover pattern. Restyle its
admin-controls as `.btn`/`.btn-ghost`. Rebuild `page.html`'s single-page
view as an `.article` block (no meta line, since pages have no date/tags),
with the same admin-controls restyling.

**Test**: template test asserting `pages_list.html` no longer renders a
`card`/`row-cols` grid and that both templates' admin-controls use
`.btn`/`.btn-ghost`.

## TF47.8 — Tag page

**Status**: not done

**Description**: Rebuild `tag_page.html` as a full-width mixed post/link
listing reusing `.post`/`.linkitem` rows as appropriate per each result's
content type, dropping the Bootstrap badge for the tag name in the heading
(plain `#tag` styling) and the type-indicator icons and collection badge
(kept as plain text, e.g. `· {{ collection }}`, consistent with TF47.5).

**Test**: template test asserting rendered output for a mixed blog+raindrop
result set uses `.post`/`.linkitem` rows with no `badge` classes.

## TF47.9 — 404 page

**Status**: not done

**Description**: Rebuild `404.html` inside the Console shell/typography:
plain heading treatment (no Bootstrap `display-1`/`text-danger`), action
links as `.btn`/`.btn-ghost`, "you might be looking for" list restyled
without the Bootstrap `card bg-light` wrapper (a plain bordered block using
`--panel`, or just a plain list — no card).

**Test**: template test asserting no `card`/`display-1`/`btn-primary`
classes remain and that action links use `.btn`/`.btn-ghost`.

## TF47.10 — Full visual regression pass

**Status**: not done

**Description**: Run `uv run bg server --reload` against real local
content. Walk every in-scope route (home, blog index, a single post with
tags, a single post with `image_size` set, link blog index with
collections, a single raindrop, pages index, a single page, a tag page
with mixed content, a bad URL) in both light and dark mode, and at a
mobile width (≤860px). Check every item in F47's "How to Demo" section and
the design handoff's acceptance checklist. Confirm the admin-only controls
still correctly show/hide based on auth state, and that delete/edit/search
functionality is unaffected (JS untouched, only markup/CSS changed).

**Test**: none beyond the automated template-structure tests in
TF47.0-TF47.9 — this step is manual, human-judgment visual QA across many
states not practical to assert in an automated test.

## TF47.11 — Remove now-dead `style.css` rules

**Status**: not done

**Description**: Once TF47.0-TF47.9 land, `static/css/style.css`'s
Bootstrap-override rules (the `--bs-primary` tokens, `.card-body`/
`.excerpt-heading` fixes, etc.) are dead — Bootstrap is no longer loaded on
any in-scope page. Delete the file (or whatever's left of it after
TF47.1 moves the search-dropdown rules out) and its `<link>` in
`base.html`, and confirm nothing else references it.

**Test**: `grep -r "style.css"` across `templates/` returns nothing;
full test suite still green (confirms nothing else depended on it).

## TF47.12 — Merge to main

**Status**: not done

**Description**: Only after TF47.10's visual QA pass is clean on the
`feature/f47-console-theme` branch: merge to `main`, then follow the
normal single-branch workflow from there (run tests, commit if anything
needs squashing/cleanup, push, deploy). Delete the feature branch once
merged.

**Test**: none — this step is the merge/deploy operation itself, verified
by the full test suite passing on `main` post-merge and a live check of
the deployed site.
