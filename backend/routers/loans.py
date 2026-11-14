from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db, db_transaction, handle_db_error, FINE_PER_DAY
from schemas.loans import LoanIssue, LoanReturn, LoanResponse

router = APIRouter(prefix="/api/loans", tags=["Loans"])


def _format_loan_record(row: dict) -> dict:
    today = date.today()
    due_date = row["Due_date"]
    return_date = row.get("Return_date")

    is_overdue = False
    days_overdue = 0
    if return_date:
        status = "returned"
        if return_date > due_date:
            is_overdue = True
            days_overdue = (return_date - due_date).days
    else:
        if today > due_date:
            status = "overdue"
            is_overdue = True
            days_overdue = (today - due_date).days
        else:
            status = "active"

    return {
        "ID_Loans": row["ID_Loans"],
        "Members_ID_Members": row["Members_ID_Members"],
        "Copies_ID_Copies": row["Copies_ID_Copies"],
        "Books_ID_Books": row.get("Books_ID_Books"),
        "Book_Title": row.get("Book_Title"),
        "Member_Name": row.get("Member_Name"),
        "Loan_date": row["Loan_date"],
        "Due_date": due_date,
        "Return_date": return_date,
        "Fine_Amount": float(row.get("Fine_Amount") or 0.0),
        "Status": status,
        "Is_Overdue": is_overdue,
        "Days_Overdue": days_overdue
    }


