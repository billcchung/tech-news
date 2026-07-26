import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from .archive import build_partitions, load_partitions, write_archive
from .articles import enrich_article
from .sources import SOURCES


Runner = Callable[..., subprocess.CompletedProcess]


def read_git_snapshots(
    repo: Path,
    news_path: str = "site/news.json",
    runner: Runner = subprocess.run,
) -> Tuple[List[dict], List[str]]:
    log_result = runner(
        ["git", "log", "--format=%H", "--", news_path],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    if log_result.returncode != 0:
        raise RuntimeError(log_result.stderr.strip() or "git log failed")
    snapshots = []
    warnings = []
    for commit in filter(None, log_result.stdout.splitlines()):
        show_result = runner(
            ["git", "show", f"{commit}:{news_path}"],
            cwd=repo,
            capture_output=True,
            text=True,
        )
        if show_result.returncode != 0:
            warnings.append(f"{commit}: {show_result.stderr.strip() or 'git show failed'}")
            continue
        try:
            snapshots.append(json.loads(show_result.stdout))
        except json.JSONDecodeError:
            warnings.append(f"{commit}: invalid JSON")
    return snapshots, warnings


def backfill_snapshots(
    snapshots: Sequence[dict],
    archive_dir: Path,
    now: datetime,
    initial_warnings: Optional[Sequence[str]] = None,
) -> Dict[str, object]:
    warnings = list(initial_warnings or ())
    valid = []
    for position, snapshot in enumerate(snapshots):
        try:
            updated, items = _normalize_snapshot(snapshot)
        except (KeyError, TypeError, ValueError) as error:
            warnings.append(f"snapshot {position}: {error}")
            continue
        valid.append((updated, items))
    valid.sort(key=lambda entry: entry[0])

    incoming = [item for _, items in valid for item in items]
    existing = load_partitions(archive_dir)
    partitions = build_partitions(existing, incoming)
    write_archive(archive_dir, partitions, now)
    return {
        "snapshot_count": len(valid),
        "article_count": sum(len(items) for items in partitions.values()),
        "warnings": warnings,
    }


def _normalize_snapshot(snapshot: dict) -> Tuple[datetime, List[dict]]:
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be an object")
    updated = _parse_timestamp(snapshot["updated"])
    raw_items = snapshot["items"]
    if not isinstance(raw_items, list):
        raise ValueError("items must be a list")
    sources = {source.name: source for source in SOURCES}
    normalized = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            raise ValueError("article must be an object")
        source_name = raw_item.get("source")
        source = sources.get(str(source_name))
        if source is None:
            raise ValueError(f"unknown source: {source_name}")
        for field in ("title", "link", "summary", "published"):
            if field not in raw_item:
                raise ValueError(f"article missing field: {field}")
        candidate = {
            "title": raw_item["title"],
            "link": raw_item["link"],
            "summary": raw_item["summary"],
            "source": source.name,
            "category": source.category,
            "default_tags": source.default_tags,
            "published": raw_item["published"],
        }
        normalized.append(enrich_article(candidate, updated))
    return updated, normalized


def _parse_timestamp(raw: object) -> datetime:
    if not isinstance(raw, str):
        raise ValueError("updated must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("updated must be an ISO timestamp") from error
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)
