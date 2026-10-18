# TF50 WordPress Taxonomy as Tag Signal for Feature F50
**Date Created:** 2026-10-18

## TF50.0 — WXR parsing

**Status**: done

**Description**: Pure function in a new `src/salasblog2/wp_taxonomy.py`.

* It parses the WordPress export file into one record per published post:
  slug, title, date, and term nicenames from both categories and tags.
* It uses stdlib `xml.etree.ElementTree` with the WordPress namespaces.

**Test**: a small fixture WXR with a post, a draft, a page and an
attachment. Only the published post comes back, with the right terms.

## TF50.1 — Matching WordPress posts to local posts

**Status**: done

**Description**: Match each record to a content file.

* Match by normalized slug first, then by normalized title.
* HTML entities, the `8220`-style numeric-entity leftovers and
  non-alphanumerics are stripped before comparing.
* Unmatched records are returned, not dropped.

**Test**: fixtures for an exact slug, a slug with entity leftovers, a
title-only match, a non-ASCII title (`Curaçao`) and no match.

## TF50.2 — Term-to-curated-tag mapping

**Status**: done

**Description**: Build the term-to-tag map from `02-doc/tag-hints.md`.

* Each curated tag maps to itself, and each of its synonyms maps to it.
* The existing tag-hints parser is reused, not duplicated.
* `uncategorized` and `post-format-*` are ignored.
* Unmapped terms are counted for the report.
* Merge and ignore decisions live in `02-doc/wp-term-merges.json`, a
  reviewed data file. Each entry maps a term to a target tag, or to `null`
  to ignore that term. It replaces the planned `config.yaml` exclusion list.
  With the user's blanket approval (2026-10-18), `technology` was kept.

**Test**: a synonym maps to its parent, a structural term is ignored, an
excluded mapping is skipped, and an unmapped term is counted.

## TF50.2a — Promote frequent non-curated terms

**Status**: done

**Description**: Count unmapped terms across the published posts. Any term
on **4 or more** posts becomes a promotion candidate.

* This reuses F46's `promote_recurring_candidates` in `tag_cleanup.py`
  rather than duplicating it.
  No threshold parameter was needed, because TF46.14 already set F46's
  constant to 4.
* Near-synonyms are merged before promotion.
  That covers variants of a curated tag (`robots` → `robotics`), variants
  of each other (`tool`/`tools`, `scale`/`scaling`/`scalability`), and
  misspellings (`entrepeneurship`).
  Each group's post counts are summed before the threshold is checked.

* Candidates go into a review file in two groups:
  * new curated tags
  * synonyms of an existing curated tag, with the parent proposed by the
    session and approved by the user
* The approved result is written into `02-doc/tag-hints.md`. Each new tag
  is a curated line with its usage count. Each synonym is added inside its
  parent's parentheses.
* The term-to-tag map is then rebuilt, so the promoted terms get applied
  in TF50.3.
* Duplicate WordPress posts (the same post republished under a later date)
  that match one local file have their terms unioned.

**Test**: the threshold boundary (3 posts isn't promoted, 4 is), and a
term counts once per post. The `tag-hints.md` writer is checked for new
curated lines and for adding a synonym to an existing parent, and the file
must re-parse afterwards.

## TF50.3 — Proposals and CLI `bg wp-tags`

**Status**: done

**Description**: Turn each matched post's mapped tags into an F46 proposal
via `build_proposal`, which keeps the merge additive.

* Write a proposals JSON that `scripts/apply_tag_batch.py` accepts as-is.
* Print a summary: posts matched, posts gaining tags, counts per added tag,
  and the top unmapped terms.

**Test**: the proposal JSON round-trips through the F46 apply logic on
fixture posts. Existing tags are kept and bodies are byte-identical.

## TF50.4 — Tests

**Status**: done

**Description**: Dedicated `tests/test_wp_taxonomy.py` covering TF50.0-TF50.3,
then a full-suite run.

## TF50.5 — Review and production run

**Status**: done

**Description**:

* Generate the proposals against production's `/data/content` via
  `fly ssh`.
* Build a review summary so the user can decide on generic mappings like
  `technology`.
* Apply the reviewed proposals.
* Regenerate the site, run `sync_to_github()` and pull locally.

**Test**: manual. Record the command, the counts, the mappings excluded
and a spot-check of five posts.

**Result (2026-10-18)**:

* The review was waived: the user gave blanket approval to every open
  question.
  * Merges were judged in-session and recorded in
    `02-doc/wp-term-merges.json`.
  * `technology` was kept.
  * Noise terms were ignored: `links`, `list`, `time`, `usa`,
    `background`, `free`, `interesting`, `article`, `description`.
* Locally, `bg wp-tags --wxr <export> --promote` added **41 curated tags**
  and added aliases to 46 existing ones. This was committed in `1ce25b5f`.
* The production `/app` checkout was refreshed with `git fetch` and
  `checkout`, and the export was uploaded to `/tmp/wp-export.xml`.
* On production, `bg wp-tags --content /data/content` matched 2,453 local
  posts. 4 WordPress posts didn't match.
  * **1,821 posts gain tags.** The biggest gains were `personal` 890,
    `technology` 668, `blogging` 183, `howto` 129 and `politics` 54.
  * No proposal dropped an existing tag.
* `scripts/apply_tag_batch.py /tmp/wp-proposals.json` applied tags to
  1,821 posts. Then `bg generate` ran and `sync_to_github()` returned True.
* Sync commit `74a3596b` touched 1,821 files, all in `content/blog/`.
  A per-file check against the parent commit found:
  * 0 body changes
  * 0 frontmatter changes other than `tags`/`tag_review`
  * 0 real tags lost
* Spot check: `/tags/howto/` returns 200, and
  `/blog/2011-02-23-engineering.html` lists `personal`,
  `software-engineering` and `technology`.