@router.get("", response_model=List[LoanResponse])
def get_loans(
    status: Optional[str] = None,
    member_id: Optional[int] = None,
    book_id: Optional[int] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db=Depends(get_db)
):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                l.ID_Loans,
                l.Due_date,
                l.Loan_date,
                l.Return_date,
                l.Fine_Amount,
                l.Members_ID_Members,
                l.Copies_ID_Copies,
                cp.Books_ID_Books,
                b.Title AS Book_Title,
                CONCAT(m.First_Name, ' ', m.Last_Name) AS Member_Name
            FROM Loans l
            JOIN Members m ON l.Members_ID_Members = m.ID_Members
            JOIN Copies cp ON l.Copies_ID_Copies = cp.ID_Copies
            JOIN Books b ON cp.Books_ID_Books = b.ID_Books
            WHERE 1=1
        """
        params = []

        if member_id is not None:
            query += " AND l.Members_ID_Members = %s"
            params.append(member_id)

        if book_id is not None:
            query += " AND cp.Books_ID_Books = %s"
            params.append(book_id)

        if search:
            query += """
                AND (
                    b.Title LIKE %s 
                    OR m.First_Name LIKE %s 
                    OR m.Last_Name LIKE %s
                )
            """
            s_term = f"%{search}%"
            params.extend([s_term, s_term, s_term])

        if status == "active":
            query += " AND l.Return_date IS NULL"
        elif status == "returned":
            query += " AND l.Return_date IS NOT NULL"
        elif status == "overdue":
            query += " AND l.Return_date IS NULL AND l.Due_date < %s"
            params.append(date.today())

        query += " ORDER BY l.ID_Loans DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])

        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        return [_format_loan_record(r) for r in rows]
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/{loan_id}", response_model=LoanResponse)
def get_loan(loan_id: int, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                l.ID_Loans,
                l.Due_date,
                l.Loan_date,
                l.Return_date,
                l.Fine_Amount,
                l.Members_ID_Members,
                l.Copies_ID_Copies,
                cp.Books_ID_Books,
                b.Title AS Book_Title,
                CONCAT(m.First_Name, ' ', m.Last_Name) AS Member_Name
            FROM Loans l
            JOIN Members m ON l.Members_ID_Members = m.ID_Members
            JOIN Copies cp ON l.Copies_ID_Copies = cp.ID_Copies
            JOIN Books b ON cp.Books_ID_Books = b.ID_Books
            WHERE l.ID_Loans = %s
        """
        cursor.execute(query, (loan_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Loan not found")
        return _format_loan_record(row)
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.post("", response_model=LoanResponse, status_code=201)
def issue_loan(loan_in: LoanIssue, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)

            # 1. Validate member
            cursor.execute(
                "SELECT ID_Members, First_Name, Last_Name FROM Members WHERE ID_Members = %s",
                (loan_in.Members_ID_Members,)
            )
            member = cursor.fetchone()
            if not member:
                raise HTTPException(
                    status_code=400,
                    detail=f"Member with ID {loan_in.Members_ID_Members} not found"
                )

            # 2. Identify Copy
            copy_id = loan_in.Copies_ID_Copies
            if not copy_id and loan_in.Books_ID_Books:
                cursor.execute(
                    "SELECT ID_Copies FROM Copies WHERE Books_ID_Books = %s",
                    (loan_in.Books_ID_Books,)
                )
                copy_row = cursor.fetchone()
                if not copy_row:
                    raise HTTPException(
                        status_code=400,
                        detail=f"No copy record found for book ID {loan_in.Books_ID_Books}"
                    )
                copy_id = copy_row["ID_Copies"]

            # Lock and check copy availability
            cursor.execute(
                """
                SELECT 
                    cp.ID_Copies,
                    cp.Books_ID_Books,
                    cp.Available_Copies,
                    cp.Total_Copies,
                    b.Title AS Book_Title
                FROM Copies cp
                JOIN Books b ON cp.Books_ID_Books = b.ID_Books
                WHERE cp.ID_Copies = %s
                FOR UPDATE
                """,
                (copy_id,)
            )
            copy = cursor.fetchone()
            if not copy:
                raise HTTPException(status_code=400, detail=f"Copy with ID {copy_id} not found")

            if copy["Available_Copies"] <= 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"No available copies of '{copy['Book_Title']}' left to loan."
                )

            loan_date = loan_in.Loan_date or date.today()

            # 3. Decrement available copies
            cursor.execute(
                "UPDATE Copies SET Available_Copies = Available_Copies - 1 WHERE ID_Copies = %s",
                (copy_id,)
            )

            # 4. Insert loan
            cursor.execute(
                """
                INSERT INTO Loans (Members_ID_Members, Copies_ID_Copies, Loan_date, Due_date, Fine_Amount)
                VALUES (%s, %s, %s, %s, 0.00)
                """,
                (loan_in.Members_ID_Members, copy_id, loan_date, loan_in.Due_date)
            )
            new_loan_id = cursor.lastrowid

            return {
                "ID_Loans": new_loan_id,
                "Members_ID_Members": loan_in.Members_ID_Members,
                "Copies_ID_Copies": copy_id,
                "Books_ID_Books": copy["Books_ID_Books"],
                "Book_Title": copy["Book_Title"],
                "Member_Name": f"{member['First_Name']} {member['Last_Name']}".strip(),
                "Loan_date": loan_date,
                "Due_date": loan_in.Due_date,
                "Return_date": None,
                "Fine_Amount": 0.0,
                "Status": "active",
                "Is_Overdue": False,
                "Days_Overdue": 0
            }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.post("/{loan_id}/return", response_model=LoanResponse)
def return_loan(loan_id: int, return_data: LoanReturn = None, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                """
                SELECT 
                    l.ID_Loans,
                    l.Due_date,
                    l.Loan_date,
                    l.Return_date,
                    l.Fine_Amount,
                    l.Members_ID_Members,
                    l.Copies_ID_Copies,
                    cp.Books_ID_Books,
                    b.Title AS Book_Title,
                    CONCAT(m.First_Name, ' ', m.Last_Name) AS Member_Name
                FROM Loans l
                JOIN Members m ON l.Members_ID_Members = m.ID_Members
                JOIN Copies cp ON l.Copies_ID_Copies = cp.ID_Copies
                JOIN Books b ON cp.Books_ID_Books = b.ID_Books
                WHERE l.ID_Loans = %s
                FOR UPDATE
                """,
                (loan_id,)
            )
            loan = cursor.fetchone()
            if not loan:
                raise HTTPException(status_code=404, detail="Loan not found")

            if loan["Return_date"] is not None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Loan #{loan_id} has already been returned on {loan['Return_date']}"
                )

            effective_return_date = (return_data.Return_date if return_data and return_data.Return_date else date.today())
            
            # Calculate overdue fine
            days_overdue = max(0, (effective_return_date - loan["Due_date"]).days)
            if return_data and return_data.Fine_Amount is not None:
                final_fine = float(return_data.Fine_Amount)
            else:
                final_fine = float(days_overdue * FINE_PER_DAY)

            # Update loan
            cursor.execute(
                """
                UPDATE Loans
                SET Return_date = %s,
                    Fine_Amount = %s
                WHERE ID_Loans = %s
                """,
                (effective_return_date, final_fine, loan_id)
            )

            # Restore copy availability
            cursor.execute(
                """
                UPDATE Copies
                SET Available_Copies = LEAST(Total_Copies, Available_Copies + 1)
                WHERE ID_Copies = %s
                """,
                (loan["Copies_ID_Copies"],)
            )

            loan["Return_date"] = effective_return_date
            loan["Fine_Amount"] = final_fine
            return _format_loan_record(loan)
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.delete("/{loan_id}")
def delete_loan(loan_id: int, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute(
                "SELECT ID_Loans, Return_date, Copies_ID_Copies FROM Loans WHERE ID_Loans = %s",
                (loan_id,)
            )
            loan = cursor.fetchone()
            if not loan:
                raise HTTPException(status_code=404, detail="Loan not found")

            # If loan was still active, safely restore available copy count
            if loan["Return_date"] is None:
                cursor.execute(
                    """
                    UPDATE Copies 
                    SET Available_Copies = LEAST(Total_Copies, Available_Copies + 1)
                    WHERE ID_Copies = %s
                    """,
                    (loan["Copies_ID_Copies"],)
                )

            cursor.execute("DELETE FROM Loans WHERE ID_Loans = %s", (loan_id,))
            return {"message": "Loan record deleted successfully", "ID_Loans": loan_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()
