# F50 — Use WordPress Categories and Tags as a Tag-Cleanup Signal
**Priority**: Medium
**Date Created:** 2026-10-18
**Done:** no
**Tasks File Created:** yes
**Tests Written:** no
**Test Passing:** no
**Description**: The WordPress export (`~/Desktop/wordpress-export/pitosalas039blog.wordpress.2022-06-04.000.xml`)
records the categories and tags each post had on the old blog. The
Markdown import didn't keep many of them.

This feature maps those WordPress terms onto the curated vocabulary in
`02-doc/tag-hints.md` (each curated tag plus its parenthesized synonyms).
It then proposes the resulting curated tags for each matching post, through
the same additive, verify-then-write pipeline F46 uses.

## Findings (2026-10-18, against local `content/blog`)

* 2,491 of the 2,521 published WordPress posts match a local post, by slug
  or, failing that, by title.
* **899** matched posts would gain at least one curated tag.
* Of the 901 matched posts that have no real (non-numeric) tag today,
  **371** would gain one.
* The biggest additions:

  | Curated tag | Posts gaining it |
  |-------------|------------------|
  | `technology` | 645 |
  | `blogging` | 110 |
  | `politics` | 56 |
  | `programming` | 39 |
  | `cli` | 22 |
  | `social-media` | 18 |
  | `security` | 18 |

* Common WordPress terms that map to nothing curated: `post-format-link`,
  `links`, `howto`, `cooltool`, `explainer`, `raspi`, `opencv`, `cosi105`.
* Production's `/data/content` has drifted from local, so the real numbers
  will differ.

## Rules

* **Additive only.** No existing tag is ever removed, the same as F46.
* **Only curated tags are written.** A WordPress term counts only when it
  matches a curated tag or one of its synonyms.
* **Frequent non-curated terms are promoted.** A WordPress term that
  matches nothing curated, but appears on 4 or more published posts, is
  added to the Curated Tags list in `02-doc/tag-hints.md`.
  After that it gets applied like any other curated tag.
  Terms at or below that threshold show up in a report and are never
  applied.
* **Near-duplicates of a curated tag become synonyms, not new tags.**
  `robots` goes under `robotics` and `math` under `mathematics`, for
  example.
  Variants of each other (`tool`/`tools`) and misspellings
  (`entrepeneurship`) are merged the same way.
  Counts are summed across each merged group before the 4+ threshold is
  checked.
  The user approves the list of merges; nothing is merged automatically
  without approval.
* **Whether a generic WP category is applied is the user's call.**
  `Technology` on its own would add `technology` to 645 posts. The review
  step lets the user exclude a mapping before anything is applied.
* WordPress structural terms (`uncategorized`, `post-format-*`) are
  ignored.

## Relationship to F46

* F50 is a separate signal that feeds F46's existing apply step
  (`apply_tag_batch`).
* It doesn't change F46's selection logic.
* It can run before or after F46's remaining batches.

## How to Demo
**Setup**: the WordPress export is reachable on the production machine,
or a mapping JSON built from it has been copied there.

**Steps**:
1. Run `bg wp-tags --wxr <file> --content <dir>`. It writes a proposals
   JSON and a summary of counts per mapping.
2. The user reviews it and excludes any mappings they don't want.
3. Apply the reviewed proposals with the F46 apply script against
   `/data/content`.

**Expected output**: the matched posts carry the extra curated tags.
No tag was removed and no post body changed.

## Process Gate
After creating this feature file and the corresponding task file, **stop and present the plan to the user**. Do not write any code or content until the user gives explicit approval to proceed.
