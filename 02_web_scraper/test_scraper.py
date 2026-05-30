import pytest
import json
import csv
from pathlib import Path
from bs4 import BeautifulSoup
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from scraper import Quote, parse_quotes, get_next_page_url, filter_quotes, save_csv, save_json


# ── Sample HTML fixture ───────────────────────────────────────────

SAMPLE_HTML = """
<html><body>
  <div class="quote">
    <span class="text">\u201cLife is what happens when you\u2019re busy making other plans.\u201d</span>
    <small class="author">John Lennon</small>
    <div class="tags">
      <a class="tag">life</a>
      <a class="tag">planning</a>
    </div>
  </div>
  <div class="quote">
    <span class="text">\u201cThe world is a book and those who do not travel read only one page.\u201d</span>
    <small class="author">Saint Augustine</small>
    <div class="tags">
      <a class="tag">travel</a>
      <a class="tag">reading</a>
    </div>
  </div>
  <ul class="pager">
    <li class="next"><a href="/page/2/">Next</a></li>
  </ul>
</body></html>
"""

LAST_PAGE_HTML = """
<html><body>
  <div class="quote">
    <span class="text">\u201cOnly one page here.\u201d</span>
    <small class="author">Someone</small>
    <div class="tags"><a class="tag">test</a></div>
  </div>
</body></html>
"""


@pytest.fixture
def sample_soup():
    return BeautifulSoup(SAMPLE_HTML, "html.parser")

@pytest.fixture
def last_page_soup():
    return BeautifulSoup(LAST_PAGE_HTML, "html.parser")

@pytest.fixture
def sample_quotes():
    return [
        Quote("Life is what happens", "John Lennon",     ["life", "inspirational"]),
        Quote("Two things are infinite", "Albert Einstein", ["science", "humor"]),
        Quote("So it goes.",           "Kurt Vonnegut",  ["life", "humor"]),
        Quote("Stay hungry, stay foolish", "Steve Jobs", ["inspirational"]),
    ]


# ── Quote model ───────────────────────────────────────────────────

class TestQuote:
    def test_tags_str_joins_with_comma(self):
        q = Quote("Text", "Author", ["love", "life", "humor"])
        assert q.tags_str() == "love, life, humor"

    def test_tags_str_empty(self):
        q = Quote("Text", "Author", [])
        assert q.tags_str() == ""

    def test_to_dict_has_all_fields(self):
        q = Quote("Text", "Author", ["tag1"])
        d = q.to_dict()
        assert set(d.keys()) == {"text", "author", "tags"}

    def test_to_dict_tags_is_list(self):
        q = Quote("Text", "Author", ["a", "b"])
        assert isinstance(q.to_dict()["tags"], list)


# ── Parsing ───────────────────────────────────────────────────────

class TestParsing:
    def test_parse_returns_correct_count(self, sample_soup):
        quotes = parse_quotes(sample_soup)
        assert len(quotes) == 2

    def test_parse_extracts_author(self, sample_soup):
        quotes = parse_quotes(sample_soup)
        assert quotes[0].author == "John Lennon"
        assert quotes[1].author == "Saint Augustine"

    def test_parse_extracts_tags(self, sample_soup):
        quotes = parse_quotes(sample_soup)
        assert "life" in quotes[0].tags
        assert "planning" in quotes[0].tags

    def test_parse_strips_quote_characters(self, sample_soup):
        quotes = parse_quotes(sample_soup)
        assert not quotes[0].text.startswith("\u201c")
        assert not quotes[0].text.endswith("\u201d")

    def test_parse_empty_page(self):
        soup = BeautifulSoup("<html><body></body></html>", "html.parser")
        assert parse_quotes(soup) == []

    def test_next_page_url_found(self, sample_soup):
        url = get_next_page_url(sample_soup)
        assert url == "https://quotes.toscrape.com/page/2/"

    def test_next_page_url_none_on_last_page(self, last_page_soup):
        assert get_next_page_url(last_page_soup) is None


# ── Filtering ─────────────────────────────────────────────────────

class TestFilter:
    def test_filter_by_tag(self, sample_quotes):
        result = filter_quotes(sample_quotes, tag="humor")
        assert len(result) == 2
        assert all(any("humor" in t for t in q.tags) for q in result)

    def test_filter_by_tag_case_insensitive(self, sample_quotes):
        result = filter_quotes(sample_quotes, tag="HUMOR")
        assert len(result) == 2

    def test_filter_by_author(self, sample_quotes):
        result = filter_quotes(sample_quotes, author="Einstein")
        assert len(result) == 1
        assert result[0].author == "Albert Einstein"

    def test_filter_by_author_partial_match(self, sample_quotes):
        result = filter_quotes(sample_quotes, author="john")
        assert len(result) == 1
        assert result[0].author == "John Lennon"

    def test_filter_by_tag_and_author(self, sample_quotes):
        result = filter_quotes(sample_quotes, tag="humor", author="Einstein")
        assert len(result) == 1

    def test_filter_no_match_returns_empty(self, sample_quotes):
        result = filter_quotes(sample_quotes, tag="nonexistent")
        assert result == []

    def test_no_filter_returns_all(self, sample_quotes):
        result = filter_quotes(sample_quotes)
        assert len(result) == len(sample_quotes)


# ── Export ────────────────────────────────────────────────────────

class TestExport:
    def test_save_csv_creates_file(self, tmp_path, sample_quotes):
        path = str(tmp_path / "out.csv")
        save_csv(sample_quotes, path)
        assert Path(path).exists()

    def test_save_csv_has_header(self, tmp_path, sample_quotes):
        path = str(tmp_path / "out.csv")
        save_csv(sample_quotes, path)
        with open(path, newline="", encoding="utf-8") as f:
            header = next(csv.reader(f))
        assert header == ["text", "author", "tags"]

    def test_save_csv_row_count(self, tmp_path, sample_quotes):
        path = str(tmp_path / "out.csv")
        save_csv(sample_quotes, path)
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.reader(f))
        assert len(rows) == len(sample_quotes) + 1   # +1 for header

    def test_save_json_creates_file(self, tmp_path, sample_quotes):
        path = str(tmp_path / "out.json")
        save_json(sample_quotes, path)
        assert Path(path).exists()

    def test_save_json_is_valid(self, tmp_path, sample_quotes):
        path = str(tmp_path / "out.json")
        save_json(sample_quotes, path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data) == len(sample_quotes)

    def test_save_json_roundtrip(self, tmp_path, sample_quotes):
        path = str(tmp_path / "out.json")
        save_json(sample_quotes, path)
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert data[0]["author"] == sample_quotes[0].author
        assert data[0]["tags"]   == sample_quotes[0].tags
