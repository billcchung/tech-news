# Tech News Taxonomy and Archive Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Expand the curated feed catalogue to twenty sources, add controlled article categories and tags, retain articles in monthly archives, and provide tested archive browsing on GitHub Pages.

**Architecture:** Source configuration owns stable categories and default tags. An enrichment module derives canonical URLs, IDs, and keyword tags; an archive module merges enriched articles into monthly JSON partitions and derives the manifest. The current feed stays at `site/news.json`, while browser logic in `site/app.mjs` loads current or archived datasets and applies combined filters.

**Tech Stack:** Python 3.12 standard library, JavaScript ES modules, Node built-in test runner, RSS/Atom, static JSON, GitHub Actions, GitHub Pages

## Global Constraints

- The site remains static and requires no API keys or third-party services.
- Exactly twenty curated direct feeds are configured.
- Categories and tags come only from the controlled vocabularies in the accepted specification.
- Generated summaries and deep-dive content are excluded.
- Monthly archive files have no retention limit.
- Python and JavaScript tests run before every fetch and deployment.

---

### Task 1: Source catalogue and taxonomy

**Files:**
- Modify: `news_fetcher/models.py`
- Modify: `news_fetcher/sources.py`
- Create: `news_fetcher/taxonomy.py`
- Modify: `tests/test_sources.py`
- Create: `tests/test_taxonomy.py`

**Interfaces:**
- Produces: `Source(name: str, category: str, feed_url: str, allowed_hosts: tuple[str, ...], default_tags: tuple[str, ...])`
- Produces: `CATEGORIES: tuple[str, ...]`
- Produces: `TAGS: tuple[str, ...]`
- Produces: `infer_tags(title: str, summary: str, default_tags: Sequence[str]) -> list[str]`

- [ ] **Step 1: Write failing source and taxonomy tests**

```python
def test_sources_use_controlled_categories_and_tags(self):
    self.assertEqual(len(SOURCES), 20)
    for source in SOURCES:
        self.assertIn(source.category, CATEGORIES)
        self.assertTrue(set(source.default_tags) <= set(TAGS))

def test_infer_tags_combines_defaults_and_keyword_matches(self):
    self.assertEqual(
        infer_tags("Kubernetes security release", "", ("open-source",)),
        ["kubernetes", "open-source", "security"],
    )

def test_infer_tags_uses_word_boundaries(self):
    self.assertEqual(infer_tags("A new painting tool", "", ()), [])
```

- [ ] **Step 2: Run focused tests and confirm the expected failures**

Run: `python3 -m unittest tests.test_sources tests.test_taxonomy -v`

Expected: import or constructor failures because taxonomy constants, tag inference, and `default_tags` do not exist.

- [ ] **Step 3: Add the controlled vocabularies, explicit keyword expressions, updated existing-source assignments, and seven approved feeds**

Use the exact category, feed, host, and default-tag tables from `docs/superpowers/specs/2026-07-26-taxonomy-and-archive-design.md`. `infer_tags` must join title and summary, compare case-insensitively, union matches with defaults, and return sorted values.

- [ ] **Step 4: Run the focused tests**

Run: `python3 -m unittest tests.test_sources tests.test_taxonomy -v`

Expected: all source and taxonomy tests pass.

- [ ] **Step 5: Commit**

```bash
git add news_fetcher/models.py news_fetcher/sources.py news_fetcher/taxonomy.py tests/test_sources.py tests/test_taxonomy.py
git commit -m "feat: add curated source taxonomy"
```

### Task 2: Stable article enrichment

**Files:**
- Create: `news_fetcher/articles.py`
- Modify: `news_fetcher/aggregation.py`
- Modify: `tests/test_aggregation.py`
- Create: `tests/test_articles.py`

**Interfaces:**
- Consumes: `Source`, `infer_tags`
- Produces: `canonicalize_url(url: str) -> str`
- Produces: `article_id(url: str) -> str`
- Produces: `enrich_article(item: Mapping[str, object], first_seen: datetime) -> dict[str, object]`
- Changes: `aggregate(...)` returns enriched articles with `id`, `tags`, and `first_seen`

- [ ] **Step 1: Write failing canonicalization and enrichment tests**

```python
def test_canonicalize_url_removes_fragment_and_tracking_parameters(self):
    self.assertEqual(
        canonicalize_url("HTTPS://Example.com/post/?utm_source=x&keep=1#comments"),
        "https://example.com/post?keep=1",
    )

def test_article_id_is_stable_for_tracking_variants(self):
    self.assertEqual(
        article_id("https://example.com/post?utm_medium=rss"),
        article_id("https://example.com/post"),
    )

def test_aggregate_adds_tags_and_first_seen(self):
    result = aggregate((self.source,), self.reader, self.now)
    self.assertEqual(result["items"][0]["first_seen"], self.now.isoformat())
    self.assertIn("security", result["items"][0]["tags"])
```

- [ ] **Step 2: Run focused tests and confirm failures**

