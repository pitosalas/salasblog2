#!/usr/bin/env python3
# link_check — Report links in content that point at this site but resolve to nothing
# Author: Pito Salas and Claude Code
"""
A self-link is any link target that is a root-relative path (`/blog/x.html`)
or an absolute salas.com URL. It is *alive* when either:

* it is a legacy URL with a redirect in the reviewed URL map, or
* the generated site has a file for it - resolved the way the server does:
  a directory serves its `index.html`, and an extensionless path is tried
  with `.html` appended.

Everything else is reported as dead. Checking against the generated output
rather than the content tree means tag pages, list pages, and static assets
are covered without re-deriving the generator's URL rules.
"""

import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

from salasblog2.legacy_links import link_targets, normalize_legacy_url

SELF_PATH = re.compile(r"^(?:https?://(?:www\.)?salas\.com)?(/(?!/)[^?#]*)")


@dataclass(frozen=True)
class DeadLink:
    source_file: str
    url: str


def is_served(url_path: str, output_dir: Path) -> bool:
    relative = unquote(url_path).lstrip("/")
    candidate = output_dir / relative
    if candidate.is_dir():
        candidate = candidate / "index.html"
    if not candidate.suffix and not candidate.exists():
        candidate = candidate.with_name(f"{candidate.name}.html")
    return candidate.is_file()


def is_alive(url: str, output_dir: Path, redirects: dict[str, str]) -> bool:
    """True unless url is a self-link that neither serves a file nor redirects."""
    match = SELF_PATH.match(url)
    if match is None:
        return True
    legacy = normalize_legacy_url(url)
    if legacy is not None and legacy[0] in redirects:
        return True
    return is_served(match.group(1), output_dir)


def find_dead_self_links(
    content_dirs: list[Path], output_dir: Path, redirects: dict[str, str]
) -> list[DeadLink]:
    if not output_dir.is_dir():
        raise FileNotFoundError(f"Generated site not found at {output_dir}")
    dead = []
    for content_dir in content_dirs:
        for md_file in sorted(content_dir.glob("*.md")):
            for url in link_targets(md_file.read_text(encoding="utf-8")):
                if not is_alive(url, output_dir, redirects):
                    dead.append(DeadLink(md_file.name, url))
    return dead
