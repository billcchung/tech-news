import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from news_fetcher.aggregation import NoArticlesError
from news_fetcher.cli import main, update_outputs, write_payload


def article(article_id="article-1"):
    return {
        "id": article_id,
        "title": "Tech",
        "link": f"https://example.com/{article_id}",
        "summary": "Publisher excerpt",
        "source": "Example",
        "category": "Software Engineering",
        "tags": ["programming"],
        "published": "2026-07-12T07:00:00+00:00",
        "first_seen": "2026-07-12T08:00:00+00:00",
    }


class CliTests(unittest.TestCase):
    def test_write_payload_atomically_replaces_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "nested" / "news.json"
            destination.parent.mkdir()
            destination.write_text("old", encoding="utf-8")

            write_payload(destination, {"items": [{"title": "New"}]})

            self.assertEqual(
                json.loads(destination.read_text(encoding="utf-8")),
                {"items": [{"title": "New"}]},
            )
            self.assertEqual(list(destination.parent.glob(".news.json.*.tmp")), [])

    def test_main_preserves_existing_file_when_aggregation_has_no_articles(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "news.json"
            destination.write_text("existing", encoding="utf-8")

            with patch(
                "news_fetcher.cli.aggregate",
                side_effect=NoArticlesError("nothing fetched"),
            ):
                exit_code = main([str(destination)])

            self.assertEqual(exit_code, 1)
            self.assertEqual(destination.read_text(encoding="utf-8"), "existing")

    def test_main_writes_aggregated_payload(self):
        payload = {
            "updated": "2026-07-12T08:00:00+00:00",
            "failed_sources": [],
            "items": [article()],
        }
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "news.json"

            with patch("news_fetcher.cli.aggregate", return_value=payload):
                exit_code = main([str(destination)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), payload)
            archived = json.loads(
                (destination.parent / "archive" / "2026-07.json").read_text(encoding="utf-8")
            )
            self.assertEqual([item["id"] for item in archived["items"]], ["article-1"])

    def test_update_outputs_preserves_news_when_archive_is_malformed(self):
        payload = {
            "updated": "2026-07-12T08:00:00+00:00",
            "failed_sources": [],
            "items": [article()],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            destination = root / "news.json"
            archive_dir = root / "archive"
            archive_dir.mkdir()
            destination.write_text("existing", encoding="utf-8")
            (archive_dir / "2026-07.json").write_text("{bad", encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "invalid archive JSON"):
                update_outputs(destination, archive_dir, payload)

            self.assertEqual(destination.read_text(encoding="utf-8"), "existing")


if __name__ == "__main__":
    unittest.main()
