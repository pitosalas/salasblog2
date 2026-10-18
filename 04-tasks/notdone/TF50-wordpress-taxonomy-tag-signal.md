# TF50 WordPress Taxonomy as Tag Signal for Feature F50
**Date Created:** 2026-10-18

## TF50.0 — WXR parsing

**Status**: not done

**Description**: Pure function in a new `src/salasblog2/wp_taxonomy.py`.

* It parses the WordPress export file into one record per published post:
  slug, title, date, and term nicenames from both categories and tags.
* It uses stdlib `xml.etree.ElementTree` with the WordPress namespaces.

**Test**: a small fixture WXR with a post, a draft, a page and an
attachment. Only the published post comes back, with the right terms.

## TF50.1 — Matching WordPress posts to local posts

**Status**: not done

**Description**: Match each record to a content file.

* Match by normalized slug first, then by normalized title.
* HTML entities, the `8220`-style numeric-entity leftovers and
  non-alphanumerics are stripped before comparing.
* Unmatched records are returned, not dropped.

**Test**: fixtures for an exact slug, a slug with entity leftovers, a
title-only match, a non-ASCII title (`Curaçao`) and no match.

## TF50.2 — Term-to-curated-tag mapping

**Status**: not done

**Description**: Build the term-to-tag map from `02-doc/tag-hints.md`.

* Each curated tag maps to itself, and each of its synonyms maps to it.
* The existing tag-hints parser is reused, not duplicated.
* `uncategorized` and `post-format-*` are ignored.
* Unmapped terms are counted for the report.
* An exclusion list in `config.yaml` (`wp_tags.exclude_mappings`) lets the
  user switch off a mapping, such as `technology`.

**Test**: a synonym maps to its parent, a structural term is ignored, an
excluded mapping is skipped, and an unmapped term is counted.

## TF50.2a — Promote frequent non-curated terms

**Status**: not done

**Description**: Count unmapped terms across the published posts. Any term
on **4 or more** posts becomes a promotion candidate.

* This reuses F46's `promote_recurring_candidates` in `tag_cleanup.py`
  rather than duplicating it.
  That function's threshold becomes a parameter, so F50 can pass 4.
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

**Test**: the threshold boundary (3 posts isn't promoted, 4 is), and a
term counts once per post. The `tag-hints.md` writer is checked for new
curated lines and for adding a synonym to an existing parent, and the file
must re-parse afterwards.

## TF50.3 — Proposals and CLI `bg wp-tags`

**Status**: not done

**Description**: Turn each matched post's mapped tags into an F46 proposal
via `build_proposal`, which keeps the merge additive.

* Write a proposals JSON that `scripts/apply_tag_batch.py` accepts as-is.
* Print a summary: posts matched, posts gaining tags, counts per added tag,
  and the top unmapped terms.

**Test**: the proposal JSON round-trips through the F46 apply logic on
fixture posts. Existing tags are kept and bodies are byte-identical.

## TF50.4 — Tests

**Status**: not done

**Description**: Dedicated `tests/test_wp_taxonomy.py` covering TF50.0-TF50.3,
then a full-suite run.

## TF50.5 — Review and production run

**Status**: not done

**Description**:

* Generate the proposals against production's `/data/content` via
  `fly ssh`.
* Build a review summary so the user can decide on generic mappings like
  `technology`.
* Apply the reviewed proposals.
* Regenerate the site, run `sync_to_github()` and pull locally.

**Test**: manual. Record the command, the counts, the mappings excluded
and a spot-check of five posts.
