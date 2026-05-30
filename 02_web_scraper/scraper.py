"""
Quotes Web Scraper
==================
Scrapes quotes, authors, and tags from quotes.toscrape.com

Usage:
    python scraper.py                        # scrape all pages, save CSV + JSON
    python scraper.py --pages 3              # limit to 3 pages
    python scraper.py --tag love             # filter by tag
    python scraper.py --author "Einstein"    # filter by author
    python scraper.py --stats               # show summary stats after scraping
"""

import argparse
import csv
import json
import time
import sys
import io
from dataclasses import dataclass, asdict
from collections import Counter

import requests
from bs4 import BeautifulSoup

# ── Windows UTF-8 fix ─────────────────────────────────────────────
# Rewrap stdout/stderr so special characters never crash on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

BASE_URL = "https://quotes.toscrape.com"

CURLY_QUOTES = str.maketrans({
    "\u201c": '"', "\u201d": '"',
    "\u2018": "'", "\u2019": "'",
    "\u2014": "-", "\u2013": "-",
    "\u2026": "...",
})

def clean(text: str) -> str:
    """Replace fancy Unicode punctuation with plain ASCII equivalents."""
    return text.translate(CURLY_QUOTES).strip()


# ── Data Model ────────────────────────────────────────────────────

@dataclass
class Quote:
    text:   str
    author: str
    tags:   list

    def to_dict(self) -> dict:
        return asdict(self)

    def tags_str(self) -> str:
        return ", ".join(self.tags)


# ── HTTP helpers ──────────────────────────────────────────────────

def get_soup(url: str) -> BeautifulSoup:
    headers = {"User-Agent": "Mozilla/5.0 (educational scraper)"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.exceptions.ConnectionError:
        sys.exit("Error: Could not connect. Check your internet connection.")
    except requests.exceptions.Timeout:
        sys.exit("Error: Request timed out.")
    except requests.exceptions.HTTPError as e:
        sys.exit(f"HTTP error: {e}")
    return BeautifulSoup(response.text, "html.parser")


# ── Parsing ───────────────────────────────────────────────────────

def parse_quotes(soup: BeautifulSoup) -> list:
    quotes = []
    for div in soup.select("div.quote"):
        text   = clean(div.select_one("span.text").get_text(strip=True))
        author = clean(div.select_one("small.author").get_text(strip=True))
        tags   = [clean(tag.get_text(strip=True)) for tag in div.select("a.tag")]
        quotes.append(Quote(text=text, author=author, tags=tags))
    return quotes


def get_next_page_url(soup: BeautifulSoup):
    next_btn = soup.select_one("li.next > a")
    if not next_btn:
        return None
    return BASE_URL + next_btn["href"]


# ── Core scrape loop ──────────────────────────────────────────────

def scrape(max_pages=None) -> list:
    all_quotes = []
    url   = BASE_URL
    page  = 1

    while url:
        if max_pages and page > max_pages:
            break
        print(f"  Scraping page {page}...", end=" ", flush=True)
        soup  = get_soup(url)
        found = parse_quotes(soup)
        all_quotes.extend(found)
        print(f"{len(found)} quotes found")
        url   = get_next_page_url(soup)
        page += 1
        time.sleep(0.5)

    return all_quotes


# ── Filtering ─────────────────────────────────────────────────────

def filter_quotes(quotes, tag=None, author=None) -> list:
    if tag:
        quotes = [q for q in quotes if any(tag.lower() in t.lower() for t in q.tags)]
    if author:
        quotes = [q for q in quotes if author.lower() in q.author.lower()]
    return quotes


# ── Export ────────────────────────────────────────────────────────

def save_csv(quotes, filename="quotes.csv") -> None:
    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f)
        writer.writerow(["text", "author", "tags"])
        for q in quotes:
            writer.writerow([q.text, q.author, q.tags_str()])
    print(f"  Saved {len(quotes)} quotes -> {filename}")


def save_json(quotes, filename="quotes.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump([q.to_dict() for q in quotes], f, indent=2, ensure_ascii=False)
    print(f"  Saved {len(quotes)} quotes -> {filename}")


# ── Stats ─────────────────────────────────────────────────────────

def print_stats(quotes) -> None:
    if not quotes:
        print("No quotes to analyse.")
        return

    author_counts = Counter(q.author for q in quotes)
    tag_counts    = Counter(tag for q in quotes for tag in q.tags)

    print(f"\n{'─'*40}")
    print(f"  Total quotes  : {len(quotes)}")
    print(f"  Unique authors: {len(author_counts)}")
    print(f"  Unique tags   : {len(tag_counts)}")

    print(f"\n  Top 5 authors:")
    for author, count in author_counts.most_common(5):
        print(f"    {count:>3}x  {author}")

    print(f"\n  Top 10 tags:")
    for tag, count in tag_counts.most_common(10):
        print(f"    {count:>3}x  {tag}")
    print(f"{'─'*40}\n")


# ── CLI ───────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scraper",
        description="Scrape quotes from quotes.toscrape.com and export to CSV + JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
examples:
  python scraper.py
  python scraper.py --pages 3
  python scraper.py --tag love
  python scraper.py --author "Einstein"
  python scraper.py --pages 5 --stats
        """,
    )
    parser.add_argument("--pages",    type=int, metavar="N",
                        help="Max pages to scrape (default: all)")
    parser.add_argument("--tag",      type=str,
                        help="Filter by tag (case-insensitive)")
    parser.add_argument("--author",   type=str,
                        help="Filter by author name (partial match)")
    parser.add_argument("--stats",    action="store_true",
                        help="Print summary statistics")
    parser.add_argument("--out-csv",  default="quotes.csv",  metavar="FILE",
                        help="CSV output filename (default: quotes.csv)")
    parser.add_argument("--out-json", default="quotes.json", metavar="FILE",
                        help="JSON output filename (default: quotes.json)")
    return parser


def main() -> None:
    args = build_parser().parse_args()

    print(f"\nScraping quotes.toscrape.com"
          + (f" (max {args.pages} pages)" if args.pages else " (all pages)") + "...\n")

    quotes   = scrape(max_pages=args.pages)
    print(f"\nTotal scraped: {len(quotes)} quotes")

    filtered = filter_quotes(quotes, tag=args.tag, author=args.author)
    if args.tag or args.author:
        filters = []
        if args.tag:    filters.append(f"tag='{args.tag}'")
        if args.author: filters.append(f"author='{args.author}'")
        print(f"After filter ({', '.join(filters)}): {len(filtered)} quotes")

    if not filtered:
        print("No quotes matched your filters. Nothing saved.")
        return

    print("\nExporting...")
    save_csv(filtered,  filename=args.out_csv)
    save_json(filtered, filename=args.out_json)

    if args.stats:
        print_stats(filtered)

    print("\nDone!")


if __name__ == "__main__":
    main()