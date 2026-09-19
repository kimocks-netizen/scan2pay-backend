import calendar
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.audit import log_admin_action
from app.core.config import get_settings
from app.core.deps import require_admin, require_staff
from app.db.connection import get_db
from app.services.paystack_service import initiate_transfer, get_balance, PaystackError
from app.services.settlement_service import run_settlements
from app.services.sms_service import send_sms

router = APIRouter()
settings = get_settings()

SIMULATE_TRANSFERS = settings.environment != "prod"


class WithdrawalStatusUpdate(BaseModel):
    status: str
    reason: str | None = None


class MerchantAdminUpdate(BaseModel):
    status: str | None = None
    plan: str | None = None


class UserAdminUpdate(BaseModel):
    status: str | None = None


class PricingVersionCreate(BaseModel):
    name: str
    plan_id: str
    monthly_subscription_cents: int = 0
    platform_fee_percent: float
    platform_fixed_fee_cents: int = 0
    provider_percent: float = 2.90
    provider_fixed_cents: int = 100
    fee_bearer: str = "merchant"
    effective_from: str
    note: str = ""


# ── Pricing ──────────────────────────────────────────────────────────────────


@router.get("/kyc/bank-checks")
async def list_bank_checks(staff_id: str = Depends(require_staff)):
    """Merchants who have run Paystack bank validation — for admin KYC review."""
    db = get_db()
    res = db.table("merchants") \
        .select("id,business_name,kyc_status,payout_bank,payout_account_masked,payout_account_name,bank_verified,bank_holder_match,bank_accepts_credits,bank_account_open,bank_open_3_months,bank_verification_msg,bank_validated_at") \
        .not_.is_("bank_validated_at", "null") \
        .order("bank_validated_at", desc=True) \
        .execute()
    return res.data or []


@router.get("/pricing")
async def list_pricing_versions(admin_id: str = Depends(require_admin)):
    db = get_db()
    res = db.table("pricing_versions").select("*").order("version", desc=True).execute()
    return res.data or []


@router.get("/plans")
async def list_plans(admin_id: str = Depends(require_admin)):
    db = get_db()
    res = db.table("plans").select("*").eq("active", True).order("monthly_price_cents").execute()
    return res.data or []


@router.post("/pricing")
async def publish_pricing_version(
    body: PricingVersionCreate,
    admin_id: str = Depends(require_admin),
):
    db = get_db()

    # Get next version number for this plan
    existing = db.table("pricing_versions").select("version") \
        .eq("plan_id", body.plan_id).order("version", desc=True).limit(1).execute()
    next_version = (existing.data[0]["version"] + 1) if existing.data else 1

    # Retire current published version for this plan
    db.table("pricing_versions").update({"status": "retired"}) \
        .eq("plan_id", body.plan_id).eq("status", "published").execute()

    import secrets
    pv_id = f"pv_{secrets.token_hex(6)}"

    res = db.table("pricing_versions").insert({
        "id": pv_id,
        "version": next_version,
        "name": body.name,
        "plan_id": body.plan_id,
        "monthly_subscription_cents": body.monthly_subscription_cents,
        "platform_fee_percent": body.platform_fee_percent,
        "platform_fixed_fee_cents": body.platform_fixed_fee_cents,
        "provider_percent": body.provider_percent,
        "provider_fixed_cents": body.provider_fixed_cents,
        "fee_bearer": body.fee_bearer,
        "effective_from": body.effective_from,
        "status": "published",
        "created_by": admin_id,
        "note": body.note,
    }).execute()
    log_admin_action(admin_id, "pricing.publish", "plan", body.plan_id, {"version": next_version, "name": body.name})
    return res.data[0]


# ── Merchants ────────────────────────────────────────────────────────────────

