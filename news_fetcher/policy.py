from typing import Tuple
from urllib.parse import urlsplit


def is_allowed_article_url(url: str, allowed_hosts: Tuple[str, ...]) -> bool:
    parsed = urlsplit(url)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return False
    hostname = parsed.hostname.lower().rstrip(".")
    return any(
        hostname == allowed.lower().rstrip(".")
        or hostname.endswith("." + allowed.lower().rstrip("."))
        for allowed in allowed_hosts
    )
