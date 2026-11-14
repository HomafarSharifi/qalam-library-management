"""
Loans module for Qalam Library System.
Exposes router and handler functions for loan and return operations.
"""
from routers.loans import (
    router,
    get_loans,
    get_loan,
    issue_loan,
    return_loan,
    delete_loan
)
from schemas.loans import (
    LoanIssue,
    LoanReturn,
    LoanResponse
)
from database import get_connection, get_db

__all__ = [
    "router",
    "get_loans",
    "get_loan",
    "issue_loan",
    "return_loan",
    "delete_loan",
    "LoanIssue",
    "LoanReturn",
    "LoanResponse",
    "get_connection",
    "get_db"
]