@router.get("/merchants")
async def list_all_merchants(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    staff_id: str = Depends(require_staff),
):
    db = get_db()
    q = db.table("merchants").select("id,user_id,business_name,display_name,slug,status,plan_id,trading_category,city,province,created_at,archived_at,archive_reason", count="exact").order("created_at", desc=True).limit(limit).offset(offset)
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
    log_admin_action(admin_id, "merchant.update", "merchant", merchant_id, updates)
    return res.data[0]


class MerchantArchiveRequest(BaseModel):
    reason: str


@router.post("/merchants/{merchant_id}/archive")
async def archive_merchant_admin(
    merchant_id: str,
    body: MerchantArchiveRequest,
    admin_id: str = Depends(require_admin),
):
    """
    Admin-forced archive — bypasses the eligibility checks the merchant's own
    DELETE /merchants/me is subject to (e.g. closing a fraudulent account).
    Use with care: money owing in either direction is NOT re-checked here.
    """
    db = get_db()
    m = db.table("merchants").select("id,user_id").eq("id", merchant_id).execute()
    if not m.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found."})
    user_id = m.data[0]["user_id"]

    now = datetime.now(timezone.utc).isoformat()
    db.table("payment_codes").update({"active": False}).eq("merchant_id", merchant_id).execute()
    db.table("merchants").update({
        "status": "closed", "archived_at": now, "archived_by": admin_id, "archive_reason": body.reason,
    }).eq("id", merchant_id).execute()
    db.table("users").update({
        "status": "archived", "archived_at": now, "archived_by": admin_id, "archive_reason": body.reason,
    }).eq("id", user_id).execute()

    log_admin_action(admin_id, "merchant.archive", "merchant", merchant_id, {"reason": body.reason})
    return {"status": "closed", "archived_at": now}


@router.post("/merchants/{merchant_id}/reactivate")
async def reactivate_merchant_admin(merchant_id: str, admin_id: str = Depends(require_admin)):
    """Manual reactivation, without waiting for the merchant to re-register."""
    db = get_db()
    m = db.table("merchants").select("id,user_id,status").eq("id", merchant_id).execute()
    if not m.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found."})
    if m.data[0]["status"] != "closed":
        raise HTTPException(status_code=422, detail={"code": "not_archived", "message": "This account isn't archived."})
    user_id = m.data[0]["user_id"]

    now = datetime.now(timezone.utc).isoformat()
    db.table("merchants").update({"status": "active"}).eq("id", merchant_id).execute()
    user_res = db.table("users").select("reactivation_count").eq("id", user_id).execute()
    count = (user_res.data[0]["reactivation_count"] if user_res.data else 0) or 0
    db.table("users").update({
        "status": "active", "reactivated_at": now, "reactivation_count": count + 1,
    }).eq("id", user_id).execute()
    db.table("payment_codes").update({"active": True}).eq("merchant_id", merchant_id).eq("is_primary", True).execute()

    log_admin_action(admin_id, "merchant.reactivate", "merchant", merchant_id, None)
    return {"status": "active", "reactivated_at": now}


# ── Users ─────────────────────────────────────────────────────────────────────

@router.get("/users")
async def list_all_users(
    status: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    staff_id: str = Depends(require_staff),
):
    db = get_db()
    q = db.table("users").select("id,full_name,phone,email,user_type,status,created_at,archived_at,archive_reason,reactivated_at", count="exact").order("created_at", desc=True).limit(limit).offset(offset)
    if status:
        q = q.eq("status", status)
    res = q.execute()
    users = res.data or []

    if users:
        user_ids = [u["id"] for u in users]
        # attach roles
        roles_res = db.table("user_roles").select("user_id,role").in_("user_id", user_ids).execute()
        roles_map: dict[str, list] = {}
        for r in (roles_res.data or []):
            roles_map.setdefault(r["user_id"], []).append(r["role"])
        # attach merchant_id for merchant users
        merchants_res = db.table("merchants").select("user_id,id").in_("user_id", user_ids).execute()
        merchant_map = {m["user_id"]: m["id"] for m in (merchants_res.data or [])}
        for u in users:
            u["roles"] = roles_map.get(u["id"], [])
            u["merchant_id"] = merchant_map.get(u["id"])

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
    log_admin_action(admin_id, "user.update", "user", user_id, updates)
    return res.data[0]


