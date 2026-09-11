# F47 — Console Theme Visual Refresh

**Priority**: Medium

**Date Created:** 2026-09-11

**Done:** yes

**Tasks File Created:** yes

**Tests Written:** yes

**Test Passing:** yes

**Description**: A visual-only refresh of the public-facing site to the
"Console" theme. Design source is two screenshots the user provided
directly (dark and light home page views) — **not** the external
`/Users/pitosalas/Downloads/des-hand/` handoff folder, which the user
said to disregard.

Same information architecture, same routes, same nav — new look only:
monospace UI chrome, hairline 1px rules instead of Bootstrap
cards/shadows/badges, a compact one-line header (`~/pito salas`), a
two-column home page (recent posts left, link blog right), one amber
accent, and a light/dark toggle (button in the header, persisted via
`localStorage`).

Work happens on the dedicated branch `feature/site-redesign`, not
`main` directly, given the size of the change — merge-back is a final
task, gated on a full visual QA pass against both the light and dark
reference screenshots.

### Scope — templates getting the refresh

`base.html` (shell: head, nav, footer) plus every template that extends
it and is actually rendered by `generator.py`/`server.py`:

- `home.html` — the real homepage (`index.html`), matches
  `reference-home.html` / `02-home.png` (light) / `01-home.png` (dark).
- `blog_list.html`, `blog_post.html`
- `raindrops_list.html`, `raindrop_post.html`
- `pages_list.html`, `page.html`
- `tag_page.html`
- `404.html`

**Now also in scope** (added 2026-09-11, after the 9 templates above
were done): `admin_login.html`, `post_editor.html`, `admin.html`,
`stats_page.html`. These are standalone documents (their own
`<!DOCTYPE>`/Bootstrap CDN links, not `{% extends "base.html" %}`), and
there is still no design reference for them — the Console look
(monospace, hairline rules, one amber accent, light/dark toggle) is
extended to them by inference from the public-facing templates, not
from a screenshot. Functionality (forms, EasyMDE editor, tag picklist,
admin tabs, delete/edit flows, stats display) must not change — visual
only, same as the rest of this feature.

### Dead-template cleanup (found while scoping this feature)

- `templates/admin_new.html` — no route anywhere renders it; fully dead.
  Delete.
- `templates/includes/navigation.html`, `pagination.html`,
  `post-navigation.html` — never referenced by `{% include %}` anywhere;
  fully dead. Delete.
- `templates/overview.html` — **not dead**: `generator.py`'s
  `generate_overview_page()` (called from the main generation pipeline)
  still renders it to `output/overview.html`. It's orphaned from nav, not
  a rendering dead-end. Deleting the template would break generation
  unless `generate_overview_page()` (and the already-dead, never-called
  `generate_overview_as_home()`) are also removed from `generator.py`.
  That code-level decision is a separate call from the template refresh
  and is called out as its own task below rather than folded silently
  into "delete the dead templates."

## How to Demo

**Setup**: `make dev` (or equivalent) running locally, `feature/site-redesign`
checked out.

**Steps**:
1. Load the homepage; compare against `02-home.png` (light, default) and
   toggle to dark, compare against `01-home.png`.
2. Click through nav to Blog, a blog post, Link Blog, a raindrop post,
   Pages, a page, a tag page, and a bad URL (404) — confirm each carries
   the same header/footer/chrome and the toggle persists across
   navigation.
3. Reload the page after toggling dark mode — confirm it stays dark
   (`localStorage` persistence).

**Expected output**: All 9 public templates plus the 4 admin/editor
pages render in the Console visual style in both light and dark mode;
no Bootstrap chrome remains anywhere in the repo; all admin
functionality (login, create/edit posts and pages, delete flows, stats,
raindrop sync, tag picklist) behaves exactly as before.

## Process Gate
After creating this feature file and the corresponding task file, **stop
and present the plan to the user**. Do not write any code or content
until the user gives explicit approval to proceed.
