import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from typing import Iterator, Optional

from .models import FeedEntry


ATOM = "{http://www.w3.org/2005/Atom}"


def strip_html(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", unescape(without_tags)).strip()


def parse_date(raw: str) -> Optional[datetime]:
    if not raw:
        return None
    raw = raw.strip()
    try:
        parsed = parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        try:
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_feed(xml_bytes: bytes) -> Iterator[FeedEntry]:
    root = ET.fromstring(xml_bytes)
    if root.tag == f"{ATOM}feed":
        yield from _parse_atom(root)
    else:
        yield from _parse_rss(root)


def _parse_atom(root: ET.Element) -> Iterator[FeedEntry]:
    for entry in root.findall(f"{ATOM}entry"):
        link = ""
        for candidate in entry.findall(f"{ATOM}link"):
            if candidate.get("rel", "alternate") == "alternate":
                link = candidate.get("href", "")
                break
        yield FeedEntry(
            title=strip_html(entry.findtext(f"{ATOM}title", "")),
            link=link.strip(),
            summary=strip_html(
                entry.findtext(f"{ATOM}summary", "")
                or entry.findtext(f"{ATOM}content", "")
            ),
            published=parse_date(
                entry.findtext(f"{ATOM}published", "")
                or entry.findtext(f"{ATOM}updated", "")
            ),
        )


def _parse_rss(root: ET.Element) -> Iterator[FeedEntry]:
    for item in root.iter("item"):
        yield FeedEntry(
            title=strip_html(item.findtext("title", "")),
            link=(item.findtext("link") or "").strip(),
            summary=strip_html(item.findtext("description", "")),
            published=parse_date(item.findtext("pubDate", "")),
        )

