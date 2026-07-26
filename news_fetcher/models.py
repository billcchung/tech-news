from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple


@dataclass(frozen=True)
class FeedEntry:
    title: str
    link: str
    summary: str
    published: Optional[datetime]


@dataclass(frozen=True)
class Source:
    name: str
    category: str
    feed_url: str
    allowed_hosts: Tuple[str, ...]
    default_tags: Tuple[str, ...] = ()
