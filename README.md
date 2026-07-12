# Tech News

Static news aggregator for Cloud, DevOps/SRE, AI, and general technology. GitHub Actions tests the fetcher, reads curated RSS feeds daily, commits `site/news.json`, and deploys to GitHub Pages. No frameworks, build step, API keys, or third-party Python packages are required.

## Structure

```
news_fetcher/sources.py          # curated direct-feed configuration
news_fetcher/feed_parser.py      # RSS and Atom parsing
news_fetcher/policy.py           # article-host allowlist
news_fetcher/aggregation.py      # concurrent fetch, filtering, sorting, deduplication
news_fetcher/cli.py              # HTTP client and atomic JSON output
scripts/fetch_news.py            # stable command-line entry point
tests/                           # network-free unit and integration tests
site/index.html                  # filters, search, and dark mode
site/news.json                   # generated data committed by CI
.github/workflows/update-news.yml
```

## Sources

Cloud: AWS Blog, Google Cloud Blog, Azure Blog. DevOps/SRE: Kubernetes Blog, CNCF, HashiCorp Blog, DevOps.com. AI: OpenAI News, Hugging Face Blog. Tech: Ars Technica Technology Lab, MIT Technology Review, IEEE Spectrum, InfoQ.

Only direct feeds from technology publications, vendors, and foundations are included. Each source has an article-host allowlist, so a feed cannot forward unrelated third-party publishers. Add or change sources in `news_fetcher/sources.py` and update `tests/test_sources.py` with the intended policy.

## Setup

```bash
cd tech-news-site
git init -b main
git add .
git commit -m "Initial commit"
gh repo create tech-news --public --source=. --push
# or create the repo on github.com and:
# git remote add origin git@github.com:YOUR_USER/tech-news.git && git push -u origin main
```

Then in the repo on GitHub:

1. Settings → Pages → Source: **GitHub Actions**
2. Settings → Actions → General → Workflow permissions: **Read and write permissions**
3. Actions tab → "Update news and deploy" → **Run workflow** (first run; after that it runs daily at 06:00 UTC)

Site appears at `https://YOUR_USER.github.io/tech-news/`.

## Local use

```bash
python3 -m unittest discover -s tests -v
python3 scripts/fetch_news.py site/news.json
cd site && python3 -m http.server 8000
# open http://localhost:8000
```

## Notes

- Schedule is in `.github/workflows/update-news.yml` (`cron: "0 6 * * *"`). GitHub may delay scheduled runs by up to ~15 minutes.
- A feed failure does not stop other sources; unavailable sources appear in the page header.
- The script exits without replacing `news.json` if every feed fails or every item violates its source policy.
- Output replacement is atomic. Items are deduplicated by normalized URL, capped at 15 per feed and 120 total.
