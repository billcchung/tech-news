import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from news_fetcher.archive import (
    article_month,
    build_manifest,
    build_partitions,
    load_partitions,
    merge_articles,
    write_archive,
)


def article(
    article_id,
    published="2026-07-25T10:00:00+00:00",
    first_seen="2026-07-26T06:00:00+00:00",
    summary="original",
):
    return {
        "id": article_id,
        "title": f"Article {article_id}",
        "link": f"https://example.com/{article_id}",
        "summary": summary,
        "source": "Example",
        "category": "Software Engineering",
        "tags": ["programming"],
        "published": published,
        "first_seen": first_seen,
    }


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 26, 6, 0, tzinfo=timezone.utc)

    def test_article_month_uses_published_date(self):
        self.assertEqual(article_month(article("one", published="2026-06-30T23:00:00+00:00")), "2026-06")

    def test_article_month_uses_first_seen_when_undated(self):
        self.assertEqual(article_month(article("one", published=None)), "2026-07")

    def test_merge_is_idempotent_and_preserves_first_seen(self):
        old = article("same", first_seen="2026-07-01T00:00:00+00:00")
        updated = article(
            "same",
            first_seen="2026-07-26T06:00:00+00:00",
            summary="updated",
        )

        merged = merge_articles([old], [updated, updated])

        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0]["first_seen"], "2026-07-01T00:00:00+00:00")
        self.assertEqual(merged[0]["summary"], "updated")

    def test_merge_keeps_existing_publication_date_when_update_omits_it(self):
        old = article("same", published="2026-06-20T00:00:00+00:00")
        updated = article("same", published=None, summary="updated")

        merged = merge_articles([old], [updated])

        self.assertEqual(merged[0]["published"], "2026-06-20T00:00:00+00:00")

    def test_build_partitions_moves_updated_article_to_its_publication_month(self):
        old = article("same", published=None)
        updated = article("same", published="2026-06-20T00:00:00+00:00")

        partitions = build_partitions({"2026-07": [old]}, [updated])

        self.assertEqual(list(partitions), ["2026-06"])
        self.assertEqual(partitions["2026-06"][0]["id"], "same")

    def test_manifest_counts_partitions_newest_first(self):
        manifest = build_manifest(
            {"2026-06": [article("old")], "2026-07": [article("new")]},
            self.now,
        )

        self.assertEqual(
            manifest["months"],
            [{"month": "2026-07", "count": 1}, {"month": "2026-06", "count": 1}],
        )

    def test_write_and_load_archive_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_dir = Path(directory)
            partitions = {"2026-07": [article("one")]}

            write_archive(archive_dir, partitions, self.now)
            loaded = load_partitions(archive_dir)

            self.assertEqual(loaded, partitions)
            manifest = json.loads((archive_dir / "index.json").read_text())
            self.assertEqual(manifest["months"], [{"month": "2026-07", "count": 1}])
            self.assertEqual(list(archive_dir.glob(".*.tmp")), [])

    def test_load_rejects_malformed_archive_without_rewriting_it(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_dir = Path(directory)
            path = archive_dir / "2026-07.json"
            path.write_text("{bad", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "invalid archive JSON"):
                load_partitions(archive_dir)

            self.assertEqual(path.read_text(encoding="utf-8"), "{bad")

    def test_load_rejects_article_missing_required_fields(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_dir = Path(directory)
            path = archive_dir / "2026-07.json"
            path.write_text(
                json.dumps({"month": "2026-07", "updated": self.now.isoformat(), "items": [{"id": "only"}]}),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(ValueError, "missing fields"):
                load_partitions(archive_dir)

    def test_write_removes_partition_that_is_no_longer_present(self):
        with tempfile.TemporaryDirectory() as directory:
            archive_dir = Path(directory)
            write_archive(
                archive_dir,
                {"2026-06": [article("old", published="2026-06-20T00:00:00+00:00")]},
                self.now,
            )

            write_archive(archive_dir, {"2026-07": [article("new")]}, self.now)

            self.assertFalse((archive_dir / "2026-06.json").exists())
            self.assertTrue((archive_dir / "2026-07.json").exists())


if __name__ == "__main__":
    unittest.main()
