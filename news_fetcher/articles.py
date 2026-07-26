import hashlib
from datetime import datetime
from typing import Dict, Mapping
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .taxonomy import infer_tags


TRACKING_PARAMETERS = {
    "ref",
    "source",
    "utm_campaign",
    "utm_content",
    "utm_medium",
    "utm_source",
    "utm_term",
}


def canonicalize_url(url: str) -> str:
    parsed = urlsplit(url)
    hostname = (parsed.hostname or "").lower()
    if parsed.port:
        hostname = f"{hostname}:{parsed.port}"
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(
        sorted(
            (key, value)
            for key, value in parse_qsl(parsed.query, keep_blank_values=True)
            if key.lower() not in TRACKING_PARAMETERS
        )
    )
    return urlunsplit((parsed.scheme.lower(), hostname, path, query, ""))


def article_id(url: str) -> str:
    return hashlib.sha256(canonicalize_url(url).encode("utf-8")).hexdigest()


def enrich_article(
    item: Mapping[str, object],
    first_seen: datetime,
) -> Dict[str, object]:
    enriched = dict(item)
    defaults = tuple(enriched.pop("default_tags", ()))
    enriched["id"] = article_id(str(enriched["link"]))
    enriched["tags"] = infer_tags(
        str(enriched.get("title", "")),
        str(enriched.get("summary", "")),
        defaults,
    )
    enriched["first_seen"] = first_seen.isoformat()
    return enriched
