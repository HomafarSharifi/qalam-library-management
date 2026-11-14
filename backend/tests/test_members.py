import sys
import os
import unittest
from datetime import date
from fastapi import HTTPException

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.mock_db import MockDatabaseState, MockConnection
from routers.members import (
    get_members,
    get_member,
    create_member,
    update_member,
    delete_member
)
from schemas.members import MemberCreate, MemberUpdate


class TestMembersRouter(unittest.TestCase):
    def setUp(self):
        self.state = MockDatabaseState()
        self.state.seed_sample_data()
        self.db = MockConnection(self.state)

    def test_get_members(self):
        members = get_members(db=self.db)
        self.assertEqual(len(members), 2)
        m1 = next(m for m in members if m["ID_Members"] == 1)
        self.assertEqual(m1["Active_Loans_Count"], 1)
        m2 = next(m for m in members if m["ID_Members"] == 2)
        self.assertEqual(m2["Active_Loans_Count"], 0)

    def test_get_member_by_id_success(self):
        m = get_member(1, db=self.db)
        self.assertEqual(m["ID_Members"], 1)
        self.assertEqual(m["First_Name"], "مینا")
        self.assertEqual(m["Last_Name"], "احمدی")

    def test_get_member_by_id_not_found(self):
        with self.assertRaises(HTTPException) as ctx:
            get_member(999, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_create_member_success(self):
        payload = MemberCreate(
            First_Name="مریم",
            Last_Name="حسینی",
            Contact="0788345678",
            Email="maryam@example.com",
            Joined_Date=date(2025, 6, 10)
        )
        created = create_member(payload, db=self.db)
        self.assertEqual(created["First_Name"], "مریم")
        self.assertEqual(created["Email"], "maryam@example.com")
        self.assertIn("ID_Members", created)

    def test_create_member_duplicate_email(self):
        payload = MemberCreate(
            First_Name="مینا",
            Last_Name="دوم",
            Contact="0711111111",
            Email="mina@example.com"
        )
        with self.assertRaises(HTTPException) as ctx:
            create_member(payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("already exists", ctx.exception.detail)

    def test_update_member_success(self):
        payload = MemberUpdate(
            First_Name="مینا",
            Last_Name="احمدی‌پور",
            Contact="0700999999",
            Email="mina_new@example.com"
        )
        updated = update_member(1, payload, db=self.db)
        self.assertEqual(updated["Last_Name"], "احمدی‌پور")
        self.assertEqual(updated["Email"], "mina_new@example.com")

    def test_update_member_duplicate_email(self):
        payload = MemberUpdate(
            First_Name="مینا",
            Last_Name="احمدی",
            Contact="0700123456",
            Email="farid@example.com"
        )
        with self.assertRaises(HTTPException) as ctx:
            update_member(1, payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)

    def test_update_member_not_found(self):
        payload = MemberUpdate(
            First_Name="ناشناس",
            Last_Name="ناشناس",
            Contact="0700000000"
        )
        with self.assertRaises(HTTPException) as ctx:
            update_member(999, payload, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)

    def test_delete_member_conflict_with_active_loans(self):
        with self.assertRaises(HTTPException) as ctx:
            delete_member(1, db=self.db)
        self.assertEqual(ctx.exception.status_code, 409)
        self.assertIn("active book loan(s) still outstanding", ctx.exception.detail)

    def test_delete_member_success_no_active_loans(self):
        res = delete_member(2, db=self.db)
        self.assertEqual(res["ID_Members"], 2)

        with self.assertRaises(HTTPException) as ctx:
            get_member(2, db=self.db)
        self.assertEqual(ctx.exception.status_code, 404)


if __name__ == "__main__":
    unittest.main()
