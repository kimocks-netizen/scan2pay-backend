import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.core.deps import get_current_user_id
from app.db.connection import get_db
from app.services.paystack_service import PaystackError, initialize_transaction

logger = logging.getLogger(__name__)
router = APIRouter()

CHARGE_TTL_MINUTES = 5
AMOUNT_MIN = 100
AMOUNT_MAX = 5_000_000


class ChargeCreate(BaseModel):
    amount_cents: int = Field(..., ge=AMOUNT_MIN, le=AMOUNT_MAX)
    label: str = "Amount due"


class PublicPayInit(BaseModel):
    amount_cents: int | None = Field(None, ge=AMOUNT_MIN, le=AMOUNT_MAX)
    customer_email: str | None = None
    customer_label: str = "Customer"


def _merchant_id(user_id: str, db) -> str:
    res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]["id"]


def _make_txn_id(db) -> str:
    import secrets
    # use random suffix to avoid collisions — count+1 can duplicate under concurrent requests
    rand = secrets.token_hex(3).upper()
    try:
        n = (db.table("transactions").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(rand, 16) % 100000
    return f"txn_{str(n).zfill(6)}{rand}"


def _calc_fees(amount_cents: int, plan_percent: float) -> tuple[int, int, int]:
    platform = round(amount_cents * plan_percent / 100)
    provider = round(amount_cents * 2.9 / 100) + 100
    net = amount_cents - platform - provider
    return platform, provider, net


def _get_primary_code(mid: str, db) -> dict:
    res = db.table("payment_codes").select("*").eq("merchant_id", mid).eq("is_primary", True).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Primary QR code not found."})
    return res.data[0]


@router.post("/charges", status_code=201)
async def create_charge(body: ChargeCreate, user_id: str = Depends(get_current_user_id)):
    """
    Type 2 charge flow — creates a pending transaction against the merchant's
    permanent primary QR. The QR itself never changes. The amount is stored on
    the transaction and surfaced to the customer when they scan.
    """
    db = get_db()
    mid = _merchant_id(user_id, db)
    pc = _get_primary_code(mid, db)

    # cancel any existing active charge session (merchant started a new one)
    try:
        expires_cutoff = datetime.now(timezone.utc).isoformat()
        existing = (
            db.table("transactions")
            .select("id")
            .eq("merchant_id", mid)
            .eq("payment_code_id", pc["id"])
            .eq("status", "pending")
            .eq("charge_session", True)
            .gt("charge_expires_at", expires_cutoff)
            .execute()
        )
        if existing.data:
            db.table("transactions").update({"status": "failed", "failure_reason": "superseded"}).in_(
                "id", [r["id"] for r in existing.data]
            ).execute()
    except Exception:
        pass  # migration not run yet — safe to ignore

    # fees
    mch_res = db.table("merchants").select("plan_id").eq("id", mid).execute()
    plan_id = mch_res.data[0]["plan_id"] if mch_res.data else "plan_free"
    plan_res = db.table("plans").select("platform_fee_percent").eq("id", plan_id).execute()
    plan_percent = float(plan_res.data[0]["platform_fee_percent"]) if plan_res.data else 2.5
    platform_fee, provider_fee, net = _calc_fees(body.amount_cents, plan_percent)

    pricing_res = db.table("pricing_versions").select("id").eq("plan_id", plan_id).order("created_at", desc=True).limit(1).execute()
    pricing_version = pricing_res.data[0]["id"] if pricing_res.data else "pv_unknown"

    txn_id = _make_txn_id(db)
    txn_reference = f"STP{txn_id.replace('txn_', '').upper()}"
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=CHARGE_TTL_MINUTES)

    # call Paystack first so we can store access_code on the transaction
    try:
        result = initialize_transaction(
            email="anonymous@scan2pay.co.za",
            amount_cents=body.amount_cents,
            reference=txn_reference,
            metadata={
                "merchant_id": mid,
                "payment_code_id": pc["id"],
                "single_use": "false",
                "txn_id": txn_id,
                "charge_session": "true",
            },
        )
    except PaystackError as e:
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})

    insert_data = {
        "id": txn_id,
        "reference": txn_reference,
        "paystack_reference": result["reference"],
        "merchant_id": mid,
        "payment_code_id": pc["id"],
        "item": body.label,
        "amount_cents": body.amount_cents,
        "platform_fee_cents": platform_fee,
        "provider_fee_cents": provider_fee,
        "net_cents": net,
        "status": "pending",
        "method": "card",
        "customer_label": "Customer",
        "settlement_status": "pending",
        "pricing": {"plan_percent": plan_percent, "provider_rate": 2.9, "provider_fixed": 100},
        "plan_id_at_time": plan_id,
        "pricing_version": pricing_version,
    }
    # add charge session fields if migration has been run
    try:
        insert_data["charge_session"] = True
        insert_data["charge_expires_at"] = expires_at.isoformat()
        insert_data["access_code_paystack"] = result["access_code"]
    except Exception:
        pass
    db.table("transactions").insert(insert_data).execute()

    return {
        "txn_id": txn_id,
        "reference": txn_reference,
        "access_code": result["access_code"],
        "amount_cents": body.amount_cents,
        "qr_reference": pc["reference"],   # permanent QR reference to show on screen
        "expires_at": expires_at.isoformat(),
    }


