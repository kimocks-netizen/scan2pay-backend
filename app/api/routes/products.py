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
    previous_price_cents: int | None = None
    sku: str | None = None
    category: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    price_cents: int | None = Field(None, ge=100)
    previous_price_cents: int | None = None
    sku: str | None = None
    category: str | None = None
    active: bool | None = None


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _make_id(db) -> str:
    try:
        n = (db.table("products").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"prd_{str(n).zfill(3)}"


@router.get("/merchants/me/products")
async def list_products(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    res = db.table("products").select("*").eq("merchant_id", mid).order("created_at", desc=True).execute()
    return res.data


@router.post("/merchants/me/products", status_code=201)
async def create_product(body: ProductCreate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    pid = _make_id(db)
    res = db.table("products").insert({
        "id": pid,
        "merchant_id": mid,
        **body.model_dump(exclude_none=True),
    }).execute()
    return res.data[0]


@router.patch("/merchants/me/products/{product_id}")
async def update_product(product_id: str, body: ProductUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("products").select("id").eq("id", product_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Product not found."})
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return existing.data[0]
    res = db.table("products").update(updates).eq("id", product_id).execute()
    return res.data[0]


@router.delete("/merchants/me/products/{product_id}", status_code=204)
async def delete_product(product_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    existing = db.table("products").select("id").eq("id", product_id).eq("merchant_id", mid).execute()
    if not existing.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Product not found."})
    db.table("products").delete().eq("id", product_id).execute()
