from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Callable, Dict, List, Sequence
from urllib.parse import urlsplit, urlunsplit

from .feed_parser import parse_feed
from .models import Source
from .policy import is_allowed_article_url


class NoArticlesError(RuntimeError):
    """Raised when an aggregation run has no acceptable articles."""


def fetch_source(
    source: Source,
    read_url: Callable[[str], bytes],
    max_items: int,
) -> List[Dict[str, object]]:
    items = []
    for entry in parse_feed(read_url(source.feed_url)):
        if not entry.title or not is_allowed_article_url(entry.link, source.allowed_hosts):
            continue
        items.append(
            {
                "title": entry.title[:300],
                "link": entry.link,
                "summary": entry.summary[:400],
                "source": source.name,
                "category": source.category,
                "published": entry.published.isoformat() if entry.published else None,
            }
        )
        if len(items) >= max_items:
            break
    return items


def aggregate(
    sources: Sequence[Source],
    read_url: Callable[[str], bytes],
    now: datetime,
    max_per_feed: int = 15,
    max_total: int = 120,
) -> Dict[str, object]:
    items_by_source = {}
    failed_names = set()
    worker_count = min(6, max(1, len(sources)))
    with ThreadPoolExecutor(max_workers=worker_count) as pool:
        futures = {
            pool.submit(fetch_source, source, read_url, max_per_feed): source
            for source in sources
        }
        for future in as_completed(futures):
            source = futures[future]
            try:
                source_items = future.result()
                items_by_source[source.name] = source_items
                if not source_items:
                    failed_names.add(source.name)
            except Exception:
                failed_names.add(source.name)

    all_items = [
        item
        for source in sources
        for item in items_by_source.get(source.name, [])
    ]
    all_items.sort(key=lambda item: item["published"] or "0000", reverse=True)

    seen = set()
    deduplicated = []
    for item in all_items:
        canonical_url = _canonical_url(str(item["link"]))
        if canonical_url in seen:
            continue
        seen.add(canonical_url)
        deduplicated.append(item)

    if not deduplicated:
        raise NoArticlesError("all feeds failed or produced no acceptable articles")

    return {
        "updated": now.isoformat(),
        "failed_sources": [source.name for source in sources if source.name in failed_names],
        "items": deduplicated[:max_total],
    }


def _canonical_url(url: str) -> str:
    parsed = urlsplit(url)
    return urlunsplit(
        (
            parsed.scheme.lower(),
            parsed.netloc.lower(),
            parsed.path.rstrip("/") or "/",
            parsed.query,
            "",
        )
    )
