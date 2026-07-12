import unittest
from datetime import datetime, timezone
from pathlib import Path

from news_fetcher.feed_parser import parse_date, parse_feed, strip_html


FIXTURES = Path(__file__).parent / "fixtures"


class FeedParserTests(unittest.TestCase):
    def test_strip_html_unescapes_entities_and_collapses_whitespace(self):
        self.assertEqual(strip_html("<p>A &amp;\n B</p>"), "A & B")

    def test_parse_date_supports_rfc822_and_iso8601(self):
        expected = datetime(2026, 7, 10, 12, 30, tzinfo=timezone.utc)
        self.assertEqual(parse_date("Fri, 10 Jul 2026 12:30:00 GMT"), expected)
        self.assertEqual(parse_date("2026-07-10T12:30:00Z"), expected)
        self.assertIsNone(parse_date("not a date"))

    def test_parse_rss_entry(self):
        entries = list(parse_feed((FIXTURES / "rss.xml").read_bytes()))

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].title, "Cloud & AI")
        self.assertEqual(entries[0].link, "https://example.com/articles/cloud-ai")
        self.assertEqual(entries[0].summary, "A & B")
        self.assertEqual(entries[0].published.isoformat(), "2026-07-10T12:30:00+00:00")

    def test_parse_atom_prefers_alternate_link_and_content(self):
        entries = list(parse_feed((FIXTURES / "atom.xml").read_bytes()))

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].link, "https://example.com/articles/platform-update")
        self.assertEqual(entries[0].summary, "New runtime")
        self.assertEqual(entries[0].published.isoformat(), "2026-07-11T09:15:00+00:00")


if __name__ == "__main__":
    unittest.main()
