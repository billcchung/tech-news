#!/usr/bin/env python3
"""Fetch tech news from RSS/Atom feeds and write news.json.

Stdlib only — no pip installs needed in CI.
"""
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html import unescape
from pathlib import Path

FEEDS = [
    # (name, category, url)
    ("AWS Blog",          "Cloud",      "https://aws.amazon.com/blogs/aws/feed/"),
    ("Google Cloud Blog", "Cloud",      "https://cloudblog.withgoogle.com/rss/"),
    ("Azure Blog",        "Cloud",      "https://azure.microsoft.com/en-us/blog/feed/"),
    ("Kubernetes Blog",   "DevOps/SRE", "https://kubernetes.io/feed.xml"),
    ("CNCF",              "DevOps/SRE", "https://www.cncf.io/feed/"),
    ("HashiCorp Blog",    "DevOps/SRE", "https://www.hashicorp.com/blog/feed.xml"),
    ("DevOps.com",        "DevOps/SRE", "https://devops.com/feed/"),
    ("OpenAI News",       "AI",         "https://openai.com/news/rss.xml"),
    ("Hugging Face Blog", "AI",         "https://huggingface.co/blog/feed.xml"),
    ("Hacker News",       "Tech",       "https://hnrss.org/frontpage"),
]

MAX_PER_FEED = 15
MAX_TOTAL = 120
ATOM = "{http://www.w3.org/2005/Atom}"
TIMEOUT = 30
UA = "Mozilla/5.0 (compatible; tech-news-bot/1.0; +https://github.com)"


def strip_html(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", text or "")
    return re.sub(r"\s+", " ", unescape(text)).strip()


def parse_date(raw: str):
    """Parse RFC822 (RSS) or ISO8601 (Atom) dates; return aware UTC datetime or None."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        dt = parsedate_to_datetime(raw)
    except (ValueError, TypeError):
        try:
            dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def parse_feed(xml_bytes: bytes):
    """Yield dicts with title/link/summary/date from RSS 2.0 or Atom XML."""
    root = ET.fromstring(xml_bytes)
    if root.tag == f"{ATOM}feed":  # Atom
        for entry in root.findall(f"{ATOM}entry"):
            link = ""
            for l in entry.findall(f"{ATOM}link"):
                if l.get("rel", "alternate") == "alternate":
                    link = l.get("href", "")
                    break
            yield {
                "title": strip_html(entry.findtext(f"{ATOM}title", "")),
                "link": link,
                "summary": strip_html(
                    entry.findtext(f"{ATOM}summary", "")
                    or entry.findtext(f"{ATOM}content", "")
                ),
                "date": parse_date(
                    entry.findtext(f"{ATOM}published", "")
                    or entry.findtext(f"{ATOM}updated", "")
                ),
            }
    else:  # RSS 2.0 (channel/item)
        for item in root.iter("item"):
            yield {
                "title": strip_html(item.findtext("title", "")),
                "link": (item.findtext("link") or "").strip(),
                "summary": strip_html(item.findtext("description", "")),
                "date": parse_date(item.findtext("pubDate", "")),
            }


def fetch_one(name: str, category: str, url: str):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        data = resp.read()
    items = []
    for entry in parse_feed(data):
        if not entry["title"] or not entry["link"]:
            continue
        items.append({
            "title": entry["title"][:300],
            "link": entry["link"],
            "summary": entry["summary"][:400],
            "source": name,
            "category": category,
            "published": entry["date"].isoformat() if entry["date"] else None,
        })
        if len(items) >= MAX_PER_FEED:
            break
    return items


def main():
    out_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("site/news.json")
    all_items, errors = [], []

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch_one, n, c, u): n for n, c, u in FEEDS}
        for fut in as_completed(futures):
            name = futures[fut]
            try:
                items = fut.result()
                all_items.extend(items)
                print(f"OK   {name}: {len(items)} items")
            except Exception as e:
                errors.append(name)
                print(f"FAIL {name}: {e}", file=sys.stderr)

    # Dedupe by link, newest first (undated items sink to the bottom)
    seen, deduped = set(), []
    for item in all_items:
        if item["link"] not in seen:
            seen.add(item["link"])
            deduped.append(item)
    deduped.sort(key=lambda x: x["published"] or "0000", reverse=True)
    deduped = deduped[:MAX_TOTAL]

    if not deduped:
        print("All feeds failed — refusing to overwrite news.json", file=sys.stderr)
        sys.exit(1)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "updated": datetime.now(timezone.utc).isoformat(),
        "failed_sources": errors,
        "items": deduped,
    }, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(deduped)} items to {out_path} ({len(errors)} feed(s) failed)")


if __name__ == "__main__":
    main()