Run: `python3 -m unittest tests.test_articles tests.test_aggregation -v`

Expected: missing `news_fetcher.articles` and absent enriched fields.

- [ ] **Step 3: Implement canonicalization, SHA-256 IDs, and enrichment**

Tracking parameters are `utm_source`, `utm_medium`, `utm_campaign`, `utm_term`, `utm_content`, `ref`, and `source`. Preserve other query parameters in sorted order. Reuse the canonical URL for deduplication.

- [ ] **Step 4: Run focused tests**

Run: `python3 -m unittest tests.test_articles tests.test_aggregation -v`

Expected: all article and aggregation tests pass.

- [ ] **Step 5: Commit**

```bash
git add news_fetcher/articles.py news_fetcher/aggregation.py tests/test_articles.py tests/test_aggregation.py
git commit -m "feat: enrich articles with stable metadata"
```

### Task 3: Monthly archive store

**Files:**
- Create: `news_fetcher/archive.py`
- Create: `tests/test_archive.py`

**Interfaces:**
- Produces: `article_month(article: Mapping[str, object]) -> str`
- Produces: `merge_articles(existing: Sequence[dict], incoming: Sequence[dict]) -> list[dict]`
- Produces: `build_partitions(existing: Mapping[str, Sequence[dict]], incoming: Sequence[dict]) -> dict[str, list[dict]]`
- Produces: `build_manifest(partitions: Mapping[str, Sequence[dict]], updated: datetime) -> dict`
- Produces: `load_partitions(archive_dir: Path) -> dict[str, list[dict]]`
- Produces: `write_archive(archive_dir: Path, partitions: Mapping[str, Sequence[dict]], updated: datetime) -> None`

- [ ] **Step 1: Write failing archive behavior tests**

```python
def test_undated_article_uses_first_seen_month(self):
    article = {"published": None, "first_seen": "2026-07-26T06:00:00+00:00"}
    self.assertEqual(article_month(article), "2026-07")

def test_merge_is_idempotent_and_preserves_first_seen(self):
    merged = merge_articles([self.old], [self.updated])
    self.assertEqual(len(merged), 1)
    self.assertEqual(merged[0]["first_seen"], self.old["first_seen"])
    self.assertEqual(merged[0]["summary"], self.updated["summary"])

def test_manifest_counts_partitions_newest_first(self):
    manifest = build_manifest({"2026-06": [self.old], "2026-07": [self.updated]}, self.now)
    self.assertEqual(
        manifest["months"],
        [{"month": "2026-07", "count": 1}, {"month": "2026-06", "count": 1}],
    )
```

- [ ] **Step 2: Run archive tests and confirm the missing-module failure**

Run: `python3 -m unittest tests.test_archive -v`

Expected: failure because `news_fetcher.archive` does not exist.

- [ ] **Step 3: Implement validated loading, merge rules, partition building, derived manifests, and atomic writes**

Reject partition filenames or payload months that do not match `YYYY-MM`. Validate required article fields before returning loaded data. Write changed partitions before `index.json`.

- [ ] **Step 4: Run archive tests**

Run: `python3 -m unittest tests.test_archive -v`

Expected: all archive tests pass.

- [ ] **Step 5: Commit**

```bash
git add news_fetcher/archive.py tests/test_archive.py
git commit -m "feat: add monthly news archive"
```

### Task 4: Archive-aware CLI and historical backfill

**Files:**
- Modify: `news_fetcher/cli.py`
- Create: `news_fetcher/backfill.py`
- Create: `scripts/backfill_archive.py`
- Modify: `tests/test_cli.py`
- Create: `tests/test_backfill.py`

**Interfaces:**
- Consumes: aggregation payloads and archive functions
- Produces: `update_outputs(news_path: Path, archive_dir: Path, payload: dict) -> None`
- Produces: `read_git_snapshots(repo: Path, news_path: str, run_git: Callable[..., CompletedProcess]) -> tuple[list[dict], list[str]]`
- Produces: `backfill(repo: Path, archive_dir: Path, snapshots: Sequence[dict]) -> dict`
- Changes: CLI accepts optional archive path, defaulting to `site/archive`

- [ ] **Step 1: Write failing CLI and backfill tests**

```python
def test_update_outputs_merges_current_items_into_archive(self):
    update_outputs(self.news_path, self.archive_dir, self.payload)
    month = json.loads((self.archive_dir / "2026-07.json").read_text())
    self.assertEqual([item["id"] for item in month["items"]], ["article-1"])

def test_malformed_archive_preserves_existing_news(self):
    (self.archive_dir / "2026-07.json").write_text("{bad")
    with self.assertRaises(ValueError):
        update_outputs(self.news_path, self.archive_dir, self.payload)
    self.assertEqual(self.news_path.read_text(), "existing")

def test_backfill_deduplicates_articles_across_snapshots(self):
    result = backfill(self.repo, self.archive_dir, [self.older_snapshot, self.newer_snapshot])
    self.assertEqual(result["article_count"], 1)
```

