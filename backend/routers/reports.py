from datetime import date
from typing import List
from fastapi import APIRouter, Depends, Query
from database import get_db, handle_db_error, FINE_PER_DAY
from schemas.reports import DashboardStats, TopBookItem, RecentActivityItem, MonthlyActivityItem

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT COUNT(*) AS total_books FROM Books")
        total_books = cursor.fetchone()["total_books"]

        cursor.execute("SELECT COUNT(*) AS total_members FROM Members")
        total_members = cursor.fetchone()["total_members"]

        cursor.execute("SELECT COUNT(*) AS active_loans FROM Loans WHERE Return_date IS NULL")
        active_loans = cursor.fetchone()["active_loans"]

        cursor.execute(
            "SELECT COUNT(*) AS overdue_loans FROM Loans WHERE Return_date IS NULL AND Due_date < %s",
            (date.today(),)
        )
        overdue_loans = cursor.fetchone()["overdue_loans"]

        cursor.execute("SELECT COALESCE(SUM(Total_Copies), 0) AS total_c, COALESCE(SUM(Available_Copies), 0) AS avail_c FROM Copies")
        copy_row = cursor.fetchone()
        total_copies = copy_row["total_c"]
        available_copies = copy_row["avail_c"]

        cursor.execute("SELECT COALESCE(SUM(Fine_Amount), 0.0) AS total_fines FROM Loans")
        total_fines = float(cursor.fetchone()["total_fines"])

        return {
            "Total_Books": total_books,
            "Total_Members": total_members,
            "Active_Loans": active_loans,
            "Overdue_Loans": overdue_loans,
            "Total_Copies": total_copies,
            "Available_Copies": available_copies,
            "Total_Fines": total_fines
        }
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/top-books", response_model=List[TopBookItem])
def get_top_books(limit: int = 5, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                b.ID_Books,
                b.Title,
                c.Name AS Category_Name,
                COUNT(l.ID_Loans) AS Loan_Count
            FROM Books b
            LEFT JOIN Categories c ON b.Categories_ID_Category = c.ID_Category
            LEFT JOIN Copies cp ON b.ID_Books = cp.Books_ID_Books
            LEFT JOIN Loans l ON cp.ID_Copies = l.Copies_ID_Copies
            GROUP BY b.ID_Books, b.Title, c.Name
            ORDER BY Loan_Count DESC, b.ID_Books ASC
            LIMIT %s
        """
        cursor.execute(query, (limit,))
        return cursor.fetchall()
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/recent", response_model=List[RecentActivityItem])
def get_recent_activity(limit: int = 5, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        query = """
            SELECT 
                l.ID_Loans,
                b.Title AS Book_Title,
                CONCAT(m.First_Name, ' ', m.Last_Name) AS Member_Name,
                l.Loan_date,
                l.Due_date,
                l.Return_date,
                CASE 
                    WHEN l.Return_date IS NOT NULL THEN 'returned'
                    WHEN l.Due_date < %s THEN 'overdue'
                    ELSE 'active'
                END AS Status
            FROM Loans l
            JOIN Members m ON l.Members_ID_Members = m.ID_Members
            JOIN Copies cp ON l.Copies_ID_Copies = cp.ID_Copies
            JOIN Books b ON cp.Books_ID_Books = b.ID_Books
            ORDER BY l.ID_Loans DESC
            LIMIT %s
        """
        cursor.execute(query, (date.today(), limit))
        return cursor.fetchall()
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/overdue")
def get_overdue_report(db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        today = date.today()
        query = """
            SELECT 
                l.ID_Loans,
                l.Due_date,
                l.Loan_date,
                DATEDIFF(%s, l.Due_date) AS Days_Overdue,
                DATEDIFF(%s, l.Due_date) * %s AS Estimated_Fine,
                m.ID_Members,
                CONCAT(m.First_Name, ' ', m.Last_Name) AS Member_Name,
                m.Contact AS Member_Contact,
                m.Email AS Member_Email,
                b.ID_Books,
                b.Title AS Book_Title
            FROM Loans l
            JOIN Members m ON l.Members_ID_Members = m.ID_Members
            JOIN Copies cp ON l.Copies_ID_Copies = cp.ID_Copies
            JOIN Books b ON cp.Books_ID_Books = b.ID_Books
            WHERE l.Return_date IS NULL AND l.Due_date < %s
            ORDER BY Days_Overdue DESC
        """
        cursor.execute(query, (today, today, FINE_PER_DAY, today))
        return cursor.fetchall()
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()


@router.get("/activity", response_model=List[MonthlyActivityItem])
def get_monthly_activity(months: int = 6, db=Depends(get_db)):
    cursor = None
    try:
        cursor = db.cursor(dictionary=True)
        # Group loans by YYYY-MM
        query = """
            SELECT 
                DATE_FORMAT(l.Loan_date, '%%Y-%%m') AS Month,
                COUNT(l.ID_Loans) AS Loans_Count,
                COUNT(CASE WHEN l.Return_date IS NOT NULL THEN 1 END) AS Returns_Count
            FROM Loans l
            GROUP BY DATE_FORMAT(l.Loan_date, '%%Y-%%m')
            ORDER BY Month DESC
            LIMIT %s
        """
        cursor.execute(query, (months,))
        rows = cursor.fetchall()
        return rows
    except Exception as e:
        raise handle_db_error(e)
    finally:
        if cursor is not None:
            cursor.close()
