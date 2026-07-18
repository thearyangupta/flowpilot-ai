from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db


api_router = APIRouter()


@api_router.get("/db-check", tags=["system"])
def database_check(
    db: Session = Depends(get_db),#depends - This endpoint needs something before it can run.Before running this endpoint, call get_db() and use the yielded value as db
) -> dict[str, str]:
    db.execute(text("SELECT 1"))

    return {
        "status": "ok",
        "database": "connected",
    }