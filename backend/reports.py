"""
Reports module for Qalam Library System.
Exposes router and handler functions for analytics and reports.
"""
from routers.reports import (
    router,
    get_dashboard_stats,
    get_top_books,
    get_recent_activity,
    get_overdue_report,
    get_monthly_activity
)
from schemas.reports import (
    DashboardStats,
    TopBookItem,
    RecentActivityItem,
    MonthlyActivityItem
)
from database import get_connection, get_db

__all__ = [
    "router",
    "get_dashboard_stats",
    "get_top_books",
    "get_recent_activity",
    "get_overdue_report",
    "get_monthly_activity",
    "DashboardStats",
    "TopBookItem",
    "RecentActivityItem",
    "MonthlyActivityItem",
    "get_connection",
    "get_db"
]
