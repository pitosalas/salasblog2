#!/usr/bin/env python3
# propose.py — Post relevance scoring and popular drop selection for the Propose feature
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import re
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple

import frontmatter

RELEVANCE_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning",
    "startup", "entrepreneurship", "productivity",
    "programming", "software", "technology",
    "education", "learning", "teaching",
    "robotics", "automation",
    "python", "javascript",
    "leadership", "management",
]

MIN_AGE_DAYS = 60
SCORE_PER_KEYWORD = 10
SCORE_PER_100_CHARS = 1
SCORE_PER_YEAR_AGO = 2
MAX_AGE_PENALTY = 40


class ScoredPost(NamedTuple):
    score: float
    filename: str
    title: str
    date: str
    url: str


@dataclass
class DropFilter:
    min_age_months: int
    min_visits: int
    top_n: int


def parse_post_date(date_value) -> date | None:
    if date_value is None:
        return None
    if isinstance(date_value, date):
        return date_value if not hasattr(date_value, "date") else date_value.date()
    try:
        return date.fromisoformat(str(date_value)[:10])
    except (ValueError, TypeError):
        return None


def score_post(title: str, content: str, post_date: date, today: date) -> float | None:
    age_days = (today - post_date).days
    if age_days < MIN_AGE_DAYS:
        return None

    text = (title + " " + content).lower()
    keyword_score = sum(
        SCORE_PER_KEYWORD
        for kw in RELEVANCE_KEYWORDS
        if re.search(r"\b" + re.escape(kw) + r"\b", text)
    )
    length_score = len(content) / 100 * SCORE_PER_100_CHARS
    years_old = age_days / 365.0
    age_penalty = min(years_old * SCORE_PER_YEAR_AGO, MAX_AGE_PENALTY)
    return keyword_score + length_score - age_penalty


def get_proposed_posts(blog_dir: Path, top_n: int) -> list[ScoredPost]:
    """Return the top_n highest-scoring old blog posts."""
    today = date.today()
    scored: list[ScoredPost] = []

    for md_file in sorted(blog_dir.glob("*.md")):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
        except OSError:
            continue

        if post.metadata.get("draft"):
            continue

        post_date = parse_post_date(post.metadata.get("date"))
        if post_date is None:
            continue

        title = post.metadata.get("title", md_file.stem)
        s = score_post(title, post.content or "", post_date, today)
        if s is None:
            continue

        filename = md_file.name
        sp = ScoredPost(
            score=s,
            filename=filename,
            title=title,
            date=str(post_date),
            url=f"/blog/{filename.replace('.md', '.html')}",
        )
        scored.append(sp)

    scored.sort(key=lambda sp: sp.score, reverse=True)
    return scored[:top_n]


def _extract_note_from_body(content: str) -> str:
    """Extract the Notes section from a raindrop markdown body."""
    marker = "**Notes:**"
    idx = content.find(marker)
    if idx == -1:
        return ""
    return content[idx + len(marker):].strip()


def _load_drop_record(md_file: Path, stats_counter, cutoff: date) -> dict | None:
    try:
        with open(md_file, "r", encoding="utf-8") as f:
            post = frontmatter.load(f)
    except OSError:
        return None

    post_date = parse_post_date(post.metadata.get("date"))
    if post_date is None or post_date > cutoff:
        return None

    stem = md_file.name.replace(".md", "")
    visits = stats_counter.get(f"/raindrops/{stem}.html")
    note = post.metadata.get("note") or _extract_note_from_body(post.content or "")

    return {
        "filename": md_file.name,
        "title": post.metadata.get("title", stem),
        "url": post.metadata.get("url", ""),
        "raindrop_url": f"/raindrops/{stem}.html",
        "note": note,
        "domain": post.metadata.get("domain", ""),
        "excerpt": post.metadata.get("excerpt", ""),
        "tags": post.metadata.get("tags", []),
        "date": str(post_date),
        "visit_count": visits,
    }


def get_proposed_drops(drops_dir: Path, stats_counter, filt: DropFilter) -> list[dict]:
    """Return popular raindrop posts suitable for blog draft generation."""
    cutoff = date.today() - timedelta(days=filt.min_age_months * 30)
    results = [
        rec
        for md_file in sorted(drops_dir.glob("*.md"))
        if (rec := _load_drop_record(md_file, stats_counter, cutoff)) is not None
        and rec["visit_count"] >= filt.min_visits
    ]
    results.sort(key=lambda d: d["visit_count"], reverse=True)
    return results[: filt.top_n]
