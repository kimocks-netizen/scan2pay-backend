import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id
from app.db.connection import get_db

router = APIRouter()

CHARGE_TTL_MINUTES = 5


class ChargeCreate(BaseModel):
    amount_cents: int = Field(..., ge=100)
    label: str
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


@router.post("/charges", status_code=201)
async def create_charge(body: ChargeCreate, user_id: str = Depends(get_current_user_id)):
    """Create a single-use, time-limited payment code (charge QR)."""
    db = get_db()
    mid = _merchant_id(user_id, db)
    pc_id = _make_id(db)
    reference = "PAY-" + secrets.token_hex(4).upper()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=CHARGE_TTL_MINUTES)

    res = db.table("payment_codes").insert({
        "id": pc_id,
        "merchant_id": mid,
        "reference": reference,
        "label": body.label,
        "caption": body.label,
        "mode": "amount",
        "amount_cents": body.amount_cents,
        "description": body.description,
        "active": True,
        "is_primary": False,
        "single_use": True,
        "expires_at": expires_at.isoformat(),
        "scans": 0,
        "payments": 0,
    }).execute()
    return res.data[0]


@router.get("/charges/{reference}")
async def get_charge(reference: str):
    """Resolve a charge reference — returns 410 if expired or already paid."""
    db = get_db()
    res = db.table("payment_codes").select("*").eq("reference", reference).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Charge not found."})
    charge = res.data[0]
    if charge.get("paid_at"):
        raise HTTPException(status_code=410, detail={"code": "already_paid", "message": "This charge has already been paid."})
    if not charge.get("active"):
        raise HTTPException(status_code=410, detail={"code": "expired", "message": "This charge has expired."})
    return charge
