# Curated Tech Sources and Fetcher Architecture

**Status:** Accepted
**Date:** 2026-07-12

## Context

The site currently includes Hacker News. Its feed points directly to external publishers, which allowed a Sportico article into the site. The fetcher also combines source configuration, HTTP access, XML parsing, item normalization, aggregation, and file output in one script. There are no automated tests.

The project must remain a small static site with a daily GitHub Actions update. Added sources must be established technology publications, and the source list must stay short.

## Source policy

Only direct feeds operated by technology publications, technology vendors, or technology foundations are eligible. Aggregator feeds that forward arbitrary third-party links are excluded. Source eligibility is enforced in configuration: every parsed article must have the configured source name and an article host allowed by that source.

Hacker News is removed. Four publications are added:

- Ars Technica Technology Lab for general information technology
- MIT Technology Review for technology research and industry coverage
- IEEE Spectrum for engineering and applied technology
- InfoQ for professional software development and architecture

The existing vendor and foundation feeds remain because their scope is directly tied to cloud, DevOps, or AI. The source list is explicit and reviewed in code; there is no automatic source discovery.

## Options considered

### Direct-source allowlist

Configure a small set of direct feeds and validate every article URL against the source's allowed hosts. This prevents an approved feed from silently acting as an aggregator. It is deterministic and easy to test. This is the selected approach.

### Keyword filtering

Keep aggregators and accept articles whose titles or summaries match technology terms. This risks false positives, false negatives, and a growing keyword policy.

### Publisher denylist

Keep aggregators and reject known non-technology domains. This only catches publishers after irrelevant content has appeared and requires continuous maintenance.

## Architecture

The fetcher becomes a small `news_fetcher` package with one responsibility per module:

- `sources.py` defines immutable source records and the curated source list.
- `feed_parser.py` converts RSS or Atom bytes into normalized feed entries.
- `policy.py` validates article URLs against the configured source hosts.
- `aggregation.py` fetches sources concurrently, applies policy, deduplicates articles, sorts them, and builds the output payload.
- `cli.py` parses the output path, runs aggregation, writes JSON atomically, and returns an exit code.
- `scripts/fetch_news.py` remains the stable GitHub Actions entry point and delegates to the package.

The package uses only Python 3.12's standard library. RSS and Atom support already fit the formats used by the selected feeds, so an external parser dependency would add installation and supply-chain cost without a needed capability.

## Data flow and failures

For each configured source, the aggregator downloads the feed, parses entries, rejects entries with missing fields or unapproved article hosts, caps accepted results per feed, and records source-level failures without aborting other work. It then deduplicates by a normalized URL, sorts dated items newest first, caps the total, and returns a JSON-ready payload.

The CLI refuses to replace the output when every feed fails or produces no acceptable items. Successful output is written to a temporary sibling file and replaced atomically, preventing a partial `news.json` if the process is interrupted.

## Test strategy

Tests use `unittest` and local XML fixtures, with injected HTTP readers for aggregation tests. Unit tests cover HTML cleanup, RFC 822 and ISO 8601 dates, RSS and Atom parsing, host policy including subdomains and deceptive suffixes, deduplication, sorting, per-feed limits, partial failures, and all-feed failure. CLI tests cover atomic JSON output and preservation of an existing file on total failure.

No test makes a network request. A separate manual smoke command runs the real fetcher against the configured feeds. GitHub Actions runs the automated suite before generating or deploying data.

## Consequences

Source relevance is controlled by a reviewable allowlist rather than article classification. Adding a source requires a source record and a policy test. The package has more files than the original script, but each boundary can be tested without network access. Standard-library-only execution remains available in GitHub Actions.
