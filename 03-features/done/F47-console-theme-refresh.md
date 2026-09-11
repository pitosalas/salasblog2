# Feature description for feature F47

## F47 — Console Theme Visual Refresh

**Priority**: Medium

**Date Created:** 2026-09-11

**Done:** no

**Tasks File Created:** yes

**Tests Written:** no

**Test Passing:** no

**Description**: A visual-only refresh of the public-facing site, from an
external design handoff (`/Users/pitosalas/Downloads/des-hand/` —
`README.md`, `salas-console.css`, `theme-toggle.js`, `reference-home.html`,
`screenshots/`). Same information architecture, same routes, same menu —
new look only.

The direction, called **Console**: monospace UI chrome, hairline 1px rules
instead of Bootstrap cards/shadows/badges, a compact one-line header
(`~/pito salas`), a two-column home page (blog left, link blog right), one
amber accent, and dark/light mode (OS preference by default, a
`localStorage` override via a toggle button). No hero, no card grid, no
shadows, no gradients, no icon library, no JS framework — CSS plus one
20-line toggle script.

### Scope — templates getting the refresh

`base.html` (shell, header, nav, footer) plus every template that extends
it and is actually rendered by `generator.py`/`server.py`:

- `home.html` — the real homepage (`index.html`), closely matches the
  handoff's `reference-home.html`.
- `blog_list.html`, `blog_post.html`
- `raindrops_list.html`, `raindrop_post.html`
- `pages_list.html`, `page.html`
- `tag_page.html`
- `404.html`

### Out of scope

- `admin.html` (938-line Bootstrap SPA), `admin_login.html`,
  `post_editor.html`, `stats_page.html` — none extend `base.html` (each has
  its own standalone `<head>` loading Bootstrap independently), and the
  handoff provides no fidelity for their specific UI (tabs, EasyMDE editor,
  sync controls, stats tables). They keep Bootstrap and their current look.
- `admin_new.html` — confirmed dead code (no route renders it; its own body
  even contains a "TODO: copy the JS from admin.html" placeholder comment).
  Not touched by this feature; a deletion candidate for a separate chore.
- `overview.html` — rendered to a real file (`output/overview.html`) but
  not linked from the site's nav and not the homepage
  (`generate_overview_as_home`, the function that would make it so, is
  itself dead code — never called). Left alone; noted as a pre-existing
  rough edge, not this feature's job to resolve.

### Gaps the handoff doesn't cover

The handoff's fidelity is for the pages it shows (mainly the home page). A
few real, live pieces of UI aren't in its reference and need original
styling using the *same token system* (`--bg`/`--ink`/`--accent`/`--line`/
etc. from `salas-console.css`), not invented from scratch:

1. **Live search dropdown** (`#search-input`/`#search-results` in
   `base.html`, styled in `static/css/style.css`) — currently hardcoded to
   a white background; needs to use `--bg`/`--panel`/`--line`/`--ink` so it
   works in dark mode.
2. **Pagination** (`blog_list.html`, `raindrops_list.html`) — currently
   Bootstrap's `.pagination`/`.page-link`. Needs a hairline-rule Console
   equivalent (the handoff's `.col-more` link style is the closest existing
   precedent).
3. **Raindrop-specific UI** (`raindrops_list.html`/`raindrop_post.html`):
   collection filter pills, cover-image thumbnails, important/broken
   indicators, the "My Comment" block, the raindrop source-URL line.
4. **Prev/next post navigation** footer (`blog_post.html`,
   `raindrop_post.html`).
5. **Per-post image sizing** (`images-small/medium/large/full` wrapper
   classes, `image_size` frontmatter field, and the current border+shadow
   treatment on inline article images) — the shadow contradicts the
   handoff's "no shadows anywhere" rule, so this becomes a 1px `--line`
   border only; the click-to-zoom link behavior (existing JS in
   `blog_post.html`) is unrelated to styling and stays as-is.
6. **Bootstrap Icons removal** (`bi bi-file-text`, `bi bi-link-45deg`, etc.,
   used to mark post-vs-link rows) — the handoff's explicit non-goal is "no
   icon library." These get dropped; the row's position (left/right column)
   or section context already distinguishes post vs. link.

### What stays exactly as it is

Routes, menu items, admin-gating logic (`.admin-controls` shown/hidden by
existing JS), delete/edit actions (`admin-delete.js`), the search feature's
JS behavior (`script.js`), pagination's underlying logic, tag data, dates'
underlying values (only the home/blog_list/tag_page *list-row* dates switch
to ISO `YYYY-MM-DD` per the handoff; raindrop rows keep the site's existing
`dd-mm-yyyy` format per the handoff's explicit instruction; single-post/page
header dates keep their current readable format, since the handoff doesn't
specify one there).

## How to Demo

**Setup**: `uv run bg server --reload` against local content.

**Steps**:
1. Visit `/` in a browser: one-line header (`~/pito salas` left, nav +
   theme toggle right), two columns (posts left, links right on the panel
   background), no cards/shadows anywhere.
2. Click the theme toggle: page switches dark/light instantly; reload the
   page — no flash of the wrong theme.
3. Visit `/blog/`, a single post, `/raindrops/`, a single raindrop,
   `/pages/`, a single page, a `/tags/<tag>/` page, and a bad URL (404) —
   confirm each uses the Console shell/typography, admin actions (as an
   authenticated admin) still work and are styled as `.btn`/`.btn-ghost`.
4. Use the search box — dropdown results are legible in both themes.
5. Resize the browser under 860px — layout collapses to one column,
   post rows stack date-above-title.

**Expected output**: every acceptance-checklist item in the design handoff
holds, on every in-scope route, in both themes, at both desktop and mobile
widths — with no routes removed and no admin/editor pages touched.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code or content until the
user gives explicit approval to proceed.
