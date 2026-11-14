import sys
import os
import unittest
from datetime import date, timedelta
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.mock_db import MockDatabaseState, MockConnection
from routers.loans import (
    get_loans,
    get_loan,
    issue_loan,
    return_loan,
    delete_loan
)
from schemas.loans import LoanIssue, LoanReturn


class TestLoansRouter(unittest.TestCase):
    def setUp(self):
        self.state = MockDatabaseState()
        self.state.seed_sample_data()
        self.db = MockConnection(self.state)

    def test_get_loans_all(self):
        loans = get_loans(db=self.db)
        self.assertEqual(len(loans), 2)
        l1 = next(l for l in loans if l["ID_Loans"] == 1)
        self.assertEqual(l1["Status"], "active")
        self.assertFalse(l1["Is_Overdue"])

        l2 = next(l for l in loans if l["ID_Loans"] == 2)
        self.assertEqual(l2["Status"], "returned")

    def test_get_loans_filtered_active(self):
        active = get_loans(status="active", db=self.db)
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["ID_Loans"], 1)

    def test_get_loans_filtered_returned(self):
        returned = get_loans(status="returned", db=self.db)
        self.assertEqual(len(returned), 1)
        self.assertEqual(returned[0]["ID_Loans"], 2)

    def test_get_loan_by_id_success(self):
        loan = get_loan(1, db=self.db)
        self.assertEqual(loan["ID_Loans"], 1)
        self.assertEqual(loan["Book_Title"], "مدیر مدرسه")
        self.assertEqual(loan["Member_Name"], "مینا احمدی")

    def test_get_loan_by_id_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            get_loan(999, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_issue_loan_success_decrements_available_copies(self):
        initial_avail = self.state.copies[2]["Available_Copies"]
        payload = LoanIssue(
            Members_ID_Members=1,
            Books_ID_Books=2,
            Loan_date=date.today(),
            Due_date=date.today() + timedelta(days=14)
        )
        issued = issue_loan(payload, db=self.db)
        self.assertIn("ID_Loans", issued)
        self.assertEqual(issued["Members_ID_Members"], 1)
        self.assertEqual(self.state.copies[2]["Available_Copies"], initial_avail - 1)

    def test_issue_loan_invalid_member(self):
        payload = LoanIssue(
            Members_ID_Members=999,
            Books_ID_Books=1,
            Due_date=date.today() + timedelta(days=7)
        )
        with self.assertRaises(HTTPException) as ctx:
            issue_loan(payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Member with ID 999 not found", ctx.exception.detail)

    def test_issue_loan_no_available_copies(self):
        self.state.copies[1]["Available_Copies"] = 0
        payload = LoanIssue(
            Members_ID_Members=1,
            Books_ID_Books=1,
            Due_date=date.today() + timedelta(days=7)
        )
        with self.assertRaises(HTTPException) as ctx:
            issue_loan(payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("No available copies", ctx.exception.detail)

    def test_return_loan_success_increments_available_copies(self):
        initial_avail = self.state.copies[1]["Available_Copies"]
        res = return_loan(1, return_data=LoanReturn(), db=self.db)
        self.assertEqual(res["ID_Loans"], 1)
        self.assertEqual(res["Status"], "returned")
        self.assertEqual(self.state.copies[1]["Available_Copies"], initial_avail + 1)

    def test_return_loan_calculates_overdue_fine(self):
        self.state.loans[1]["Due_date"] = date.today() - timedelta(days=4)
        res = return_loan(1, return_data=LoanReturn(Return_date=date.today()), db=self.db)
        self.assertEqual(res["Fine_Amount"], 20.0)
        self.assertEqual(res["Status"], "returned")

    def test_return_loan_prevent_double_return(self):
        with self.assertRaises(HTTPException) as ctx:
            return_loan(2, return_data=LoanReturn(), db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("already been returned", ctx.exception.detail)

    def test_delete_active_loan_restores_available_copies(self):
        initial_avail = self.state.copies[1]["Available_Copies"]
        res = delete_loan(1, db=self.db)
        self.assertEqual(res["ID_Loans"], 1)
        self.assertEqual(self.state.copies[1]["Available_Copies"], initial_avail + 1)

    def test_delete_returned_loan_does_not_double_restore_copies(self):
        initial_avail = self.state.copies[2]["Available_Copies"]
        res = delete_loan(2, db=self.db)
        self.assertEqual(res["ID_Loans"], 2)
        self.assertEqual(self.state.copies[2]["Available_Copies"], initial_avail)


if __name__ == "__main__":
    unittest.main()
