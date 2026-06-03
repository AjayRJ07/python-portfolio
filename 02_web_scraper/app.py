"""
Flask Web Scraper
=================
Run:
    pip install flask requests beautifulsoup4
    python app.py
Then open: http://127.0.0.1:5001
"""

import csv
import io
import json
import time
from collections import Counter
from dataclasses import asdict, dataclass

import requests
from bs4 import BeautifulSoup
from flask import Flask, Response, render_template, request

app = Flask(__name__)
BASE_URL = "https://quotes.toscrape.com"

CURLY_QUOTES = str.maketrans({
    "\u201c": '"', "\u201d": '"',
    "\u2018": "'", "\u2019": "'",
    "\u2014": "-", "\u2013": "-",
    "\u2026": "...",
})

def clean(text: str) -> str:
    return text.translate(CURLY_QUOTES).strip()


# ── Data model ────────────────────────────────────────────────────

@dataclass
class Quote:
    text:   str
    author: str
    tags:   list

    def to_dict(self):
        return asdict(self)

    def tags_str(self):
        return ", ".join(self.tags)


# ── Scraper ───────────────────────────────────────────────────────

def get_soup(url: str):
    headers = {"User-Agent": "Mozilla/5.0 (educational scraper)"}
    resp = requests.get(url, headers=headers, timeout=10)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "html.parser")


def parse_quotes(soup) -> list:
    quotes = []
    for div in soup.select("div.quote"):
        text   = clean(div.select_one("span.text").get_text(strip=True))
        author = clean(div.select_one("small.author").get_text(strip=True))
        tags   = [clean(t.get_text(strip=True)) for t in div.select("a.tag")]
        quotes.append(Quote(text=text, author=author, tags=tags))
    return quotes


def scrape(max_pages=2) -> list:
    all_quotes, url, page = [], BASE_URL, 1
    while url and page <= max_pages:
        soup = get_soup(url)
        all_quotes.extend(parse_quotes(soup))
        nxt = soup.select_one("li.next > a")
        url = (BASE_URL + nxt["href"]) if nxt else None
        page += 1
        time.sleep(0.4)
    return all_quotes


def filter_quotes(quotes, tag=None, author=None) -> list:
    if tag:
        quotes = [q for q in quotes if any(tag.lower() in t.lower() for t in q.tags)]
    if author:
        quotes = [q for q in quotes if author.lower() in q.author.lower()]
    return quotes


def get_stats(quotes: list) -> dict:
    return {
        "total":          len(quotes),
        "unique_authors": len(set(q.author for q in quotes)),
        "unique_tags":    len(set(t for q in quotes for t in q.tags)),
        "top_authors":    Counter(q.author for q in quotes).most_common(5),
        "top_tags":       Counter(t for q in quotes for t in q.tags).most_common(10),
    }


# ── Routes ────────────────────────────────────────────────────────

@app.route("/", methods=["GET", "POST"])
def index():
    quotes  = []
    stats   = {}
    error   = None
    scraped = False

    tag        = request.form.get("tag", "").strip()
    author     = request.form.get("author", "").strip()
    max_pages  = int(request.form.get("max_pages", 2))

    if request.method == "POST":
        try:
            quotes  = scrape(max_pages=max_pages)
            quotes  = filter_quotes(quotes, tag=tag or None, author=author or None)
            stats   = get_stats(quotes)
            scraped = True
        except requests.exceptions.ConnectionError:
            error = "Could not connect to quotes.toscrape.com. Check your internet."
        except Exception as e:
            error = f"Something went wrong: {str(e)}"

    return render_template("index.html",
                           quotes=quotes,
                           stats=stats,
                           error=error,
                           scraped=scraped,
                           tag=tag,
                           author=author,
                           max_pages=max_pages)


@app.route("/download/csv", methods=["POST"])
def download_csv():
    tag       = request.form.get("tag", "").strip()
    author    = request.form.get("author", "").strip()
    max_pages = int(request.form.get("max_pages", 2))

    quotes = scrape(max_pages=max_pages)
    quotes = filter_quotes(quotes, tag=tag or None, author=author or None)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["text", "author", "tags"])
    for q in quotes:
        writer.writerow([q.text, q.author, q.tags_str()])

    return Response(
        "\ufeff" + output.getvalue(),   # BOM for Excel
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=quotes.csv"}
    )


@app.route("/download/json", methods=["POST"])
def download_json():
    tag       = request.form.get("tag", "").strip()
    author    = request.form.get("author", "").strip()
    max_pages = int(request.form.get("max_pages", 2))

    quotes = scrape(max_pages=max_pages)
    quotes = filter_quotes(quotes, tag=tag or None, author=author or None)

    return Response(
        json.dumps([q.to_dict() for q in quotes], indent=2, ensure_ascii=False),
        mimetype="application/json",
        headers={"Content-Disposition": "attachment; filename=quotes.json"}
    )


if __name__ == "__main__":
    app.run(debug=True, port=5001)
