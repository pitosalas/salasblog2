#!/usr/bin/env python3
# test_visitor_type.py — Tests for visitor type classifier
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

import pytest
from salasblog2.visitor_type import classify_visitor


@pytest.mark.parametrize("ua,expected", [
    ("", "crawler"),
    ("   ", "crawler"),
    ("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)", "search_engine"),
    ("Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)", "search_engine"),
    ("Mozilla/5.0 AppleWebKit/537.36 (compatible; GPTBot/1.0; +https://openai.com/gptbot)", "ai_bot"),
    ("Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://anthropic.com/claude-bot)", "ai_bot"),
    ("Mozilla/5.0 anthropic.com/some-crawler", "ai_bot"),
    ("PerplexityBot/1.0 (+https://perplexity.ai/perplexitybot)", "ai_bot"),
    ("Mozilla/5.0 (compatible; SomeBot/1.0; +http://example.com/bot)", "crawler"),
    ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HeadlessChrome/120.0.0.0", "crawler"),
    ("python-requests/2.31.0", "crawler"),
    ("curl/7.88.1", "crawler"),
    ("MySuperSpider/1.0", "crawler"),
    ("CustomTool/2.0 SomeVendor", "crawler"),
    # browser UA without Accept-Language is a bot spoofing a browser
    ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "crawler"),
])
def test_classify_visitor_no_accept_language(ua, expected):
    assert classify_visitor(ua) == expected


@pytest.mark.parametrize("ua,accept_lang,expected", [
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "en-US,en;q=0.9",
        "human",
    ),
    (
        "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
        "en-GB,en;q=0.8",
        "human",
    ),
    (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "",
        "crawler",
    ),
])
def test_classify_visitor_with_accept_language(ua, accept_lang, expected):
    assert classify_visitor(ua, accept_lang) == expected
