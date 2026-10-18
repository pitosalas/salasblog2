# I04 Tag apply converts CRLF posts to LF

## Symptom

* `tag_cleanup.apply_tag_proposal` rewrites the whole file through
  `frontmatter.dumps`, which writes LF line endings.
* A post saved with CRLF endings comes back all LF, even when only its
  tags changed.
* Seen once, during the F50 run (sync commit `74a3596b`):
  `2026-02-28-rules-of-thumb-for-software-engineers.md` showed a
  191-line diff for a single added tag.

## What has been done

* That one file was restored on production on 2026-10-18. It now has its
  original endings plus the added tag line.
* F51's `remove_frontmatter_key` hit the same problem through
  `read_text`/`write_text` and was fixed to preserve each line's own
  ending, with a regression test.
* `apply_tag_proposal` itself is not fixed yet.
  Its body check compares parsed content, which ignores line endings, so
  it doesn't catch this.

## Theory

* Any F46 batch that touches a CRLF post will flatten its endings.
* The rendered page doesn't change, so the harm is only noisy diffs and
  the broken "only tags change" guarantee.
* A fix would write tags with a line-level edit that preserves endings,
  instead of re-serializing the frontmatter.
