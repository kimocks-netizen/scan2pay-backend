from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.deps import get_current_user_id
from app.db.connection import get_db
from app.services.paystack_service import (
    create_transfer_recipient,
    validate_bank_account,
    PaystackError,
)

router = APIRouter()
settings = get_settings()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_merchant(user_id: str, db):
    res = db.table("merchants").select("*").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant profile not found."})
    return res.data[0]


# ── Models ────────────────────────────────────────────────────────────────────

class MerchantUpdate(BaseModel):
    business_name: str | None = None
    display_name: str | None = None
    trading_category: str | None = None
    city: str | None = None
    province: str | None = None
    settlement_cycle: str | None = None


class PayoutAccountRequest(BaseModel):
    bank_code: str
    account_number: str
    account_holder: str
    id_number: str | None = None
    document_type: str = "identityNumber"  # identityNumber | passportNumber


class ReferralUpdate(BaseModel):
    referral_code: str


# ── /me routes (must be before /{merchant_id} wildcard) ──────────────────────

@router.patch("/me/referral")
async def set_referral(body: ReferralUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    merchant = _get_merchant(user_id, db)
    # Only set if not already referred
    if merchant.get("referred_by"):
        return {"referred_by": merchant["referred_by"]}
    # Validate the code is a real user
    ref = db.table("users").select("id").eq("id", body.referral_code).execute()
    if not ref.data:
        raise HTTPException(status_code=422, detail={"code": "invalid_referral", "message": "Invalid referral code."})
    res = db.table("merchants").update({"referred_by": body.referral_code}).eq("id", merchant["id"]).execute()
    return {"referred_by": res.data[0]["referred_by"]}


@router.get("/me")
async def get_my_merchant(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    return _get_merchant(user_id, db)


@router.patch("/me")
async def update_my_merchant(body: MerchantUpdate, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    merchant = _get_merchant(user_id, db)
    updates = body.model_dump(exclude_none=True)
    if not updates:
        return merchant
    res = db.table("merchants").update(updates).eq("id", merchant["id"]).execute()
    return res.data[0]


@router.patch("/me/payout-account")
async def save_payout_account(body: PayoutAccountRequest, user_id: str = Depends(get_current_user_id)):
    """
    1. In prod: KYC via POST /bank/validate — reject if not verified.
    2. Create Paystack transfer recipient.
    3. Save bank details + recipient code on merchant.
    """
    db = get_db()
    merchant = _get_merchant(user_id, db)
    mid = merchant["id"]
    is_prod = settings.environment == "prod"

    # ── Step 1: KYC (prod only) ───────────────────────────────────────────────
    if is_prod:
        if not body.id_number:
            raise HTTPException(status_code=422, detail={"code": "id_required", "message": "ID or passport number is required."})
        try:
            kyc = validate_bank_account(
                bank_code=body.bank_code,
                account_number=body.account_number,
                account_name=body.account_holder,
                id_number=body.id_number,
                account_type="personal",
                document_type=body.document_type,
            )
        except PaystackError as e:
            raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})

        if not kyc.get("verified"):
            db.table("merchants").update({"kyc_status": "failed"}).eq("id", mid).execute()
            raise HTTPException(status_code=422, detail={
                "code": "kyc_failed",
                "message": kyc.get("verificationMessage", "KYC verification failed."),
            })
        if not kyc.get("accountAcceptsCredits"):
            raise HTTPException(status_code=422, detail={
                "code": "account_no_credits",
                "message": "This account cannot receive transfers.",
            })

    # ── Step 2: Create Paystack recipient ─────────────────────────────────────
    try:
        recipient = create_transfer_recipient(
            name=body.account_holder,
            account_number=body.account_number,
            bank_code=body.bank_code,
        )
    except PaystackError as e:
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})

    bank_name = recipient.get("details", {}).get("bank_name", "")
    masked = f"**** {body.account_number[-4:]}"

    # ── Step 3: Persist ───────────────────────────────────────────────────────
    updates: dict = {
        "payout_bank": bank_name,
        "payout_bank_code": body.bank_code,
        "payout_account_masked": masked,
        "payout_account_name": body.account_holder,
        "paystack_recipient_code": recipient["recipient_code"],
        "kyc_status": "verified" if is_prod else "pending",
    }
    if is_prod:
        updates["kyc_verified_at"] = datetime.now(timezone.utc).isoformat()

    res = db.table("merchants").update(updates).eq("id", mid).execute()
    m = res.data[0]
    return {
        "id": m["id"],
        "payout_bank": m["payout_bank"],
        "payout_bank_code": m["payout_bank_code"],
        "payout_account_masked": m["payout_account_masked"],
        "payout_account_name": m["payout_account_name"],
        "paystack_recipient_code": m["paystack_recipient_code"],
        "kyc_status": m["kyc_status"],
    }


@router.get("/me/balance")
async def get_my_balance(user_id: str = Depends(get_current_user_id)):
    """
    available_cents          = settled net_cents - in-flight withdrawals
    pending_settlement_cents = earned but not yet settled by cron
    in_flight_cents          = pending + approved withdrawal amounts
    withdrawn_cents          = total paid withdrawals
    """
    db = get_db()
    merchant = _get_merchant(user_id, db)
    mid = merchant["id"]

    settled_res = db.table("transactions").select("net_cents") \
        .eq("merchant_id", mid).eq("status", "success").eq("settlement_status", "settled").execute()
    settled = sum(r["net_cents"] for r in (settled_res.data or []))

    pending_res = db.table("transactions").select("net_cents") \
        .eq("merchant_id", mid).eq("status", "success").eq("settlement_status", "pending").execute()
    pending_settlement = sum(r["net_cents"] for r in (pending_res.data or []))

    inflight_res = db.table("withdrawals").select("amount_cents") \
        .eq("merchant_id", mid).in_("status", ["pending", "approved"]).execute()
    in_flight = sum(r["amount_cents"] for r in (inflight_res.data or []))

    withdrawn_res = db.table("withdrawals").select("amount_cents") \
        .eq("merchant_id", mid).eq("status", "paid").execute()
    withdrawn = sum(r["amount_cents"] for r in (withdrawn_res.data or []))

    return {
        "available_cents": max(0, settled - in_flight),
        "pending_settlement_cents": pending_settlement,
        "in_flight_cents": in_flight,
        "withdrawn_cents": withdrawn,
    }


# ── /{merchant_id} wildcard — must be last ────────────────────────────────────

@router.get("/{merchant_id}")
async def get_merchant(merchant_id: str):
    db = get_db()
    res = db.table("merchants") \
        .select("id,business_name,display_name,slug,trading_category,city,province,status") \
        .eq("id", merchant_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found."})
    return res.data[0]
