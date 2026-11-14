from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db, db_transaction, handle_db_error
from schemas.books import BookCreate, BookUpdate, CopiesUpdate, BookResponse

router = APIRouter(prefix="/api/books", tags=["Books"])


def _fetch_book_details(cursor, book_id: int) -> Optional[dict]:
    """Helper to fetch full details of a single book with authors and copies."""
    query = """
        SELECT 
            b.ID_Books,
            b.Title,
            b.ISBN,
            b.Description,
            b.Categories_ID_Category,
            c.Name AS Category_Name,
            cp.ID_Copies,
            COALESCE(cp.Total_Copies, 0) AS Total_Copies,
            COALESCE(cp.Available_Copies, 0) AS Available_Copies
        FROM Books b
        LEFT JOIN Categories c ON b.Categories_ID_Category = c.ID_Category
        LEFT JOIN Copies cp ON b.ID_Books = cp.Books_ID_Books
        WHERE b.ID_Books = %s
    """
    cursor.execute(query, (book_id,))
    book = cursor.fetchone()
    if not book:
        return None

    # Fetch authors
    author_query = """
        SELECT 
            a.ID_Authors,
            CONCAT(a.First_Name, ' ', a.Last_Name) AS Full_Name
        FROM Books_Authors ba
        JOIN Authors a ON ba.Authors_ID_Authors = a.ID_Authors
        WHERE ba.Books_ID_Books = %s
        ORDER BY a.Last_Name, a.First_Name ASC
    """
    cursor.execute(author_query, (book_id,))
    authors = cursor.fetchall()
    book["Authors_ID_Authors"] = [a["ID_Authors"] for a in authors]
    book["Authors_Names"] = [a["Full_Name"] for a in authors]
    return book


