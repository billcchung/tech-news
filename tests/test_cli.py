import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from news_fetcher.aggregation import NoArticlesError
from news_fetcher.cli import main, write_payload


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
            "items": [{"title": "Tech"}],
        }
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "news.json"

            with patch("news_fetcher.cli.aggregate", return_value=payload):
                exit_code = main([str(destination)])

            self.assertEqual(exit_code, 0)
            self.assertEqual(json.loads(destination.read_text(encoding="utf-8")), payload)


if __name__ == "__main__":
    unittest.main()
