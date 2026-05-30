# Web Scraper 🕷️

A command-line web scraper that extracts quotes, authors, and tags from [quotes.toscrape.com](https://quotes.toscrape.com) — a legal, purpose-built practice site.

Part of my [Python Portfolio](../README.md).

---

## Features

- Scrapes **all 10 pages** automatically (or limit with `--pages`)
- Filter results by **tag** or **author**
- Exports to both **CSV** and **JSON**
- Prints **summary statistics** — top authors, top tags
- Polite crawling with rate limiting (0.5s delay between pages)
- Clean error handling for network issues

---

## Setup

```bash
cd 02_web_scraper
pip install -r requirements.txt
```

---

## Usage

```bash
# Scrape everything (all 100 quotes across 10 pages)
python scraper.py

# Limit to 3 pages
python scraper.py --pages 3

# Filter by tag
python scraper.py --tag love

# Filter by author (partial match)
python scraper.py --author "Einstein"

# Combine filters with stats
python scraper.py --tag humor --author "Twain" --stats

# Custom output filenames
python scraper.py --out-csv my_quotes.csv --out-json my_quotes.json
```

### Sample output

```
Scraping quotes.toscrape.com (all pages)...

  Scraping page 1... 10 quotes found
  Scraping page 2... 10 quotes found
  ...

Total scraped: 100 quotes

Exporting...
  Saved 100 quotes → quotes.csv
  Saved 100 quotes → quotes.json

────────────────────────────────────────
  Total quotes  : 100
  Unique authors: 51
  Unique tags   : 140

  Top 5 authors:
      5x  Albert Einstein
      5x  Mark Twain
      4x  Oscar Wilde
      ...

  Top 10 tags:
     14x  love
     13x  inspirational
     ...
────────────────────────────────────────
```

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Project Structure

```
02_web_scraper/
├── scraper.py              # Main scraper
├── requirements.txt
├── .gitignore
├── README.md
└── tests/
    └── test_scraper.py     # 22 tests — no network calls needed
```

---

## Concepts Covered

| Concept | Where |
|---|---|
| HTTP requests + headers | `get_soup()` |
| HTML parsing | `parse_quotes()` with BeautifulSoup |
| Pagination handling | `get_next_page_url()` |
| Dataclasses | `Quote` model |
| CSV export | `save_csv()` |
| JSON export | `save_json()` |
| argparse | `build_parser()` |
| Mocking in tests | `unittest.mock` |
| Error handling | Network errors, HTTP errors |

---

## Tech Stack

Python 3.11+ · requests · BeautifulSoup4 · argparse · dataclasses · pytest
