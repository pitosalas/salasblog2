#!/usr/bin/env python3
# legacy_match — Match legacy self-link URLs to current posts and build the reviewed URL map
# Author: Pito Salas and Claude Code
"""
Builds `02-doc/legacy-url-map.json`: for each legacy normalized path (see
`legacy_links`), the current post URL it should point to, a confidence
level, and the evidence behind the match.

Evidence by scheme:

* `mt` - title and date of the archived page (from `wayback`).
* `wp` / `squarespace` - the date and slug in the URL itself.
* `radio-day` - only the date; the old page listed a whole day's posts.

Dates shifted by up to a day across migrations (000522 is Nov 28 in the
archive, `2004-11-29` now), so candidates are posts within
`DATE_WINDOW_DAYS` of the evidence date. Among those, the best title (or
slug) similarity decides:

* `exact` - normalized titles/slugs are identical.
* `fuzzy` - similarity >= `FUZZY_THRESHOLD`, or the sole post of a
  radio-day date. Needs human review.
* `unmatched` - nothing close enough; `new` is null.

Only entries whose `new` is non-null are acted on by the rewrite and the
redirects, so review consists of fixing or nulling `new` on fuzzy entries.
"""

import html
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, timedelta
from difflib import SequenceMatcher
from pathlib import Path

import frontmatter

from salasblog2.wayback import ArchivedPost

DATE_WINDOW_DAYS = 2
FUZZY_THRESHOLD = 0.6
FILENAME_DATE = re.compile(r"^(\d{4}-\d{2}-\d{2})-(.*)$")
# WordPress-imported filenames carry HTML entity numbers in place of
# punctuation (`didn8217t`), so they're dropped before comparing.
ENTITY_DIGITS = re.compile(r"(?<=[a-z])(8211|8212|8216|8217|8220|8221|8230)")
URL_DATE_SLUG = re.compile(r"/(\d{4})/(\d{1,2})/(\d{1,2})/([^/]+?)(?:\.html)?$")
URL_DATE = re.compile(r"/(\d{4})/(\d{2})/(\d{2})\.html$")


@dataclass(frozen=True)
class CurrentPost:
    stem: str
    title: str
    post_date: date

    @property
    def url(self) -> str:
        return f"/blog/{self.stem}.html"

    @property
    def slug(self) -> str:
        match = FILENAME_DATE.match(self.stem)
        return match.group(2) if match else self.stem


def comparable(text: str) -> str:
    """Lowercase alphanumerics only, with entities and accents flattened."""
    text = unicodedata.normalize("NFKD", html.unescape(text)).lower()
    text = ENTITY_DIGITS.sub("", text)
    return re.sub(r"[^a-z0-9]+", "", text)


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, comparable(left), comparable(right)).ratio()


def load_current_posts(blog_dir: Path) -> list[CurrentPost]:
    posts = []
    for md_file in sorted(blog_dir.glob("*.md")):
        if md_file.name.startswith("draft-"):
            continue
        metadata = frontmatter.load(md_file).metadata
        filename_date = FILENAME_DATE.match(md_file.stem)
        raw_date = metadata.get("date") or (filename_date and filename_date.group(1))
        if not raw_date:
            raise ValueError(f"{md_file.name} has no date in frontmatter or filename")
        post_date = date.fromisoformat(str(raw_date)[:10])
        posts.append(CurrentPost(md_file.stem, str(metadata.get("title", "")), post_date))
    return posts


def posts_near(posts: list[CurrentPost], target: date) -> list[CurrentPost]:
    window = timedelta(days=DATE_WINDOW_DAYS)
    return [post for post in posts if abs(post.post_date - target) <= window]


def best_match(candidates: list[CurrentPost], key_of, wanted: str) -> dict:
    """Map entry fields for the candidate whose key_of(post) best matches wanted."""
    scored = sorted(
        ((similarity(key_of(post), wanted), post) for post in candidates),
        key=lambda pair: -pair[0],
    )
    nearby = [{"url": post.url, "score": round(score, 2)} for score, post in scored[:3]]
    if not scored or scored[0][0] < FUZZY_THRESHOLD:
        return {"new": None, "confidence": "unmatched", "candidates": nearby}
    score, post = scored[0]
    is_exact = comparable(key_of(post)) == comparable(wanted)
    confidence = "exact" if is_exact else "fuzzy"
    return {"new": post.url, "confidence": confidence, "candidates": nearby}


def match_archived(archived: ArchivedPost | None, posts: list[CurrentPost]) -> dict:
    if archived is None:
        return {"new": None, "confidence": "unmatched", "evidence": "not archived"}
    candidates = posts_near(posts, date.fromisoformat(archived.date))
    entry = best_match(candidates, lambda post: post.title, archived.title)
    entry["evidence"] = {"title": archived.title, "date": archived.date,
                         "snapshot": archived.snapshot_url}
    return entry


def match_dated_slug(path: str, posts: list[CurrentPost]) -> dict:
    year, month, day, slug = URL_DATE_SLUG.search(path).groups()
    url_date = date(int(year), int(month), int(day))
    candidates = posts_near(posts, url_date)
    by_slug = best_match(candidates, lambda post: post.slug, slug)
    by_title = best_match(candidates, lambda post: post.title, slug)
    entry = by_title if by_title["confidence"] == "exact" else by_slug
    entry["evidence"] = {"slug": slug, "date": url_date.isoformat()}
    return entry


def match_radio_day(path: str, posts: list[CurrentPost]) -> dict:
    year, month, day = URL_DATE.search(path).groups()
    day_posts = [p for p in posts if p.post_date == date(int(year), int(month), int(day))]
    evidence = {"date": f"{year}-{month}-{day}", "posts_that_day": len(day_posts)}
    if len(day_posts) == 1:
        return {"new": day_posts[0].url, "confidence": "fuzzy", "evidence": evidence}
    candidates = [{"url": post.url} for post in day_posts]
    return {"new": None, "confidence": "unmatched", "evidence": evidence,
            "candidates": candidates}


def build_url_map(
    paths_by_scheme: dict[str, list[str]],
    archived_by_path: dict[str, ArchivedPost | None],
    posts: list[CurrentPost],
) -> dict[str, dict]:
    """Map entry for every legacy path, keyed by normalized path."""
    url_map = {}
    for scheme, paths in paths_by_scheme.items():
        for path in paths:
            if scheme == "mt":
                entry = match_archived(archived_by_path[path], posts)
            elif scheme == "radio-day":
                entry = match_radio_day(path, posts)
            else:
                entry = match_dated_slug(path, posts)
            url_map[path] = {"scheme": scheme, **entry}
    return dict(sorted(url_map.items()))
