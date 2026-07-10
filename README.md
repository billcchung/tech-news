# Tech News

Static news aggregator for Cloud, DevOps/SRE, and AI. GitHub Actions fetches RSS feeds daily, commits `site/news.json`, and deploys to GitHub Pages. No frameworks, no build step, no API keys.

## Structure

```
scripts/fetch_news.py            # stdlib-only feed fetcher → site/news.json
site/index.html                  # single-file frontend (filters, search, dark mode)
site/news.json                   # generated data (committed by CI)
.github/workflows/update-news.yml
```

## Sources

Cloud: AWS Blog, Google Cloud Blog, Azure Blog. DevOps/SRE: Kubernetes Blog, CNCF, HashiCorp, DevOps.com. AI: OpenAI News, Hugging Face Blog. Tech: Hacker News frontpage. Edit the `FEEDS` list in `scripts/fetch_news.py` to change them.

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

## Local test

```bash
python3 scripts/fetch_news.py site/news.json
cd site && python3 -m http.server 8000
# open http://localhost:8000
```

## Notes

- Schedule is in `.github/workflows/update-news.yml` (`cron: "0 6 * * *"`). GitHub may delay scheduled runs by up to ~15 minutes.
- A feed failing doesn't fail the run; failed sources are listed in the page header. The script only errors if **all** feeds fail, so a bad run never wipes existing data.
- Items are deduped by URL, capped at 15/feed and 120 total.
