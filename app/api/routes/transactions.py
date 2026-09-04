from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.deps import get_current_user_id
from app.db.connection import get_db

router = APIRouter()


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


@router.get("/merchants/me/transactions")
async def list_transactions(
    status: str | None = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    mid = _merchant_id(user_id, db)
    q = db.table("transactions").select("*").eq("merchant_id", mid).order("created_at", desc=True).limit(limit).offset(offset)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    return {"data": res.data, "count": len(res.data), "offset": offset}


@router.get("/merchants/me/transactions/{txn_id}")
async def get_transaction(txn_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    res = db.table("transactions").select("*").eq("id", txn_id).eq("merchant_id", mid).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Transaction not found."})
    return res.data[0]
