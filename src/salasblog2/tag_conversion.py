#!/usr/bin/env python3
# tag_conversion — One-time in-place conversion of existing content onto the curated tags
# Author: Pito Salas and Claude Code
# Version: 2
# Created: 2026-10-20
# Updated: 2026-10-20
# Open Source Under MIT license
"""
Rewrites the `tags` of existing raindrop and blog files onto the closed
curated list (F55), in place.

Only the `tags:` entry of the frontmatter changes. `replace_frontmatter_tags`
swaps exactly those lines (the key plus any `- item` lines under it) and
keeps every other byte, including each line's own ending, so CRLF files
survive. The conversion also records the tags the file had before in an
`original_tags:` entry right after `tags:`, so the finer old topics stay
with the post. Each rewrite is checked by re-parsing: the other frontmatter
keys and the body must be unchanged and both tag lists must be as intended.

Raindrops go straight through `canonicalize_tags`. Blog posts do too, except
for the generic `technology` and `personal` tags: on a post with no other
curated tag they are kept as markers for the judgment pass (TF55.7); on a
post that has a real topic they are dropped.

Nothing here talks to Raindrop.io; existing files are the only input.
"""

from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

from salasblog2.tag_vocabulary import CanonicalTags, canonicalize_tags

GENERIC_BLOG_TAGS = ("technology", "personal")
ORIGINAL_TAGS_KEY = "original_tags"

TagConverter = Callable[[list[str], dict[str, str]], CanonicalTags]


@dataclass
class ConversionReport:
    files_changed: int = 0
    tags_kept: int = 0
    now_untagged: int = 0
    dropped: Counter = field(default_factory=Counter)


def convert_blog_tags(tags: list[str], alias_map: dict[str, str]) -> CanonicalTags:
    """Canonicalize a blog post's tags, keeping a generic tag only when the
    post would otherwise have no curated tag."""
    canonical = canonicalize_tags(tags, alias_map)
    if canonical.kept:
        return canonical
    generics = [tag for tag in canonical.dropped if tag in GENERIC_BLOG_TAGS]
    dropped = [tag for tag in canonical.dropped if tag not in GENERIC_BLOG_TAGS]
    return CanonicalTags(kept=list(dict.fromkeys(generics)), dropped=dropped)


def render_list(key: str, values: list[str], eol: str) -> str:
    if not values:
        return f"{key}: []{eol}"
    return f"{key}:{eol}" + "".join(f"- {value}{eol}" for value in values)


def replace_frontmatter_tags(
    text: str, tags: list[str], original_tags: list[str] | None = None
) -> str:
    """Return `text` with its frontmatter `tags:` entry replaced by `tags`,
    followed by an `original_tags:` entry when `original_tags` is given.

    The entry is the `tags:` line plus the indented or `- ` lines under it.
    The new lines use the old line's ending. Raises if the file has no
    frontmatter or no `tags:` key, rather than inventing one.
    """
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\r\n") != "---":
        raise ValueError("no frontmatter")
    for start in range(1, len(lines)):
        line = lines[start]
        if line.rstrip("\r\n") == "---":
            break
        if not line.startswith("tags:"):
            continue
        end = start + 1
        while end < len(lines) and is_continuation(lines[end]):
            end += 1
        eol = line[len(line.rstrip("\r\n")) :] or "\n"
        entry = render_list("tags", tags, eol)
        if original_tags is not None:
            entry += render_list(ORIGINAL_TAGS_KEY, original_tags, eol)
        return "".join(lines[:start]) + entry + "".join(lines[end:])
    raise ValueError("frontmatter has no tags: key")


def is_continuation(line: str) -> bool:
    if line.rstrip("\r\n") == "---":
        return False
    return line.startswith((" ", "\t", "-"))


def read_tags(post: frontmatter.Post) -> list[str]:
    raw = post.metadata.get("tags") or []
    if not isinstance(raw, list):
        raise ValueError(f"tags is not a list: {raw!r}")
    return [str(tag) for tag in raw]


def verify_rewrite(
    original: str,
    rewritten: str,
    tags: list[str],
    original_tags: list[str] | None = None,
) -> None:
    before = frontmatter.loads(original)
    after = frontmatter.loads(rewritten)
    if after.content != before.content:
        raise ValueError("body changed")
    if read_tags(after) != tags:
        raise ValueError(f"tags did not persist: {after.metadata.get('tags')!r}")
    rewritten_keys = {"tags"}
    if original_tags is not None:
        rewritten_keys.add(ORIGINAL_TAGS_KEY)
        if after.metadata.get(ORIGINAL_TAGS_KEY) != original_tags:
            raise ValueError("original_tags did not persist")
    others_before = {
        k: v for k, v in before.metadata.items() if k not in rewritten_keys
    }
    others_after = {k: v for k, v in after.metadata.items() if k not in rewritten_keys}
    if others_after != others_before:
        raise ValueError("other frontmatter changed")


def convert_directory(
    content_dir: Path,
    convert: TagConverter,
    alias_map: dict[str, str],
    is_apply: bool,
) -> ConversionReport:
    """Convert every `*.md` file's tags in `content_dir`, recording the old
    ones as `original_tags`. Writes only when `is_apply`; a dry run reports
    the same counts and writes nothing. A changing file that already has
    `original_tags` is refused rather than overwritten."""
    report = ConversionReport()
    for path in sorted(content_dir.glob("*.md")):
        text = path.read_bytes().decode("utf-8")
        try:
            post = frontmatter.loads(text)
            tags = read_tags(post)
            result = convert(tags, alias_map)
            report.tags_kept += len(result.kept)
            if result.kept == tags:
                continue
            report.dropped.update(result.dropped)
            report.files_changed += 1
            report.now_untagged += not result.kept
            if ORIGINAL_TAGS_KEY in post.metadata:
                raise ValueError(f"already has {ORIGINAL_TAGS_KEY}")
            new_text = replace_frontmatter_tags(text, result.kept, tags)
            verify_rewrite(text, new_text, result.kept, tags)
        except ValueError as e:
            raise ValueError(f"{path.name}: {e}") from e
        if is_apply:
            path.write_bytes(new_text.encode("utf-8"))
    return report


def select_generic_posts(blog_dir: Path, generic_tag: str, limit: int) -> list[Path]:
    """Up to `limit` posts (by filename) still carrying `generic_tag`, for
    the judgment pass. Self-tracking: once a decision replaces the tag, the
    post stops matching."""
    selected = []
    for path in sorted(blog_dir.glob("*.md")):
        if generic_tag in read_tags(frontmatter.load(path)):
            selected.append(path)
        if len(selected) >= limit:
            break
    return selected


def apply_tag_decisions(
    blog_dir: Path, decisions: list[dict], alias_map: dict[str, str], is_apply: bool
) -> list[str]:
    """Replace each decided post's tags with `decision["tags"]`, converted
    through the aliases. A decision naming a tag outside the curated list is
    refused before any file is written. Returns the filenames changed."""
    resolved = []
    for decision in decisions:
        canonical = canonicalize_tags(decision["tags"], alias_map)
        if canonical.dropped:
            raise ValueError(
                f"{decision['filename']}: not curated tags {canonical.dropped}"
            )
        resolved.append((decision["filename"], canonical.kept))
    changed = []
    for filename, tags in resolved:
        path = blog_dir / filename
        text = path.read_bytes().decode("utf-8")
        new_text = replace_frontmatter_tags(text, tags)
        verify_rewrite(text, new_text, tags)
        if new_text == text:
            continue
        if is_apply:
            path.write_bytes(new_text.encode("utf-8"))
        changed.append(filename)
    return changed
