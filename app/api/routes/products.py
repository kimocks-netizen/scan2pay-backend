import secrets
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id
from app.db.connection import get_db

router = APIRouter()


class ProductCreate(BaseModel):
    name: str
    description: str | None = None
    price_cents: int = Field(..., ge=100)
    sku: str | None = None
    category: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price_cents: int | None = Field(None, ge=100)
    sku: str | None = None
    category: str | None = None
    active: bool | None = None


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _make_product_id(db) -> str:
    try:
        n = (db.table("products").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"prd_{str(n).zfill(3)}"


def _make_code_id(db) -> str:
    try:
        n = (db.table("payment_codes").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"pc_{str(n).zfill(3)}"


@router.get("/merchants/me/products")
async def list_products(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    # join payment_codes to get the QR reference per product
    products = db.table("products").select("*").eq("merchant_id", mid).order("created_at", desc=True).execute()
    if not products.data:
        return []
    # fetch linked payment codes in one query
    product_ids = [p["id"] for p in products.data]
    codes = db.table("payment_codes").select("product_id,reference").in_("product_id", product_ids).execute()
    code_map = {c["product_id"]: c["reference"] for c in (codes.data or [])}
    for p in products.data:
        p["qr_reference"] = code_map.get(p["id"])
    return products.data


@router.post("/merchants/me/products", status_code=201)
async def create_product(body: ProductCreate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    pid = _make_product_id(db)

    # create product
    prod_res = db.table("products").insert({
        "id": pid,
        "merchant_id": mid,
        "name": body.name,
        "description": body.description,
        "price_cents": body.price_cents,
        "previous_price_cents": body.price_cents,
        "sku": body.sku,
        "category": body.category,
        "active": True,
    }).execute()
    product = prod_res.data[0]

    # auto-create a permanent fixed-mode payment code for this product
    pc_id = _make_code_id(db)
    reference = "PRD-" + secrets.token_hex(4).upper()
    db.table("payment_codes").insert({
        "id": pc_id,
        "merchant_id": mid,
        "reference": reference,
        "label": body.name,
        "caption": body.name,
        "mode": "fixed",
        "product_id": pid,
        "amount_cents": None,   # fixed mode — price comes from product at scan time
        "active": True,
        "is_primary": False,
        "single_use": False,
        "scans": 0,
        "payments": 0,
    }).execute()

    product["qr_reference"] = reference
    return product


@router.patch("/merchants/me/products/{product_id}")
async def update_product(product_id: str, body: ProductUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("products").select("*").eq("id", product_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Product not found."})

    updates = body.model_dump(exclude_none=True)
    if not updates:
        return existing.data[0]

    # snapshot previous price before update
    if "price_cents" in updates:
        updates["previous_price_cents"] = existing.data[0]["price_cents"]

    prod_res = db.table("products").update(updates).eq("id", product_id).execute()
    product = prod_res.data[0]

    # keep payment code label in sync with product name
    if "name" in updates:
        db.table("payment_codes").update({"label": updates["name"], "caption": updates["name"]}).eq("product_id", product_id).execute()

    # if product disabled, deactivate its payment code too
    if "active" in updates:
        db.table("payment_codes").update({"active": updates["active"]}).eq("product_id", product_id).execute()

    # attach qr_reference
    code = db.table("payment_codes").select("reference").eq("product_id", product_id).execute()
    product["qr_reference"] = code.data[0]["reference"] if code.data else None
    return product


@router.delete("/merchants/me/products/{product_id}", status_code=204)
async def delete_product(product_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("products").select("id").eq("id", product_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Product not found."})
    # deactivate payment code (don't delete — preserves transaction history)
    db.table("payment_codes").update({"active": False}).eq("product_id", product_id).execute()
    db.table("products").delete().eq("id", product_id).execute()
