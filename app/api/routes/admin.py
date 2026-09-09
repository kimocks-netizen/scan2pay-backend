from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.deps import require_admin
from app.db.connection import get_db
from app.services.paystack_service import initiate_transfer, PaystackError
from app.services.settlement_service import run_settlements

router = APIRouter()
settings = get_settings()

SIMULATE_TRANSFERS = settings.environment != "prod"


class WithdrawalStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


# ── Settlements ───────────────────────────────────────────────────────────────

@router.get("/settlements/pending")
async def list_pending_settlements(admin_id: str = Depends(require_admin)):
    """Merchants that have success+pending transactions — grouped summary."""
    db = get_db()
    txns = (
        db.table("transactions")
        .select("merchant_id, net_cents, paid_at")
        .eq("status", "success")
        .eq("settlement_status", "pending")
        .execute()
        .data or []
    )
    if not txns:
        return []

    merchant_ids = list({t["merchant_id"] for t in txns})
    merchants = (
        db.table("merchants")
        .select("id, business_name, display_name")
        .in_("id", merchant_ids)
        .execute()
        .data or []
    )
    name_map = {m["id"]: m.get("display_name") or m.get("business_name") for m in merchants}

    by_merchant: dict[str, dict] = {}
    for t in txns:
        mid = t["merchant_id"]
        if mid not in by_merchant:
            by_merchant[mid] = {"txn_count": 0, "pending_cents": 0, "oldest_paid_at": t["paid_at"]}
        by_merchant[mid]["txn_count"] += 1
        by_merchant[mid]["pending_cents"] += t["net_cents"]
        if t["paid_at"] and (not by_merchant[mid]["oldest_paid_at"] or t["paid_at"] < by_merchant[mid]["oldest_paid_at"]):
            by_merchant[mid]["oldest_paid_at"] = t["paid_at"]

    return [
        {
            "merchant_id": mid,
            "merchant_name": name_map.get(mid, mid),
            **data,
        }
        for mid, data in by_merchant.items()
    ]


@router.post("/settlements/run")
async def run_settlement_now(
    merchant_id: str | None = None,
    admin_id: str = Depends(require_admin),
):
    """
    Manually trigger settlement.
    - No merchant_id → run all merchants that have eligible pending transactions.
    - merchant_id=X  → run only that merchant.
    """
    db = get_db()
    result = run_settlements(db, merchant_id=merchant_id)
    return result


# ── Withdrawals ───────────────────────────────────────────────────────────────

@router.get("/withdrawals")
async def list_all_withdrawals(
    status: str | None = None,
    admin_id: str = Depends(require_admin),
):
    db = get_db()
    q = db.table("withdrawals").select("*").order("requested_at", desc=True)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    return res.data or []


@router.patch("/withdrawals/{withdrawal_id}/status")
async def update_withdrawal_status(
    withdrawal_id: str,
    body: WithdrawalStatusUpdate,
    admin_id: str = Depends(require_admin),
):
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail={"code": "invalid_status", "message": "Status must be 'approved' or 'rejected'."})

    db = get_db()
    wd_res = db.table("withdrawals").select("*").eq("id", withdrawal_id).execute()
    if not wd_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Withdrawal not found."})

    wd = wd_res.data[0]
    if wd["status"] != "pending":
        raise HTTPException(status_code=409, detail={
            "code": "already_decided",
            "message": f"Withdrawal is already '{wd['status']}'.",
        })

    now = datetime.now(timezone.utc).isoformat()

    if body.status == "rejected":
        res = db.table("withdrawals").update({
            "status": "rejected",
            "failure_reason": body.reason,
            "decided_at": now,
            "decided_by": admin_id,
        }).eq("id", withdrawal_id).execute()
        return res.data[0]

    # ── Approve: fetch merchant recipient code ────────────────────────────────
    merchant_res = db.table("merchants").select("paystack_recipient_code,payout_bank,payout_account_masked") \
        .eq("id", wd["merchant_id"]).execute()
    if not merchant_res.data:
        raise HTTPException(status_code=404, detail={"code": "merchant_not_found", "message": "Merchant not found."})

    merchant = merchant_res.data[0]
    if not merchant.get("paystack_recipient_code"):
        raise HTTPException(status_code=422, detail={
            "code": "no_recipient_code",
            "message": "Merchant has no Paystack recipient code.",
        })

    if SIMULATE_TRANSFERS:
        # Test mode — skip Paystack, mark approved with simulated transfer code
        res = db.table("withdrawals").update({
            "status": "approved",
            "transfer_code": "SIMULATED",
            "decided_at": now,
            "decided_by": admin_id,
        }).eq("id", withdrawal_id).execute()
        return res.data[0]

    # ── Prod: initiate real Paystack transfer ─────────────────────────────────
    try:
        transfer = initiate_transfer(
            amount_cents=wd["amount_cents"],
            recipient_code=merchant["paystack_recipient_code"],
            reference=wd["reference"],
            reason=f"Scan2Pay payout — {wd['reference']}",
        )
    except PaystackError as e:
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})

    res = db.table("withdrawals").update({
        "status": "approved",
        "transfer_code": transfer.get("transfer_code"),
        "decided_at": now,
        "decided_by": admin_id,
    }).eq("id", withdrawal_id).execute()
    return res.data[0]
