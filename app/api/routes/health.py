from fastapi import APIRouter
from app.db.connection import get_db

router = APIRouter()


@router.get("")
async def health():
    try:
        get_db().table("plans").select("id").limit(1).execute()
        db_status = "ok"
    except Exception:
        db_status = "error"
    return {"status": "ok", "db": db_status}
