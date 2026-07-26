import json
import os
import re
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Mapping, Sequence


MONTH_PATTERN = re.compile(r"^\d{4}-(?:0[1-9]|1[0-2])$")
ARTICLE_FIELDS = {
    "id",
    "title",
    "link",
    "summary",
    "source",
    "category",
    "tags",
    "published",
    "first_seen",
}


def article_month(article: Mapping[str, object]) -> str:
    timestamp = article.get("published") or article.get("first_seen")
    if not isinstance(timestamp, str) or len(timestamp) < 7:
        raise ValueError("article has no valid published or first_seen timestamp")
    month = timestamp[:7]
    if not MONTH_PATTERN.fullmatch(month):
        raise ValueError(f"invalid article month: {month}")
    return month


def merge_articles(
    existing: Sequence[dict],
    incoming: Sequence[dict],
) -> List[dict]:
    merged: Dict[str, dict] = {}
    for candidate in list(existing) + list(incoming):
        _validate_article(candidate)
        article_id = str(candidate["id"])
        previous = merged.get(article_id)
        if previous is None:
            merged[article_id] = dict(candidate)
            continue
        updated = dict(candidate)
        updated["first_seen"] = previous["first_seen"]
        if updated.get("published") is None and previous.get("published") is not None:
            updated["published"] = previous["published"]
        merged[article_id] = updated
    return sorted(merged.values(), key=_sort_key, reverse=True)


def build_partitions(
    existing: Mapping[str, Sequence[dict]],
    incoming: Sequence[dict],
) -> Dict[str, List[dict]]:
    existing_articles = [
        item
        for month_items in existing.values()
        for item in month_items
    ]
    all_articles = merge_articles(existing_articles, incoming)
    grouped: Dict[str, List[dict]] = {}
    for item in all_articles:
        grouped.setdefault(article_month(item), []).append(item)
    return {month: grouped[month] for month in sorted(grouped)}


def build_manifest(
    partitions: Mapping[str, Sequence[dict]],
    updated: datetime,
) -> dict:
    return {
        "updated": updated.isoformat(),
        "months": [
            {"month": month, "count": len(partitions[month])}
            for month in sorted(partitions, reverse=True)
        ],
    }


def load_partitions(archive_dir: Path) -> Dict[str, List[dict]]:
    if not archive_dir.exists():
        return {}
    partitions: Dict[str, List[dict]] = {}
    for path in sorted(archive_dir.glob("*.json")):
        if path.name == "index.json":
            continue
        month = path.stem
        if not MONTH_PATTERN.fullmatch(month):
            raise ValueError(f"invalid archive filename: {path.name}")
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as error:
            raise ValueError(f"invalid archive JSON: {path}") from error
        if not isinstance(payload, dict) or payload.get("month") != month:
            raise ValueError(f"archive month mismatch: {path}")
        items = payload.get("items")
        if not isinstance(items, list):
            raise ValueError(f"archive items must be a list: {path}")
        for item in items:
            _validate_article(item)
            if article_month(item) != month:
                raise ValueError(f"article stored in wrong archive month: {path}")
        partitions[month] = items
    return partitions


def write_archive(
    archive_dir: Path,
    partitions: Mapping[str, Sequence[dict]],
    updated: datetime,
) -> None:
    archive_dir.mkdir(parents=True, exist_ok=True)
    for month, items in partitions.items():
        if not MONTH_PATTERN.fullmatch(month):
            raise ValueError(f"invalid archive month: {month}")
        for item in items:
            _validate_article(item)
            if article_month(item) != month:
                raise ValueError(f"article assigned to wrong archive month: {month}")
        _write_json(
            archive_dir / f"{month}.json",
            {"month": month, "updated": updated.isoformat(), "items": list(items)},
        )

    expected_files = {f"{month}.json" for month in partitions}
    for path in archive_dir.glob("*.json"):
        if path.name != "index.json" and path.name not in expected_files:
            path.unlink()

    _write_json(archive_dir / "index.json", build_manifest(partitions, updated))


def _validate_article(article: object) -> None:
    if not isinstance(article, dict):
        raise ValueError("archive article must be an object")
    missing = ARTICLE_FIELDS - set(article)
    if missing:
        raise ValueError(f"archive article missing fields: {', '.join(sorted(missing))}")
    if not isinstance(article["tags"], list):
        raise ValueError("archive article tags must be a list")


def _sort_key(article: Mapping[str, object]) -> str:
    return str(article.get("published") or article.get("first_seen") or "")


def _write_json(path: Path, payload: object) -> None:
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
