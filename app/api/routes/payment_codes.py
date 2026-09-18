import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id
from app.db.connection import get_db

router = APIRouter()


class CodeCreate(BaseModel):
    label: str = Field(..., min_length=1, max_length=100)
    caption: str | None = Field(None, max_length=100)
    mode: str = "variable"
    product_id: str | None = None
    amount_cents: int | None = Field(None, ge=100, le=9_900_000)
    description: str | None = Field(None, max_length=500)
    placement: str | None = Field(None, max_length=100)


class CodeUpdate(BaseModel):
    label: str | None = Field(None, min_length=1, max_length=100)
    caption: str | None = Field(None, max_length=100)
    placement: str | None = Field(None, max_length=100)
    active: bool | None = None
    description: str | None = Field(None, max_length=500)
    amount_cents: int | None = Field(None, ge=100, le=9_900_000)


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _make_id() -> str:
    return "pc_" + secrets.token_hex(5)


@router.get("/merchants/me/payment-codes")
async def list_codes(
    single_use: str | None = Query(None),
    active: str | None = Query(None),
    mode: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_products: str | None = Query(None),
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    mid = _merchant_id(user_id, db)

    count_q = db.table("payment_codes").select("id", count="exact").eq("merchant_id", mid)
    data_q = db.table("payment_codes").select("*").eq("merchant_id", mid).order("created_at", desc=True).limit(limit).offset(offset)

    if not (include_products and include_products.lower() == "true"):
        count_q = count_q.is_("product_id", "null")
        data_q = data_q.is_("product_id", "null")
    if single_use is not None:
        is_single = single_use.lower() == "true"
        count_q = count_q.eq("single_use", is_single)
        data_q = data_q.eq("single_use", is_single)
    if active is not None:
        is_active = active.lower() == "true"
        count_q = count_q.eq("active", is_active)
        data_q = data_q.eq("active", is_active)
    if mode:
        count_q = count_q.eq("mode", mode)
        data_q = data_q.eq("mode", mode)

    count_res = count_q.execute()
    total = count_res.count if count_res.count is not None else 0
    data_res = data_q.execute()
    return {"data": data_res.data or [], "total": total, "offset": offset}


@router.post("/merchants/me/payment-codes", status_code=201)
async def create_code(body: CodeCreate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)

    # only variable and amount modes allowed here — fixed/product QRs are created via /products
    if body.mode not in ("variable", "amount"):
        raise HTTPException(status_code=400, detail={"code": "invalid_mode", "message": "Use the Products page to create fixed-price product QR codes."})
    if body.mode == "amount" and not body.amount_cents:
        raise HTTPException(status_code=422, detail={"code": "amount_required", "message": "amount_cents is required for fixed-amount codes."})
    if body.mode == "variable" and body.amount_cents:
        raise HTTPException(status_code=422, detail={"code": "invalid_field", "message": "variable codes cannot have amount_cents."})

    pc_id = _make_id()
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
    existing = db.table("payment_codes").select("id,is_primary,product_id").eq("id", code_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found."})
    row = existing.data[0]
    if row.get("is_primary"):
        raise HTTPException(status_code=400, detail={"code": "cannot_delete_primary", "message": "Cannot delete the primary payment code."})
    if row.get("product_id"):
        raise HTTPException(status_code=400, detail={"code": "product_code", "message": "This QR belongs to a product. Delete or disable the product instead."})
    db.table("payment_codes").delete().eq("id", code_id).execute()

