from .categories import router as categories_router
from .authors import router as authors_router
from .books import router as books_router
from .members import router as members_router
from .loans import router as loans_router
from .reports import router as reports_router

__all__ = [
    "categories_router",
    "authors_router",
    "books_router",
    "members_router",
    "loans_router",
    "reports_router"
]
