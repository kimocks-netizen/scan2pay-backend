from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user_id
from app.db.connection import get_db

router = APIRouter()


class MerchantUpdate(BaseModel):
    business_name: str | None = None
    display_name: str | None = None
    trading_category: str | None = None
    city: str | None = None
    province: str | None = None
    settlement_cycle: str | None = None
    payout_bank: str | None = None
    payout_bank_code: str | None = None
    payout_account_masked: str | None = None


def _get_merchant(user_id: str, db):
    res = db.table("merchants").select("*").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]


@router.get("/me")
async def get_my_merchant(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    return _get_merchant(user_id, db)


@router.patch("/me")
async def update_my_merchant(body: MerchantUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    merchant = _get_merchant(user_id, db)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return merchant
    res = db.table("merchants").update(updates).eq("id", merchant["id"]).execute()
    return res.data[0]


@router.get("/{merchant_id}")
async def get_merchant(merchant_id: str):
    db = get_db()
    res = db.table("merchants").select("id,business_name,display_name,slug,trading_category,city,province,status").eq("id", merchant_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found."})
    return res.data[0]
