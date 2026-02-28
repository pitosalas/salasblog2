#!/usr/bin/env python3
# test_visitor_type.py — Tests for visitor type classifier
# Author: Pito Salas and Claude Code
# Open Source Under MIT license

from salasblog2.visitor_type import classify_visitor


class TestClassifyVisitor:
    def test_empty_ua_returns_crawler(self):
        assert classify_visitor("") == "crawler"

    def test_none_like_empty_returns_crawler(self):
        assert classify_visitor("   ") == "crawler"

    def test_googlebot_returns_search_engine(self):
        assert classify_visitor("Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)") == "search_engine"

    def test_bingbot_returns_search_engine(self):
        assert classify_visitor("Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)") == "search_engine"

    def test_gptbot_returns_ai_bot(self):
        assert classify_visitor("Mozilla/5.0 AppleWebKit/537.36 (compatible; GPTBot/1.0; +https://openai.com/gptbot)") == "ai_bot"

    def test_claudebot_returns_ai_bot(self):
        assert classify_visitor("Mozilla/5.0 (compatible; ClaudeBot/1.0; +https://anthropic.com/claude-bot)") == "ai_bot"

    def test_anthropic_url_in_ua_returns_ai_bot(self):
        assert classify_visitor("Mozilla/5.0 anthropic.com/some-crawler") == "ai_bot"

    def test_perplexitybot_returns_ai_bot(self):
        assert classify_visitor("PerplexityBot/1.0 (+https://perplexity.ai/perplexitybot)") == "ai_bot"

    def test_chrome_browser_returns_human(self):
        assert classify_visitor("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "en-US,en;q=0.9") == "human"

    def test_firefox_browser_returns_human(self):
        assert classify_visitor("Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0", "en-GB,en;q=0.8") == "human"

    def test_browser_ua_without_accept_language_returns_crawler(self):
        # Browser UA but no Accept-Language — likely a bot spoofing a browser
        assert classify_visitor("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "") == "crawler"

    def test_compatible_bot_disguised_as_browser_not_human(self):
        # Has Mozilla/ but also "compatible;" — should not be classified as human
        ua = "Mozilla/5.0 (compatible; SomeBot/1.0; +http://example.com/bot)"
        assert classify_visitor(ua) != "human"

    def test_headless_chrome_returns_crawler(self):
        assert classify_visitor("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 HeadlessChrome/120.0.0.0") == "crawler"

    def test_python_requests_returns_crawler(self):
        assert classify_visitor("python-requests/2.31.0") == "crawler"

    def test_curl_returns_crawler(self):
        assert classify_visitor("curl/7.88.1") == "crawler"

    def test_generic_spider_returns_crawler(self):
        assert classify_visitor("MySuperSpider/1.0") == "crawler"

    def test_unrecognized_ua_returns_crawler(self):
        assert classify_visitor("CustomTool/2.0 SomeVendor") == "crawler"
