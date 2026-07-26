import json
import os
import sys
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence

from .aggregation import NoArticlesError, aggregate
from .archive import build_partitions, load_partitions, write_archive
from .sources import SOURCES


TIMEOUT = 30
USER_AGENT = "Mozilla/5.0 (compatible; tech-news-bot/2.0; +https://github.com)"


def read_url(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        return response.read()


def write_payload(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(payload, temporary, indent=1, ensure_ascii=False)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def update_outputs(news_path: Path, archive_dir: Path, payload: dict) -> None:
    try:
        updated = datetime.fromisoformat(str(payload["updated"]).replace("Z", "+00:00"))
    except (KeyError, ValueError) as error:
        raise ValueError("payload has an invalid updated timestamp") from error
    existing = load_partitions(archive_dir)
    items = payload.get("items")
    if not isinstance(items, list):
        raise ValueError("payload items must be a list")
    partitions = build_partitions(existing, items)
    write_archive(archive_dir, partitions, updated)
    write_payload(news_path, payload)


def main(argv: Optional[Sequence[str]] = None) -> int:
    arguments = list(argv) if argv is not None else sys.argv[1:]
    output_path = Path(arguments[0]) if arguments else Path("site/news.json")
    archive_path = Path(arguments[1]) if len(arguments) > 1 else output_path.parent / "archive"
    try:
        payload = aggregate(
            SOURCES,
            read_url,
            datetime.now(timezone.utc),
            max_per_feed=12,
            max_total=240,
        )
    except NoArticlesError as error:
        print(f"Fetch failed: {error}; existing output was preserved", file=sys.stderr)
        return 1
    try:
        update_outputs(output_path, archive_path, payload)
    except ValueError as error:
        print(f"Archive update failed: {error}; current output was preserved", file=sys.stderr)
        return 1
    print(
        f"Wrote {len(payload['items'])} items to {output_path} "
        f"and {archive_path} ({len(payload['failed_sources'])} feed(s) failed)"
    )
    return 0
