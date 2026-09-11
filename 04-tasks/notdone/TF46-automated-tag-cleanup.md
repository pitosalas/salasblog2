# TF46 Automated Tag Cleanup for Full Blog Corpus

**Date Created:** 2026-09-09

## TF46.0 — Post-selection logic

**Status**: done

**Description**: Pure function (new `src/salasblog2/tag_cleanup.py`) that
scans `content/blog/*.md` frontmatter and returns posts needing work: zero
tags, or at least one numeric tag (reuse the existing `tag.isdigit()`
convention already used elsewhere for tag badges/ranking). Supports a
`limit` parameter for batch size. No saved progress state — re-scanning
after a post is fixed naturally excludes it.

Considered generalizing selection to sweep the whole corpus regardless of
tag state (an offset-based `select_posts`), but reverted: the user's actual
ask (additive-only, "don't remove pre-existing tags") is about not losing a
post's real tags while fixing its numeric junk, not about re-visiting posts
that are already fine. `needs_tag_cleanup`/`select_posts_needing_cleanup`
already self-track correctly for that — a post drops out of the query the
moment it's fixed, no offset or progress file needed - and remain the sole
selector.

**Test**: fixture posts covering empty tags, numeric tags, mixed
numeric+real tags, already-clean tags, and the `limit` cutoff.

## TF46.1 — Tag-proposal extraction and validation

**Status**: done — revised from the original API-based design

**Description**: Originally planned as a Claude API call (`anthropic`
client, same pattern as `draft_generator.py`). Dropped after discovering
this local `ANTHROPIC_API_KEY` draws from a separate pay-as-you-go credit
balance, not the Claude Code subscription already in use — no way to bill a
standalone API key against that subscription.

Revised design: `summarize_post()` extracts title/current tags/excerpt
(no API call). Tag decisions are then made directly by Claude acting in an
assisted session (or a human), reading the summaries and proposing tags.

Two further corrections from the user during the TF46.5 trial:

1. Tags are free-form, not restricted to `BLOG_TAGS` — that vocabulary is a
   curated *suggestion* list (already established by F42/F45), not an
   enforced one. The first trial pass wrongly restricted proposals to it and
   missed obvious, useful entity/topic tags (`blogbridge`, `javaone`,
   `mars`, `tivo`). `validate_proposed_tags()` now only sanitizes real junk
   (numeric, empty, duplicates) — it doesn't gate on vocabulary membership.
2. The pipeline is additive-only. `build_proposal()` unions a post's
   existing tags with newly proposed ones before sanitizing, so nothing
   already on a post is ever removed — only numeric junk is dropped.

**Test**: `summarize_post`, `summaries_to_json`, `validate_proposed_tags`,
and `build_proposal` (including the additive-merge and no-duplicate cases)
all covered in `tests/test_tag_cleanup.py` — no external API calls anywhere
in this pipeline.

## TF46.2 — Batch runner scripts

**Status**: done

**Description**: `scripts/select_tag_candidates.py` — selects the next
batch (via TF46.0) up to a configurable size (`config.yaml`,
`tag_cleanup.batch_size`, 500) and writes title/excerpt/current-tags
summaries to a JSON file. `scripts/build_proposals.py` — takes that
candidates file plus a decisions file (tags chosen per TF46.1) and writes
the validated, reviewable proposals JSON. Neither touches content files or
calls an external API.

**Test**: the underlying logic (selection, summarization, validation, JSON
shape) is fully covered in `tests/test_tag_cleanup.py`. The scripts
themselves are thin argparse/config/path wiring around that logic —
consistent with `cli.py`, the repo's other CLI entry point, which also has
no dedicated test file — so they're not separately unit-tested.

## TF46.3 — Apply-batch script

**Status**: done

