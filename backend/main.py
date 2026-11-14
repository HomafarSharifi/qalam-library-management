import logging
import mysql.connector
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from database import get_connection, handle_db_error
from routers import (
    categories_router,
    authors_router,
    books_router,
    members_router,
    loans_router,
    reports_router
)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("qalam")

app = FastAPI(
    title="Qalam Library Management API",
    version="1.0.0",
    description="RESTful API for the Qalam Library Management System."
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(mysql.connector.Error)
async def mysql_exception_handler(request: Request, exc: mysql.connector.Error):
    http_exc = handle_db_error(exc)
    logger.warning(f"Database error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=http_exc.status_code,
        content={"detail": http_exc.detail}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error on {request.method} {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "An unexpected server error occurred. Please try again later."}
    )


@app.get("/")
def home():
    return {
        "name": "Qalam Library API",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }


@app.get("/health")
def health_check():
    """Health check endpoint that verifies database connectivity."""
    db_status = "connected"
    try:
        conn = get_connection()
        conn.close()
    except Exception as e:
        db_status = f"unreachable: {str(e)}"
        return JSONResponse(
            status_code=503,
            content={"status": "degraded", "database": db_status}
        )

    return {"status": "healthy", "database": db_status}


# Register feature routers
app.include_router(categories_router)
app.include_router(authors_router)
app.include_router(books_router)
app.include_router(members_router)
app.include_router(loans_router)
app.include_router(reports_router)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
