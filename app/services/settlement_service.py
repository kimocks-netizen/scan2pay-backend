import logging
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# How many days after payment before it becomes withdrawable.
# T+2 is standard — gives time for chargebacks to surface.
CLEARING_DAYS: int = int(getattr(settings, "settlement_clearing_days", 2))

# Flag merchant if unpaid fees exceed this many months of their plan fee.
FEE_DEBT_MONTHS_THRESHOLD = 2


def _make_payout_id() -> str:
    return f"pout_{secrets.token_hex(5)}"


def _get_active_pricing(db, plan_id: str) -> dict | None:
    """Return the currently published pricing version for a plan."""
    res = (
        db.table("pricing_versions")
        .select("*")
        .eq("plan_id", plan_id)
        .eq("status", "published")
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def _is_fee_due(fee_last_charged_at: str | None) -> bool:
    """True if the merchant has never been charged or last charge was 30+ days ago."""
    if not fee_last_charged_at:
        return True
    last = datetime.fromisoformat(fee_last_charged_at.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - last).days >= 30


def run_settlements(db, merchant_id: str | None = None) -> dict:
    """
    Settle all eligible transactions and deduct monthly plan fees.

    Eligible = status='success', settlement_status='pending',
               paid_at <= now() - CLEARING_DAYS.

    Fee logic per merchant:
    - Look up active pricing version for their plan_id
    - If monthly fee > 0 and fee is due (30+ days since last charge):
        - Deduct from payout if enough funds, else add shortfall to fee_owed_cents
    - If fee_owed_cents > 2 months of plan fee → log a warning (no auto-suspend)

    Returns a summary dict.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=CLEARING_DAYS)).isoformat()

    # Fetch all eligible transactions
    q = (
        db.table("transactions")
        .select("id, merchant_id, net_cents")
        .eq("status", "success")
        .eq("settlement_status", "pending")
        .lte("paid_at", cutoff)
    )
    if merchant_id:
        q = q.eq("merchant_id", merchant_id)

    txns = q.execute().data or []

    if not txns:
        logger.info("run_settlements: no eligible transactions (cutoff=%s)", cutoff)
        return {"merchants_settled": 0, "txn_count": 0, "total_cents": 0, "details": []}

    # Group by merchant
    by_merchant: dict[str, list] = {}
    for t in txns:
        by_merchant.setdefault(t["merchant_id"], []).append(t)

    # Fetch merchant records for all affected merchants
    merchant_ids = list(by_merchant.keys())
    merchants_res = db.table("merchants") \
        .select("id, plan_id, fee_owed_cents, fee_last_charged_at") \
        .in_("id", merchant_ids).execute()
    merchant_map = {m["id"]: m for m in (merchants_res.data or [])}

    details = []
    for mid, merchant_txns in by_merchant.items():
        total_net = sum(t["net_cents"] for t in merchant_txns)
        txn_ids = [t["id"] for t in merchant_txns]
        payout_id = _make_payout_id()
        merchant = merchant_map.get(mid, {})

        # ── Fee deduction ─────────────────────────────────────────────────────
        plan_id = merchant.get("plan_id", "plan_free")
        fee_owed = merchant.get("fee_owed_cents", 0) or 0
        fee_last_charged = merchant.get("fee_last_charged_at")
        fee_deducted = 0
        merchant_updates: dict = {}

        pricing = _get_active_pricing(db, plan_id)
        monthly_fee = pricing["monthly_subscription_cents"] if pricing else 0

        if monthly_fee > 0:
            # Add any carried-over debt to this month's fee if due
            total_fee_due = fee_owed + (monthly_fee if _is_fee_due(fee_last_charged) else 0)

            if total_fee_due > 0:
                if total_net >= total_fee_due:
                    # Full deduction
                    fee_deducted = total_fee_due
                    total_net -= fee_deducted
                    merchant_updates["fee_owed_cents"] = 0
                    merchant_updates["fee_last_charged_at"] = now.isoformat()
                else:
                    # Partial — deduct what we can, carry the rest forward
                    fee_deducted = total_net
                    remaining_debt = total_fee_due - fee_deducted
                    total_net = 0
                    merchant_updates["fee_owed_cents"] = remaining_debt
                    if _is_fee_due(fee_last_charged):
                        merchant_updates["fee_last_charged_at"] = now.isoformat()

                    # Warn if debt exceeds threshold
                    if remaining_debt > FEE_DEBT_MONTHS_THRESHOLD * monthly_fee:
                        logger.warning(
                            "merchant=%s fee_owed=%d exceeds %d months threshold — consider flagging",
                            mid, remaining_debt, FEE_DEBT_MONTHS_THRESHOLD,
                        )

        if merchant_updates:
            db.table("merchants").update(merchant_updates).eq("id", mid).execute()

        # ── Create payout row ─────────────────────────────────────────────────
        db.table("payouts").insert({
            "id": payout_id,
            "merchant_id": mid,
            "amount_cents": total_net,
            "transaction_count": len(merchant_txns),
            "period_start": cutoff,
            "period_end": now.isoformat(),
            "status": "pending",
        }).execute()

        db.table("transactions").update({
            "settlement_status": "settled",
            "payout_id": payout_id,
        }).in_("id", txn_ids).execute()

        logger.info(
            "settled merchant=%s txns=%d net=%d fee_deducted=%d payout=%s",
            mid, len(merchant_txns), total_net, fee_deducted, payout_id,
        )
        details.append({
            "merchant_id": mid,
            "txn_count": len(merchant_txns),
            "amount_cents": total_net,
            "fee_deducted_cents": fee_deducted,
            "payout_id": payout_id,
        })

    return {
        "merchants_settled": len(details),
        "txn_count": sum(d["txn_count"] for d in details),
        "total_cents": sum(d["amount_cents"] for d in details),
        "total_fees_deducted_cents": sum(d["fee_deducted_cents"] for d in details),
        "details": details,
    }
