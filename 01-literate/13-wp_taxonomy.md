---
version: "1.0"
generated: "2026-10-19"
---

# `wp_taxonomy.py` — Recovering Old WordPress Categories as Tags

## What this module is for

When the blog moved off WordPress.com, posts kept their text but lost most
of their categories and tags. Many came across with no tags, or with
meaningless numeric category IDs like `298`. The WordPress export file
(WXR, an RSS dialect) still records each post's terms. This module turns
them back into tags, as ordinary F46 tag proposals (F50).

It's a pipeline of four small steps:

```mermaid
flowchart LR
    A[WXR export] -->|parse_wxr| B[WpPost: slug, title, terms]
    B -->|match_posts| C[local filename → WpPost]
    C -->|resolve_terms| D[curated tag names]
    D -->|build_wp_proposals| E[F46 TagProposal JSON]
    B -->|promote_terms| F[tag-hints.md: new tags + aliases]
```

On production it matched 2,453 local posts and added curated tags to
1,821 of them. Because it only adds tags, it removed none.

## Parsing the export

`parse_wxr` uses the standard library's `ElementTree` with the WordPress
namespace. It keeps only items whose `wp:post_type` is `post` and whose
`wp:status` is `publish`, so drafts, pages, attachments and menu items are
dropped. Categories and tags share one `<category nicename="...">` element
in WXR, so they're read together as a post's *terms*, de-duplicated in
order.

## Matching posts across two systems

Neither system shares an ID with the other, so matching is by *normalized
text*:

```python
def match_key(text: str) -> str:
    text = ENTITY_LEFTOVER.sub("", html.unescape(text).lower())
    return re.sub(r"[^a-z0-9]", "", text)
```

`ENTITY_LEFTOVER` removes two kinds of debris left by the original import:

- HTML entities such as `&gt;`
- bare numeric leftovers like `8220` and `8217`, where a curly quote's
  entity code ended up in the filename
  (`2004-11-29-why-improv-didn8217t-succeed.md`)

After that, only `[a-z0-9]` survives, so punctuation, spaces and accents
can't cause a mismatch.

Matching tries the filename's slug first, then the post title. Two things
complicated it:

- **Truncated slugs.** Early filenames were cut short, so the title fallback
  matters.
- **Duplicates inside WordPress.** The export holds some posts twice, once
  under a 2005 date and again under 2008, while the local import kept one
  file. Both copies match the same filename. Rather than letting the second
  overwrite the first, `match_posts` **unions their terms**, which is the
  right answer when both copies are the same post. That also explained an
  early finding of "60 misdated posts": they weren't misdated at all.

## Resolving a term to a curated tag

A WordPress term becomes a tag in two steps:

1. **Merge.** `02-doc/wp-term-merges.json` is a reviewed table mapping a
   term to a near-synonym or a corrected spelling (`robots` → `robotics`,
   `entrepeneurship` → `startups`), or to `null` to ignore noise like
   `links` and `free`.
2. **Alias.** The result goes through the curated alias map, so a declared
   alias lands on its primary.

```python
target = merges.get(term, term)
if target is None:
    continue
resolved.append(alias_map.get(target, target))
```

Structural terms are dropped first: `uncategorized`, `post-format-*` and
numeric IDs (`STRUCTURAL_TERM`).

## Promotion: growing the curated list from the data

`promote_terms` has the vocabulary side effect. It reuses F46's
`promote_recurring_candidates` unchanged:

- Every published WordPress post becomes a placeholder `TagProposal`
  whose `candidate_tags` are its resolved terms that aren't curated yet.
- Any candidate on **4 or more** posts is appended to the curated list.

Reusing that function means F46 and F50 can't disagree about what
"recurring" means. Afterwards, every merge whose target is now curated is
recorded as an alias of that target in `tag-hints.md`
(`utils.add_curated_aliases`). The merge decisions then live on in the
vocabulary, not just in a JSON file. This run added 41 tags and about 200
aliases.

## Proposals: additive, through F46's safety net

`build_wp_proposals` makes, for each matched post, its current tags plus
its resolved curated tags. It goes through `tag_cleanup.build_proposal`, so
the F46 rules hold automatically:

- Existing tags are never removed.
- Only curated tags are added.

Posts that would gain nothing are left out. The output is the same JSON
`scripts/apply_tag_batch.py` already applies, which keeps the frontmatter
write and its body check in one place.

## Observations for future improvement

- **F55 supersedes most of this.** With a closed 16-tag list, promotion
  (`promote_terms`, `--promote`) is being removed. What remains useful is
  `parse_wxr` and `match_posts`.
- **`match_posts` mutates the first match's term list** when merging a
  duplicate. It copies the `WpPost` on first sight, so the caller's objects
  are safe, but returning fresh merged records would make that clearer.
- **Matching is exact on the normalized key.** A post whose title was
  edited after import won't match. The 4 unmatched WordPress posts were
  left as they are; a fuzzy fallback such as date plus title similarity
  would recover some, at the cost of possible false matches.
