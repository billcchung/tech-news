import json
import subprocess
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from news_fetcher.backfill import backfill_snapshots, read_git_snapshots


def snapshot(updated, summary):
    return {
        "updated": updated,
        "failed_sources": [],
        "items": [
            {
                "title": "Architecture update",
                "link": "https://www.infoq.com/news/example?utm_source=rss",
                "summary": summary,
                "source": "InfoQ",
                "category": "Tech",
                "published": "2026-07-10T10:00:00+00:00",
            }
        ],
    }


class BackfillTests(unittest.TestCase):
    def test_backfill_deduplicates_snapshots_and_preserves_first_seen(self):
        snapshots = [
            snapshot("2026-07-12T06:00:00+00:00", "new"),
            snapshot("2026-07-10T06:00:00+00:00", "old"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            archive_dir = Path(directory)

            result = backfill_snapshots(
                snapshots,
                archive_dir,
                datetime(2026, 7, 26, 6, 0, tzinfo=timezone.utc),
            )

            payload = json.loads((archive_dir / "2026-07.json").read_text())
            self.assertEqual(result["article_count"], 1)
            self.assertEqual(payload["items"][0]["first_seen"], "2026-07-10T06:00:00+00:00")
            self.assertEqual(payload["items"][0]["summary"], "new")
            self.assertEqual(payload["items"][0]["category"], "Software Engineering")
            self.assertIn("architecture", payload["items"][0]["tags"])

    def test_backfill_skips_invalid_snapshot_and_reports_warning(self):
        snapshots = [{"updated": "bad", "items": "not-a-list"}, snapshot("2026-07-10T06:00:00+00:00", "ok")]
        with tempfile.TemporaryDirectory() as directory:
            result = backfill_snapshots(
                snapshots,
                Path(directory),
                datetime(2026, 7, 26, 6, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(result["snapshot_count"], 1)
        self.assertEqual(len(result["warnings"]), 1)

    def test_backfill_keeps_valid_articles_when_snapshot_contains_removed_source(self):
        mixed = snapshot("2026-07-10T06:00:00+00:00", "valid")
        mixed["items"].append(
            {
                "title": "Aggregator item",
                "link": "https://example.com/aggregated",
                "summary": "removed",
                "source": "Hacker News",
                "category": "Tech",
                "published": "2026-07-10T09:00:00+00:00",
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            result = backfill_snapshots(
                [mixed],
                Path(directory),
                datetime(2026, 7, 26, 6, 0, tzinfo=timezone.utc),
            )

        self.assertEqual(result["snapshot_count"], 1)
        self.assertEqual(result["article_count"], 1)
        self.assertEqual(len(result["warnings"]), 1)
        self.assertIn("unknown source: Hacker News", result["warnings"][0])

    def test_read_git_snapshots_reports_unreadable_commit(self):
        responses = {
            ("log", "--format=%H", "--", "site/news.json"): subprocess.CompletedProcess(
                [], 0, stdout="good\nbad\n", stderr=""
            ),
            ("show", "good:site/news.json"): subprocess.CompletedProcess(
                [], 0, stdout=json.dumps(snapshot("2026-07-10T06:00:00+00:00", "ok")), stderr=""
            ),
            ("show", "bad:site/news.json"): subprocess.CompletedProcess(
                [], 1, stdout="", stderr="missing"
            ),
        }

        def runner(arguments, **_):
            return responses[tuple(arguments[1:])]

        snapshots, warnings = read_git_snapshots(Path("/repo"), runner=runner)

        self.assertEqual(len(snapshots), 1)
        self.assertEqual(warnings, ["bad: missing"])


if __name__ == "__main__":
    unittest.main()
