from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.deps import require_admin
from app.db.connection import get_db
from app.services.paystack_service import initiate_transfer, get_balance, PaystackError
from app.services.settlement_service import run_settlements

router = APIRouter()
settings = get_settings()

SIMULATE_TRANSFERS = settings.environment != "prod"


class WithdrawalStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


class MerchantAdminUpdate(BaseModel):
    status: str | None = None   # active | suspended
    plan: str | None = None


class UserAdminUpdate(BaseModel):
    status: str | None = None   # active | suspended


# ── Merchants ────────────────────────────────────────────────────────────────

@router.get("/merchants")
async def list_all_merchants(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
):
    db = get_db()
    q = db.table("merchants").select("id,business_name,display_name,slug,status,plan,trading_category,city,province,created_at", count="exact").order("created_at", desc=True).limit(limit).offset(offset)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    return {"data": res.data or [], "total": res.count or 0}


@router.patch("/merchants/{merchant_id}")
async def update_merchant_admin(
    merchant_id: str,
    body: MerchantAdminUpdate,
    admin_id: str = Depends(require_admin),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail={"code": "no_fields", "message": "Nothing to update."})
    if "status" in updates and updates["status"] not in ("active", "suspended"):
        raise HTTPException(status_code=422, detail={"code": "invalid_status", "message": "Status must be active or suspended."})
    db = get_db()
    res = db.table("merchants").update(updates).eq("id", merchant_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found."})
    return res.data[0]


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_all_users(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
):
    db = get_db()
    q = db.table("users").select("id,phone,email,status,created_at", count="exact").order("created_at", desc=True).limit(limit).offset(offset)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    users = res.data or []

    # attach roles
    if users:
        user_ids = [u["id"] for u in users]
        roles_res = db.table("user_roles").select("user_id,role").in_("user_id", user_ids).execute()
        roles_map: dict[str, list] = {}
        for r in (roles_res.data or []):
            roles_map.setdefault(r["user_id"], []).append(r["role"])
        for u in users:
            u["roles"] = roles_map.get(u["id"], [])

    return {"data": users, "total": res.count or 0}


@router.patch("/users/{user_id}")
async def update_user_admin(
    user_id: str,
    body: UserAdminUpdate,
    admin_id: str = Depends(require_admin),
):
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail={"code": "no_fields", "message": "Nothing to update."})
    if "status" in updates and updates["status"] not in ("active", "suspended"):
        raise HTTPException(status_code=422, detail={"code": "invalid_status", "message": "Status must be active or suspended."})
    db = get_db()
    res = db.table("users").update(updates).eq("id", user_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found."})
    return res.data[0]


# ── Transactions (platform-wide) ──────────────────────────────────────────────

@router.get("/transactions")
async def list_all_transactions(
    status: str | None = Query(None),
    method: str | None = Query(None),
    settlement_status: str | None = Query(None),
    merchant_id: str | None = Query(None),
    since: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
):
    db = get_db()
    base = "id,merchant_id,reference,amount_cents,fee_cents,net_cents,status,method,settlement_status,created_at,paid_at,customer_label"
    count_q = db.table("transactions").select("id", count="exact")
    data_q = db.table("transactions").select(base).order("created_at", desc=True).limit(limit).offset(offset)
    if status:
        count_q = count_q.eq("status", status)
        data_q = data_q.eq("status", status)
    if method:
        count_q = count_q.eq("method", method)
        data_q = data_q.eq("method", method)
    if settlement_status:
        count_q = count_q.eq("settlement_status", settlement_status)
        data_q = data_q.eq("settlement_status", settlement_status)
    if merchant_id:
        count_q = count_q.eq("merchant_id", merchant_id)
        data_q = data_q.eq("merchant_id", merchant_id)
    if since:
        count_q = count_q.gte("created_at", since)
        data_q = data_q.gte("created_at", since)

    count_res = count_q.execute()
    total = count_res.count if count_res.count is not None else 0
    data_res = data_q.execute()
    return {"data": data_res.data or [], "total": total, "offset": offset}


# ── Balance ───────────────────────────────────────────────────────────────────

@router.get("/balance")
async def get_platform_balance(admin_id: str = Depends(require_admin)):
    """Paystack platform balance in ZAR cents."""
    try:
        return get_balance()
    except PaystackError as e:
        raise HTTPException(status_code=502, detail={"code": e.code, "message": e.message})


# ── Audit log ─────────────────────────────────────────────────────────────────

@router.get("/audit")
async def list_audit_log(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
):
    db = get_db()
    res = db.table("webhook_events") \
        .select("id,event_type,reference,payload,created_at", count="exact") \
        .order("created_at", desc=True) \
        .limit(limit).offset(offset) \
        .execute()
    return {"data": res.data or [], "total": res.count or 0}


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
