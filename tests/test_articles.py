import unittest
from datetime import datetime, timezone

from news_fetcher.articles import article_id, canonicalize_url, enrich_article


class ArticleTests(unittest.TestCase):
    def test_canonicalize_url_removes_fragment_tracking_and_trailing_slash(self):
        self.assertEqual(
            canonicalize_url(
                "HTTPS://Example.COM/post/?utm_source=rss&keep=1&ref=home#comments"
            ),
            "https://example.com/post?keep=1",
        )

    def test_canonicalize_url_sorts_preserved_query_parameters(self):
        self.assertEqual(
            canonicalize_url("https://example.com/post?z=2&a=1"),
            "https://example.com/post?a=1&z=2",
        )

    def test_article_id_is_stable_for_tracking_variants(self):
        self.assertEqual(
            article_id("https://example.com/post?utm_medium=rss"),
            article_id("https://example.com/post"),
        )

    def test_enrich_article_adds_stable_metadata(self):
        first_seen = datetime(2026, 7, 26, 6, 0, tzinfo=timezone.utc)
        article = enrich_article(
            {
                "title": "Kubernetes security release",
                "link": "https://example.com/post",
                "summary": "Open source fixes",
                "source": "Example",
                "category": "Security & Privacy",
                "default_tags": ("open-source",),
                "published": "2026-07-25T10:00:00+00:00",
            },
            first_seen,
        )

        self.assertEqual(article["first_seen"], first_seen.isoformat())
        self.assertEqual(article["tags"], ["kubernetes", "open-source", "security"])
        self.assertEqual(len(article["id"]), 64)
        self.assertNotIn("default_tags", article)


if __name__ == "__main__":
    unittest.main()
