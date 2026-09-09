import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user_id
from app.db.connection import get_db

router = APIRouter()

MIN_WITHDRAWAL_CENTS = 5000  # R50


def _make_id() -> str:
    return f"wd_{secrets.token_hex(5)}"


def _make_reference() -> str:
    return f"WD-{secrets.token_hex(4).upper()}"


def _get_merchant(user_id: str, db):
    res = db.table("merchants").select("*").eq("user_id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found."})
    return res.data[0]


class WithdrawalRequest(BaseModel):
    amount_cents: int
    note: str | None = None


@router.get("/merchants/me/withdrawals")
async def list_withdrawals(
    limit: int = 20,
    offset: int = 0,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    merchant = _get_merchant(user_id, db)
    mid = merchant["id"]

    count_res = db.table("withdrawals").select("id", count="exact").eq("merchant_id", mid).execute()
    total = count_res.count if count_res.count is not None else len(count_res.data)

    data_res = db.table("withdrawals") \
        .select("*") \
        .eq("merchant_id", mid) \
        .order("requested_at", desc=True) \
        .limit(limit).offset(offset) \
        .execute()
    return {"data": data_res.data or [], "total": total}


@router.post("/merchants/me/withdrawals", status_code=201)
async def request_withdrawal(body: WithdrawalRequest, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    merchant = _get_merchant(user_id, db)
    mid = merchant["id"]

    # ── Guard: bank account configured ───────────────────────────────────────
    if not merchant.get("paystack_recipient_code"):
        raise HTTPException(status_code=422, detail={
            "code": "no_bank_account",
            "message": "Set up your payout account in Settings before withdrawing.",
        })

    # ── Guard: minimum amount ─────────────────────────────────────────────────
    if body.amount_cents < MIN_WITHDRAWAL_CENTS:
        raise HTTPException(status_code=422, detail={
            "code": "amount_below_minimum",
            "message": f"Minimum withdrawal is R{MIN_WITHDRAWAL_CENTS // 100}.",
        })

    # ── Compute available balance (re-check inside same request) ──────────────
    settled_res = db.table("transactions") \
        .select("net_cents") \
        .eq("merchant_id", mid) \
        .eq("status", "success") \
        .eq("settlement_status", "settled") \
        .execute()
    settled = sum(r["net_cents"] for r in (settled_res.data or []))

    inflight_res = db.table("withdrawals") \
        .select("amount_cents") \
        .eq("merchant_id", mid) \
        .in_("status", ["pending", "approved"]) \
        .execute()
    in_flight = sum(r["amount_cents"] for r in (inflight_res.data or []))

    available = max(0, settled - in_flight)

    if body.amount_cents > available:
        raise HTTPException(status_code=422, detail={
            "code": "insufficient_balance",
            "message": f"Available balance is R{available / 100:.2f}.",
        })

    # ── Insert withdrawal ─────────────────────────────────────────────────────
    row = {
        "id": _make_id(),
        "reference": _make_reference(),
        "merchant_id": mid,
        "amount_cents": body.amount_cents,
        "bank": merchant["payout_bank"],
        "account_masked": merchant["payout_account_masked"],
        "status": "pending",
        "note": body.note,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }
    res = db.table("withdrawals").insert(row).execute()
    return res.data[0]


@router.delete("/merchants/me/withdrawals/{withdrawal_id}", status_code=204)
async def cancel_withdrawal(withdrawal_id: str, user_id: str = Depends(get_current_user_id)):
    db = get_db()
    merchant = _get_merchant(user_id, db)

    wd_res = db.table("withdrawals").select("*").eq("id", withdrawal_id).eq("merchant_id", merchant["id"]).execute()
    if not wd_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Withdrawal not found."})

    wd = wd_res.data[0]
    if wd["status"] != "pending":
        raise HTTPException(status_code=409, detail={
            "code": "not_cancellable",
            "message": f"Cannot cancel a withdrawal with status '{wd['status']}'.",
        })

    db.table("withdrawals").delete().eq("id", withdrawal_id).execute()
