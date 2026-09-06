import logging
import secrets
import sys
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id
from app.db.connection import get_db
from app.services.paystack_service import PaystackError, initialize_transaction

logger = logging.getLogger(__name__)
router = APIRouter()

AMOUNT_MIN = 100
AMOUNT_MAX = 5_000_000


class PaymentInitRequest(BaseModel):
    payment_code_reference: str
    amount_cents: int | None = Field(None, ge=AMOUNT_MIN, le=AMOUNT_MAX)
    customer_email: str | None = None
    customer_label: str = "Anonymous"


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _calc_fees(amount_cents: int, plan_percent: float) -> tuple[int, int, int]:
    platform = round(amount_cents * plan_percent / 100)
    provider = round(amount_cents * 2.9 / 100) + 100
    net = amount_cents - platform - provider
    return platform, provider, net


def _make_txn_id(db) -> str:
    try:
        n = (db.table("transactions").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"txn_{str(n).zfill(6)}"


@router.post("/initialise", status_code=201)
async def initialise_payment(body: PaymentInitRequest, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)

    # resolve payment code
    pc_res = db.table("payment_codes").select("*").eq("reference", body.payment_code_reference).eq("merchant_id", mid).execute()
    if not pc_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found."})
    pc = pc_res.data[0]

    if not pc.get("active"):
        raise HTTPException(status_code=410, detail={"code": "expired", "message": "This payment code is no longer active."})

    # resolve amount
    if pc["mode"] == "amount":
        amount_cents = pc["amount_cents"]
    elif body.amount_cents:
        amount_cents = body.amount_cents
    else:
        raise HTTPException(status_code=422, detail={"code": "amount_required", "message": "This payment code requires an amount."})

    if not (AMOUNT_MIN <= amount_cents <= AMOUNT_MAX):
        raise HTTPException(status_code=422, detail={"code": "invalid_amount", "message": f"Amount must be between {AMOUNT_MIN} and {AMOUNT_MAX} cents."})

    # get merchant plan for fee calc
    mch_res = db.table("merchants").select("plan_id").eq("id", mid).execute()
    plan_id = mch_res.data[0]["plan_id"] if mch_res.data else "plan_free"
    plan_res = db.table("plans").select("platform_fee_percent").eq("id", plan_id).execute()
    plan_percent = float(plan_res.data[0]["platform_fee_percent"]) if plan_res.data else 2.5

    platform_fee, provider_fee, net = _calc_fees(amount_cents, plan_percent)

    # pricing snapshot
    pricing_res = db.table("pricing_versions").select("id").eq("plan_id", plan_id).order("created_at", desc=True).limit(1).execute()
    pricing_version = pricing_res.data[0]["id"] if pricing_res.data else "pv_unknown"

    txn_id = _make_txn_id(db)
    reference = f"STP{txn_id.replace('txn_', '').upper()}"
    email = body.customer_email or "anonymous@scan2pay.co.za"

    # persist pending transaction BEFORE calling Paystack
    sys.stderr.write(f"[payments] Inserting pending txn {txn_id} for merchant {mid}\n")
    sys.stderr.flush()
    logger.info("Inserting pending txn %s for merchant %s", txn_id, mid)
    db.table("transactions").insert({
        "id": txn_id,
        "reference": reference,
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
        "customer_email": email if body.customer_email else None,
        "settlement_status": "pending",
        "pricing": {"plan_percent": plan_percent, "provider_rate": 2.9, "provider_fixed": 100},
        "plan_id_at_time": plan_id,
        "pricing_version": pricing_version,
    }).execute()

    logger.info("Calling Paystack initialize for txn %s ref %s", txn_id, reference)
    # call Paystack
    try:
        result = initialize_transaction(
            email=email,
            amount_cents=amount_cents,
            reference=reference,
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

    # store paystack reference
    db.table("transactions").update({"paystack_reference": result["reference"]}).eq("id", txn_id).execute()

    return {
        "txn_id": txn_id,
        "reference": reference,
        "access_code": result["access_code"],
        "authorization_url": result["authorization_url"],
        "amount_cents": amount_cents,
        "platform_fee_cents": platform_fee,
        "provider_fee_cents": provider_fee,
        "net_cents": net,
    }


@router.get("/{txn_id}")
async def get_payment(txn_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    mid = _merchant_id(user_id, db)
    res = db.table("transactions").select("*").eq("id", txn_id).eq("merchant_id", mid).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Transaction not found."})
    return res.data[0]
