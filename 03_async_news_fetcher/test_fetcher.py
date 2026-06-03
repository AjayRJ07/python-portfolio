"""
Tests for Async News Fetcher
Run: pytest tests/ -v
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from fetcher import Article, FetchResult, parse_rss, filter_results


# ── Sample RSS XML ─────────────────────────────────────────────────

VALID_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Breaking: Python 4.0 Released</title>
      <link>https://example.com/python4</link>
      <description>Python 4.0 brings major improvements.</description>
      <pubDate>Mon, 03 Jun 2025 10:00:00 GMT</pubDate>
    </item>
    <item>
      <title>AI Takes Over the World (Not Really)</title>
      <link>https://example.com/ai</link>
      <description>A lighthearted look at AI progress.</description>
      <pubDate>Mon, 03 Jun 2025 09:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>"""

EMPTY_RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel></channel></rss>"""

MALFORMED_RSS = "This is not valid XML at all <<<>>>"


# ── Article model ─────────────────────────────────────────────────

class TestArticle:
    def test_defaults(self):
        a = Article(title="Test", link="http://x.com", source="Test Source")
        assert a.description == ""
        assert a.published   == ""

    def test_to_dict_keys(self):
        a = Article(title="T", link="L", source="S", description="D", published="P")
        assert set(a.to_dict().keys()) == {"title", "link", "source", "description", "published"}


# ── FetchResult model ─────────────────────────────────────────────

class TestFetchResult:
    def test_success_true_when_no_error(self):
        r = FetchResult(source="BBC", url="http://x.com",
                        articles=[Article("T", "L", "BBC")])
        assert r.success is True

    def test_success_false_when_error(self):
        r = FetchResult(source="BBC", url="http://x.com", error="Timeout")
        assert r.success is False

    def test_to_dict_includes_count(self):
        r = FetchResult(source="BBC", url="http://x.com",
                        articles=[Article("T", "L", "BBC")])
        assert r.to_dict()["count"] == 1


# ── RSS Parser ────────────────────────────────────────────────────

class TestParseRSS:
    def test_parses_valid_rss(self):
        articles = parse_rss(VALID_RSS, "TestFeed")
        assert len(articles) == 2

    def test_extracts_title(self):
        articles = parse_rss(VALID_RSS, "TestFeed")
        assert articles[0].title == "Breaking: Python 4.0 Released"

    def test_extracts_link(self):
        articles = parse_rss(VALID_RSS, "TestFeed")
        assert articles[0].link == "https://example.com/python4"

    def test_extracts_description(self):
        articles = parse_rss(VALID_RSS, "TestFeed")
        assert "Python 4.0" in articles[0].description

    def test_sets_source(self):
        articles = parse_rss(VALID_RSS, "MySource")
        assert all(a.source == "MySource" for a in articles)

    def test_empty_feed_returns_empty_list(self):
        articles = parse_rss(EMPTY_RSS, "Empty")
        assert articles == []

    def test_malformed_xml_returns_empty_list(self):
        articles = parse_rss(MALFORMED_RSS, "Bad")
        assert articles == []

    def test_strips_html_from_description(self):
        rss = VALID_RSS.replace(
            "Python 4.0 brings major improvements.",
            "<p>Python 4.0 brings <b>major</b> improvements.</p>"
        )
        articles = parse_rss(rss, "TestFeed")
        assert "<p>" not in articles[0].description
        assert "<b>" not in articles[0].description
