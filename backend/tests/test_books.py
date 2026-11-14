import sys
import os
import unittest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.mock_db import MockDatabaseState, MockConnection
from routers.books import (
    get_books,
    get_book,
    create_book,
    update_book,
    update_book_copies,
    delete_book
)
from schemas.books import BookCreate, BookUpdate, CopiesUpdate


class TestBooksRouter(unittest.TestCase):
    def setUp(self):
        self.state = MockDatabaseState()
        self.state.seed_sample_data()
        self.db = MockConnection(self.state)

    def test_get_books(self):
        books = get_books(db=self.db)
        self.assertEqual(len(books), 2)
        b1 = next(b for b in books if b["ID_Books"] == 1)
        self.assertEqual(b1["Title"], "مدیر مدرسه")
        self.assertEqual(b1["Category_Name"], "ادبیات")
        self.assertEqual(b1["Total_Copies"], 5)
        self.assertEqual(b1["Available_Copies"], 4)
        self.assertIn(1, b1["Authors_ID_Authors"])

    def test_get_book_by_id_success(self):
        book = get_book(1, db=self.db)
        self.assertEqual(book["ID_Books"], 1)
        self.assertEqual(book["Title"], "مدیر مدرسه")
        self.assertEqual(book["Authors_Names"], ["جلال آل احمد"])

    def test_get_book_by_id_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            get_book(999, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_create_book_success(self):
        payload = BookCreate(
            Title="تاریخ بیهقی",
            ISBN="9789640000059",
            Description="تاریخ نگاری کهن",
            Categories_ID_Category=2,
            Authors_ID_Authors=[1],
            Total_Copies=10
        )
        created = create_book(payload, db=self.db)
        self.assertEqual(created["Title"], "تاریخ بیهقی")
        self.assertEqual(created["Total_Copies"], 10)
        self.assertEqual(created["Available_Copies"], 10)
        self.assertIn("ID_Books", created)

    def test_create_book_invalid_category(self):
        payload = BookCreate(
            Title="کتاب بدون دسته",
            Categories_ID_Category=999
        )
        with self.assertRaises(HTTPException) as ctx:
            create_book(payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Category with ID 999 does not exist", ctx.exception.detail)

    def test_create_book_invalid_author(self):
        payload = BookCreate(
            Title="کتاب بدون نویسنده معتبر",
            Categories_ID_Category=1,
            Authors_ID_Authors=[999]
        )
        with self.assertRaises(HTTPException) as ctx:
            create_book(payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Author with ID 999 does not exist", ctx.exception.detail)

    def test_create_book_duplicate_isbn(self):
        payload = BookCreate(
            Title="کتاب تکراری",
            ISBN="9789640000011",
            Categories_ID_Category=1
        )
        with self.assertRaises(HTTPException) as ctx:
            create_book(payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("already exists", ctx.exception.detail)

    def test_update_book_success(self):
        payload = BookUpdate(
            Title="مدیر مدرسه - ویرایش جدید",
            ISBN="9789640000011",
            Description="شرح ویرایش شده",
            Categories_ID_Category=1,
            Authors_ID_Authors=[1, 2]
        )
        updated = update_book(1, payload, db=self.db)
        self.assertEqual(updated["Title"], "مدیر مدرسه - ویرایش جدید")
        self.assertEqual(len(updated["Authors_ID_Authors"]), 2)

    def test_update_book_not_found(self):
        payload = BookUpdate(
            Title="کتاب ناموجود",
            Categories_ID_Category=1
        )
        with self.assertRaises(HTTPException) as ctx:
            update_book(999, payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_update_book_copies_success(self):
        payload = CopiesUpdate(Total_Copies=10)
        res = update_book_copies(1, payload, db=self.db)
        self.assertEqual(res["Total_Copies"], 10)
        self.assertEqual(res["Available_Copies"], 9)

    def test_update_book_copies_cannot_reduce_below_borrowed(self):
        payload = CopiesUpdate(Total_Copies=0)
        with self.assertRaises(HTTPException) as ctx:
            update_book_copies(1, payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 400)
        self.assertIn("Cannot reduce total copies below 1", ctx.exception.detail)

    def test_delete_book_conflict_when_copies_on_loan(self):
        with self.assertRaises(HTTPException) as ctx:
            delete_book(1, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("currently on loan", ctx.exception.detail)

    def test_delete_book_success_when_no_active_loans(self):
        res = delete_book(2, db=self.db)
        self.assertEqual(res["ID_Books"], 2)

        with self.assertRaises(HTTPException) as ctx:
            get_book(2, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
