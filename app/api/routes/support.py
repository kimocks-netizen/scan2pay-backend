from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.core.deps import get_current_user_id, require_admin, require_staff
from app.db.connection import get_db

router = APIRouter()

BONUS_THRESHOLD = 1000


def _current_period() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _period_bounds(period: str) -> tuple[str, str]:
    year, month = int(period[:4]), int(period[5:7])
    start = f"{period}-01T00:00:00+00:00"
    if month == 12:
        end = f"{year + 1}-01-01T00:00:00+00:00"
    else:
        end = f"{year}-{month + 1:02d}-01T00:00:00+00:00"
    return start, end


# ── Support: my referral code (just their user_id — short enough) ─────────────

@router.get("/support/me")
async def get_support_profile(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    roles = db.table("user_roles").select("role").eq("user_id", user_id).in_("role", ["admin", "support"]).execute()
    if not roles.data:
        raise HTTPException(status_code=403, detail="Staff access required")

    user = db.table("users").select("id,full_name,phone,email").eq("id", user_id).execute()
    if not user.data:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        **user.data[0],
        "referral_code": user_id,  # user_id IS the referral code for now
        "role": roles.data[0]["role"],
    }


# ── Support: my stats for a given period ─────────────────────────────────────

@router.get("/support/my-stats")
async def get_my_support_stats(
    period: str = Query(default=""),
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    roles = db.table("user_roles").select("role").eq("user_id", user_id).in_("role", ["admin", "support"]).execute()
    if not roles.data:
        raise HTTPException(status_code=403, detail="Staff access required")

    if not period:
        period = _current_period()

    start, end = _period_bounds(period)

    # Merchants this support agent referred this period
    assigned = db.table("merchants") \
        .select("id,business_name,created_at") \
        .eq("referred_by", user_id) \
        .gte("created_at", start) \
        .lt("created_at", end) \
        .order("created_at", desc=True) \
        .execute()

    assigned_merchants = assigned.data or []

    # Enrich with first transaction date — only merchants who transacted count toward commission
    merchant_ids = [m["id"] for m in assigned_merchants]
    first_txns: dict[str, str] = {}
    if merchant_ids:
        txn_res = db.table("transactions") \
            .select("merchant_id,created_at") \
            .in_("merchant_id", merchant_ids) \
            .eq("status", "success") \
            .order("created_at") \
            .execute()
        for t in (txn_res.data or []):
            if t["merchant_id"] not in first_txns:
                first_txns[t["merchant_id"]] = t["created_at"]

    recent_signups = [
        {
            "id": m["id"],
            "business_name": m["business_name"],
            "created_at": m["created_at"],
            "has_transacted": m["id"] in first_txns,
            "first_transaction_at": first_txns.get(m["id"]),
        }
        for m in assigned_merchants
    ][:10]

    # Only count merchants who have made at least one successful transaction
    assigned_count = sum(1 for m in assigned_merchants if m["id"] in first_txns)

    # Unassigned merchants this period (no referred_by)
    unassigned_res = db.table("merchants") \
        .select("id", count="exact") \
        .is_("referred_by", "null") \
        .gte("created_at", start) \
        .lt("created_at", end) \
        .execute()
    unassigned_total = unassigned_res.count or 0

    # Active support agents (to split unassigned pool)
    support_res = db.table("user_roles").select("user_id").eq("role", "support").execute()
    support_count = max(1, len(support_res.data or []))
    unassigned_share = unassigned_total // support_count

    total = assigned_count + unassigned_share

    # Previous period rollover from commission snapshot
    prev_year, prev_month = int(period[:4]), int(period[5:7])
    if prev_month == 1:
        prev_period = f"{prev_year - 1}-12"
    else:
        prev_period = f"{prev_year}-{prev_month - 1:02d}"

    prev_snap = db.table("support_commissions") \
        .select("rollover") \
        .eq("support_user_id", user_id) \
        .eq("period", prev_period) \
        .execute()
    rollover_in = prev_snap.data[0]["rollover"] if prev_snap.data else 0

    effective_total = total + rollover_in
    bonus_units = effective_total // BONUS_THRESHOLD
    rollover_out = effective_total % BONUS_THRESHOLD

    return {
        "period": period,
        "referral_code": user_id,
        "assigned_count": assigned_count,
        "unassigned_share": unassigned_share,
        "unassigned_total": unassigned_total,
        "support_agents": support_count,
        "rollover_in": rollover_in,
        "total": effective_total,
        "threshold": BONUS_THRESHOLD,
        "bonus_units": bonus_units,
        "rollover_out": rollover_out,
        "recent_signups": recent_signups,
    }


# ── Admin: all support stats for a period ────────────────────────────────────

@router.get("/admin/support-stats")
async def get_all_support_stats(
    period: str = Query(default=""),
    admin_id: str = Depends(require_admin),
):
    if not period:
        period = _current_period()

    start, end = _period_bounds(period)
    db = get_db()

    support_agents = db.table("user_roles") \
        .select("user_id") \
        .eq("role", "support") \
        .execute()

    unassigned_res = db.table("merchants") \
        .select("id", count="exact") \
        .is_("referred_by", "null") \
        .gte("created_at", start) \
        .lt("created_at", end) \
        .execute()
    unassigned_total = unassigned_res.count or 0
    support_count = max(1, len(support_agents.data or []))
    unassigned_share = unassigned_total // support_count

    rows = []
    for agent in (support_agents.data or []):
        uid = agent["user_id"]
        user = db.table("users").select("full_name,phone").eq("id", uid).execute()
        assigned = db.table("merchants") \
            .select("id", count="exact") \
            .eq("referred_by", uid) \
            .gte("created_at", start) \
            .lt("created_at", end) \
            .execute()
        assigned_count = assigned.count or 0
        total = assigned_count + unassigned_share
        rows.append({
            "user_id": uid,
            "full_name": user.data[0]["full_name"] if user.data else uid,
            "phone": user.data[0]["phone"] if user.data else "",
            "assigned_count": assigned_count,
            "unassigned_share": unassigned_share,
            "total": total,
            "bonus_units": total // BONUS_THRESHOLD,
            "rollover": total % BONUS_THRESHOLD,
        })

    return {
        "period": period,
        "unassigned_total": unassigned_total,
        "support_agents": support_count,
        "agents": rows,
    }
