import unittest
from urllib.parse import urlsplit

from news_fetcher.sources import SOURCES


class SourceConfigurationTests(unittest.TestCase):
    def test_sources_are_unique_https_feeds_with_allowed_hosts(self):
        names = [source.name for source in SOURCES]

        self.assertEqual(len(names), len(set(names)))
        for source in SOURCES:
            self.assertEqual(urlsplit(source.feed_url).scheme, "https")
            self.assertTrue(source.allowed_hosts)

    def test_source_list_excludes_aggregators_and_adds_selected_publications(self):
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
            },
        )


if __name__ == "__main__":
    unittest.main()
