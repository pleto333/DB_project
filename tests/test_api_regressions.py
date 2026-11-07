import unittest
from unittest.mock import Mock, patch
from src.api_ai.AI import app
from src.api_ai import gemini, server


def endpoint(path):
    return next(route.endpoint for route in app.routes if route.path == path)


class ApiRegressionTests(unittest.TestCase):
    def test_health(self):
        self.assertEqual(endpoint('/health')(), {'status': 'ok'})

    def test_rest_json(self):
        response = Mock(status_code=200)
        response.json.return_value = {'candidates': [{'content': {'parts': [{'text': '{"recommendations": []}'}]}}]}
        with patch.object(gemini.requests, 'post', return_value=response):
            text = gemini._generate_content_with_rest('test', 'model', 'news')
        self.assertEqual(gemini._parse_gemini_json(text), {'recommendations': []})

    def test_rate_limit(self):
        with patch.object(gemini.requests, 'post', return_value=Mock(status_code=429)):
            with self.assertRaises(gemini.GeminiRateLimitError):
                gemini._generate_content_with_rest('test', 'model', 'news')

    def test_dummy_does_not_write(self):
        with patch.object(server, 'save_analysis_to_db') as save:
            self.assertIn('recommendations', endpoint('/analyze')(server.AnalyzeRequest(use_dummy_ai=True)))
            save.assert_not_called()

    def check_news(self, matched, expected):
        latest = {'analysis_date': '2026-11-07', 'recommendations': [{'stock_code': '005930'}]}
        unrelated = {'published_at': '2026-11-07', 'title': 'Unrelated company'}
        with patch('src.db.database.get_latest_analysis_json', return_value=latest), patch('src.db.database.get_news_by_stock', return_value=matched), patch('src.db.database.get_latest_news_articles', return_value=[unrelated]) as fallback:
            self.assertEqual(endpoint('/stocks/{code}/news')('005930', 'Samsung'), {'articles': expected})
            fallback.assert_not_called()

    def test_no_unrelated_fallback(self):
        self.check_news([], [])

    def test_old_news_filtered(self):
        self.check_news([{'published_at': '2026-11-06'}], [])

    def test_current_related_news_kept(self):
        article = {'published_at': '2026-11-07', 'title': 'Samsung'}
        self.check_news([article], [article])


if __name__ == '__main__':
    unittest.main()
