# F54 — Blog Index Sidebar: Tags and Year Archive
**Priority**: Medium
**Date Created:** 2026-10-19
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: Add a right-hand column to the blog listing pages that looks
just like the home page's right column (the shaded "Link Blog" column). It
indexes the blog two ways.

1. **Tags.** Every blog tag with its post count, each linking to its
   `/tags/<tag>/` page.
2. **Archive by year.** Each year with its post count, each linking to a
   new `/blog/<year>/` page listing that year's posts.

## Why these two indexes

* The blog has **2,823 posts across 20 years** (2004–2026), shown 20 to a
  page, about 141 pages.
* Today the only ways in are paging back through the list or searching.
* **Tags** answer "what has he written about X?". After F46 and F50 there are
  **82 distinct blog tags**, all curated, which fit comfortably in a
  column. The biggest are `personal` 922, `technology` 899, `politics` 225,
  `business` 216 and `ruby` 209.
* **Years** answer "what was he writing about in 2005?". Posts are already
  grouped by month on the listing pages, so a year archive is a natural
  next level.

## Other indexes considered, not included

These are listed for a future feature, not built here:

* **Most-read posts**, from the visit stats. It would need the stats data
  at generation time, plus a policy for bots versus humans.
* **Series or related posts**, such as the Improv posts. There's no series
  metadata today.
* **A search box in the column.** Search already lives in the site header.

## Behavior

* **Where the column appears:**
  * every blog listing page (`/blog/index.html` and `/blog/page-N.html`)
  * every new year page
  * every tag page

  This keeps navigation the same wherever you land.
* **Looks like the home page's right column:** the same shaded background,
  the left hairline border and the section headings. On narrow screens it
  stacks below the main column, as the home page does.
* **The grid styling is shared.** The home page and the blog pages use one
  two-column layout stylesheet rather than copies of it.
* **The tag list:**
  * blog posts only, so raindrop tags from Raindrop.io aren't listed
  * numeric leftover tags excluded
  * sorted by count, highest first
  * counts use exactly the same posts as the blog listing
* **Year pages:** `/blog/<year>/index.html`, holding that year's posts newest
  first, grouped by month, in the same format as the blog listing. They are
  not paginated, since the busiest year (2022) has 338 posts.
* **Tag pages now separate the two content types.** Today a tag page mixes
  blog posts and raindrops. They become two sections, "Posts" first, then
  "Links", so clicking a tag from the blog column leads with blog posts.
* **Incremental edits** (saving a post in the editor) also regenerate:
  * the tag pages for that post's tags, which fixes a gap where a brand-new
    tag had no page until the next full regeneration
  * that post's year page

  The column on *other* listing pages refreshes at the next full
  regeneration. **Accepted trade-off:** a count may be off by one until
  then, rather than rewriting all ~141 listing pages on every save.

## Out of scope

* `draft-*.md` files in `content/blog/` without a `draft:` frontmatter flag
  are rendered and listed like normal posts today. That's a separate issue.
  They'll be counted the same way the listing counts them.

## How to Demo
**Setup**: deployed to production and fully regenerated.

**Steps**:
1. Open `https://salas.com/blog/`. A shaded right column shows "Tags" with
   counts and "Archive" with years and counts.
2. Click `robotics`. The tag page lists blog posts under "Posts", then any
   raindrops under "Links", with the same right column.
3. Click `2005` in the archive. `/blog/2005/` lists 2005's posts by month.
4. Narrow the window to phone width. The column moves below the posts.
5. Edit a post in the web editor and add a new tag. That tag's page exists
   right after saving.

**Expected output**: the blog can be browsed by topic and by year from any
blog listing page.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