# ── Growth analytics ─────────────────────────────────────────────────────────
#
# Week/fortnight comparisons are elapsed-day-matched: the "previous" window is
# truncated to the same number of days as the current (partial) one, so e.g.
# on a Wednesday we compare "Sun–Wed this week" against "Sun–Wed last week"
# rather than a partial week against a full one.
#
# Month comparison is different on purpose: it always uses the last two FULLY
# COMPLETE calendar months (e.g. August vs July), never the current partial
# month — comparing a partial month against a complete one is misleading, so
# that comparison simply isn't offered until the month ends. The current
# (partial) month still shows up as the latest bar in `monthly_12`.

def _to_date(iso: str) -> date:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).date()


def _week_start(d: date) -> date:
    """Most recent Sunday on/before `d` (Sunday-anchored calendar week)."""
    days_since_sunday = (d.weekday() + 1) % 7
    return d - timedelta(days=days_since_sunday)


def _month_bounds(d: date) -> tuple[date, date]:
    start = d.replace(day=1)
    end = d.replace(day=calendar.monthrange(d.year, d.month)[1])
    return start, end


def _count_between(rows: list[dict], start: date, end: date) -> int:
    return sum(1 for r in rows if start <= _to_date(r["created_at"]) <= end)


def _active_between(txn_rows: list[dict], start: date, end: date) -> int:
    """Count of distinct merchants with >=1 successful transaction in [start, end]."""
    merchant_ids = {
        r["merchant_id"] for r in txn_rows
        if r.get("paid_at") and start <= _to_date(r["paid_at"]) <= end
    }
    return len(merchant_ids)


def _period(rows_m: list[dict], rows_u: list[dict], start: date, end: date, txn_rows: list[dict] | None = None) -> dict:
    period = {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "merchants": _count_between(rows_m, start, end),
        "users": _count_between(rows_u, start, end),
    }
    if txn_rows is not None:
        # "Active" = had >=1 successful payment in the window. Every regular
        # account has exactly one merchant row (merchants.user_id), so active
        # merchants and active users are the same underlying count here —
        # staff (admin/support) never process payments, so they're excluded
        # either way. Returned as two fields for symmetry with the totals
        # the frontend already renders per-audience (Businesses vs Users).
        active = _active_between(txn_rows, start, end)
        period["active_merchants"] = active
        period["active_users"] = active
    return period


