# F46 — Automated Tag Cleanup for Full Blog Corpus

**Priority**: Medium

**Date Created:** 2026-09-09

**Done:** no

**Tasks File Created:** yes

**Tests Written:** no

**Test Passing:** no

**Description**: A full-corpus scan (2026-09-09) found the tag cleanup started
under F45 covers a small fraction of the blog:

* 2,819 total posts.
* 2,745 with either zero tags, or at least one leftover numeric
  WordPress-import tag (e.g. `1105`, `1662`).
* Only 74 posts currently have clean, real tags.

Reviewing that many posts by hand (reading each one in chat, one at a time,
the way the two prior 100-post batches were done) doesn't scale. This
feature builds a scripted pipeline instead. Final design, after two
corrections from the user during the TF46.5 trial:

1. **Selection stays self-tracking** — a post "needs work" if it has zero
   tags or any numeric leftover, computed fresh each run by scanning
   frontmatter. A whole-corpus, offset-based sweep (touching already-clean
   posts too) was considered and reverted — the user's actual ask was that
   fixing a post's junk tags must never cost it a real tag it already had,
   not that already-fine posts need revisiting. Self-tracking selection
   already shrinks correctly as posts get fixed, with no progress file.

2. **Additive-only** — a post's existing tags are never removed, only added
   to. `build_proposal` unions a post's current tags with newly proposed
   ones before sanitizing. The one exception is numeric junk, which is
   dropped regardless of whether it was already on the post — that's the
   actual cleanup this feature exists to do.

3. **Tag hints, user-editable** — `02-doc/tag-hints.md` holds recurring
   entities/people/projects/naming conventions/exclusions the user wants
   respected. Read before deciding tags for every batch; the user edits it
   directly, no code change needed to update guidance.

4. **Tag proposal, free-form** — originally planned as a scripted call to
   the Claude API (`anthropic` client, same pattern as `draft_generator.py`),
   dropped after discovering the local `ANTHROPIC_API_KEY` draws from a
   separate pay-as-you-go credit balance, not the Claude Code subscription
   already in use. Instead: a script extracts each post's title/excerpt/
   current tags (no API call), and Claude — acting directly in an assisted
   session — reads those summaries and proposes tags. Tags are free-form
   (F42/F45 already established this — `BLOG_TAGS` is a curated suggestion
   list, not an enforced vocabulary), mixing general categories with
   specific, well-known entities/topics genuinely emphasized in the post
   (e.g. `blogbridge`, `javaone`, `mars`, `tivo`) — not just incidental
   mentions. `validate_proposed_tags` sanitizes in code (numeric junk, empty
   strings, duplicates), not just by instruction.

5. **One validation trial, then autonomous** — not a manual review of every
   batch. A 100-post trial's proposals go to a review artifact so the user
   can spot-check that the algorithm is working correctly — not read every
   post's proposal one by one. Two rounds of correction happened here before
   the design above was right (vocabulary was too restrictive; tags weren't
   additive) — both fed back into the code and re-validated on the same
   trial batch before scaling up.

6. **Apply** — writes the merged tag list into each post's frontmatter only.
   Body content is verified byte-identical before/after (except the
   frontmatter block itself), same rigor as the two prior manual batches.
   Normal test suite runs, then a commit.

7. **Once the trial is validated**, the remaining corpus runs automatically
   in batches (`config.yaml` `tag_cleanup.batch_size`, 500) with no
   per-batch approval gate, pushed to GitHub after each — each batch
   still verified (body-diff safety net, frontmatter re-parse, test suite)
   and committed on its own, but without pausing for review each time.

**Out of scope**:

* Auto-expanding `BLOG_TAGS` with new category suggestions — entity/topic
  tags are just applied directly now (free-form), but a genuinely new
  *general category* (like the `curacao`/`boston`/etc. tags added by hand
  last session) is still the user's call, not this pipeline's.
* The unrelated sync gap where 3 production-only posts never reached
  GitHub — already known, not yet filed as an issue, not this feature's job.
* Re-diagnosing why the prior session's "100 most recent" batch didn't
  survive on disk — noted above, not investigated further here. That
  batch's posts get a pass again naturally once the full-corpus sweep
  reaches them.

## How to Demo

**Setup**: run locally against real content. No API key needed — tag
proposals come from Claude acting directly in an assisted session.

**Steps**:
1. Run the batch script on a 100-post trial against real content.
2. Confirm proposals mix general categories with specific entity/topic tags
   that are genuinely emphasized in each post, not incidental mentions.
3. Confirm a post's existing real tags are always preserved in the proposal,
   with only numeric junk dropped and good new tags added.
4. Spot-check the trial's proposals (via the review artifact) to confirm the
   algorithm is working correctly — not an exhaustive per-post read.
5. Run the apply step; confirm frontmatter updated, body byte-identical,
   full test suite still green.
6. Once validated, let the remaining corpus run automatically in batches,
   each one verified and committed without a manual approval pause.

**Expected output**: one validated trial, then an autonomous batch process
that brings every post's tags into good shape — no numeric junk, real
existing tags kept, good new category/entity tags added — without requiring
every post, or every batch, to be reviewed by hand.

## Process Gate
After creating this feature file and the corresponding task file, **stop and
present the plan to the user**. Do not write any code or content until the
user gives explicit approval to proceed.
