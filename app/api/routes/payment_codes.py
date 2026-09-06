import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id
from app.db.connection import get_db

router = APIRouter()


class CodeCreate(BaseModel):
    label: str
    caption: str | None = None
    mode: str = "variable"          # fixed | amount | variable
    product_id: str | None = None
    amount_cents: int | None = Field(None, ge=100)
    description: str | None = None
    placement: str | None = None


class CodeUpdate(BaseModel):
    label: str | None = None
    caption: str | None = None
    placement: str | None = None
    active: bool | None = None
    description: str | None = None


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _make_id(db) -> str:
    try:
        n = (db.table("payment_codes").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"pc_{str(n).zfill(3)}"


@router.get("/merchants/me/payment-codes")
async def list_codes(
    single_use: str | None = None,
    limit: int | None = None,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    mid = _merchant_id(user_id, db)
    q = db.table("payment_codes").select("*").eq("merchant_id", mid).order("created_at", desc=True)
    if single_use is not None:
        q = q.eq("single_use", single_use.lower() == "true")
    if limit is not None:
        q = q.limit(limit)
    res = q.execute()
    return res.data


@router.post("/merchants/me/payment-codes", status_code=201)
async def create_code(body: CodeCreate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    pc_id = _make_id(db)
    reference = "QR-" + secrets.token_hex(4).upper()
    res = db.table("payment_codes").insert({
        "id": pc_id,
        "merchant_id": mid,
        "reference": reference,
        "scans": 0,
        "payments": 0,
        "active": True,
        "is_primary": False,
        "single_use": False,
        **body.model_dump(exclude_none=True),
    }).execute()
    return res.data[0]


@router.patch("/merchants/me/payment-codes/{code_id}")
async def update_code(code_id: str, body: CodeUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("payment_codes").select("id").eq("id", code_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found."})
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return existing.data[0]
    res = db.table("payment_codes").update(updates).eq("id", code_id).execute()
    return res.data[0]


@router.delete("/merchants/me/payment-codes/{code_id}", status_code=204)
async def delete_code(code_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("payment_codes").select("id,is_primary").eq("id", code_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found."})
    if existing.data[0].get("is_primary"):
        raise HTTPException(status_code=400, detail={"code": "cannot_delete_primary", "message": "Cannot delete the primary payment code."})
    db.table("payment_codes").delete().eq("id", code_id).execute()


@router.get("/pay/{reference}")
async def resolve_code(reference: str):
    """Public endpoint — resolves a QR reference to merchant + code info."""
    db = get_db()
    res = db.table("payment_codes").select("*").eq("reference", reference).eq("active", True).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found or inactive."})
    code = res.data[0]
    merchant = db.table("merchants").select("id,display_name,trading_category,city").eq("id", code["merchant_id"]).execute()
    return {"code": code, "merchant": merchant.data[0] if merchant.data else None}
