from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db, db_transaction, handle_db_error
from schemas.authors import AuthorCreate, AuthorUpdate, AuthorResponse

router = APIRouter(prefix="/api/authors", tags=["Authors"])


@router.get("", response_model=List[AuthorResponse])
def get_authors(
    search: Optional[str] = None,
    db=Depends(get_db)
):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                a.ID_Authors,
                a.First_Name,
                a.Last_Name,
                COUNT(ba.Books_ID_Books) AS Book_Count
            FROM Authors a
            LEFT JOIN Books_Authors ba ON a.ID_Authors = ba.Authors_ID_Authors
        """
        params = []
        if search:
            query += " WHERE a.First_Name LIKE %s OR a.Last_Name LIKE %s"
            params.extend([f"%{search}%", f"%{search}%"])

        query += " GROUP BY a.ID_Authors, a.First_Name, a.Last_Name ORDER BY a.Last_Name, a.First_Name ASC"
        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                a.ID_Authors,
                a.First_Name,
                a.Last_Name,
                COUNT(ba.Books_ID_Books) AS Book_Count
            FROM Authors a
            LEFT JOIN Books_Authors ba ON a.ID_Authors = ba.Authors_ID_Authors
            WHERE a.ID_Authors = %s
            GROUP BY a.ID_Authors, a.First_Name, a.Last_Name
        """
        cursor.execute(query, (author_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Author not found")
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.post("", response_model=AuthorResponse, status_code=201)
def create_author(author: AuthorCreate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "INSERT INTO Authors (First_Name, Last_Name) VALUES (%s, %s)",
                (author.First_Name.strip(), author.Last_Name.strip())
            )
            new_id = cursor.lastrowid
            return {
                "ID_Authors": new_id,
                "First_Name": author.First_Name.strip(),
                "Last_Name": author.Last_Name.strip(),
                "Book_Count": 0
            }
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.put("/{author_id}", response_model=AuthorResponse)
def update_author(author_id: int, author: AuthorUpdate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Authors FROM Authors WHERE ID_Authors = %s", (author_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Author not found")

            cursor.execute(
                "UPDATE Authors SET First_Name = %s, Last_Name = %s WHERE ID_Authors = %s",
                (author.First_Name.strip(), author.Last_Name.strip(), author_id)
            )

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Books_Authors WHERE Authors_ID_Authors = %s",
                (author_id,)
            )
            count_row = cursor.fetchone()
            book_count = count_row["cnt"] if count_row else 0

            return {
                "ID_Authors": author_id,
                "First_Name": author.First_Name.strip(),
                "Last_Name": author.Last_Name.strip(),
                "Book_Count": book_count
            }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.delete("/{author_id}")
def delete_author(author_id: int, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Authors FROM Authors WHERE ID_Authors = %s", (author_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Author not found")

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Books_Authors WHERE Authors_ID_Authors = %s",
                (author_id,)
            )
            row = cursor.fetchone()
            if row and row["cnt"] > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot delete author: linked to {row['cnt']} book(s)."
                )

            cursor.execute("DELETE FROM Authors WHERE ID_Authors = %s", (author_id,))
            return {"message": "Author deleted successfully", "ID_Authors": author_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()
