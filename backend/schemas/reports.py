from datetime import date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict


class DashboardStats(BaseModel):
    Total_Books: int = 0
    Total_Members: int = 0
    Active_Loans: int = 0
    Overdue_Loans: int = 0
    Total_Copies: int = 0
    Available_Copies: int = 0
    Total_Fines: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class TopBookItem(BaseModel):
    ID_Books: int
    Title: str
    Loan_Count: int
    Category_Name: Optional[str] = None


class RecentActivityItem(BaseModel):
    ID_Loans: int
    Book_Title: str
    Member_Name: str
    Loan_date: date
    Due_date: date
    Return_date: Optional[date] = None
    Status: str


class MonthlyActivityItem(BaseModel):
    Month: str
    Loans_Count: int = 0
    Returns_Count: int = 0
