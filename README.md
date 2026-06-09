# Python Portfolio 🐍

A collection of Python projects covering **Core** and **Advanced** concepts — built as part of a full-stack AI/ML portfolio.

> **Author:** Ajay RJ &nbsp;·&nbsp; [github.com/AjayRJ07](https://github.com/AjayRJ07) &nbsp;·&nbsp; ajayrj412@gmail.com

---

## Projects

| # | Project | Concepts | Level |
|---|---------|----------|-------|
| 01 | [CLI Task Manager](#01-cli-task-manager) | OOP · argparse · File I/O · JSON · pytest | Core |
| 02 | [Web Scraper](#02-web-scraper) | requests · BeautifulSoup · CSV · JSON export | Core |
| 03 | [Async News Fetcher](#03-async-news-fetcher) | asyncio · aiohttp · RSS · concurrency | Advanced |
| 04 | [Design Patterns Demo](#04-design-patterns-demo) | Decorators · Cache · Rate Limiter · Circuit Breaker | Advanced |

---

## 01 CLI Task Manager

**Folder:** `01_task_manager/`

A command-line task manager with a Flask web UI — run both from the same folder.

**Features:**
- Add tasks with **priority** (high / medium / low) and **due dates**
- Mark tasks done · delete · bulk-clear completed
- Filter by priority and status
- Overdue detection — tasks past their due date are flagged automatically
- Persistent JSON storage — tasks survive between sessions

**Run CLI:**
```bash
cd 01_task_manager
pip install -r requirements.txt

python task_manager.py add "Submit report" --due 2025-06-20 --priority high
python task_manager.py list
python task_manager.py list --priority high --pending
python task_manager.py done 1
python task_manager.py delete 2
python task_manager.py clear-done
```

**Run Flask UI:**
```bash
python app.py
# Open http://127.0.0.1:5000
```

**Run Tests:**
```bash
pytest tests/ -v
```

**Concepts:** OOP with dataclasses · Enums · argparse subcommands · JSON File I/O · Properties · Sorting & filtering · pytest

---

## 02 Web Scraper

**Folder:** `02_web_scraper/`

Scrapes quotes, authors, and tags from [quotes.toscrape.com](https://quotes.toscrape.com) — a legal, purpose-built practice site — with a Flask UI for in-browser downloads.

**Features:**
- Scrapes all 10 pages automatically with polite rate limiting (0.5s delay)
- Filter by **tag** or **author** (case-insensitive, partial match)
- Exports to both **CSV** and **JSON**
- Summary statistics — top authors, most-used tags
- Flask UI with download buttons

**Run CLI:**
```bash
cd 02_web_scraper
pip install -r requirements.txt

python scraper.py                          # scrape all 100 quotes
python scraper.py --pages 3               # limit to 3 pages
python scraper.py --tag love              # filter by tag
python scraper.py --author "Einstein"     # filter by author
python scraper.py --pages 5 --stats      # with summary stats
```

**Run Flask UI:**
```bash
python app.py
# Open http://127.0.0.1:5001
```

**Run Tests:**
```bash
pytest tests/ -v
```

**Concepts:** requests · BeautifulSoup CSS selectors · Pagination · dataclasses · CSV/JSON export · argparse · Mock-based testing (no network needed for tests)

---

## 03 Async News Fetcher

**Folder:** `03_async_news_fetcher/`

Fetches live headlines from 8 RSS sources **simultaneously** using asyncio — significantly faster than sequential requests.

**Sources:** BBC News · Reuters · Al Jazeera · NPR · The Guardian · Hacker News · TechCrunch · NASA

**Features:**
- All 8 sources fetched concurrently with `asyncio.gather()`
- Benchmark table — per-source timing + speedup vs sequential
- Flask UI with source checkboxes and collapsible results per source
- Per-source error handling — one failure doesn't stop the rest

**Run CLI:**
```bash
cd 03_async_news_fetcher
pip install -r requirements.txt

python cli.py                                        # fetch all sources
python cli.py --sources "BBC News" "TechCrunch"      # specific sources
python cli.py --benchmark                            # show timing table
python cli.py --list-sources                         # list available sources
```

**Run Flask UI:**
```bash
python app.py
# Open http://127.0.0.1:5002
```

**Run Tests:**
```bash
pytest tests/ -v
```

**Sample benchmark output:**
```
Source               Articles    Time   Status
──────────────────── ────────  ──────  ──────
Hacker News                10   0.41s  OK
BBC News                   10   0.63s  OK
TechCrunch                 10   0.87s  OK
...
Total (concurrent):  1.24s
Est. sequential:     7.80s
Speedup:             6.3x faster
```

**Concepts:** asyncio · aiohttp · asyncio.gather() · RSS/XML parsing · Concurrent I/O · Per-task error handling

---

## 04 Design Patterns Demo

**Folder:** `04_design_patterns/`

Production-grade implementations of 4 real-world Python patterns — each one is interactive in the Flask UI.

| Pattern | What it does | Real-world use |
|---------|-------------|----------------|
| `@retry` | Retries failing functions with exponential backoff | API calls · DB connections |
| `@cache` | Memoizes results with TTL and max size limit | DB queries · heavy computations |
| `@rate_limit` | Limits calls per time window (sliding window) | External APIs · login endpoints |
| `CircuitBreaker` | Blocks calls after N failures, auto-recovers | Microservices · payment gateways |

**Run CLI:**
```bash
cd 04_design_patterns
pip install -r requirements.txt

python cli.py                       # run all 4 demos
python cli.py --pattern retry
python cli.py --pattern cache
python cli.py --pattern ratelimit
python cli.py --pattern circuit
```

**Run Flask UI:**
```bash
python app.py
# Open http://127.0.0.1:5003
# All 4 patterns are interactive — trigger each one live with buttons
```

**Run Tests:**
```bash
pytest tests/ -v
```

**Concepts:** Decorators with arguments · functools.wraps · threading.Lock · Enum state machine · Memoization · Sliding window · Thread safety

---

## Repo Structure

```
python-portfolio/
├── README.md
├── 01_task_manager/
│   ├── task_manager.py       # CLI app
│   ├── app.py                # Flask UI — port 5000
│   ├── requirements.txt
│   ├── templates/
│   └── tests/
├── 02_web_scraper/
│   ├── scraper.py            # CLI scraper
│   ├── app.py                # Flask UI — port 5001
│   ├── requirements.txt
│   ├── templates/
│   └── tests/
├── 03_async_news_fetcher/
│   ├── fetcher.py            # Core async logic
│   ├── cli.py                # CLI entry point
│   ├── app.py                # Flask UI — port 5002
│   ├── requirements.txt
│   ├── templates/
│   └── tests/
└── 04_design_patterns/
    ├── patterns.py           # All 4 patterns
    ├── cli.py                # CLI demo
    ├── app.py                # Flask UI — port 5003
    ├── requirements.txt
    ├── templates/
    └── tests/
```

---

## Tech Stack

| Category | Libraries |
|---|---|
| Core Python | argparse · dataclasses · json · enum · functools · threading |
| Web Scraping | requests · BeautifulSoup4 |
| Async | asyncio · aiohttp |
| Web UI | Flask · Jinja2 |
| Testing | pytest |

---

## Quick Start

```bash
git clone https://github.com/AjayRJ07/python-portfolio.git
cd python-portfolio

# Pick any project
cd 01_task_manager
pip install -r requirements.txt
python task_manager.py --help
```
