"""
Async News Fetcher — Core Module
=================================
Fetches headlines from multiple RSS feeds simultaneously using asyncio + aiohttp.
Used by both the CLI (cli.py) and Flask UI (app.py).
"""

import asyncio
import time
from dataclasses import dataclass, field
from datetime import datetime
from xml.etree import ElementTree as ET

import aiohttp

# ── News Sources ──────────────────────────────────────────────────

SOURCES = {
    "BBC News":         "http://feeds.bbci.co.uk/news/rss.xml",
    "Reuters":          "https://feeds.reuters.com/reuters/topNews",
    "Al Jazeera":       "https://www.aljazeera.com/xml/rss/all.xml",
    "NPR News":         "https://feeds.npr.org/1001/rss.xml",
    "The Guardian":     "https://www.theguardian.com/world/rss",
    "Hacker News":      "https://hnrss.org/frontpage",
    "TechCrunch":       "https://techcrunch.com/feed/",
    "NASA News":        "https://www.nasa.gov/rss/dyn/breaking_news.rss",
}

# ── Data Models ───────────────────────────────────────────────────

@dataclass
class Article:
    title:       str
    link:        str
    source:      str
    description: str  = ""
    published:   str  = ""

    def to_dict(self) -> dict:
        return {
            "title":       self.title,
            "link":        self.link,
            "source":      self.source,
            "description": self.description,
            "published":   self.published,
        }


@dataclass
class FetchResult:
    source:   str
    url:      str
    articles: list = field(default_factory=list)
    error:    str  = ""
    duration: float = 0.0

    @property
    def success(self) -> bool:
        return not self.error

    def to_dict(self) -> dict:
        return {
            "source":   self.source,
            "url":      self.url,
            "articles": [a.to_dict() for a in self.articles],
            "error":    self.error,
            "duration": round(self.duration, 3),
            "count":    len(self.articles),
        }


# ── RSS Parser ────────────────────────────────────────────────────

def parse_rss(xml_text: str, source: str) -> list:
    """Parse RSS XML and return a list of Article objects."""
    articles = []
    try:
        root = ET.fromstring(xml_text)
        # Handle both RSS and Atom namespaces
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        items = root.findall(".//item") or root.findall(".//atom:entry", ns)

        for item in items[:10]:   # max 10 per source
            def tag(name):
                el = item.find(name)
                return el.text.strip() if el is not None and el.text else ""

            title       = tag("title")
            link        = tag("link") or tag("guid")
            description = tag("description") or tag("summary")
            published   = tag("pubDate") or tag("published") or tag("updated")

            # Clean description — strip HTML tags simply
            import re
            description = re.sub(r"<[^>]+>", "", description)[:200]

            if title:
                articles.append(Article(
                    title=title,
                    link=link,
                    source=source,
                    description=description,
                    published=published,
                ))
    except ET.ParseError:
        pass   # handled as error in caller
    return articles


# ── Async Fetch ───────────────────────────────────────────────────

async def fetch_one(
    session: aiohttp.ClientSession,
    source:  str,
    url:     str,
) -> FetchResult:
    """Fetch and parse a single RSS feed asynchronously."""
    start = time.perf_counter()
    try:
        async with session.get(
            url,
            timeout=aiohttp.ClientTimeout(total=10),
            headers={"User-Agent": "Mozilla/5.0 (async news fetcher — educational)"},
            ssl=False,
        ) as resp:
            resp.raise_for_status()
            text     = await resp.text(errors="replace")
            articles = parse_rss(text, source)
            return FetchResult(
                source=source, url=url, articles=articles,
                duration=time.perf_counter() - start,
            )
    except asyncio.TimeoutError:
        return FetchResult(source=source, url=url,
                           error="Timeout", duration=time.perf_counter() - start)
    except aiohttp.ClientError as e:
        return FetchResult(source=source, url=url,
                           error=str(e)[:80], duration=time.perf_counter() - start)
    except Exception as e:
        return FetchResult(source=source, url=url,
                           error=f"Unexpected: {str(e)[:80]}", duration=time.perf_counter() - start)


async def fetch_all(sources: dict) -> tuple:
    """
    Fetch all sources concurrently.
    Returns (results, total_duration).
    """
    start = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        tasks   = [fetch_one(session, name, url) for name, url in sources.items()]
        results = await asyncio.gather(*tasks)
    return list(results), time.perf_counter() - start


# ── Public API ────────────────────────────────────────────────────

def filter_results(results: list, keyword: str = "") -> list:
    """Filter articles across all results by keyword (title or description)."""
    if not keyword:
        return results
    kw = keyword.lower()
    filtered = []
    for r in results:
        matching = [a for a in r.articles
                    if kw in a.title.lower() or kw in a.description.lower()]
        filtered.append(FetchResult(
            source=r.source, url=r.url,
            articles=matching, error=r.error, duration=r.duration,
        ))
    return filtered


def run_fetch(selected_sources: dict = None) -> tuple:
    """
    Entry point for both CLI and Flask.
    Returns (results, total_duration, benchmark_info).
    """
    sources = selected_sources or SOURCES
    results, total_duration = asyncio.run(fetch_all(sources))

    successful  = [r for r in results if r.success]
    failed      = [r for r in results if not r.success]
    all_articles = [a for r in successful for a in r.articles]

    benchmark = {
        "total_sources":     len(sources),
        "successful":        len(successful),
        "failed":            len(failed),
        "total_articles":    len(all_articles),
        "total_duration":    round(total_duration, 2),
        "avg_per_source":    round(total_duration / len(sources), 2) if sources else 0,
        "fetched_at":        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }
    return results, total_duration, benchmark
