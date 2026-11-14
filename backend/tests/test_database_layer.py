import sys
import os
import unittest
from unittest.mock import MagicMock
from fastapi import HTTPException
import mysql.connector

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from database import (
    handle_db_error,
    db_transaction,
    set_connection_override,
    get_connection,
    get_db_config
)


class TestDatabaseLayer(unittest.TestCase):

    def tearDown(self):
        set_connection_override(None)

    def test_handle_db_error_duplicate(self):
        err = mysql.connector.Error(errno=1062, msg="Duplicate entry 'test' for key 'Name_UNIQUE'")
        exc = handle_db_error(err)
        self.assertIsInstance(exc, HTTPException)
        self.assertEqual(exc.status_code, 409)
        self.assertIn("Duplicate entry", exc.detail)

    def test_handle_db_error_fk_parent_row(self):
        err = mysql.connector.Error(errno=1451, msg="Cannot delete or update a parent row")
        exc = handle_db_error(err)
        self.assertIsInstance(exc, HTTPException)
        self.assertEqual(exc.status_code, 409)
        self.assertIn("Cannot delete or update", exc.detail)

    def test_handle_db_error_fk_child_row(self):
        err = mysql.connector.Error(errno=1452, msg="Cannot add or update a child row")
        exc = handle_db_error(err)
        self.assertIsInstance(exc, HTTPException)
        self.assertEqual(exc.status_code, 400)
        self.assertIn("Referenced record", exc.detail)

    def test_handle_db_error_unreachable(self):
        err = mysql.connector.Error(errno=2003, msg="Can't connect to MySQL server")
        exc = handle_db_error(err)
        self.assertIsInstance(exc, HTTPException)
        self.assertEqual(exc.status_code, 503)
        self.assertIn("unreachable", exc.detail)

    def test_handle_db_error_generic_mysql(self):
        err = mysql.connector.Error(errno=9999, msg="Some unexpected error")
        exc = handle_db_error(err)
        self.assertIsInstance(exc, HTTPException)
        self.assertEqual(exc.status_code, 500)

    def test_handle_db_error_passthrough_http_exception(self):
        original = HTTPException(status_code=404, detail="Not found")
        exc = handle_db_error(original)
        self.assertEqual(exc.status_code, 404)
        self.assertEqual(exc.detail, "Not found")

    def test_db_transaction_success(self):
        mock_conn = MagicMock()
        with db_transaction(mock_conn):
            pass
        mock_conn.commit.assert_called_once()
        mock_conn.rollback.assert_not_called()

    def test_db_transaction_rollback_on_error(self):
        mock_conn = MagicMock()
        with self.assertRaises(HTTPException):
            with db_transaction(mock_conn):
                raise HTTPException(status_code=400, detail="Custom bad request")
        mock_conn.rollback.assert_called_once()
        mock_conn.commit.assert_not_called()

    def test_set_connection_override(self):
        mock_provider = MagicMock()
        mock_conn = MagicMock()
        mock_provider.return_value = mock_conn
        set_connection_override(mock_provider)

        conn = get_connection()
        self.assertEqual(conn, mock_conn)
        mock_provider.assert_called_once()

    def test_get_db_config(self):
        cfg = get_db_config()
        self.assertIn("host", cfg)
        self.assertIn("port", cfg)
        self.assertIn("user", cfg)
        self.assertIn("database", cfg)


if __name__ == "__main__":
    unittest.main()
