import secrets
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id
from app.db.connection import get_db
from app.services.paystack_service import PaystackError, initialize_transaction

router = APIRouter()

CHARGE_TTL_MINUTES = 5
AMOUNT_MIN = 100
AMOUNT_MAX = 5_000_000


class ChargeCreate(BaseModel):
    amount_cents: int = Field(..., ge=100)
    label: str
    description: str | None = None


class PublicPayInit(BaseModel):
    amount_cents: int | None = Field(None, ge=AMOUNT_MIN, le=AMOUNT_MAX)
    customer_email: str | None = None
    customer_label: str = "Customer"


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _make_pc_id(db) -> str:
    try:
        n = (db.table("payment_codes").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"pc_{str(n).zfill(3)}"


def _make_txn_id(db) -> str:
    try:
        n = (db.table("transactions").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"txn_{str(n).zfill(6)}"


def _calc_fees(amount_cents: int, plan_percent: float) -> tuple[int, int, int]:
    platform = round(amount_cents * plan_percent / 100)
    provider = round(amount_cents * 2.9 / 100) + 100
    net = amount_cents - platform - provider
    return platform, provider, net


@router.post("/charges", status_code=201)
async def create_charge(body: ChargeCreate, user_id: str = Depends(get_current_user_id)):
    """Create a single-use, time-limited payment code (charge QR)."""
    db = get_db()
    mid = _merchant_id(user_id, db)
    pc_id = _make_pc_id(db)
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


@router.post("/pay/{reference}/initialise", status_code=201)
async def public_pay_initialise(reference: str, body: PublicPayInit):
    """Public — no auth. Customer initiates payment from the pay page."""
    db = get_db()

    # resolve code
    pc_res = db.table("payment_codes").select("*").eq("reference", reference).execute()
    if not pc_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found."})
    pc = pc_res.data[0]

    if not pc.get("active"):
        raise HTTPException(status_code=410, detail={"code": "expired", "message": "This payment code is no longer active."})
    if pc.get("expires_at") and datetime.fromisoformat(pc["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail={"code": "expired", "message": "This payment request has expired."})

    # resolve amount
    if pc["mode"] == "amount":
        amount_cents = pc["amount_cents"]
    elif body.amount_cents:
        amount_cents = body.amount_cents
    else:
        raise HTTPException(status_code=422, detail={"code": "amount_required", "message": "Please enter an amount."})

    mid = pc["merchant_id"]

    # fees
    mch_res = db.table("merchants").select("plan_id").eq("id", mid).execute()
    plan_id = mch_res.data[0]["plan_id"] if mch_res.data else "plan_free"
    plan_res = db.table("plans").select("platform_fee_percent").eq("id", plan_id).execute()
    plan_percent = float(plan_res.data[0]["platform_fee_percent"]) if plan_res.data else 2.5
    platform_fee, provider_fee, net = _calc_fees(amount_cents, plan_percent)

    pricing_res = db.table("pricing_versions").select("id").eq("plan_id", plan_id).order("created_at", desc=True).limit(1).execute()
    pricing_version = pricing_res.data[0]["id"] if pricing_res.data else "pv_unknown"

    txn_id = _make_txn_id(db)
    txn_reference = f"STP{txn_id.replace('txn_', '').upper()}"
    email = body.customer_email or "anonymous@scan2pay.co.za"

    db.table("transactions").insert({
        "id": txn_id,
        "reference": txn_reference,
        "merchant_id": mid,
        "payment_code_id": pc["id"],
        "item": pc.get("label", "Payment"),
        "amount_cents": amount_cents,
        "platform_fee_cents": platform_fee,
        "provider_fee_cents": provider_fee,
        "net_cents": net,
        "status": "pending",
        "method": "card",
        "customer_label": body.customer_label,
        "customer_email": body.customer_email,
        "settlement_status": "pending",
        "pricing": {"plan_percent": plan_percent, "provider_rate": 2.9, "provider_fixed": 100},
        "plan_id_at_time": plan_id,
        "pricing_version": pricing_version,
    }).execute()

    try:
        result = initialize_transaction(
            email=email,
            amount_cents=amount_cents,
            reference=txn_reference,
            metadata={
                "merchant_id": mid,
                "payment_code_id": pc["id"],
                "single_use": "true" if pc.get("single_use") else "false",
                "txn_id": txn_id,
            },
        )
    except PaystackError as e:
        db.table("transactions").update({"status": "failed", "failure_reason": e.message}).eq("id", txn_id).execute()
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})

    db.table("transactions").update({"paystack_reference": result["reference"]}).eq("id", txn_id).execute()

    return {
        "txn_id": txn_id,
        "access_code": result["access_code"],
        "amount_cents": amount_cents,
    }
