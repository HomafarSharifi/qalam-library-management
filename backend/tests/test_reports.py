import sys
import os
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.mock_db import MockDatabaseState, MockConnection
from routers.reports import (
    get_dashboard_stats,
    get_top_books,
    get_recent_activity,
    get_overdue_report,
    get_monthly_activity
)


class TestReportsRouter(unittest.TestCase):
    def setUp(self):
        self.state = MockDatabaseState()
        self.state.seed_sample_data()
        self.db = MockConnection(self.state)

    def test_dashboard_stats(self):
        stats = get_dashboard_stats(db=self.db)
        self.assertEqual(stats["Total_Books"], 2)
        self.assertEqual(stats["Total_Members"], 2)
        self.assertEqual(stats["Active_Loans"], 1)
        self.assertEqual(stats["Total_Copies"], 8)
        self.assertEqual(stats["Available_Copies"], 6)

    def test_top_books(self):
        top = get_top_books(limit=5, db=self.db)
        self.assertGreaterEqual(len(top), 1)
        self.assertIn("Title", top[0])
        self.assertIn("Loan_Count", top[0])

    def test_recent_activity(self):
        recent = get_recent_activity(limit=5, db=self.db)
        self.assertEqual(len(recent), 2)
        self.assertIn("Book_Title", recent[0])
        self.assertIn("Member_Name", recent[0])
        self.assertIn("Status", recent[0])

    def test_overdue_report(self):
        self.state.loans[1]["Due_date"] = date.today() - timedelta(days=5)
        overdue = get_overdue_report(db=self.db)
        self.assertEqual(len(overdue), 1)
        self.assertEqual(overdue[0]["Days_Overdue"], 5)
        self.assertEqual(overdue[0]["Estimated_Fine"], 25.0)

    def test_monthly_activity(self):
        activity = get_monthly_activity(months=6, db=self.db)
        self.assertIsInstance(activity, list)
        self.assertGreaterEqual(len(activity), 1)
        self.assertIn("Month", activity[0])
        self.assertIn("Loans_Count", activity[0])


if __name__ == "__main__":
    unittest.main()
