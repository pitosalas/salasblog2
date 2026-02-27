#!/usr/bin/env python3
# visitor_type.py — Classify HTTP visitors by type from User-Agent string
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

SEARCH_ENGINE_PATTERNS = [
    "googlebot", "bingbot", "slurp", "duckduckbot",
    "baiduspider", "yandexbot", "sogou", "exabot",
    "facebot", "ia_archiver",
]

AI_BOT_PATTERNS = [
    "gptbot", "claudebot", "anthropic-ai", "perplexitybot",
    "ccbot", "cohere-ai", "youbot", "imagesiftbot",
    "google-extended", "diffbot",
]

BROWSER_PATTERNS = [
    "mozilla/", "chrome/", "safari/", "firefox/",
    "edge/", "opera/", "opr/",
]

GENERIC_BOT_PATTERNS = [
    "bot", "crawler", "spider", "scraper",
    "fetcher", "scan", "checker",
]


def classify_visitor(user_agent: str) -> str:
    """Classify a visitor as human, ai_bot, search_engine, crawler, or unknown."""
    if not user_agent:
        return "unknown"
    ua = user_agent.lower()
    for pattern in AI_BOT_PATTERNS:
        if pattern in ua:
            return "ai_bot"
    for pattern in SEARCH_ENGINE_PATTERNS:
        if pattern in ua:
            return "search_engine"
    for pattern in BROWSER_PATTERNS:
        if pattern in ua:
            return "human"
    for pattern in GENERIC_BOT_PATTERNS:
        if pattern in ua:
            return "crawler"
    return "unknown"
