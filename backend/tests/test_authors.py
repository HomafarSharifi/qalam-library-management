import sys
import os
import unittest
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.mock_db import MockDatabaseState, MockConnection
from routers.authors import (
    get_authors,
    get_author,
    create_author,
    update_author,
    delete_author
)
from ..schemas.authors import AuthorCreate, AuthorUpdate


class TestAuthorsRouter(unittest.TestCase):
    def setUp(self):
        self.state = MockDatabaseState()
        self.state.seed_sample_data()
        self.db = MockConnection(self.state)

    def test_get_authors(self):
        authors = get_authors(search=None, db=self.db)
        self.assertEqual(len(authors), 2)
        self.assertEqual(authors[0]["First_Name"], "جلال")
        self.assertEqual(authors[0]["Book_Count"], 1)

    def test_get_author_by_id_success(self):
        author = get_author(1, db=self.db)
        self.assertEqual(author["ID_Authors"], 1)
        self.assertEqual(author["First_Name"], "جلال")
        self.assertEqual(author["Last_Name"], "آل احمد")

    def test_get_author_by_id_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            get_author(999, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_create_author_success(self):
        payload = AuthorCreate(First_Name="محمد", Last_Name="غبار")
        created = create_author(payload, db=self.db)
        self.assertEqual(created["First_Name"], "محمد")
        self.assertEqual(created["Last_Name"], "غبار")
        self.assertIn("ID_Authors", created)

    def test_update_author_success(self):
        payload = AuthorUpdate(First_Name="سیمین بانو", Last_Name="دانشور")
        updated = update_author(2, payload, db=self.db)
        self.assertEqual(updated["First_Name"], "سیمین بانو")
        self.assertEqual(updated["ID_Authors"], 2)

    def test_update_author_not_found(self):
        payload = AuthorUpdate(First_Name="تست", Last_Name="تست")
        with self.assertRaises(HTTPException) as ctx:
            update_author(999, payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_delete_author_conflict_when_linked(self):
        with self.assertRaises(HTTPException) as ctx:
            delete_author(1, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("linked to 1 book", ctx.exception.detail)

    def test_delete_author_success_when_unlinked(self):
        new_auth = create_author(AuthorCreate(First_Name="شاعر", Last_Name="ناشناس"), db=self.db)
        a_id = new_auth["ID_Authors"]
        res = delete_author(a_id, db=self.db)
        self.assertEqual(res["ID_Authors"], a_id)

        with self.assertRaises(HTTPException) as ctx:
            get_author(a_id, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
