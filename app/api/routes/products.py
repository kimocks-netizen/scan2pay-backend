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


def _make_product_id() -> str:
    return "prd_" + secrets.token_hex(5)


def _make_code_id() -> str:
    return "pc_" + secrets.token_hex(5)


def _make_qr_reference() -> str:
    return "PRD-" + secrets.token_hex(4).upper()


@router.get("/merchants/me/products")
async def list_products(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    products = db.table("products").select("*").eq("merchant_id", mid).order("created_at", desc=True).execute()
    if not products.data:
        return []
    product_ids = [p["id"] for p in products.data]
    codes = db.table("payment_codes").select("product_id,reference,payments").in_("product_id", product_ids).execute()
    code_map = {c["product_id"]: c for c in (codes.data or [])}
    for p in products.data:
        code = code_map.get(p["id"])
        p["qr_reference"] = code["reference"] if code else None
        p["payments"] = code["payments"] if code else 0
    return products.data


@router.post("/merchants/me/products", status_code=201)
async def create_product(body: ProductCreate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    pid = _make_product_id()

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

    if not prod_res.data:
        raise HTTPException(status_code=500, detail={"code": "insert_failed", "message": "Product insert failed."})
    product = prod_res.data[0]

    # auto-create a permanent fixed-mode payment code for this product
    reference = _make_qr_reference()
    try:
        db.table("payment_codes").insert({
            "id": _make_code_id(),
            "merchant_id": mid,
            "reference": reference,
            "label": body.name,
            "caption": body.name,
            "mode": "fixed",
            "product_id": pid,
            "active": True,
            "is_primary": False,
            "single_use": False,
            "scans": 0,
            "payments": 0,
        }).execute()
    except Exception as e:
        # roll back the product so we never have an orphan without a QR
        db.table("products").delete().eq("id", pid).execute()
        raise HTTPException(status_code=500, detail={"code": "qr_failed", "message": f"Could not create QR code: {e}"})

    product["qr_reference"] = reference
    return product


@router.post("/merchants/me/products/{product_id}/backfill-qr", status_code=200)
async def backfill_qr(product_id: str, user_id: str = Depends(get_current_user_id)):
    """Creates a QR code for a product that was orphaned without one."""
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("products").select("*").eq("id", product_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Product not found."})
    # check if a code already exists
    code_check = db.table("payment_codes").select("reference").eq("product_id", product_id).execute()
    if code_check.data:
        product = existing.data[0]
        product["qr_reference"] = code_check.data[0]["reference"]
        return product
    reference = _make_qr_reference()
    db.table("payment_codes").insert({
        "id": _make_code_id(),
        "merchant_id": mid,
        "reference": reference,
        "label": existing.data[0]["name"],
        "caption": existing.data[0]["name"],
        "mode": "fixed",
        "product_id": product_id,
        "active": True,
        "is_primary": False,
        "single_use": False,
        "scans": 0,
        "payments": 0,
    }).execute()
    product = existing.data[0]
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


@router.post("/merchants/me/products/{product_id}/regenerate-qr", status_code=200)
async def regenerate_qr(product_id: str, user_id: str = Depends(get_current_user_id)):
    """Issue a brand-new QR reference for a product. Old reference stops working."""
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("products").select("*").eq("id", product_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Product not found."})
    new_reference = _make_qr_reference()
    db.table("payment_codes").update({"reference": new_reference, "active": True}).eq("product_id", product_id).execute()
    product = existing.data[0]
    product["qr_reference"] = new_reference
    return product
