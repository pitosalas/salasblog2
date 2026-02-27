#!/usr/bin/env python3
# visitor_type.py — Classify HTTP visitors by type from User-Agent string
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

# Known AI bot UA substrings — checked first; many disguise as browsers
AI_BOT_PATTERNS = [
    "gptbot", "chatgpt", "openai",
    "claudebot", "claude-web", "anthropic",
    "perplexitybot", "perplexity",
    "ccbot", "commoncrawl",
    "cohere-ai", "coherebot",
    "google-extended", "googleother",
    "diffbot", "bytespider",
    "amazonbot", "applebot-extended",
    "youbot", "iaskspider", "piplbot",
    "meta-externalagent", "meta-externalfetcher",
    "imagesiftbot", "omgilibot",
    "ai2bot", "friendlycrawler",
    "timpibot", "seekr",
]

# Domains found in bot homepage URLs embedded in UA strings
AI_BOT_URL_PATTERNS = [
    "openai.com", "anthropic.com", "perplexity.ai",
    "cohere.com", "you.com", "diffbot.com",
]

SEARCH_ENGINE_PATTERNS = [
    "googlebot", "bingbot", "slurp", "duckduckbot",
    "baiduspider", "yandexbot", "sogou", "exabot",
    "facebot", "ia_archiver", "msnbot", "teoma",
    "ask jeeves", "naverbot", "seznam",
]

# Signals that reveal a bot even inside a browser-like UA
BOT_SIGNALS = [
    "compatible;",        # e.g. "Mozilla/5.0 (compatible; GPTBot/1.0 ...)"
    "headlesschrome",     # headless browser
    "phantomjs",
    "puppeteer",
    "selenium",
    "webdriver",
    "python-requests",
    "python-urllib",
    "go-http-client",
    "java/",
    "curl/",
    "wget/",
    "libwww",
    "+http",              # bots often embed their URL: "+https://example.com/botinfo"
]

GENERIC_BOT_PATTERNS = [
    "bot", "crawler", "spider", "scraper",
    "fetcher", "scan", "checker", "archiver",
    "monitor", "probe", "harvest",
]

# Real browser tokens — only trusted after ruling out bot signals
BROWSER_PATTERNS = [
    "mozilla/", "chrome/", "safari/", "firefox/",
    "edge/", "opera/", "opr/",
]


def _has_bot_signal(ua: str) -> bool:
    """Return True if UA contains any signal that suggests a non-human client."""
    return any(s in ua for s in BOT_SIGNALS)


def classify_visitor(user_agent: str) -> str:
    """Classify a visitor as human, ai_bot, search_engine, crawler, or unknown."""
    if not user_agent:
        return "unknown"
    ua = user_agent.lower()

    # AI bots first — even if they include browser tokens
    for pattern in AI_BOT_PATTERNS:
        if pattern in ua:
            return "ai_bot"
    for pattern in AI_BOT_URL_PATTERNS:
        if pattern in ua:
            return "ai_bot"

    # Search engines
    for pattern in SEARCH_ENGINE_PATTERNS:
        if pattern in ua:
            return "search_engine"

    # Browser UA — only trusted if no bot signals present
    has_browser = any(p in ua for p in BROWSER_PATTERNS)
    if has_browser and not _has_bot_signal(ua):
        return "human"

    # Generic bot keywords or any bot signal without a browser token → crawler
    for pattern in GENERIC_BOT_PATTERNS:
        if pattern in ua:
            return "crawler"

    if _has_bot_signal(ua) or has_browser:
        return "crawler"

    return "unknown"
