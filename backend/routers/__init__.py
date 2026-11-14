from routers.categories import router as categories_router
from routers.authors import router as authors_router
from routers.books import router as books_router
from routers.members import router as members_router
from routers.loans import router as loans_router
from routers.reports import router as reports_router

__all__ = [
    "categories_router",
    "authors_router",
    "books_router",
    "members_router",
    "loans_router",
    "reports_router"
]
