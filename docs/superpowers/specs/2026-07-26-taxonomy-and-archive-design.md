# Tech News Taxonomy and Archive

**Status:** Accepted
**Date:** 2026-07-26

## Context

The site currently publishes one rolling `site/news.json` file from thirteen direct technology feeds. Each source has one broad category, articles have no tags, and every daily run replaces the previous dataset. RSS descriptions are displayed when available. Generated summaries and deep-dive content are outside this release.

The site must remain static, run on GitHub Pages, and update in GitHub Actions without API keys or third-party services.

## Decision

Add seven technically focused direct feeds, replace the current category names with a controlled taxonomy, attach deterministic tags to every article, and preserve articles in monthly JSON archive partitions.

The application remains a Python standard-library data pipeline with a dependency-free browser frontend. Browser filtering logic moves into a JavaScript module so it can be tested with Node's built-in test runner.

## Options considered

### Monthly JSON partitions

Store each article once in `site/archive/YYYY-MM.json` and publish a small archive manifest. This keeps archive requests bounded, works directly on GitHub Pages, and produces reviewable generated files. This is the selected option.

### Daily snapshots

Store one complete feed response per day. This is simple but duplicates articles across many files and grows the repository faster.

### SQLite with static export

Maintain a SQLite database and export files during deployment. This offers richer queries but adds a second source of truth and a build stage that the current scale does not require.

## Source catalogue

The existing thirteen feeds remain. Add these seven sources:

| Source | Category | Feed | Allowed article hosts | Default tags |
|---|---|---|---|---|
| Cloudflare Blog | Cloud & Infrastructure | `https://blog.cloudflare.com/rss/` | `blog.cloudflare.com` | `cloud`, `networking`, `security`, `web` |
| GitHub Engineering | Software Engineering | `https://github.blog/engineering/feed/` | `github.blog` | `dev-tools`, `open-source`, `programming` |
| Netflix TechBlog | Software Engineering | `https://netflixtechblog.com/feed` | `netflixtechblog.com` | `architecture`, `databases`, `programming` |
| Mozilla Hacks | Software Engineering | `https://hacks.mozilla.org/feed/` | `hacks.mozilla.org` | `open-source`, `programming`, `web` |
| KrebsOnSecurity | Security & Privacy | `https://krebsonsecurity.com/feed/` | `krebsonsecurity.com` | `privacy`, `security` |
| Google Project Zero | Security & Privacy | `https://googleprojectzero.blogspot.com/feeds/posts/default` | `googleprojectzero.blogspot.com`, `projectzero.googleblog.com`, `projectzero.google` | `research`, `security` |
| Google DeepMind | AI & ML | `https://deepmind.google/blog/rss.xml` | `deepmind.google` | `ai`, `research` |

The existing sources use these assignments:

| Source | Category | Default tags |
|---|---|---|
| AWS Blog | Cloud & Infrastructure | `cloud` |
| Google Cloud Blog | Cloud & Infrastructure | `cloud` |
| Azure Blog | Cloud & Infrastructure | `cloud` |
| Kubernetes Blog | DevOps & Reliability | `cloud-native`, `kubernetes`, `open-source` |
| CNCF | DevOps & Reliability | `cloud-native`, `open-source` |
| HashiCorp Blog | DevOps & Reliability | `cloud`, `dev-tools` |
| DevOps.com | DevOps & Reliability | `dev-tools`, `observability` |
| OpenAI News | AI & ML | `ai`, `research` |
| Hugging Face Blog | AI & ML | `ai`, `open-source` |
| Ars Technica | General Tech | none |
| MIT Technology Review | General Tech | `research` |
| IEEE Spectrum | Hardware & Emerging Tech | `hardware`, `research` |
| InfoQ | Software Engineering | `architecture`, `programming` |

Source records gain `default_tags: tuple[str, ...]`. Zero default tags are allowed for broad publications. Configuration tests lock the exact source set, require HTTPS feeds, and verify categories and tags against their controlled vocabularies.

## Categories and tags

Every source has exactly one category:

- `AI & ML`
- `Cloud & Infrastructure`
- `DevOps & Reliability`
- `Software Engineering`
- `Security & Privacy`
- `Hardware & Emerging Tech`
- `General Tech`

The controlled tag vocabulary is:

- `ai`
- `architecture`
- `cloud`
- `cloud-native`
- `databases`
- `dev-tools`
- `hardware`
- `kubernetes`
- `networking`
- `observability`
- `open-source`
- `privacy`
- `programming`
- `research`
- `security`
- `web`

An article begins with its source's default tags. A deterministic keyword matcher inspects the title and RSS description and adds matching tags from the same vocabulary. Tags are unique and sorted. Rules are explicit regular expressions with word boundaries; unknown terms never create new tags.

The keyword groups are:

