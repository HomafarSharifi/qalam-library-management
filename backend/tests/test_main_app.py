import sys
import os
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app, home, health_check


class TestMainApp(unittest.TestCase):

    def test_app_metadata(self):
        self.assertEqual(app.title, "Qalam Library Management API")
        self.assertEqual(app.version, "1.0.0")

    def test_home_endpoint(self):
        res = home()
        self.assertEqual(res["status"], "online")
        self.assertEqual(res["name"], "Qalam Library API")

    @patch("main.get_connection")
    def test_health_check_healthy(self, mock_get_conn):
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn

        res = health_check()
        self.assertEqual(res["status"], "healthy")
        self.assertEqual(res["database"], "connected")
        mock_conn.close.assert_called_once()

    @patch("main.get_connection")
    def test_health_check_degraded(self, mock_get_conn):
        mock_get_conn.side_effect = Exception("Connection timed out")

        res = health_check()
        self.assertEqual(res.status_code, 503)

    def test_routes_registered(self):
        paths = list(app.openapi()["paths"].keys())
        self.assertIn("/", paths)
        self.assertIn("/health", paths)
        self.assertIn("/api/categories", paths)
        self.assertIn("/api/authors", paths)
        self.assertIn("/api/books", paths)
        self.assertIn("/api/members", paths)
        self.assertIn("/api/loans", paths)
        self.assertIn("/api/reports/stats", paths)
        self.assertIn("/api/loans/{loan_id}/return", paths)


if __name__ == "__main__":
    unittest.main()