@router.get("", response_model=List[BookResponse])
def get_books(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    author_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT DISTINCT b.ID_Books
            FROM Books b
            LEFT JOIN Categories c ON b.Categories_ID_Category = c.ID_Category
            LEFT JOIN Books_Authors ba ON b.ID_Books = ba.Books_ID_Books
            LEFT JOIN Authors a ON ba.Authors_ID_Authors = a.ID_Authors
            WHERE 1=1
        """
        params = []
        if search:
            query += """
                AND (
                    b.Title LIKE %s 
                    OR b.ISBN LIKE %s 
                    OR b.Description LIKE %s 
                    OR a.First_Name LIKE %s 
                    OR a.Last_Name LIKE %s
                )
            """
            s_term = f"%{search}%"
            params.extend([s_term, s_term, s_term, s_term, s_term])

        if category_id is not None:
            query += " AND b.Categories_ID_Category = %s"
            params.append(category_id)

        if author_id is not None:
            query += " AND ba.Authors_ID_Authors = %s"
            params.append(author_id)

        query += " ORDER BY b.ID_Books DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])

        cursor.execute(query, tuple(params))
        book_ids = [row["ID_Books"] for row in cursor.fetchall()]

        results = []
        for b_id in book_ids:
            item = _fetch_book_details(cursor, b_id)
            if item:
                results.append(item)
        return results
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/{book_id}", response_model=BookResponse)
def get_book(book_id: int, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        book = _fetch_book_details(cursor, book_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")
        return book
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.post("", response_model=BookResponse, status_code=201)
def create_book(book: BookCreate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)

            # Validate Category exists
            cursor.execute(
                "SELECT ID_Category FROM Categories WHERE ID_Category = %s",
                (book.Categories_ID_Category,)
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail=f"Category with ID {book.Categories_ID_Category} does not exist"
                )

            # Validate Authors exist
            for a_id in book.Authors_ID_Authors:
                cursor.execute("SELECT ID_Authors FROM Authors WHERE ID_Authors = %s", (a_id,))
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Author with ID {a_id} does not exist"
                    )

            # Check unique ISBN if provided
            if book.ISBN and book.ISBN.strip():
                cursor.execute("SELECT ID_Books FROM Books WHERE ISBN = %s", (book.ISBN.strip(),))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail=f"Book with ISBN '{book.ISBN.strip()}' already exists"
                    )

            # Insert book
            insert_query = """
                INSERT INTO Books (Title, ISBN, Description, Categories_ID_Category)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(
                insert_query,
                (
                    book.Title.strip(),
                    book.ISBN.strip() if book.ISBN and book.ISBN.strip() else None,
                    book.Description,
                    book.Categories_ID_Category
                )
            )
            new_book_id = cursor.lastrowid

            # Insert author associations
            for a_id in set(book.Authors_ID_Authors):
                cursor.execute(
                    "INSERT INTO Books_Authors (Books_ID_Books, Authors_ID_Authors) VALUES (%s, %s)",
                    (new_book_id, a_id)
                )

            # Insert copies row
            total_copies = max(0, book.Total_Copies)
            cursor.execute(
                """
                INSERT INTO Copies (Books_ID_Books, Total_Copies, Available_Copies)
                VALUES (%s, %s, %s)
                """,
                (new_book_id, total_copies, total_copies)
            )

            result = _fetch_book_details(cursor, new_book_id)
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.put("/{book_id}", response_model=BookResponse)
def update_book(book_id: int, book: BookUpdate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Books FROM Books WHERE ID_Books = %s", (book_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Book not found")

            # Validate Category exists
            cursor.execute(
                "SELECT ID_Category FROM Categories WHERE ID_Category = %s",
                (book.Categories_ID_Category,)
            )
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=400,
                    detail=f"Category with ID {book.Categories_ID_Category} does not exist"
                )

            # Validate Authors exist
            for a_id in book.Authors_ID_Authors:
                cursor.execute("SELECT ID_Authors FROM Authors WHERE ID_Authors = %s", (a_id,))
                if not cursor.fetchone():
                    raise HTTPException(
                        status_code=400,
                        detail=f"Author with ID {a_id} does not exist"
                    )

            # Check unique ISBN if updated
            if book.ISBN and book.ISBN.strip():
                cursor.execute(
                    "SELECT ID_Books FROM Books WHERE ISBN = %s AND ID_Books != %s",
                    (book.ISBN.strip(), book_id)
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail=f"Another book with ISBN '{book.ISBN.strip()}' already exists"
                    )

            # Update book
            cursor.execute(
                """
                UPDATE Books
                SET Title = %s,
                    ISBN = %s,
                    Description = %s,
                    Categories_ID_Category = %s
                WHERE ID_Books = %s
                """,
                (
                    book.Title.strip(),
                    book.ISBN.strip() if book.ISBN and book.ISBN.strip() else None,
                    book.Description,
                    book.Categories_ID_Category,
                    book_id
                )
            )

            # Sync authors: remove old, insert new
            cursor.execute("DELETE FROM Books_Authors WHERE Books_ID_Books = %s", (book_id,))
            for a_id in set(book.Authors_ID_Authors):
                cursor.execute(
                    "INSERT INTO Books_Authors (Books_ID_Books, Authors_ID_Authors) VALUES (%s, %s)",
                    (book_id, a_id)
                )

            result = _fetch_book_details(cursor, book_id)
            return result
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.put("/{book_id}/copies")
def update_book_copies(book_id: int, copies_data: CopiesUpdate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT ID_Copies, Total_Copies, Available_Copies FROM Copies WHERE Books_ID_Books = %s",
                (book_id,)
            )
            copy_row = cursor.fetchone()
            if not copy_row:
                raise HTTPException(status_code=404, detail="Copies record for book not found")

            currently_borrowed = copy_row["Total_Copies"] - copy_row["Available_Copies"]
            if copies_data.Total_Copies < currently_borrowed:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot reduce total copies below {currently_borrowed} (currently borrowed copies count)."
                )

            new_available = copies_data.Total_Copies - currently_borrowed
            cursor.execute(
                """
                UPDATE Copies
                SET Total_Copies = %s, Available_Copies = %s
                WHERE ID_Copies = %s
                """,
                (copies_data.Total_Copies, new_available, copy_row["ID_Copies"])
            )

            return {
                "message": "Copies updated successfully",
                "ID_Copies": copy_row["ID_Copies"],
                "Books_ID_Books": book_id,
                "Total_Copies": copies_data.Total_Copies,
                "Available_Copies": new_available
            }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.delete("/{book_id}")
def delete_book(book_id: int, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Books FROM Books WHERE ID_Books = %s", (book_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Book not found")

            # Check if copies have active loans
            cursor.execute("SELECT ID_Copies FROM Copies WHERE Books_ID_Books = %s", (book_id,))
            copy_row = cursor.fetchone()
            if copy_row:
                copy_id = copy_row["ID_Copies"]
                cursor.execute(
                    "SELECT COUNT(*) AS active_count FROM Loans WHERE Copies_ID_Copies = %s AND Return_date IS NULL",
                    (copy_id,)
                )
                loan_check = cursor.fetchone()
                if loan_check and loan_check["active_count"] > 0:
                    raise HTTPException(
                        status_code=409,
                        detail="Cannot delete book while copies are currently on loan."
                    )
                # Remove historical returned loans if any before deleting copies to satisfy foreign key
                cursor.execute("DELETE FROM Loans WHERE Copies_ID_Copies = %s", (copy_id,))
                cursor.execute("DELETE FROM Copies WHERE ID_Copies = %s", (copy_id,))

            # Remove book_authors
            cursor.execute("DELETE FROM Books_Authors WHERE Books_ID_Books = %s", (book_id,))
            # Remove book
            cursor.execute("DELETE FROM Books WHERE ID_Books = %s", (book_id,))

            return {"message": "Book deleted successfully", "ID_Books": book_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()