| Tag | Terms |
|---|---|
| `ai` | AI, artificial intelligence, machine learning, LLM, inference |
| `architecture` | architecture, distributed system, microservice, serverless |
| `cloud` | AWS, Azure, Google Cloud, cloud computing |
| `cloud-native` | cloud native, cloud-native, container, CNCF |
| `databases` | database, SQL, PostgreSQL, MySQL, data warehouse |
| `dev-tools` | GitHub, GitLab, IDE, compiler, developer tool, CI/CD |
| `hardware` | chip, semiconductor, CPU, GPU, quantum computing, robot |
| `kubernetes` | Kubernetes, K8s |
| `networking` | DNS, HTTP, network, TCP, TLS, CDN |
| `observability` | observability, telemetry, tracing, monitoring |
| `open-source` | open source, open-source |
| `privacy` | privacy, surveillance, tracking |
| `programming` | programming language, Python, Rust, Java, JavaScript, TypeScript, Go |
| `research` | research, paper, benchmark |
| `security` | security, vulnerability, exploit, malware, ransomware, CVE |
| `web` | browser, WebAssembly, Wasm, CSS, HTML, web platform |

## Article data model

Generated articles use this contract:

```json
{
  "id": "sha256 hex digest of the canonical URL",
  "title": "Article title",
  "link": "https://approved-source.example/article",
  "summary": "Publisher-provided RSS excerpt",
  "source": "Source name",
  "category": "Software Engineering",
  "tags": ["architecture", "programming"],
  "published": "2026-07-26T01:00:00+00:00",
  "first_seen": "2026-07-26T06:00:00+00:00"
}
```

The canonical URL removes fragments, lowercases scheme and host, and removes known tracking parameters before hashing and deduplication. `first_seen` records the first feed run that observed the article and never changes.

## Archive format

`site/news.json` remains the current-feed endpoint and uses the expanded article contract.

`site/archive/YYYY-MM.json` contains:

```json
{
  "month": "2026-07",
  "updated": "2026-07-26T06:00:00+00:00",
  "items": []
}
```

Articles are assigned to their publication month. Undated articles use their `first_seen` month. Items are unique by `id` and sorted newest first.

When an existing article appears again, the archive preserves its original `first_seen`. The newest observation refreshes its title, link, summary, source, category, and tags. A non-null existing publication date is retained if a later observation omits it.

`site/archive/index.json` contains:

```json
{
  "updated": "2026-07-26T06:00:00+00:00",
  "months": [
    {"month": "2026-07", "count": 240}
  ]
}
```

Months are sorted newest first. The archive has no retention limit.

## Update and backfill flow

The daily update performs these steps:

1. Fetch up to twelve accepted articles from each configured source.
2. Add stable IDs, categories, tags, and `first_seen`.
3. Load existing monthly partitions and merge articles idempotently.
4. Stage changed archive partitions, the manifest, and `news.json` in temporary sibling files.
5. Replace archive partitions first, then the manifest, then `news.json`.
6. Commit all generated files in the existing GitHub Actions step.

If a process stops during replacement, a later run repairs the manifest from the partition files. A malformed existing archive aborts the update and preserves the existing files.

A one-time backfill command reads committed versions of `site/news.json`, uses each payload's `updated` value as `first_seen`, deduplicates by article ID, and writes the monthly partitions. Snapshots with invalid JSON or missing required article fields are reported and skipped. The backfill command never modifies Git history.

## Frontend

The page adds:

- category buttons with item counts
- tag chips limited to tags present in the loaded dataset
- a month selector with `Current` followed by archived months
- combined search, category, and tag filtering
- article grouping by publication day

Selecting an archived month loads only its monthly file. Changing back to `Current` reloads `news.json`. Invalid or failed archive requests display an error without removing the previously loaded articles.

The existing RSS description remains labeled as a publisher excerpt. The article title continues to link to the original publication.

## Error handling

Source failures remain isolated and appear in the page status. An update with no accepted current articles does not replace current or archive data. Archive JSON validation happens before writes. Archive month values must match `YYYY-MM` before they are used to construct browser paths.

The archive manifest is derived from partition contents rather than incremented counters, preventing count drift.

## Testing

Python tests cover:

- exact source configuration, feed hosts, categories, and default tags
- keyword matching, word boundaries, sorted tags, and unknown terms
- canonical URLs, stable IDs, tracking-parameter removal, and deduplication
- publication-month assignment and undated fallback
- idempotent archive merges and `first_seen` preservation
- manifest ordering and derived counts
- backfill across duplicate historical snapshots and invalid snapshots
- CLI success, total-feed failure, malformed archive handling, and atomic file replacement

JavaScript tests cover:

- combined category, tag, and text filters
- available tag and category counts
- publication-day grouping
- validated archive paths
- preservation of the current dataset when an archive request fails

GitHub Actions runs `python -m unittest discover -s tests -v` and `node --test tests_js/*.test.mjs` before fetching or deploying.

## Scale and follow-up

Twenty sources at twelve entries each cap a run at 240 current articles. Monthly partitions should remain small enough for direct browser loading at this scale. If a monthly file exceeds 2 MB, revisit weekly partitions or pagination.

Generated summaries and deep-dive content remain deferred. A future content-generation feature must have its own design, cost limit, attribution policy, and failure behavior.
