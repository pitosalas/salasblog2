"""
Post relevance scoring for the "Propose" feature.
Identifies old blog posts that are especially relevant to repost.
"""
from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import NamedTuple

import frontmatter

# Keywords that boost a post's relevance score
RELEVANCE_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning",
    "startup", "entrepreneurship", "productivity",
    "programming", "software", "technology",
    "education", "learning", "teaching",
    "robotics", "automation",
    "python", "javascript",
    "leadership", "management",
]

# Minimum age: exclude posts from the past two months
MIN_AGE_DAYS = 60

# Score weights
SCORE_PER_KEYWORD = 10
SCORE_PER_100_CHARS = 1
SCORE_PER_YEAR_AGO = 2   # prefer newer (subtract per year of age)
MAX_AGE_PENALTY = 40


class ScoredPost(NamedTuple):
    score: float
    filename: str
    title: str
    date: str
    url: str


def _parse_date(date_value) -> date | None:
    """Parse date from frontmatter (str or date/datetime)."""
    if date_value is None:
        return None
    if isinstance(date_value, date):
        return date_value if not hasattr(date_value, 'date') else date_value.date()
    try:
        return date.fromisoformat(str(date_value)[:10])
    except (ValueError, TypeError):
        return None


def score_post(title: str, content: str, post_date: date, today: date) -> float | None:
    """Calculate relevance score for a single post. Returns None if the post is too recent."""
    age_days = (today - post_date).days

    # Exclude posts from the past two months
    if age_days < MIN_AGE_DAYS:
        return None

    text = (title + " " + content).lower()

    # Keyword score (whole-word matching)
    keyword_score = sum(
        SCORE_PER_KEYWORD
        for kw in RELEVANCE_KEYWORDS
        if re.search(r'\b' + re.escape(kw) + r'\b', text)
    )

    # Length score (prefer longer posts)
    length_score = len(content) / 100 * SCORE_PER_100_CHARS

    # Recency score: prefer newer old posts (subtract for each year of age)
    years_old = age_days / 365.0
    age_penalty = min(years_old * SCORE_PER_YEAR_AGO, MAX_AGE_PENALTY)

    return keyword_score + length_score - age_penalty


def get_proposed_posts(blog_dir: Path, top_n: int = 10) -> list[ScoredPost]:
    """Return the top_n highest-scoring old blog posts."""
    today = date.today()
    scored: list[tuple[float, ScoredPost]] = []

    for md_file in sorted(blog_dir.glob("*.md")):
        try:
            with open(md_file, "r", encoding="utf-8") as f:
                post = frontmatter.load(f)
        except Exception:
            continue

        post_date = _parse_date(post.metadata.get("date"))
        if post_date is None:
            continue

        title = post.metadata.get("title", md_file.stem)
        content = post.content or ""

        s = score_post(title, content, post_date, today)
        if s is None:
            continue

        filename = md_file.name
        url = f"/blog/{filename.replace('.md', '.html')}"
        scored.append((s, ScoredPost(score=s, filename=filename,
                                     title=title, date=str(post_date), url=url)))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [sp for _, sp in scored[:top_n]]
