---
version: "1.1"
generated: "2026-10-20"
---

# `wp_taxonomy.py` — Recovering Old WordPress Categories as Tags

## What this module is for

When the blog moved off WordPress.com, posts kept their text but lost most
of their categories and tags. Many came across with no tags, or with
meaningless numeric category IDs like `298`. The WordPress export file
(WXR, an RSS dialect) still records each post's terms. This module turns
them back into tags, as ordinary F46 tag proposals (F50).

It's a pipeline of three small steps:

```mermaid
flowchart LR
    A[WXR export] -->|parse_wxr| B[WpPost: slug, title, terms]
    B -->|match_posts| C[local filename → WpPost]
    C -->|resolve_terms| D[curated tag names]
    D -->|build_wp_proposals| E[F46 TagProposal JSON]
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
2. **Canonicalize.** The merged names go through
   `tag_vocabulary.canonicalize_tags`, the same function every other tag
   writer uses. An alias lands on its primary, and since F55 anything the
   closed list doesn't know is dropped rather than passed through.

```python
merged = [
    merges.get(term, term) for term in terms if not STRUCTURAL_TERM.match(term)
]
targets = [target for target in merged if target is not None]
return canonicalize_tags(targets, alias_map).kept
```

Structural terms are dropped first: `uncategorized`, `post-format-*` and
numeric IDs (`STRUCTURAL_TERM`).

## Promotion (removed in F55)

The F50 run also grew the curated list from the data: terms recurring on 4
or more posts became curated tags, and merges were recorded as aliases.
That run added 41 tags and about 200 aliases. **F55 closed the list and
removed `promote_terms` and `--promote`**, so this module no longer writes
`tag-hints.md`.

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

- **The module is now mostly historical.** With F50 applied and promotion
  gone, what remains reusable is `parse_wxr` and `match_posts`. If no
  further WordPress work is planned, the proposal path could be retired.
- **`match_posts` mutates the first match's term list** when merging a
  duplicate. It copies the `WpPost` on first sight, so the caller's objects
  are safe, but returning fresh merged records would make that clearer.
- **Matching is exact on the normalized key.** A post whose title was
  edited after import won't match. The 4 unmatched WordPress posts were
  left as they are; a fuzzy fallback such as date plus title similarity
  would recover some, at the cost of possible false matches.
