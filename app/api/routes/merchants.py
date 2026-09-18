from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

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
    business_name: str | None = Field(None, min_length=2, max_length=100)
    display_name: str | None = Field(None, min_length=2, max_length=100)
    trading_category: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)
    province: str | None = Field(None, max_length=100)
    settlement_cycle: str | None = Field(None, max_length=50)


class PayoutAccountRequest(BaseModel):
    bank_code: str = Field(..., max_length=20)
    account_number: str = Field(..., max_length=30)
    account_holder: str = Field(..., min_length=2, max_length=100)
    id_number: str | None = Field(None, max_length=20)
    document_type: str = Field("identityNumber", max_length=30)


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

    # ── Step 1: Paystack bank validation (both envs — blocks in prod, informational in test) ──
    if body.id_number:
        try:
            kyc = validate_bank_account(
                bank_code=body.bank_code,
                account_number=body.account_number,
                account_name=body.account_holder,
                id_number=body.id_number,
                account_type="personal",
                document_type=body.document_type,
            )
            # Always store result so admin sees it in KYC queue
            db.table("merchants").update({
                "bank_verified":         kyc.get("verified", False),
                "bank_holder_match":     kyc.get("accountHolderMatch", False),
                "bank_accepts_credits":  kyc.get("accountAcceptsCredits", False),
                "bank_account_open":     kyc.get("accountOpen", False),
                "bank_open_3_months":    kyc.get("accountOpenForMoreThanThreeMonths", False),
                "bank_verification_msg": kyc.get("verificationMessage"),
                "bank_validated_at":     datetime.now(timezone.utc).isoformat(),
            }).eq("id", mid).execute()

            # Only block in prod — test mode always returns verified=false
            if is_prod:
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
        except PaystackError as e:
            if is_prod:
                raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})
            # Test mode — Paystack blocked the call (e.g. passport in test, ZAR unsupported)
            # Store a placeholder so admin knows validation was attempted but blocked
            db.table("merchants").update({
                "bank_verified":         False,
                "bank_holder_match":     None,
                "bank_accepts_credits":  None,
                "bank_account_open":     None,
                "bank_open_3_months":    None,
                "bank_verification_msg": f"Validation blocked in test mode: {e.message}",
                "bank_validated_at":     datetime.now(timezone.utc).isoformat(),
            }).eq("id", mid).execute()
    elif is_prod:
        raise HTTPException(status_code=422, detail={"code": "id_required", "message": "ID or passport number is required."})

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

    # ── Step 3: Invalidate old KYC docs — bank changed, docs must be re-verified
    existing_docs = db.table("merchant_documents").select("id,s3_key").eq("merchant_id", mid).execute()
    for doc in (existing_docs.data or []):
        from app.services.s3_service import delete_object
        delete_object(doc["s3_key"])
    db.table("merchant_documents").delete().eq("merchant_id", mid).execute()

    # ── Step 4: Persist ───────────────────────────────────────────────────────
    updates: dict = {
        "payout_bank": bank_name,
        "payout_bank_code": body.bank_code,
        "payout_account_masked": masked,
        "payout_account_name": body.account_holder,
        "paystack_recipient_code": recipient["recipient_code"],
        "kyc_status": "verified" if is_prod else "pending",  # prod: Paystack validated; test: needs doc re-upload
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


# ── Account deletion (self-service, archive-only) ─────────────────────────────
#
# We never hard-delete on request. Eligible only when there's nothing left
# outstanding in either direction; otherwise the merchant is told exactly
# why not. Reactivation happens automatically if they ever register again
# with the same phone/email (see auth.py) — see migration 018 for the
# archived-then-never-returned purge that runs after 90 days.

def _archive_eligibility(merchant_id: str, db) -> list[dict]:
    """
    Returns structured blockers, not pre-formatted strings — the frontend
    renders amounts bold/colour-coded by `type`, which it can only do
    reliably from structured facts, not by parsing sentences.
    Empty list = eligible.
    """
    reasons = []

    pending = db.table("transactions").select("id", count="exact") \
        .eq("merchant_id", merchant_id).eq("status", "pending").execute()
    if (pending.count or 0) > 0:
        reasons.append({"type": "pending_transactions", "count": pending.count})

    inflight_res = db.table("withdrawals").select("amount_cents") \
        .eq("merchant_id", merchant_id).in_("status", ["pending", "approved"]).execute()
    in_flight = sum(r["amount_cents"] for r in (inflight_res.data or []))
    if in_flight > 0:
        reasons.append({"type": "withdrawal_in_progress", "amount_cents": in_flight})

    earned_res = db.table("transactions").select("net_cents") \
        .eq("merchant_id", merchant_id).eq("status", "success").execute()
    earned = sum(r["net_cents"] for r in (earned_res.data or []))
    paid_res = db.table("withdrawals").select("amount_cents") \
        .eq("merchant_id", merchant_id).eq("status", "paid").execute()
    paid = sum(r["amount_cents"] for r in (paid_res.data or []))
    outstanding = earned - paid - in_flight
    if outstanding > 0:
        reasons.append({"type": "balance_owed", "amount_cents": outstanding})

    return reasons


@router.delete("/me")
async def delete_my_account(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    merchant = _get_merchant(user_id, db)

    reasons = _archive_eligibility(merchant["id"], db)
    if reasons:
        raise HTTPException(status_code=409, detail={
            "code": "not_eligible",
            "message": "Your account can't be closed yet.",
            "reasons": reasons,
        })

    now = datetime.now(timezone.utc).isoformat()
    db.table("payment_codes").update({"active": False}).eq("merchant_id", merchant["id"]).execute()
    db.table("merchants").update({
        "status": "closed", "archived_at": now, "archived_by": user_id,
    }).eq("id", merchant["id"]).execute()
    db.table("users").update({
        "status": "archived", "archived_at": now, "archived_by": user_id,
    }).eq("id", user_id).execute()

    return {"status": "closed", "archived_at": now}


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
