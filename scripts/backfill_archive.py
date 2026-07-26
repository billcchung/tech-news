#!/usr/bin/env python3
"""Build monthly archive files from committed news.json snapshots."""

import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from news_fetcher.backfill import backfill_snapshots, read_git_snapshots  # noqa: E402


def main() -> int:
    archive_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "site" / "archive"
    snapshots, warnings = read_git_snapshots(ROOT)
    result = backfill_snapshots(
        snapshots,
        archive_dir,
        datetime.now(timezone.utc),
        initial_warnings=warnings,
    )
    for warning in result["warnings"]:
        print(f"WARN {warning}", file=sys.stderr)
    print(
        f"Backfilled {result['article_count']} articles from "
        f"{result['snapshot_count']} snapshots into {archive_dir}"
    )
    return 0 if result["snapshot_count"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
