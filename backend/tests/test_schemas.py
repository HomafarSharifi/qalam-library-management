import sys
import os
from datetime import date, timedelta
import unittest
from pydantic import ValidationError

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from schemas.categories import CategoryCreate, CategoryUpdate, CategoryResponse
from schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse
from schemas.books import BookCreate, BookUpdate, CopiesUpdate, BookResponse
from schemas.members import MemberCreate, MemberUpdate, MemberResponse
from schemas.loans import LoanIssue, LoanReturn, LoanResponse
from schemas.reports import DashboardStats, TopBookItem, RecentActivityItem, MonthlyActivityItem


class TestSchemas(unittest.TestCase):

    def test_category_validation(self):
        c = CategoryCreate(Name="ادبیات")
        self.assertEqual(c.Name, "ادبیات")

        with self.assertRaises(ValidationError):
            CategoryCreate(Name="")

        cr = CategoryResponse(ID_Category=1, Name="ادبیات", Book_Count=5)
        self.assertEqual(cr.ID_Category, 1)
        self.assertEqual(cr.Book_Count, 5)

    def test_author_validation(self):
        a = AuthorCreate(First_Name="جلال", Last_Name="آل احمد")
        self.assertEqual(a.First_Name, "جلال")
        self.assertEqual(a.Last_Name, "آل احمد")

        ar = AuthorResponse(ID_Authors=1, First_Name="جلال", Last_Name="آل احمد", Book_Count=3)
        self.assertEqual(ar.Full_Name, "جلال آل احمد")

        with self.assertRaises(ValidationError):
            AuthorCreate(First_Name="", Last_Name="آل احمد")

    def test_book_validation(self):
        b = BookCreate(
            Title="مدیر مدرسه",
            ISBN="9789640000011",
            Categories_ID_Category=1,
            Authors_ID_Authors=[1, 2],
            Total_Copies=5
        )
        self.assertEqual(b.Title, "مدیر مدرسه")
        self.assertEqual(b.Total_Copies, 5)

        with self.assertRaises(ValidationError):
            BookCreate(
                Title="کتاب منفی",
                Categories_ID_Category=1,
                Total_Copies=-1
            )

        with self.assertRaises(ValidationError):
            BookCreate(
                Title="",
                Categories_ID_Category=1
            )

        cu = CopiesUpdate(Total_Copies=10)
        self.assertEqual(cu.Total_Copies, 10)

        with self.assertRaises(ValidationError):
            CopiesUpdate(Total_Copies=-3)

    def test_member_validation(self):
        m = MemberCreate(
            First_Name="مینا",
            Last_Name="احمدی",
            Contact="0700123456",
            Email="mina@example.com"
        )
        self.assertEqual(m.First_Name, "مینا")

        mr = MemberResponse(
            ID_Members=1,
            First_Name="مینا",
            Last_Name="احمدی",
            Contact="0700123456",
            Joined_Date=date(2025, 2, 14),
            Active_Loans_Count=2
        )
        self.assertEqual(mr.Full_Name, "مینا احمدی")
        self.assertEqual(mr.Active_Loans_Count, 2)

        with self.assertRaises(ValidationError):
            MemberCreate(First_Name="علی", Last_Name="رضایی", Contact="0")

    def test_loan_validation(self):
        today = date.today()
        tomorrow = today + timedelta(days=1)
        yesterday = today - timedelta(days=1)

        l = LoanIssue(
            Members_ID_Members=1,
            Books_ID_Books=1,
            Loan_date=today,
            Due_date=tomorrow
        )
        self.assertEqual(l.Members_ID_Members, 1)

        with self.assertRaises(ValidationError):
            LoanIssue(
                Members_ID_Members=1,
                Books_ID_Books=1,
                Loan_date=today,
                Due_date=yesterday
            )

        with self.assertRaises(ValidationError):
            LoanIssue(
                Members_ID_Members=1,
                Due_date=tomorrow
            )

        with self.assertRaises(ValidationError):
            LoanReturn(Fine_Amount=-10.0)

    def test_report_validation(self):
        stats = DashboardStats(
            Total_Books=10,
            Total_Members=25,
            Active_Loans=3,
            Overdue_Loans=1,
            Total_Copies=40,
            Available_Copies=37,
            Total_Fines=15.0
        )
        self.assertEqual(stats.Total_Books, 10)
        self.assertEqual(stats.Available_Copies, 37)


if __name__ == "__main__":
    unittest.main()
