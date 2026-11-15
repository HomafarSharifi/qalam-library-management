from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from database import db_transaction, get_db

router = APIRouter(prefix="/api/admin", tags=["Administration"])


class ClearDatabaseRequest(BaseModel):
    confirmation: str


@router.delete("/data")
def clear_database_data(payload: ClearDatabaseRequest, db=Depends(get_db)):
    """Delete all Qalam records while preserving the database schema."""
    if payload.confirmation != "حذف همه اطلاعات":
        raise HTTPException(status_code=400, detail="عبارت تأیید حذف صحیح نیست.")

    cursor = None
    deleted: Dict[str, int] = {}
    try:
        with db_transaction(db):
            cursor = db.cursor()
            # Delete dependent records before their referenced parent rows.
            for table_name in (
                "Loans",
                "Books_Authors",
                "Copies",
                "Books",
                "Categories",
                "Authors",
                "Members",
            ):
                cursor.execute(f"DELETE FROM {table_name}")
                deleted[table_name] = cursor.rowcount
        return {"message": "تمام اطلاعات حذف شد و ساختار پایگاه داده حفظ گردید.", "deleted": deleted}
    finally:
        if cursor is not None:
            cursor.close()