@router.get("/pay/{reference}")
async def resolve_code(reference: str):
    """
    Public — resolves any QR reference to merchant + code info.
    For the primary QR, checks if there is an active charge session
    and if so returns the fixed amount from it instead of variable.
    """
    db = get_db()
    res = db.table("payment_codes").select("*").eq("reference", reference).eq("active", True).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found or inactive."})
    code = res.data[0]

    # resolve product price for fixed-mode codes (Type 3)
    product = None
    if code.get("product_id"):
        pr = db.table("products").select("id,name,description,price_cents,category").eq("id", code["product_id"]).execute()
        if pr.data:
            product = pr.data[0]
            code["amount_cents"] = product["price_cents"]

    # check for active charge session on this QR (Type 2 — merchant set an amount)
    charge_session = None
    if code.get("is_primary") and not code.get("product_id"):
        try:
            now = datetime.now(timezone.utc).isoformat()
            session_res = (
                db.table("transactions")
                .select("id,amount_cents,charge_expires_at,access_code_paystack")
                .eq("payment_code_id", code["id"])
                .eq("status", "pending")
                .eq("charge_session", True)
                .gt("charge_expires_at", now)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if session_res.data:
                s = session_res.data[0]
                charge_session = {
                    "txn_id": s["id"],
                    "amount_cents": s["amount_cents"],
                    "expires_at": s["charge_expires_at"],
                    "access_code": s.get("access_code_paystack"),
                }
                code["mode"] = "amount"
                code["amount_cents"] = s["amount_cents"]
        except Exception:
            logger.warning("charge_session query failed — migration 011 may not be run yet")

    merchant = db.table("merchants").select("id,display_name,trading_category,city,province").eq("id", code["merchant_id"]).execute()
    return {
        "code": code,
        "merchant": merchant.data[0] if merchant.data else None,
        "product": product,
        "charge_session": charge_session,
    }


@router.post("/pay/{reference}/initialise", status_code=201)
async def public_pay_initialise(reference: str, body: PublicPayInit):
    """Public — no auth. Customer initiates payment from the pay page."""
    db = get_db()

    pc_res = db.table("payment_codes").select("*").eq("reference", reference).execute()
    if not pc_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Payment code not found."})
    pc = pc_res.data[0]

    if not pc.get("active"):
        raise HTTPException(status_code=410, detail={"code": "expired", "message": "This payment code is no longer active."})

    # check for active charge session — if found, use it directly (Paystack already initialised)
    if pc.get("is_primary"):
        try:
            now = datetime.now(timezone.utc).isoformat()
            session_res = (
                db.table("transactions")
                .select("id,amount_cents,paystack_reference,charge_expires_at,access_code_paystack")
                .eq("payment_code_id", pc["id"])
                .eq("status", "pending")
                .eq("charge_session", True)
                .gt("charge_expires_at", now)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            if session_res.data:
                s = session_res.data[0]
                access_code = s.get("access_code_paystack")
                if not access_code:
                    from app.services.paystack_service import initialize_transaction as _init
                    email = body.customer_email or "anonymous@scan2pay.co.za"
                    try:
                        result = _init(
                            email=email,
                            amount_cents=s["amount_cents"],
                            reference=s["paystack_reference"],
                            metadata={"merchant_id": pc["merchant_id"], "payment_code_id": pc["id"], "txn_id": s["id"], "single_use": "false"},
                        )
                        access_code = result["access_code"]
                    except PaystackError as e:
                        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})
                return {"txn_id": s["id"], "access_code": access_code, "amount_cents": s["amount_cents"]}
        except HTTPException:
            raise
        except Exception:
            logger.warning("charge_session lookup failed in initialise — migration 011 may not be run yet")

    # no charge session — normal flow (variable or fixed/product)
    if pc.get("expires_at") and datetime.fromisoformat(pc["expires_at"]) < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail={"code": "expired", "message": "This payment request has expired."})

    # resolve amount
    if pc["mode"] == "amount":
        amount_cents = pc["amount_cents"]
    elif pc["mode"] == "fixed" and pc.get("product_id"):
        pr = db.table("products").select("price_cents").eq("id", pc["product_id"]).execute()
        if not pr.data:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Product not found."})
        amount_cents = pr.data[0]["price_cents"]
    elif body.amount_cents:
        amount_cents = body.amount_cents
    else:
        raise HTTPException(status_code=422, detail={"code": "amount_required", "message": "Please enter an amount."})

    mid = pc["merchant_id"]
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
                "single_use": "false",
                "txn_id": txn_id,
            },
        )
    except PaystackError as e:
        db.table("transactions").update({"status": "failed", "failure_reason": e.message}).eq("id", txn_id).execute()
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})

    db.table("transactions").update({"paystack_reference": result["reference"]}).eq("id", txn_id).execute()

    return {"txn_id": txn_id, "access_code": result["access_code"], "amount_cents": amount_cents}
