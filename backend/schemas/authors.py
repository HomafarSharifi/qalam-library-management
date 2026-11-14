from pydantic import BaseModel, Field, ConfigDict, computed_field


class AuthorBase(BaseModel):
    First_Name: str = Field(..., min_length=1, max_length=45, description="Author first name")
    Last_Name: str = Field(..., min_length=1, max_length=45, description="Author last name")


class AuthorCreate(AuthorBase):
    pass


class AuthorUpdate(AuthorBase):
    pass


class AuthorResponse(AuthorBase):
    ID_Authors: int
    Book_Count: int = 0

    @computed_field
    @property
    def Full_Name(self) -> str:
        return f"{self.First_Name} {self.Last_Name}".strip()

    model_config = ConfigDict(from_attributes=True)
