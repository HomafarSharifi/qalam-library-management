"""
Books module for Qalam Library System.
Exposes router and handler functions for book operations.
"""
from routers.books import (
    router,
    get_books,
    get_book,
    create_book,
    update_book,
    update_book_copies,
    delete_book,
    _fetch_book_details
)
from schemas.books import (
    BookBase,
    BookCreate,
    BookUpdate,
    CopiesUpdate,
    BookResponse
)
from database import get_connection, get_db

__all__ = [
    "router",
    "get_books",
    "get_book",
    "create_book",
    "update_book",
    "update_book_copies",
    "delete_book",
    "BookBase",
    "BookCreate",
    "BookUpdate",
    "CopiesUpdate",
    "BookResponse",
    "get_connection",
    "get_db"
]
