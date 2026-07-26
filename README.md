# Tech News

Static technology-news aggregator with curated direct feeds, controlled categories and tags, and a monthly historical archive. GitHub Actions tests the Python pipeline and browser module, updates the JSON data, commits archive changes, and deploys to GitHub Pages.

The project uses the Python standard library and browser-native JavaScript. It needs no API keys, package installation, or build step.

## Structure

```text
news_fetcher/sources.py          curated source configuration
news_fetcher/taxonomy.py         category, tag, and keyword rules
news_fetcher/articles.py         canonical URLs and stable article IDs
news_fetcher/feed_parser.py      RSS and Atom parsing
news_fetcher/policy.py           article-host allowlist
news_fetcher/aggregation.py      concurrent collection and deduplication
news_fetcher/archive.py          monthly partitions and archive manifest
news_fetcher/backfill.py         committed-history conversion
news_fetcher/cli.py              daily update and atomic output
scripts/fetch_news.py            daily command-line entry point
scripts/backfill_archive.py      one-time history backfill
site/app.mjs                     tested browser filtering and archive loading
site/index.html                  static interface
site/news.json                   current articles
site/archive/YYYY-MM.json        monthly article partitions
site/archive/index.json          archive month manifest
tests/                           Python tests
tests_js/                        Node tests
.github/workflows/update-news.yml
```

## Sources

| Category | Sources |
|---|---|
| AI & ML | OpenAI News, Hugging Face Blog, Google DeepMind |
| Cloud & Infrastructure | AWS Blog, Google Cloud Blog, Azure Blog, Cloudflare Blog |
| DevOps & Reliability | Kubernetes Blog, CNCF, HashiCorp Blog, DevOps.com |
| Software Engineering | GitHub Engineering, Netflix TechBlog, Mozilla Hacks, InfoQ |
| Security & Privacy | KrebsOnSecurity, Google Project Zero |
| Hardware & Emerging Tech | IEEE Spectrum |
| General Tech | Ars Technica, MIT Technology Review |

Only direct feeds from technology publications, vendors, and foundations are included. Each source has an article-host allowlist. Aggregator feeds that forward arbitrary publishers are excluded.

Source records also define default tags. Title and publisher-excerpt keywords add tags from a controlled vocabulary in `news_fetcher/taxonomy.py`.

## Archive

The daily command merges accepted articles into `site/archive/YYYY-MM.json`. Publication dates select the month; undated articles use the date they were first observed. Stable URL hashes prevent duplicates across runs.

`site/archive/index.json` lists months and article counts. The browser loads one month at a time and combines month, category, tag, and text filters.

To rebuild available history from committed versions of `site/news.json`:

```bash
python3 scripts/backfill_archive.py site/archive
```

The backfill reads Git history without changing it. Repeating the command is safe.

## Local use

Run both test suites:

```bash
python3 -m unittest discover -s tests -v
node --test tests_js/*.test.mjs
```

Fetch current news and update the archive:

```bash
python3 scripts/fetch_news.py site/news.json site/archive
```

Serve the static site:

```bash
cd site
python3 -m http.server 8000
```

Open `http://localhost:8000`.

## GitHub setup

1. Set Pages to use GitHub Actions in repository settings.
2. Give Actions read and write workflow permissions.
3. Run the `Update news and deploy` workflow once.

The workflow runs daily at 06:00 UTC and on pushes to `main`.

## Failure behavior

- One failed source does not stop accepted sources.
- Unavailable sources appear in the page status.
- A run with no accepted articles preserves current and archived data.
- Malformed existing archive JSON stops the update before replacing `news.json`.
- JSON files use temporary sibling files and atomic replacement.

RSS descriptions remain publisher-provided excerpts. Generated summaries and deep-dive content are not part of the current system.
