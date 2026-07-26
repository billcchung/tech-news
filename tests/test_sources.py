import unittest
from urllib.parse import urlsplit

from news_fetcher.sources import SOURCES
from news_fetcher.taxonomy import CATEGORIES, TAGS
from news_fetcher.policy import is_allowed_article_url


class SourceConfigurationTests(unittest.TestCase):
    def test_sources_are_unique_https_feeds_with_allowed_hosts(self):
        names = [source.name for source in SOURCES]

        self.assertEqual(len(names), len(set(names)))
        for source in SOURCES:
            self.assertEqual(urlsplit(source.feed_url).scheme, "https")
            self.assertTrue(source.allowed_hosts)
            self.assertIn(source.category, CATEGORIES)
            self.assertTrue(set(source.default_tags) <= set(TAGS))

    def test_source_list_matches_the_curated_catalogue(self):
        names = {source.name for source in SOURCES}
        self.assertEqual(
            names,
            {
                "AWS Blog",
                "Google Cloud Blog",
                "Azure Blog",
                "Kubernetes Blog",
                "CNCF",
                "HashiCorp Blog",
                "DevOps.com",
                "OpenAI News",
                "Hugging Face Blog",
                "Ars Technica",
                "MIT Technology Review",
                "IEEE Spectrum",
                "InfoQ",
                "Cloudflare Blog",
                "GitHub Engineering",
                "Netflix TechBlog",
                "Mozilla Hacks",
                "KrebsOnSecurity",
                "Google Project Zero",
                "Google DeepMind",
            },
        )

    def test_project_zero_accepts_its_current_article_host(self):
        source = next(source for source in SOURCES if source.name == "Google Project Zero")
        self.assertTrue(
            is_allowed_article_url(
                "https://projectzero.google/2026/05/pixel-10-exploit.html",
                source.allowed_hosts,
            )
        )


if __name__ == "__main__":
    unittest.main()
