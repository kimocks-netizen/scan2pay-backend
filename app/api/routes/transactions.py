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
    method: str | None = Query(None),
    q: str | None = Query(None),
    single_use: str | None = Query(None),
    limit: int = Query(10, ge=1, le=200),
    offset: int = Query(0, ge=0),
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    mid = _merchant_id(user_id, db)

    # count query (no limit/offset)
    count_q = db.table("transactions").select("id", count="exact").eq("merchant_id", mid)
    data_q = db.table("transactions").select("*").eq("merchant_id", mid).order("created_at", desc=True).limit(limit).offset(offset)

    if status:
        count_q = count_q.eq("status", status)
        data_q = data_q.eq("status", status)
    if method:
        count_q = count_q.eq("method", method)
        data_q = data_q.eq("method", method)
    if single_use is not None:
        is_single = single_use.lower() == "true"
        # join through payment_codes to filter single_use
        # simpler: fetch payment_code_ids that are single_use then filter
        pc_res = db.table("payment_codes").select("id").eq("merchant_id", mid).eq("single_use", is_single).execute()
        pc_ids = [r["id"] for r in pc_res.data]
        if not pc_ids:
            return {"data": [], "total": 0, "offset": offset}
        count_q = count_q.in_("payment_code_id", pc_ids)
        data_q = data_q.in_("payment_code_id", pc_ids)
    if q:
        term = f"%{q}%"
        # Supabase JS SDK doesn't support OR across columns easily; use ilike on reference
        data_q = data_q.ilike("reference", term)
        count_q = count_q.ilike("reference", term)

    count_res = count_q.execute()
    total = count_res.count if count_res.count is not None else len(count_res.data)
    data_res = data_q.execute()
    return {"data": data_res.data, "total": total, "offset": offset}


@router.get("/merchants/me/transactions/{txn_id}")
async def get_transaction(txn_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    res = db.table("transactions").select("*").eq("id", txn_id).eq("merchant_id", mid).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Transaction not found."})
    return res.data[0]