**Description**: `scripts/apply_tag_batch.py` — given a reviewed/edited
proposals JSON, writes the approved tags into each post's frontmatter only.
Verifies body content is byte-identical before/after (outside the
frontmatter block) and that the file re-parses as valid frontmatter after
the write, before moving to the next file. Raises with context (per style
guide's error-handling rule) rather than silently skipping a file that
fails verification.

**Test**: `apply_tag_proposal`/`apply_tag_batch` (the logic this script
wraps) are covered in `tests/test_tag_cleanup.py`, including a simulated
verification failure that raises instead of writing. The script itself is
thin CLI wiring, same rationale as TF46.2.

## TF46.4 — Full-feature test pass

**Status**: done

**Description**: Run the full test suite; confirm no regressions in
existing content-processing tests (`utils.py`, `generator.py`) from the new
module. Result: 579 passed, 11 skipped, 0 failed (`uv run pytest -q`,
2026-09-09) — no regressions. New `tests/test_tag_cleanup.py` (24 tests)
covers selection, summarization, tag validation, proposal building, and
apply/verify safety.

A real end-to-end smoke test (3 real posts, no mocking) also confirmed the
full pipeline works: selection → summarization → in-session tag decisions →
validation/proposal building → apply-with-verification. Reverted afterward
(`git checkout --`) since it wasn't the reviewed TF46.5 trial.

## TF46.5 — 100-post validation trial

**Status**: in progress

**Description**: Run the pipeline on a 100-post trial batch against real
content. Build a review artifact from the proposals for the user to
spot-check (not an exhaustive per-post read) that the algorithm behaves
correctly. Apply and commit the trial once confirmed. This is the one
manual checkpoint in the whole feature — every batch after this runs
autonomously (TF46.6).

Two rounds of user correction happened on this same trial batch before
sign-off:

1. First pass wrongly restricted tags to the curated `BLOG_TAGS` vocabulary
   — corrected to free-form tags mixing categories with well-known,
   emphasized entity/topic tags (`blogbridge`, `javaone`, `mars`, `tivo`,
   etc.), re-run via a fork, then a manual review pass renamed one
   ambiguous tag (`demo` → `demo2004`, since it collided with the generic
   English word).
2. Pipeline made additive-only (TF46.1: `build_proposal` unions existing
   tags with new ones before sanitizing) — re-verified as a no-op against
   this specific trial batch (its 100 posts started with only empty/numeric
   tags, so there was nothing pre-existing to preserve; `diff` confirmed
   byte-identical proposals before/after the additive-merge change). An
   offset-based whole-corpus selector was considered and reverted (see
   TF46.0) — self-tracking `select_posts_needing_cleanup` already covers
   what was actually being asked for.

Review artifact: `https://claude.ai/code/artifact/52ca483d-f560-40e2-a5ab-3a3ee82258f2`.
Applied and committed 2026-09-09 (`bc97223`) after user confirmation.

**Test**: none beyond TF46.0-TF46.3's automated coverage — this step is a
human judgment call on real output, not a new code path.

## TF46.6 — Autonomous run over the remaining corpus

**Status**: in progress

**Description**: Run the batch+apply scripts repeatedly (`config.yaml`
`tag_cleanup.batch_size`, 500 — raised from 100 partway through per user
request) over the remaining needs-cleanup posts until none remain, with no
per-batch approval pause. Selection is self-tracking
(`select_posts_needing_cleanup`) — each run naturally picks up where the
last one left off. Each batch still goes through the existing safety checks
(body-diff verification, frontmatter re-parse, full test suite), is
committed on its own, and is pushed to GitHub immediately after (per user
request) before the next batch starts.

Progress (100-post batches, before the size increase to 500): batch 1
(`bc97223`, the TF46.5 trial), batch 2 (`42c6f51`), batch 3 (`72effda`) —
300 of ~2,745 posts done as of 2026-09-09. Then 500-post batches: batch 4
(`052b57f`, 100 - size increase hadn't taken effect yet), batch 5
(`c7b20be`), batch 6 (`4405467`).

**Correction (2026-09-10)**: batches 1-6 were all run against this local
repo's `content/blog/` and pushed to GitHub - discovered mid-session that
this never reached the live site. `/data/content` (the fly.io volume) is
seeded from git only once, at first deploy; nothing pushes local/GitHub
content back into it afterward (the one exception, `pages/`, gets rsync'd
from the repo on every boot - `blog/` doesn't). So none of batches 1-6's
tags were ever live in production until this was caught.

Batch 7 (500 posts, TF46.7/TF46.8's refined curated-vocabulary pipeline)
was run correctly against the volume: `fly ssh console` to run
`select_tag_candidates.py`/`build_proposals.py`/`apply_tag_batch.py`
directly on the box against `/data/content/blog`, with candidates/decisions
shuttled up and down via `fly ssh sftp` since the actual tag-decision
judgment happens in an assisted session, not on the box. 17 non-curated
tags recurred and were queued to tag-hints.md's Proposed Tags section
(commit `af1ce6c`) - dominated by `blogbridge` (Pito's own product, this
era's biggest theme). Verified live on the volume afterward
(byte-identical body, correct tags).

**Correction**: originally reported here as "399/500 got real curated
tags, 101 had no clear fit" - wrong, that counted raw decisions (tags
proposed before curated-vocabulary filtering), not the actual applied
result. TF46.10's ground-truth check (2026-09-11) found batch 7 alone
actually landed 266/500 with real curated tags, 234 with none.

While confirming the batch, also reproduced F35 directly: `sync_to_github()`
run manually on the box fails at `git push` with "Invalid username or
token. Password authentication is not supported for Git operations." - the
production `GIT_TOKEN` is stale/invalid. This means batch 7's actual
content changes (on `/data/content/blog`) have **no GitHub backup yet** -
only the code/tag-hints.md changes (pushed from this local session) are in
git. Fixing F35 (rotate and reset the `GIT_TOKEN` secret) is now a
prerequisite for batch 7's content, and every batch after it, to reach
GitHub - not just a "nice to have."

**Test**: none beyond TF46.0-TF46.3's automated coverage - this step is
operational execution, not new logic.

## TF46.7 — Curated-vocabulary restriction and Proposed Tags queue

**Status**: done

**Description**: The user rewrote `02-doc/tag-hints.md` into a rules-first
format (Tag Cleanup rules / Curated Tags / Proposed Tags) and reversed the
TF46.1 free-form decision: the ending state is now that every tag on a post
comes from the Curated Tags list. Reworked accordingly:

1. `load_curated_tags()` parses the "Curated Tags" section of tag-hints.md
   into a flat set, stripping trailing `(clarification)` comments.
2. `split_new_tags()` divides a post's newly-proposed (not already present)
   tags into curated ones to apply and uncurated ones held back as
   `TagProposal.candidate_tags` — never written to a post directly.
3. `build_proposal()` now takes `curated_tags` and only merges the accepted
   half; existing tags are still never removed, independent of curated-list
   membership (the MANDATORY rule in tag-hints.md is absolute, doesn't yield
   to the curated-vocabulary GOAL).
4. `record_recurring_candidates()` tallies candidate tags across a batch and
   appends any that recur on more than one post to tag-hints.md's "Proposed
   Tags" section (skipping ones already listed) — satisfies the JUDGEMENT
   rule: recurring non-curated tags go to the user for approval, not applied
   silently.
5. `scripts/build_proposals.py` wires both in: loads curated tags from
   `02-doc/tag-hints.md` by default, and calls `record_recurring_candidates`
   after writing proposals.

**Test**: `TestSplitNewTags`, `TestLoadCuratedTags`, and
`TestRecordRecurringCandidates` added; `TestBuildProposal` updated for the
new signature and curated/uncurated split behavior.

## TF46.8 — One curated tag list, sourced from tag-hints.md

**Status**: done

**Description**: The user pointed out a second, separate curated list —
`BLOG_TAGS` in `utils.py` (the post-editor picklist and MarsEdit's category
picker, F42/F45) — that overlapped but didn't match tag-hints.md's new
Curated Tags section (missing the general categories like `technology`,
`personal`, `business`). Decided there should be exactly one list.

1. Merged `BLOG_TAGS`'s 17 general-category entries not already present
   into tag-hints.md's Curated Tags section, so nothing already offered in
   the UI disappears.
2. Moved the section-parsing logic to `utils.py` as
   `parse_tag_hints_section()` and `load_curated_tags()` (now returning an
   ordered `list[str]`, not a set) — the shared function `tag_cleanup.py`,
   `server.py`, and `blogger_api.py` all call against
   `02-doc/tag-hints.md`.
3. Removed the `BLOG_TAGS` constant entirely. `server.py`'s
   `generate_posts_index_cache()` and `blogger_api.py`'s
   `metaweblog_getCategories()` now call `load_curated_tags()` directly.
4. `tag_cleanup.py` keeps only pipeline-specific logic
   (`record_recurring_candidates`'s "Proposed Tags" bookkeeping); it imports
   `parse_tag_hints_section`/`load_curated_tags` from `utils.py` rather than
   duplicating them.

**Test**: `TestLoadCuratedTags`/`TestParseTagHintsSection` moved to
`tests/test_blog_tags.py` (alongside the real-file sanity checks that
replaced `TestBlogTagsConstant`); `tests/test_post_editor.py` and
`tests/test_blogger_api.py` updated to write a temp `tag-hints.md` fixture
instead of importing the removed constant.

## TF46.9 — Proposed Tags require 3+ recurrences, not 2+

**Status**: done

**Description**: The user reviewed batch 7's Proposed Tags queue and liked
it, but set a stricter bar: a candidate tag only queues once it recurs on
at least 3 posts, not 2. `record_recurring_candidates`'s threshold changed
from `n > 1` to `n >= MIN_RECURRENCE_FOR_PROPOSED_TAG` (a new module
constant, 3).

Recomputed batch 7's actual per-tag candidate counts against the real
`proposals_batch7.json` and corrected tag-hints.md's Proposed Tags section
by hand to match the new threshold: removed `google` (2), `screencasting`
(2), and `wiki` (2) - the other 14 entries (`blogbridge` at 84 down to
`orkut`/`red-sox` at 3 each) all clear the new bar.

**Test**: `TestRecordRecurringCandidates` updated - 2 recurrences no longer
queues a candidate, 3 does.

## TF46.10 — Stop re-selecting already-reviewed no-fit posts

**Status**: done

**Description**: Starting batch 9, selection began re-picking most of the
previous batch's "no fit" posts (an empty `tags: []` still counts as
"needs cleanup"), since their content hadn't changed and nothing recorded
that they'd already been reviewed. Confirmed concretely: batch 9's 500
candidates overlapped batch 8's by exactly 340 - batch 8's entire no-fit
count - leaving only 160 genuinely new posts. At that rate most of every
future batch would just re-litigate the same decisions.

Fixed with a frontmatter marker rather than a separate progress file (kept
consistent with TF46.0's "no saved progress state" design - the post's own
state is still the only source of truth):

1. `apply_tag_proposal` sets `tag_review: no_fit` on a post whose final
   tags end up empty, and clears the marker if a later call gives it real
   tags.
2. `needs_tag_cleanup` takes a new `reviewed_no_fit` argument: a post with
   empty tags no longer needs cleanup once reviewed, but numeric junk still
   always needs cleanup regardless of the marker.
3. `select_posts_needing_cleanup` reads the marker from each post's
   frontmatter to compute `reviewed_no_fit`.

Retroactively marked the posts already left no-fit by batches 7 and 8.
`proposals_batch7.json` had been wiped from the box's ephemeral `output/`
dir by the container restart that picked up the fixed `GIT_TOKEN` - used
ground truth instead: read every file in the union of batch 7's and batch
8's 500-post candidate lists (766 unique - batch 8 had already re-picked
234 of batch 7's no-fit posts) directly off `/data/content/blog`, and
marked whichever of those 766 still had empty tags (340) as `no_fit`. The
other 426 already had real curated tags from one of the two batches. No
re-deciding needed either way - a candidate's current tags fully determine
its outcome, since numeric junk is always stripped on write.

Confirmed the fix: `select_posts_needing_cleanup` dropped from 2,385 to
2,045 remaining, exactly the 340 newly-marked posts.

**Test**: `TestNeedsTagCleanup` updated for the new required argument;
`TestSelectPostsNeedingCleanup` and `TestApplyTagProposal` gained cases for
the marker being set, cleared, and respected during selection (including
that numeric junk overrides it).

## TF46.11 — Usage counts annotated on every tag-hints.md entry

**Status**: done

**Description**: At the user's request, annotated every Curated/Proposed
entry in `02-doc/tag-hints.md` with how many real posts currently carry it
(`N uses`/`N use`), computed by scanning all posts' actual frontmatter
tags on production. One-off content edit, no code change - confirmed every
then-Proposed tag showed 0 real uses (never applied, as designed). Done a
second time after batches 9-12 made the first pass stale (`technology`
82->232, `ruby` 4->124, `python` 1->80, etc.) - worth remembering these
counts need refreshing after every batch, not just once.

**Test**: none - pure content annotation, no behavior change.

## TF46.12 — Usage-count-first line format; single curated list, no queue

**Status**: done

**Description**: Two related user-directed changes to `02-doc/tag-hints.md`:

1. **Line format reversed**: every entry is now `NNNNNNN tag-name
   (comment)` - the usage count first (left-justified, 9-char field: a new
   `format_tag_hints_line()`/`TAG_HINTS_COUNT_FIELD_WIDTH` in `utils.py`),
   tag name second, optional comment last. `parse_tag_hints_section()`
   updated to strip an optional leading `\d+\s+` count before extracting
   the tag name - a line with no count prefix (e.g. one written by hand)
   still parses correctly.
2. **The Proposed Tags queue is gone.** TF46.7-TF46.9's two-tier design
   (a separate "awaiting approval" section for recurring non-curated
   tags) was reversed - there is now exactly one list. A tag recurring on
   `MIN_RECURRENCE_FOR_PROPOSED_TAG` (3+) posts in a batch is appended
   directly to the single Curated Tags list (available starting the next
   batch), not held in a separate section pending manual promotion.
   `record_recurring_candidates()` renamed to `promote_recurring_candidates()`
   to match; it now targets `utils.CURATED_TAGS_HEADER` instead of a
   removed `PROPOSED_TAGS_HEADER`. All 33 tags that had accumulated in the
   old Proposed Tags section across batches 7-12 were merged directly into
   Curated Tags in the same pass. The MANDATORY (never remove a tag) and
   GOAL (all tags come from this one list) rules are unchanged; only the
   JUDGEMENT rule's destination changed.

**Test**: `TestPromoteRecurringCandidates` (renamed from
`TestRecordRecurringCandidates`) updated - asserts a promoted tag appears
in `load_curated_tags()`'s result directly, not in a separate section.