@router.get("/growth")
async def get_growth_stats(staff_id: str = Depends(require_staff)):
    db = get_db()
    m_rows = db.table("merchants").select("created_at").limit(5000).execute().data or []
    u_rows = db.table("users").select("created_at").limit(5000).execute().data or []
    txn_rows = (
        db.table("transactions")
        .select("merchant_id,paid_at")
        .eq("status", "success")
        .order("paid_at", desc=True)
        .limit(5000)
        .execute()
        .data or []
    )

    today = datetime.now(timezone.utc).date()

    # ── Week: Sunday-anchored, elapsed-day-matched ────────────────────────────
    cur_week_start = _week_start(today)
    elapsed_week = (today - cur_week_start).days + 1
    prev_week_start = cur_week_start - timedelta(days=7)
    prev_week_end = prev_week_start + timedelta(days=elapsed_week - 1)
    week = {
        "current": _period(m_rows, u_rows, cur_week_start, today, txn_rows),
        "previous": _period(m_rows, u_rows, prev_week_start, prev_week_end, txn_rows),
        "elapsed_days": elapsed_week,
    }

    # ── Fortnight: two Sunday-anchored weeks, elapsed-day-matched ─────────────
    cur_fort_start = cur_week_start - timedelta(days=7)
    elapsed_fort = (today - cur_fort_start).days + 1
    prev_fort_start = cur_fort_start - timedelta(days=14)
    prev_fort_end = prev_fort_start + timedelta(days=elapsed_fort - 1)
    fortnight = {
        "current": _period(m_rows, u_rows, cur_fort_start, today, txn_rows),
        "previous": _period(m_rows, u_rows, prev_fort_start, prev_fort_end, txn_rows),
        "elapsed_days": elapsed_fort,
    }

    # ── Month: always the last two COMPLETE calendar months ───────────────────
    this_month_start, _ = _month_bounds(today)
    last_complete_end = this_month_start - timedelta(days=1)
    last_complete_start, _ = _month_bounds(last_complete_end)
    prev_complete_end = last_complete_start - timedelta(days=1)
    prev_complete_start, _ = _month_bounds(prev_complete_end)
    month = {
        "current": {**_period(m_rows, u_rows, last_complete_start, last_complete_end, txn_rows),
                    "label": last_complete_start.strftime("%b %Y")},
        "previous": {**_period(m_rows, u_rows, prev_complete_start, prev_complete_end, txn_rows),
                     "label": prev_complete_start.strftime("%b %Y")},
    }

    # ── Trend series for charts ────────────────────────────────────────────────
    daily_30 = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        daily_30.append({"label": d.strftime("%d %b"), **_period(m_rows, u_rows, d, d)})

    weekly_12 = []
    for i in range(11, -1, -1):
        ws = cur_week_start - timedelta(days=7 * i)
        we = ws + timedelta(days=6)
        weekly_12.append({"label": ws.strftime("%d %b"), **_period(m_rows, u_rows, ws, we)})

    monthly_12 = []
    cursor = this_month_start
    month_starts = []
    for _ in range(12):
        month_starts.append(cursor)
        cursor = (cursor - timedelta(days=1)).replace(day=1)
    for ms in reversed(month_starts):
        me = _month_bounds(ms)[1]
        monthly_12.append({
            "label": ms.strftime("%b %y"),
            "merchants": _count_between(m_rows, ms, me),
            "users": _count_between(u_rows, ms, me),
            "cum_merchants": sum(1 for r in m_rows if _to_date(r["created_at"]) <= me),
            "cum_users": sum(1 for r in u_rows if _to_date(r["created_at"]) <= me),
        })

    return {
        "week": week,
        "fortnight": fortnight,
        "month": month,
        "daily_30": daily_30,
        "weekly_12": weekly_12,
        "monthly_12": monthly_12,
        "totals": {"merchants": len(m_rows), "users": len(u_rows)},
    }


# ── Transactions (platform-wide) ──────────────────────────────────────────────

@router.get("/transactions")
async def list_all_transactions(
    status: str | None = Query(None),
    method: str | None = Query(None),
    settlement_status: str | None = Query(None),
    merchant_id: str | None = Query(None),
    since: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
    staff_id: str = Depends(require_staff),
):
    db = get_db()
    base = "id,merchant_id,reference,amount_cents,platform_fee_cents,net_cents,status,method,settlement_status,created_at,paid_at,customer_label"
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
    if q:
        # Frontend has sent `q` here for a while — the backend just never had
        # a matching param, so the admin search box has been a no-op.
        term = f"%{q}%"
        or_filter = f"reference.ilike.{term},customer_label.ilike.{term}"
        count_q = count_q.or_(or_filter)
        data_q = data_q.or_(or_filter)

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
    event_type: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
):
    db = get_db()
    query = db.table("webhook_events") \
        .select("id,event_type,provider_reference,payload,created_at", count="exact") \
        .order("created_at", desc=True) \
        .limit(limit).offset(offset)
    if event_type:
        query = query.eq("event_type", event_type)
    if q:
        query = query.or_(f"provider_reference.ilike.%{q}%")
    res = query.execute()
    return {"data": res.data or [], "total": res.count or 0}


