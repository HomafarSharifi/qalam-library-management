from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, computed_field


class MemberBase(BaseModel):
    First_Name: str = Field(..., min_length=1, max_length=45, description="Member first name")
    Last_Name: str = Field(..., min_length=1, max_length=45, description="Member last name")
    Contact: str = Field(..., min_length=3, max_length=15, description="Phone contact number")
    Email: Optional[str] = Field(None, max_length=75, description="Email address")
    Joined_Date: Optional[date] = Field(None, description="Date member joined library")


class MemberCreate(MemberBase):
    pass


class MemberUpdate(MemberBase):
    pass


class MemberResponse(MemberBase):
    ID_Members: int
    Joined_Date: date
    Active_Loans_Count: int = 0

    @computed_field
    @property
    def Full_Name(self) -> str:
        return f"{self.First_Name} {self.Last_Name}".strip()

    model_config = ConfigDict(from_attributes=True)
