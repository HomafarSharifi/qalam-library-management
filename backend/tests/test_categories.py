import sys
import os
import unittest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.mock_db import MockDatabaseState, MockConnection
from routers.categories import (
    get_categories,
    get_category,
    create_category,
    update_category,
    delete_category
)
from schemas.categories import CategoryCreate, CategoryUpdate


class TestCategoriesRouter(unittest.TestCase):
    def setUp(self):
        self.state = MockDatabaseState()
        self.state.seed_sample_data()
        self.db = MockConnection(self.state)

    def test_get_categories(self):
        cats = get_categories(search=None, db=self.db)
        self.assertEqual(len(cats), 2)
        self.assertEqual(cats[0]["Name"], "ادبیات")
        self.assertEqual(cats[0]["Book_Count"], 2)

    def test_get_category_by_id_success(self):
        cat = get_category(1, db=self.db)
        self.assertEqual(cat["ID_Category"], 1)
        self.assertEqual(cat["Name"], "ادبیات")

    def test_get_category_by_id_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            get_category(999, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_create_category_success(self):
        payload = CategoryCreate(Name="علوم")
        created = create_category(payload, db=self.db)
        self.assertEqual(created["Name"], "علوم")
        self.assertIn("ID_Category", created)

    def test_create_category_duplicate_conflict(self):
        payload = CategoryCreate(Name="ادبیات")
        with self.assertRaises(HTTPException) as ctx:
            create_category(payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_update_category_success(self):
        payload = CategoryUpdate(Name="ادبیات داستانی")
        updated = update_category(1, payload, db=self.db)
        self.assertEqual(updated["Name"], "ادبیات داستانی")
        self.assertEqual(updated["ID_Category"], 1)

    def test_update_category_duplicate_conflict(self):
        payload = CategoryUpdate(Name="تاریخ")
        with self.assertRaises(HTTPException) as ctx:
            update_category(1, payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_update_category_not_found(self):
        payload = CategoryUpdate(Name="نامعتبر")
        with self.assertRaises(HTTPException) as ctx:
            update_category(999, payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_delete_category_conflict_when_books_exist(self):
        with self.assertRaises(HTTPException) as ctx:
            delete_category(1, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("belong to this category", ctx.exception.detail)

    def test_delete_category_success_when_no_books(self):
        new_cat = create_category(CategoryCreate(Name="هنر"), db=self.db)
        cat_id = new_cat["ID_Category"]
        res = delete_category(cat_id, db=self.db)
        self.assertEqual(res["ID_Category"], cat_id)

        with self.assertRaises(HTTPException) as ctx:
            get_category(cat_id, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
