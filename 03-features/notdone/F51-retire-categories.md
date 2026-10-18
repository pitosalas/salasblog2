# F51 — Retire Post Categories
**Priority**: Low
**Date Created:** 2026-10-18
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Remove the `category` field from the blog. Tags take over
everything it was for.

## Why

* 2,813 posts have a `category:` value, but almost all of them are raw
  WordPress category IDs such as `298` or `538`. Only 9 posts have a real
  name ("General").
* Those numbers aren't the IDs used in the WordPress export. Only about 40
  of the 174 distinct values can be decoded, and only indirectly.
* What they encoded is already in tags. F50 applied every post's original
  WordPress categories as curated tags, so Life became `personal`,
  Technology became `technology`, Blogs became `blogging`, and so on.
* Nothing on the site uses the field:
  * the post editor saves it and nothing reads it back
  * `overview.html` displays it, but that page is orphaned
  * `search.js` matches against it, but no page loads that file
* **The user decided on 2026-10-18 to retire categories rather than keep
  them as a top-level section.**

## Scope

* **In:** remove the Category input from the post editor.
* **In:** remove the server code that loads and saves `category`.
* **In:** remove the category display from `overview.html`.
* **In:** delete `static/js/search.js`. No page loads it, and its category
  match is the last reader of the field.
* **In:** strip the `category:` line from post and page frontmatter on
  production.
  Only that line is removed, and every other byte stays identical.
* **Out:** MarsEdit's `metaWeblog.getCategories`. It already returns the
  curated *tags*, which is what MarsEdit's category picker should show.

## How to Demo
**Setup**: deployed, and the frontmatter strip has been run on production.

**Steps**:
1. Open the post editor for a new post and for an existing post.
   There's no Category field.
2. Save an edit to an existing post, then check its file on production.
   There's no `category:` line.
3. Run `grep -l '^category:' /data/content/blog/*.md /data/content/pages/*.md`.
   It finds nothing.

**Expected output**: categories no longer appear anywhere. Tags, titles,
dates and bodies are unchanged.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
