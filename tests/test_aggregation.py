import unittest
from datetime import datetime, timezone

from news_fetcher.aggregation import NoArticlesError, aggregate, fetch_source
from news_fetcher.models import Source


def rss(*items):
    body = "".join(
        "<item>"
        f"<title>{title}</title>"
        f"<link>{link}</link>"
        f"<description>{summary}</description>"
        f"<pubDate>{published}</pubDate>"
        "</item>"
        for title, link, summary, published in items
    )
    return f"<rss><channel>{body}</channel></rss>".encode()


class AggregationTests(unittest.TestCase):
    def setUp(self):
        self.source_a = Source("Source A", "Tech", "https://feeds.a.test/rss", ("a.test",))
        self.source_b = Source(
            "Source B", "AI", "https://feeds.b.test/rss", ("b.test", "a.test")
        )
        self.now = datetime(2026, 7, 12, 8, 0, tzinfo=timezone.utc)

    def test_fetch_source_rejects_external_hosts_and_applies_limit(self):
        payload = rss(
            ("First", "https://a.test/first", "one", "Sat, 11 Jul 2026 10:00:00 GMT"),
            ("Sport", "https://sportico.com/story", "two", "Sat, 11 Jul 2026 11:00:00 GMT"),
            ("Second", "https://a.test/second", "three", "Sat, 11 Jul 2026 12:00:00 GMT"),
        )

        items = fetch_source(self.source_a, lambda _: payload, max_items=1)

        self.assertEqual([item["title"] for item in items], ["First"])
        self.assertEqual(items[0]["source"], "Source A")

    def test_aggregate_deduplicates_and_sorts_newest_first(self):
        feeds = {
            self.source_a.feed_url: rss(
                ("Older", "https://a.test/shared#comments", "old", "Fri, 10 Jul 2026 10:00:00 GMT"),
            ),
            self.source_b.feed_url: rss(
                ("Newer", "https://b.test/new", "new", "Sat, 11 Jul 2026 10:00:00 GMT"),
                ("Duplicate", "https://a.test/shared", "duplicate", "Sat, 11 Jul 2026 09:00:00 GMT"),
            ),
        }

        result = aggregate((self.source_a, self.source_b), feeds.__getitem__, self.now)

        self.assertEqual([item["title"] for item in result["items"]], ["Newer", "Duplicate"])
        self.assertEqual(result["updated"], self.now.isoformat())
        self.assertEqual(result["items"][0]["first_seen"], self.now.isoformat())
        self.assertEqual(len(result["items"][0]["id"]), 64)
        self.assertIn("tags", result["items"][0])

    def test_aggregate_records_partial_failures_in_source_order(self):
        def reader(url):
            if url == self.source_a.feed_url:
                raise OSError("offline")
            return rss(("Working", "https://b.test/item", "ok", "Sat, 11 Jul 2026 10:00:00 GMT"))

        result = aggregate((self.source_a, self.source_b), reader, self.now)

        self.assertEqual(result["failed_sources"], ["Source A"])
        self.assertEqual(len(result["items"]), 1)

    def test_aggregate_reports_source_when_every_entry_violates_its_host_policy(self):
        feeds = {
            self.source_a.feed_url: rss(
                ("External", "https://sportico.com/story", "sports", "Sat, 11 Jul 2026 10:00:00 GMT"),
            ),
            self.source_b.feed_url: rss(
                ("Working", "https://b.test/item", "tech", "Sat, 11 Jul 2026 11:00:00 GMT"),
            ),
        }

        result = aggregate((self.source_a, self.source_b), feeds.__getitem__, self.now)

        self.assertEqual(result["failed_sources"], ["Source A"])
        self.assertEqual([item["title"] for item in result["items"]], ["Working"])

    def test_aggregate_raises_when_no_source_produces_articles(self):
        def reader(_):
            raise OSError("offline")

        with self.assertRaises(NoArticlesError):
            aggregate((self.source_a, self.source_b), reader, self.now)


if __name__ == "__main__":
    unittest.main()
