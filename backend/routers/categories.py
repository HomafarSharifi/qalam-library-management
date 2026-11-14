from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db, db_transaction, handle_db_error
from schemas.categories import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=List[CategoryResponse])
def get_categories(
    search: Optional[str] = None,
    db=Depends(get_db)
):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                c.ID_Category,
                c.Name,
                COUNT(b.ID_Books) AS Book_Count
            FROM Categories c
            LEFT JOIN Books b ON c.ID_Category = b.Categories_ID_Category
        """
        params = []
        if search:
            query += " WHERE c.Name LIKE %s"
            params.append(f"%{search}%")

        query += " GROUP BY c.ID_Category, c.Name ORDER BY c.Name ASC"
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(category_id: int, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                c.ID_Category,
                c.Name,
                COUNT(b.ID_Books) AS Book_Count
            FROM Categories c
            LEFT JOIN Books b ON c.ID_Category = b.Categories_ID_Category
            WHERE c.ID_Category = %s
            GROUP BY c.ID_Category, c.Name
        """
        cursor.execute(query, (category_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Category not found")
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.post("", response_model=CategoryResponse, status_code=201)
def create_category(category: CategoryCreate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            # Check unique name
            cursor.execute("SELECT ID_Category FROM Categories WHERE Name = %s", (category.Name,))
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail=f"Category '{category.Name}' already exists")

            cursor.execute("INSERT INTO Categories (Name) VALUES (%s)", (category.Name,))
            new_id = cursor.lastrowid
            return {
                "ID_Category": new_id,
                "Name": category.Name,
                "Book_Count": 0
            }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.put("/{category_id}", response_model=CategoryResponse)
def update_category(category_id: int, category: CategoryUpdate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Category FROM Categories WHERE ID_Category = %s", (category_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Category not found")

            # Check if name is taken by another category
            cursor.execute(
                "SELECT ID_Category FROM Categories WHERE Name = %s AND ID_Category != %s",
                (category.Name, category_id)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail=f"Category '{category.Name}' already exists")

            cursor.execute(
                "UPDATE Categories SET Name = %s WHERE ID_Category = %s",
                (category.Name, category_id)
            )

            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Books WHERE Categories_ID_Category = %s",
                (category_id,)
            )
            count_row = cursor.fetchone()
            book_count = count_row["cnt"] if count_row else 0

            return {
                "ID_Category": category_id,
                "Name": category.Name,
                "Book_Count": book_count
            }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.delete("/{category_id}")
def delete_category(category_id: int, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Category FROM Categories WHERE ID_Category = %s", (category_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Category not found")

            # Check if any books are linked
            cursor.execute(
                "SELECT COUNT(*) AS cnt FROM Books WHERE Categories_ID_Category = %s",
                (category_id,)
            )
            row = cursor.fetchone()
            if row and row["cnt"] > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot delete category: {row['cnt']} book(s) belong to this category."
                )

            cursor.execute("DELETE FROM Categories WHERE ID_Category = %s", (category_id,))
            return {"message": "Category deleted successfully", "ID_Category": category_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()