- [ ] **Step 2: Run focused tests and confirm failures**

Run: `python3 -m unittest tests.test_cli tests.test_backfill -v`

Expected: missing backfill module and missing archive output behavior.

- [ ] **Step 3: Implement archive-aware output and the read-only Git-history backfill command**

The backfill subprocess uses `git log --format=%H -- site/news.json` and `git show <commit>:site/news.json`. Invalid snapshots add a warning and do not stop valid snapshots.

- [ ] **Step 4: Run focused tests and the full Python suite**

Run: `python3 -m unittest tests.test_cli tests.test_backfill -v`

Run: `python3 -m unittest discover -s tests -v`

Expected: all Python tests pass.

- [ ] **Step 5: Commit**

```bash
git add news_fetcher/cli.py news_fetcher/backfill.py scripts/backfill_archive.py tests/test_cli.py tests/test_backfill.py
git commit -m "feat: integrate archive updates and backfill"
```

### Task 5: Archive browser and filter module

**Files:**
- Create: `site/app.mjs`
- Modify: `site/index.html`
- Create: `tests_js/app.test.mjs`

**Interfaces:**
- Produces: `filterItems(items, {category, tag, query}) -> Array`
- Produces: `categoryCounts(items) -> Array<{name, count}>`
- Produces: `availableTags(items) -> Array<{name, count}>`
- Produces: `groupByDay(items) -> Array<{day, items}>`
- Produces: `archivePath(month) -> string`
- Browser behavior: current/archive loading preserves rendered data on fetch failure

- [ ] **Step 1: Write failing JavaScript tests**

```javascript
test('combines category tag and text filters', () => {
  const result = filterItems(items, {
    category: 'Security & Privacy',
    tag: 'security',
    query: 'browser',
  });
  assert.deepEqual(result.map(item => item.id), ['security-browser']);
});

test('rejects unsafe archive month paths', () => {
  assert.throws(() => archivePath('../news'), /Invalid archive month/);
  assert.equal(archivePath('2026-07'), 'archive/2026-07.json');
});
```

- [ ] **Step 2: Run JavaScript tests and confirm the missing-module failure**

Run: `/Users/vanish/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests_js/*.test.mjs`

Expected: failure because `site/app.mjs` does not exist.

- [ ] **Step 3: Implement pure filter helpers, dataset loading, category counts, tag chips, month selection, date grouping, and publisher-excerpt labeling**

Use DOM node creation for article links and text. Do not insert article data through `innerHTML`.

- [ ] **Step 4: Run JavaScript tests**

Run: `/Users/vanish/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests_js/*.test.mjs`

Expected: all JavaScript tests pass.

- [ ] **Step 5: Commit**

```bash
git add site/app.mjs site/index.html tests_js/app.test.mjs
git commit -m "feat: add archive and taxonomy browsing"
```

### Task 6: CI, documentation, live data, and deployment

**Files:**
- Modify: `.github/workflows/update-news.yml`
- Modify: `README.md`
- Modify: `site/news.json`
- Create: `site/archive/index.json`
- Create: `site/archive/YYYY-MM.json` files produced by backfill

**Interfaces:**
- Consumes: stable Python and JavaScript test commands
- Produces: daily archive updates, documented maintenance commands, deployed static archive

- [ ] **Step 1: Add the Node test command and archive files to the workflow commit step**

The workflow runs `node --test tests_js/*.test.mjs` after Python tests and stages `site/news.json site/archive` after fetching.

- [ ] **Step 2: Update README**

Document the twenty sources, category/tag behavior, monthly archive files, backfill command, both test commands, and the deferred generated-content scope.

- [ ] **Step 3: Backfill committed history and run a live fetch**

Run: `python3 scripts/backfill_archive.py site/archive`

Run: `python3 scripts/fetch_news.py site/news.json site/archive`

Expected: archive partitions and `index.json` are created, current data contains twenty configured source names when feeds have entries, and no article violates its source host policy.

- [ ] **Step 4: Run final verification**

Run: `python3 -m unittest discover -s tests -v`

Run: `/Users/vanish/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node --test tests_js/*.test.mjs`

Run: `PYTHONPYCACHEPREFIX=/tmp/tech-news-pyc python3 -m py_compile scripts/*.py news_fetcher/*.py`

Run: `python3 -m json.tool site/news.json`

Run: `git diff --check`

Expected: zero failures, valid Python and JSON, and no whitespace errors.

- [ ] **Step 5: Review the accepted specification line by line and correct omissions**

Confirm source count, taxonomy, article contract, monthly archive format, backfill, frontend behavior, failure preservation, test coverage, and the 240-item cap.

- [ ] **Step 6: Commit, push, and monitor**

```bash
git add .github/workflows/update-news.yml README.md site/news.json site/archive
git commit -m "docs: document taxonomy and archive"
git push origin main
gh run watch <run-id> --exit-status
```

Expected: GitHub Actions tests, fetches, commits generated files, and deploys Pages successfully with no annotations.
