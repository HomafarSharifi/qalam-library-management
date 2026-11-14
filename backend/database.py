import os
from contextlib import contextmanager
from typing import Callable, Generator, Optional
import mysql.connector
from mysql.connector import pooling
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()

# Database configuration with environment variable support
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "Qalam")
DB_POOL_NAME = os.getenv("DB_POOL_NAME", "qalam_pool")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "5"))
FINE_PER_DAY = float(os.getenv("FINE_PER_DAY", "5.0"))

_connection_override: Optional[Callable[[], any]] = None
_pool: Optional[pooling.MySQLConnectionPool] = None


def get_db_config() -> dict:
    return {
        "host": DB_HOST,
        "port": DB_PORT,
        "user": DB_USER,
        "password": DB_PASSWORD,
        "database": DB_NAME,
    }


def _get_or_create_pool() -> pooling.MySQLConnectionPool:
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name=DB_POOL_NAME,
            pool_size=DB_POOL_SIZE,
            pool_reset_session=True,
            **get_db_config()
        )
    return _pool


def set_connection_override(provider: Optional[Callable[[], any]]) -> None:
    """Set an override provider for unit testing or custom mock connections."""
    global _connection_override
    _connection_override = provider


def get_connection():
    """Retrieve a connection from the custom provider, connection pool, or fallback."""
    if _connection_override is not None:
        return _connection_override()

    try:
        pool = _get_or_create_pool()
        return pool.get_connection()
    except Exception:
        # Fallback to direct connection if pooling is not supported or failed
        return mysql.connector.connect(**get_db_config())


def handle_db_error(err: Exception) -> HTTPException:
    """Map database errors to safe and informative HTTP exceptions."""
    if isinstance(err, mysql.connector.Error):
        # 1062: Duplicate entry
        if getattr(err, "errno", None) == 1062:
            return HTTPException(status_code=409, detail=f"Duplicate entry: {err.msg}")
        # 1451: Cannot delete or update a parent row (FK constraint fail)
        if getattr(err, "errno", None) == 1451:
            return HTTPException(
                status_code=409,
                detail="Cannot delete or update record because related records depend on it."
            )
        # 1452: Cannot add or update a child row (FK constraint fail)
        if getattr(err, "errno", None) == 1452:
            return HTTPException(
                status_code=400,
                detail="Referenced record (such as category, member, book, or copy) does not exist."
            )
        # 2003/2002: Can't connect to MySQL server
        if getattr(err, "errno", None) in (2002, 2003):
            return HTTPException(
                status_code=503,
                detail="Database service is currently unreachable."
            )
        return HTTPException(status_code=500, detail=f"Database error: {err.msg}")
    
    if isinstance(err, HTTPException):
        return err
    return HTTPException(status_code=500, detail=f"Internal server error: {str(err)}")


@contextmanager
def db_transaction(existing_conn=None):
    """Context manager for managing transactions with automatic commit and rollback."""
    close_when_done = False
    conn = existing_conn
    if conn is None:
        try:
            conn = get_connection()
            close_when_done = True
        except Exception as e:
            raise handle_db_error(e)

    try:
        yield conn
        if hasattr(conn, "commit"):
            conn.commit()
    except Exception as e:
        if hasattr(conn, "rollback"):
            try:
                conn.rollback()
            except Exception:
                pass
        if isinstance(e, HTTPException):
            raise e
        raise handle_db_error(e)
    finally:
        if close_when_done and hasattr(conn, "close"):
            try:
                conn.close()
            except Exception:
                pass


def get_db() -> Generator:
    """FastAPI dependency for obtaining a database connection."""
    conn = None
    try:
        conn = get_connection()
        yield conn
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if conn is not None and hasattr(conn, "close"):
            try:
                conn.close()
            except Exception:
                pass


if __name__ == "__main__":
    try:
        connection = get_connection()
        print("Connected to Qalam database successfully!")
        connection.close()
    except Exception as exc:
        print(f"Could not connect to database: {exc}")
