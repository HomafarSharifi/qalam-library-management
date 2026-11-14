from pydantic import BaseModel, Field, ConfigDict


class CategoryBase(BaseModel):
    Name: str = Field(..., min_length=1, max_length=100, description="Name of the category")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    ID_Category: int
    Book_Count: int = 0

    model_config = ConfigDict(from_attributes=True)
