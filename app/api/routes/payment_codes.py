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
    amount_cents: int | None = Field(None, ge=100)  # for updating fare on amount-mode codes


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _make_id() -> str:
    return "pc_" + secrets.token_hex(5)


@router.get("/merchants/me/payment-codes")
async def list_codes(
    single_use: str | None = None,
    limit: int | None = None,
    include_products: str | None = None,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    mid = _merchant_id(user_id, db)
    q = (
        db.table("payment_codes")
        .select("*")
        .eq("merchant_id", mid)
        .order("created_at", desc=True)
    )
    # by default exclude product QRs (managed via /products); pass include_products=true to get all
    if not (include_products and include_products.lower() == "true"):
        q = q.is_("product_id", "null")
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

