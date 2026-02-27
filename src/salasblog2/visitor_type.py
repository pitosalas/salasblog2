#!/usr/bin/env python3
# visitor_type.py — Classify HTTP visitors as human, search_engine, or ai_bot
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

SEARCH_ENGINE_PATTERNS = [
    "googlebot", "bingbot", "slurp", "duckduckbot",
    "baiduspider", "yandexbot", "sogou", "exabot",
]

AI_BOT_PATTERNS = [
    "gptbot", "claudebot", "anthropic-ai", "perplexitybot",
    "ccbot", "cohere-ai", "youbot", "imagesiftbot",
]


def classify_visitor(user_agent: str) -> str:
    """Return visitor type based on User-Agent string."""
    ua = user_agent.lower()
    for pattern in AI_BOT_PATTERNS:
        if pattern in ua:
            return "ai_bot"
    for pattern in SEARCH_ENGINE_PATTERNS:
        if pattern in ua:
            return "search_engine"
    return "human"
