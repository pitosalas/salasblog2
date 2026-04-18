#!/usr/bin/env python3
# draft_generator.py — Generate blog draft posts from raindrop data using Claude API
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import logging
from datetime import date
from pathlib import Path

import anthropic
import requests
import yaml
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CLAUDE_MODEL = "claude-sonnet-4-6"
URL_FETCH_TIMEOUT = 5
MAX_FETCHED_CHARS = 3000


def fetch_url_text(url: str) -> str:
    """Fetch plain text from a URL, returning empty string on any failure."""
    try:
        resp = requests.get(url, timeout=URL_FETCH_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        resp.encoding = resp.apparent_encoding or "utf-8"
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer"]):
            tag.decompose()
        return soup.get_text(separator=" ", strip=True)[:MAX_FETCHED_CHARS]
    except requests.RequestException as e:
        logger.warning("Could not fetch %s: %s", url, e)
        return ""


def build_prompt(drop: dict, page_text: str) -> str:
    tags = ", ".join(drop.get("tags") or []) or "none"
    note = drop.get("note") or ""
    excerpt = drop.get("excerpt") or ""
    page_section = f"\n\nPage content (first {MAX_FETCHED_CHARS} chars):\n{page_text}" if page_text else ""

    return f"""Write a single blog paragraph (around 150 words) about the following link post.
The paragraph must include a markdown hyperlink to the source URL.
Write in first person as the blog author sharing an interesting find.
End naturally — no meta-commentary, no sign-off.

Title: {drop['title']}
URL: {drop['url']}
Domain: {drop['domain']}
Tags: {tags}
Excerpt: {excerpt}
My note: {note}{page_section}

Output only the paragraph text (plain markdown), nothing else."""


def build_frontmatter(drop: dict, title: str) -> str:
    data = {
        "title": title,
        "date": date.today().isoformat(),
        "type": "blog",
        "draft": True,
        "author": "Claude.ai",
        "source_raindrop": drop["filename"],
        "source_url": drop["url"],
        "tags": drop.get("tags") or [],
    }
    return "---\n" + yaml.dump(data, allow_unicode=True, default_flow_style=False, encoding=None) + "---\n"


def call_claude(prompt: str) -> str:
    client = anthropic.Anthropic()
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=400,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text.strip()


def generate_draft_from_drop(drop: dict) -> str:
    """Generate a markdown draft blog post from a raindrop dict.

    Returns full file content (frontmatter + body) ready to write to disk.
    """
    page_text = fetch_url_text(drop["url"])
    prompt = build_prompt(drop, page_text)
    body = call_claude(prompt)
    title = drop["title"]
    fm = build_frontmatter(drop, title)
    return fm + "\n" + body + "\n"


def save_draft(content: str, filename: str, blog_dirs: list[Path]) -> None:
    """Write draft content to each directory in blog_dirs."""
    for blog_dir in blog_dirs:
        blog_dir.mkdir(parents=True, exist_ok=True)
        (blog_dir / filename).write_text(content, encoding="utf-8")
