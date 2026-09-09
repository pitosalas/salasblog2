# F45 — Tag Suggestion Picklist for Post Editor

**Priority**: Medium

**Date Created:** 2026-09-09

**Done:** no — all 4 task steps done; awaiting your live click-through in `/admin` before closing (no browser tool was available this session to verify chip click/filter interaction directly — see `04-tasks/notdone/TF45-tag-suggestion-picklist.md`'s TF45.2 notes)

**Tasks File Created:** yes

**Tests Written:** yes

**Test Passing:** yes

**Description**: The post editor's Tags field (`post_editor.html`, from F42)
only suggests from `BLOG_TAGS` — a static, hand-maintained list of 15 tags in
`utils.py` — via a single-match HTML `<datalist>`. It doesn't reflect what
tags are actually in use, and a native `<datalist>` isn't a good UI for
browsing/picking from a long list.

This feature replaces that suggestion source and widget:

* Compute the 100 most-used tags across all existing blog posts, from real
  frontmatter data rather than a hardcoded list.

* Offer those 100 tags through a picklist that's actually convenient to use
  at that size — searchable/filterable, not a plain dropdown — when creating
  or editing a post. Free-form typing of any tag (not just a suggested one)
  keeps working, matching F42's original "suggestions, not a hard vocabulary"
  design.

**Out of scope for this feature** — a separate, later activity, gated on this
one being built and approved first:

1. Once this feature is built and you've tried it, going through the first
   50 posts and adding/adjusting their tags for you to review.
2. Once you approve that batch, doing the same across all remaining posts.

Those two are content-curation passes, not code changes, and depend on this
feature existing first — they're not part of `04-tasks/TF45-*.md`'s task
list. We'll scope them as their own follow-on work once this ships.

## How to Demo

**Setup**: run locally (`make local`) against existing content.

**Steps**:
1. Open `/admin` → New Post (or edit an existing post).
2. Click into the Tags field.
3. See a picklist of the 100 most-used tags, filterable by typing.
4. Click a tag to add it to the field; click again (or an X) to remove it.
5. Type a brand-new tag not in the list — it's still accepted.

**Expected output**: tag selection driven by real usage data, comfortable to
use at 100 options, without losing the ability to type any tag freely.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code or content until the
user gives explicit approval to proceed.
