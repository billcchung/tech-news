# Curated Tech Sources Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent non-technology publishers from entering the site, add four respected direct technology feeds, and make the fetcher modular and tested.

**Architecture:** A `news_fetcher` package separates curated configuration, XML parsing, URL policy, concurrent aggregation, and atomic output. The existing script remains a thin entry point so GitHub Actions and local commands keep the same interface.

**Tech Stack:** Python 3.12 standard library, `unittest`, RSS/Atom XML, GitHub Actions, static HTML/JSON

## Global Constraints

- Only direct feeds operated by technology publications, technology vendors, or technology foundations are eligible.
- Every article host must match the configured source host or one of its subdomains.
- Hacker News is removed; Ars Technica Technology Lab, MIT Technology Review, IEEE Spectrum, and InfoQ are added.
- Automated tests make no network requests.
- Existing `python scripts/fetch_news.py site/news.json` usage remains valid.

---

### Task 1: Feed parsing and source policy

**Files:**
- Create: `news_fetcher/__init__.py`
- Create: `news_fetcher/models.py`
- Create: `news_fetcher/feed_parser.py`
- Create: `news_fetcher/policy.py`
- Create: `tests/__init__.py`
- Create: `tests/fixtures/rss.xml`
- Create: `tests/fixtures/atom.xml`
- Create: `tests/test_feed_parser.py`
- Create: `tests/test_policy.py`

**Interfaces:**
- Produces: `FeedEntry(title: str, link: str, summary: str, published: Optional[datetime])`
- Produces: `parse_feed(xml_bytes: bytes) -> Iterator[FeedEntry]`
- Produces: `is_allowed_article_url(url: str, allowed_hosts: tuple[str, ...]) -> bool`

- [ ] Write parser tests for RSS, Atom, HTML cleanup, and both date formats using local fixtures.
- [ ] Run `python3 -m unittest tests.test_feed_parser tests.test_policy -v` and verify imports fail because package modules do not exist.
- [ ] Implement the immutable entry model, parser helpers, and exact/subdomain host checks. Reject non-HTTP schemes, missing hosts, and deceptive suffixes such as `infoq.com.example.org`.
- [ ] Re-run the focused tests and verify they pass.

### Task 2: Curated source configuration

**Files:**
- Create: `news_fetcher/sources.py`
- Create: `tests/test_sources.py`

**Interfaces:**
- Produces: `Source(name: str, category: str, feed_url: str, allowed_hosts: tuple[str, ...])`
- Produces: `SOURCES: tuple[Source, ...]`

- [ ] Write tests asserting source names are unique, Hacker News is absent, the four selected publications are present, feed URLs use HTTPS, and allowed hosts are non-empty.
- [ ] Run `python3 -m unittest tests.test_sources -v` and verify it fails because source configuration is missing.
- [ ] Add the existing direct technology feeds and four selected publication feeds as immutable source records.
- [ ] Re-run the source tests and verify they pass.

### Task 3: Aggregation service

**Files:**
- Create: `news_fetcher/aggregation.py`
- Create: `tests/test_aggregation.py`

**Interfaces:**
- Consumes: `Source`, `parse_feed`, and `is_allowed_article_url`
- Produces: `fetch_source(source: Source, read_url: Callable[[str], bytes], max_items: int) -> list[dict]`
- Produces: `aggregate(sources: Sequence[Source], read_url: Callable[[str], bytes], now: datetime, max_per_feed: int = 15, max_total: int = 120) -> dict`
- Produces: `NoArticlesError`

- [ ] Write tests for host rejection, per-source caps, URL deduplication, newest-first ordering, partial failures, and total failure.
- [ ] Run `python3 -m unittest tests.test_aggregation -v` and verify the missing module causes failure.
- [ ] Implement concurrent source collection with an injectable reader, deterministic failed-source ordering, normalized URL deduplication, and JSON-ready timestamps.
- [ ] Re-run aggregation tests and verify they pass.

### Task 4: Atomic CLI and stable entry point

**Files:**
- Create: `news_fetcher/cli.py`
- Create: `tests/test_cli.py`
- Replace: `scripts/fetch_news.py`

**Interfaces:**
- Consumes: `aggregate` and `SOURCES`
- Produces: `write_payload(path: Path, payload: dict) -> None`
- Produces: `main(argv: Optional[Sequence[str]] = None) -> int`

- [ ] Write tests proving successful JSON output replaces the destination and a total aggregation failure preserves an existing destination.
- [ ] Run `python3 -m unittest tests.test_cli -v` and verify it fails because the CLI module is missing.
- [ ] Implement urllib reading, atomic sibling-file replacement, exit codes, and the thin script delegate.
- [ ] Re-run CLI tests and then `python3 -m unittest discover -s tests -v`; verify all tests pass.

### Task 5: CI, documentation, and generated data

**Files:**
- Modify: `.github/workflows/update-news.yml`
- Modify: `README.md`
- Modify: `site/news.json`

**Interfaces:**
- Consumes: stable script command from Task 4
- Produces: tested daily update workflow and current curated site data

- [ ] Add `python -m unittest discover -s tests -v` before the fetch step in GitHub Actions.
- [ ] Update README structure, source policy, source list, test command, failure behavior, and source-addition instructions.
- [ ] Run `python3 scripts/fetch_news.py site/news.json` as a live smoke test and verify the output contains no Hacker News or Sportico items.
- [ ] Run `python3 -m unittest discover -s tests -v`, `python3 -m py_compile scripts/fetch_news.py news_fetcher/*.py`, and a JSON validation command.
- [ ] Review the diff against every design requirement and correct any omissions before completion.
