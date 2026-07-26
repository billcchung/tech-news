import unittest

from news_fetcher.taxonomy import infer_tags


class TaxonomyTests(unittest.TestCase):
    def test_infer_tags_combines_defaults_and_keyword_matches(self):
        self.assertEqual(
            infer_tags(
                "Kubernetes security release",
                "An open source update",
                ("open-source",),
            ),
            ["kubernetes", "open-source", "security"],
        )

    def test_infer_tags_uses_word_boundaries(self):
        self.assertEqual(infer_tags("A new painting tool", "", ()), [])

    def test_infer_tags_matches_summary_case_insensitively(self):
        self.assertEqual(
            infer_tags("", "POSTGRESQL adds new SQL support", ()),
            ["databases"],
        )

    def test_infer_tags_rejects_unknown_defaults(self):
        with self.assertRaises(ValueError):
            infer_tags("", "", ("unknown",))


if __name__ == "__main__":
    unittest.main()
