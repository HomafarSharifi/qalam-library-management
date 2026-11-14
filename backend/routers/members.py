from datetime import date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from database import get_db, db_transaction, handle_db_error
from schemas.members import MemberCreate, MemberUpdate, MemberResponse

router = APIRouter(prefix="/api/members", tags=["Members"])


@router.get("", response_model=List[MemberResponse])
def get_members(
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
                m.ID_Members,
                m.First_Name,
                m.Last_Name,
                m.Contact,
                m.Email,
                m.Joined_Date,
                COUNT(CASE WHEN l.Return_date IS NULL AND l.ID_Loans IS NOT NULL THEN 1 END) AS Active_Loans_Count
            FROM Members m
            LEFT JOIN Loans l ON m.ID_Members = l.Members_ID_Members
            WHERE 1=1
        """
        params = []
        if search:
            query += """
                AND (
                    m.First_Name LIKE %s 
                    OR m.Last_Name LIKE %s 
                    OR m.Contact LIKE %s 
                    OR m.Email LIKE %s
                )
            """
            s_term = f"%{search}%"
            params.extend([s_term, s_term, s_term, s_term])

        query += " GROUP BY m.ID_Members, m.First_Name, m.Last_Name, m.Contact, m.Email, m.Joined_Date"
        query += " ORDER BY m.Joined_Date DESC, m.ID_Members DESC LIMIT %s OFFSET %s"
        params.extend([limit, skip])

        cursor.execute(query, tuple(params))
        return cursor.fetchall()
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/{member_id}", response_model=MemberResponse)
def get_member(member_id: int, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                m.ID_Members,
                m.First_Name,
                m.Last_Name,
                m.Contact,
                m.Email,
                m.Joined_Date,
                COUNT(CASE WHEN l.Return_date IS NULL AND l.ID_Loans IS NOT NULL THEN 1 END) AS Active_Loans_Count
            FROM Members m
            LEFT JOIN Loans l ON m.ID_Members = l.Members_ID_Members
            WHERE m.ID_Members = %s
            GROUP BY m.ID_Members, m.First_Name, m.Last_Name, m.Contact, m.Email, m.Joined_Date
        """
        cursor.execute(query, (member_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Member not found")
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.post("", response_model=MemberResponse, status_code=201)
def create_member(member: MemberCreate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)

            # Check email uniqueness if email provided
            if member.Email and member.Email.strip():
                cursor.execute("SELECT ID_Members FROM Members WHERE Email = %s", (member.Email.strip(),))
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail=f"Member with email '{member.Email.strip()}' already exists"
                    )

            joined = member.Joined_Date or date.today()
            email_val = member.Email.strip() if member.Email and member.Email.strip() else None

            cursor.execute(
                """
                INSERT INTO Members (First_Name, Last_Name, Contact, Email, Joined_Date)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (member.First_Name.strip(), member.Last_Name.strip(), member.Contact.strip(), email_val, joined)
            )
            new_id = cursor.lastrowid

            return {
                "ID_Members": new_id,
                "First_Name": member.First_Name.strip(),
                "Last_Name": member.Last_Name.strip(),
                "Contact": member.Contact.strip(),
                "Email": email_val,
                "Joined_Date": joined,
                "Active_Loans_Count": 0
            }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.put("/{member_id}", response_model=MemberResponse)
def update_member(member_id: int, member: MemberUpdate, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Members, Joined_Date FROM Members WHERE ID_Members = %s", (member_id,))
            current = cursor.fetchone()
            if not current:
                raise HTTPException(status_code=404, detail="Member not found")

            # Check email uniqueness
            if member.Email and member.Email.strip():
                cursor.execute(
                    "SELECT ID_Members FROM Members WHERE Email = %s AND ID_Members != %s",
                    (member.Email.strip(), member_id)
                )
                if cursor.fetchone():
                    raise HTTPException(
                        status_code=409,
                        detail=f"Another member with email '{member.Email.strip()}' already exists"
                    )

            joined = member.Joined_Date or current["Joined_Date"]
            email_val = member.Email.strip() if member.Email and member.Email.strip() else None

            cursor.execute(
                """
                UPDATE Members
                SET First_Name = %s,
                    Last_Name = %s,
                    Contact = %s,
                    Email = %s,
                    Joined_Date = %s
                WHERE ID_Members = %s
                """,
                (member.First_Name.strip(), member.Last_Name.strip(), member.Contact.strip(), email_val, joined, member_id)
            )

            # Get active loans count
            cursor.execute(
                "SELECT COUNT(*) AS active_count FROM Loans WHERE Members_ID_Members = %s AND Return_date IS NULL",
                (member_id,)
            )
            count_row = cursor.fetchone()
            active_count = count_row["active_count"] if count_row else 0

            return {
                "ID_Members": member_id,
                "First_Name": member.First_Name.strip(),
                "Last_Name": member.Last_Name.strip(),
                "Contact": member.Contact.strip(),
                "Email": email_val,
                "Joined_Date": joined,
                "Active_Loans_Count": active_count
            }
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.delete("/{member_id}")
def delete_member(member_id: int, db=Depends(get_db)):
    cursor = None
    try:
        with db_transaction(db):
            cursor = db.cursor(dictionary=True)
            cursor.execute("SELECT ID_Members FROM Members WHERE ID_Members = %s", (member_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail="Member not found")

            # Prevent deletion if member has unreturned loans
            cursor.execute(
                "SELECT COUNT(*) AS active_count FROM Loans WHERE Members_ID_Members = %s AND Return_date IS NULL",
                (member_id,)
            )
            loan_row = cursor.fetchone()
            if loan_row and loan_row["active_count"] > 0:
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot delete member: {loan_row['active_count']} active book loan(s) still outstanding."
                )

            # Clean up past returned loans to satisfy foreign key
            cursor.execute("DELETE FROM Loans WHERE Members_ID_Members = %s", (member_id,))
            cursor.execute("DELETE FROM Members WHERE ID_Members = %s", (member_id,))

            return {"message": "Member deleted successfully", "ID_Members": member_id}
    except HTTPException:
        raise
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()
