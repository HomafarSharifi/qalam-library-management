from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator


class LoanIssue(BaseModel):
    Members_ID_Members: int = Field(..., description="ID of borrowing member")
    Books_ID_Books: Optional[int] = Field(None, description="ID of book to borrow")
    Copies_ID_Copies: Optional[int] = Field(None, description="ID of specific copy to borrow")
    Loan_date: Optional[date] = Field(None, description="Date of issuance (defaults to today)")
    Due_date: date = Field(..., description="Due date for return")

    @model_validator(mode="after")
    def check_book_or_copy_and_dates(self):
        if not self.Books_ID_Books and not self.Copies_ID_Copies:
            raise ValueError("Either Books_ID_Books or Copies_ID_Copies must be specified.")
        
        effective_loan_date = self.Loan_date or date.today()
        if self.Due_date < effective_loan_date:
            raise ValueError("Due_date cannot be earlier than Loan_date.")
        return self


class LoanReturn(BaseModel):
    Return_date: Optional[date] = Field(None, description="Date returned (defaults to today)")
    Fine_Amount: Optional[float] = Field(None, ge=0.0, description="Optional custom fine amount")


class LoanResponse(BaseModel):
    ID_Loans: int
    Members_ID_Members: int
    Copies_ID_Copies: int
    Books_ID_Books: Optional[int] = None
    Book_Title: Optional[str] = None
    Member_Name: Optional[str] = None
    Loan_date: date
    Due_date: date
    Return_date: Optional[date] = None
    Fine_Amount: float = 0.0
    Status: str = "active"  # "active", "returned", "overdue"
    Is_Overdue: bool = False
    Days_Overdue: int = 0

    model_config = ConfigDict(from_attributes=True)
