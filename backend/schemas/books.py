from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class BookBase(BaseModel):
    Title: str = Field(..., min_length=1, max_length=100, description="Title of the book")
    ISBN: Optional[str] = Field(None, max_length=13, description="10 or 13-digit ISBN")
    Description: Optional[str] = Field(None, description="Book description or synopsis")
    Categories_ID_Category: int = Field(..., description="ID of category")


class BookCreate(BookBase):
    Authors_ID_Authors: List[int] = Field(default_factory=list, description="List of author IDs")
    Total_Copies: int = Field(default=1, ge=0, description="Initial total copies of the book")


class BookUpdate(BookBase):
    Authors_ID_Authors: List[int] = Field(default_factory=list, description="List of author IDs")


class CopiesUpdate(BaseModel):
    Total_Copies: int = Field(..., ge=0, description="Total copies available in the library")


class BookResponse(BookBase):
    ID_Books: int
    Category_Name: Optional[str] = None
    Authors_ID_Authors: List[int] = Field(default_factory=list)
    Authors_Names: List[str] = Field(default_factory=list)
    Total_Copies: int = 0
    Available_Copies: int = 0
    ID_Copies: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
