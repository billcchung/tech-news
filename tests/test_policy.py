import unittest

from news_fetcher.policy import is_allowed_article_url


class ArticleUrlPolicyTests(unittest.TestCase):
    def test_accepts_exact_host_and_subdomain(self):
        allowed = ("infoq.com",)
        self.assertTrue(is_allowed_article_url("https://www.infoq.com/news/2026/07/test/", allowed))
        self.assertTrue(is_allowed_article_url("https://infoq.com/articles/test", allowed))

    def test_rejects_external_deceptive_and_non_http_urls(self):
        allowed = ("infoq.com",)
        self.assertFalse(is_allowed_article_url("https://sportico.com/business/story", allowed))
        self.assertFalse(is_allowed_article_url("https://infoq.com.example.org/story", allowed))
        self.assertFalse(is_allowed_article_url("javascript:alert(1)", allowed))
        self.assertFalse(is_allowed_article_url("/relative/story", allowed))


if __name__ == "__main__":
    unittest.main()