@router.get("/audit-log")
async def list_admin_audit_log(
    action: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin_id: str = Depends(require_admin),
):
    """Admin write-action trail — who did what, to which resource, when."""
    db = get_db()
    query = db.table("admin_audit_log") \
        .select("id,admin_id,action,target_type,target_id,detail,created_at", count="exact") \
        .order("created_at", desc=True) \
        .limit(limit).offset(offset)
    if action:
        query = query.eq("action", action)
    if q:
        # Searches target_id/action only — admin_name isn't a column on this
        # table (it's resolved below via a join-by-hand on admin_id), and a
        # cross-table ilike lookup against `users` to support name search hit
        # an unrelated Supabase-edge (Cloudflare Worker) 500 in testing, so
        # it's left out rather than shipping something flaky.
        term = f"%{q}%"
        query = query.or_(f"target_id.ilike.{term},action.ilike.{term}")
    res = query.execute()
    entries = res.data or []

    if entries:
        admin_ids = list({e["admin_id"] for e in entries})
        admins = db.table("users").select("id,full_name").in_("id", admin_ids).execute()
        name_map = {a["id"]: a["full_name"] for a in (admins.data or [])}
        for e in entries:
            e["admin_name"] = name_map.get(e["admin_id"], "Unknown")

    return {"data": entries, "total": res.count or 0}


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
    log_admin_action(admin_id, "settlement.run", "merchant", merchant_id or "all", result if isinstance(result, dict) else None)
    return result


# ── Withdrawals ───────────────────────────────────────────────────────────────

@router.get("/withdrawals")
async def list_all_withdrawals(
    status: str | None = Query(None),
    merchant_id: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    staff_id: str = Depends(require_staff),
):
    db = get_db()
    q = db.table("withdrawals").select("*", count="exact").order("requested_at", desc=True).limit(limit).offset(offset)
    if status:
        q = q.eq("status", status)
    if merchant_id:
        q = q.eq("merchant_id", merchant_id)
    res = q.execute()
    return {"data": res.data or [], "total": res.count or 0}


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

    async def _notify_merchant(status: str):
        try:
            mch = db.table("merchants").select("user_id").eq("id", wd["merchant_id"]).execute()
            if not mch.data: return
            usr = db.table("users").select("phone").eq("id", mch.data[0]["user_id"]).execute()
            if not usr.data: return
            amount = f"R{wd['amount_cents'] / 100:.2f}"
            if status == "approved":
                msg = f"Your Scan2Pay withdrawal of {amount} has been approved and is being processed to your bank account."
            else:
                reason = body.reason or "Please contact support for more information."
                msg = f"Your Scan2Pay withdrawal of {amount} was declined. Reason: {reason}"
            await send_sms(usr.data[0]["phone"], msg)
        except Exception:
            pass  # non-fatal

    if body.status == "rejected":
        res = db.table("withdrawals").update({
            "status": "rejected",
            "failure_reason": body.reason,
            "decided_at": now,
            "decided_by": admin_id,
        }).eq("id", withdrawal_id).execute()
        await _notify_merchant("rejected")
        log_admin_action(admin_id, "withdrawal.reject", "withdrawal", withdrawal_id, {"reason": body.reason})
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
        res = db.table("withdrawals").update({
            "status": "approved",
            "transfer_code": "SIMULATED",
            "decided_at": now,
            "decided_by": admin_id,
        }).eq("id", withdrawal_id).execute()
        await _notify_merchant("approved")
        log_admin_action(admin_id, "withdrawal.approve", "withdrawal", withdrawal_id, {"simulated": True})
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
    await _notify_merchant("approved")
    log_admin_action(admin_id, "withdrawal.approve", "withdrawal", withdrawal_id, {"transfer_code": transfer.get("transfer_code")})
    return res.data[0]
