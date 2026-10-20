# F55 — Closed Curated Tag List (16 Tags)
**Priority**: High
**Date Created:** 2026-10-19
**Done:** no
**Tasks File Created:** yes
**Tests Written:** yes
**Test Passing:** yes
**Description**: Make the curated list **closed and short**. Only its 16
tags may appear on, or be added to, any blog post or raindrop. Every other
known tag becomes an alias that converts to one of the 16. Anything else is
dropped.

**Decided by the user on 2026-10-19:**

* about 10–15 broad tags, landing at 16
* `technology` split into `internet` and `computing`
* `personal` split into `life` and `places`
* `eroom`, `microsoft`, `lotus` and `amazon` go under `business`
* raindrops left with no tags stay untagged
* original raindrop tags are **not** kept
* automatic promotion of new tags ends

## The 16 tags

The full alias list (429 aliases) is in `02-doc/tag-hints-proposed.md`,
which replaces `02-doc/tag-hints.md`.

| Tag | Absorbs (examples) |
|---|---|
| programming | ruby, python, cli, web, api, database, open-source |
| business | startups, careers, crypto, microsoft (excel, windows), amazon, lotus (improv), eroom |
| computing | apple, mobile, linux, raspberry-pi, 3d-printing, tools, maps, hardware, software |
| internet | google, gmail, security, spam, email, online |
| politics | legal, trustthevote |
| blogging | blogbridge, rss (opml), podcasting, social-media, wikipedia |
| culture | books, music, movies, tv, video, games, art, history, philosophy, nyt |
| howto | explainer, tips, tutorial |
| science | mathematics, computer-science |
| education | brandeis, harvard, olin-college, research |
| robotics | computer-vision, ros, lidar |
| software-engineering | architecture, scalability, performance, concurrency, cloud |
| places | travel, boston, curacao |
| design | data-visualization, photography |
| life | food, health, humor, jewish, woodworking |
| ai | llm, chatgpt, openai, claude, machine-learning |

Placement defaults the user can still change: `nyt` under culture, `howto`
kept as a tag, `windows` under business.

## Where the rule is enforced

1. **Post editor.** The tag field only offers the 16 tags. On save the
   server converts an alias to its tag and **rejects** any other tag with a
   clear error, rather than silently dropping it.
2. **Raindrop sync.** Each raindrop's tags from Raindrop.io are converted
   through the aliases when its file is written. Unknown tags are dropped,
   and a raindrop with none left stays untagged.
3. **Site generation.** Only curated tags are shown or get tag pages. Any
   other tag found in a file is skipped and reported in the generation log.
   This guards against a hand-edited or git-restored file.
4. **No automatic promotion.** F46's 4+ recurrence promotion and F50's
   `wp-tags --promote` are removed. Only the user adds curated tags, by
   editing `tag-hints.md`.

## One-time conversion of existing content (production `/data/content`)

**Raindrops (1,547): convert in place.** Every raindrop file's tags are
rewritten through the aliases. **No `--reset` rebuild:** nothing filters
which bookmarks are downloaded, so a reset would pull all 2,608 bookmarks
from Raindrop.io. That's about 1,060 more than the site has, including any
removed from the site with the admin delete button.

Measured impact: of 1,238 tagged raindrops, 655 keep all their tags, 481
lose some, and 102 end up untagged. That's 2,476 tags kept and 817
dropped, mostly noise like `data`, `library` and `free`.

**Blog posts (2,834) take three steps:**

* **Mechanical.** Convert aliases. Remove the generic `personal` tag from
  the **471** posts that already have a real topic.
* **Judgment pass A.** **753** posts tagged only with the generic
  `technology` get `internet` or `computing`, or their real topic, decided
  from title and excerpt.
* **Judgment pass B.** **350** posts tagged only `personal` get `life` or
  `places`, or their real topic.
* Both passes start with a sample batch the user reviews before the rest is
  applied, as F46 did. Posts that end up with no fit stay untagged.

## Out of scope

* Re-reading posts that are already specifically tagged, to change their
  topic. Only the generic `technology` and `personal` tags get judgment.
* F54 (blog sidebar), which is unaffected and still parked.

## How to Demo
**Setup**: deployed, conversions applied on production, site regenerated.

**Steps**:
1. Open the post editor. The tag field offers exactly the 16 tags.
2. Try saving a post with the tag `iphone`. It's saved as `computing`.
   Try `banana`. The save is refused with an error naming the tag.
3. Check that `/tags/` pages exist only for the 16 tags, so `/tags/ruby/`
   is gone and `/tags/programming/` lists the Ruby posts.
4. Run a raindrop sync with a bookmark tagged `chatgpt` on Raindrop.io. Its
   page shows `#ai`.
5. A tally of tags across all content shows only the 16 tags.

**Expected output**: the site uses one 16-tag vocabulary everywhere, and
nothing else can be added.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
