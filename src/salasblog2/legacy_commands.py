#!/usr/bin/env python3
# legacy_commands — CLI orchestration for building the legacy URL map and rewriting links
# Author: Pito Salas and Claude Code
# Version: 1
# Created: 2026-10-17
# Updated: 2026-10-17
"""
Glue between `legacy_links` (scan/rewrite), `wayback` (archive lookups), and
`legacy_match` (matching) for the `bg legacy-map` and `bg legacy-rewrite`
commands.

The map file is the reviewed source of truth and only ever grows. Rebuilding
it keeps any entry marked `"reviewed": true` exactly as the reviewer left it,
so a rerun never undoes a human decision. It also keeps every entry the scan
no longer finds: once content is rewritten its legacy links are gone, but the
redirects still need those entries for inbound links from other sites.
"""

import difflib
import json
from collections import defaultdict
from pathlib import Path

from salasblog2.legacy_links import rewrite_legacy_links, scan_content
from salasblog2.legacy_match import build_url_map, load_current_posts
from salasblog2.wayback import resolve_paths

URL_MAP_FILE = Path(__file__).parents[2] / "02-doc" / "legacy-url-map.json"
WAYBACK_CACHE_FILE = Path(__file__).parents[2] / ".cache" / "wayback.json"
CONTENT_SUBDIRS = ("blog", "pages")


def content_dirs(content_root: Path) -> list[Path]:
    return [content_root / subdir for subdir in CONTENT_SUBDIRS]


def load_url_map(map_file: Path) -> dict[str, dict]:
    return json.loads(map_file.read_text()) if map_file.exists() else {}


def redirect_targets(url_map: dict[str, dict]) -> dict[str, str]:
    """normalized legacy path -> new URL, for entries that have one."""
    return {path: entry["new"] for path, entry in url_map.items() if entry["new"]}


def build_map(content_root: Path, map_file: Path, cache_file: Path) -> dict[str, dict]:
    links = scan_content(content_dirs(content_root))
    paths_by_scheme = defaultdict(set)
    for link in links:
        paths_by_scheme[link.scheme].add(link.normalized_path)
    sorted_paths = {scheme: sorted(paths) for scheme, paths in paths_by_scheme.items()}
    archived = resolve_paths(sorted_paths.get("mt", []), cache_file)
    posts = load_current_posts(content_root / "blog")
    url_map = build_url_map(sorted_paths, archived, posts)

    sources = defaultdict(set)
    for link in links:
        sources[link.normalized_path].add(link.source_file)
    for path, entry in url_map.items():
        entry["linked_from"] = sorted(sources[path])

    previous = load_url_map(map_file)
    url_map.update(
        {p: e for p, e in previous.items() if e.get("reviewed") or p not in url_map}
    )
    url_map = dict(sorted(url_map.items()))
    map_file.write_text(json.dumps(url_map, indent=2, ensure_ascii=False) + "\n")
    return url_map


def rewrite_content(content_root: Path, map_file: Path, is_dry_run: bool) -> int:
    """Rewrite mapped legacy links in content; print a diff per changed file."""
    targets = redirect_targets(load_url_map(map_file))
    total = 0
    for content_dir in content_dirs(content_root):
        for md_file in sorted(content_dir.glob("*.md")):
            text = md_file.read_text(encoding="utf-8")
            new_text, count = rewrite_legacy_links(text, targets)
            if count == 0:
                continue
            total += count
            diff = difflib.unified_diff(
                text.splitlines(),
                new_text.splitlines(),
                str(md_file),
                str(md_file),
                n=0,
                lineterm="",
            )
            print("\n".join(diff))
            if not is_dry_run:
                md_file.write_text(new_text, encoding="utf-8")
    action = "would rewrite" if is_dry_run else "rewrote"
    print(f"{action} {total} links")
    return total


def summarize_map(url_map: dict[str, dict]) -> str:
    counts = defaultdict(int)
    for entry in url_map.values():
        counts[(entry["scheme"], entry["confidence"])] += 1
    lines = [
        f"{scheme:12} {confidence:10} {count}"
        for (scheme, confidence), count in sorted(counts.items())
    ]
    return "\n".join(lines)
