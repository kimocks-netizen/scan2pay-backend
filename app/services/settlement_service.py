import logging
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# How many days after payment before it becomes withdrawable.
# T+2 is standard — gives time for chargebacks to surface.
CLEARING_DAYS: int = int(getattr(settings, "settlement_clearing_days", 2))


def _make_payout_id() -> str:
    return f"pout_{secrets.token_hex(5)}"


def run_settlements(db, merchant_id: str | None = None) -> dict:
    """
    Settle all eligible transactions.

    Eligible = status='success', settlement_status='pending',
               paid_at <= now() - CLEARING_DAYS.

    If merchant_id is given, only that merchant is processed.
    Otherwise all merchants with pending transactions are processed.

    Returns a summary dict.
    """
    now = datetime.now(timezone.utc)
    cutoff = (now - timedelta(days=CLEARING_DAYS)).isoformat()

    # Fetch all eligible transactions in one query
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

    # Group by merchant — only process merchants that actually have pending txns
    by_merchant: dict[str, list] = {}
    for t in txns:
        by_merchant.setdefault(t["merchant_id"], []).append(t)

    details = []
    for mid, merchant_txns in by_merchant.items():
        total_net = sum(t["net_cents"] for t in merchant_txns)
        txn_ids = [t["id"] for t in merchant_txns]
        payout_id = _make_payout_id()

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
            "settled merchant=%s txns=%d net=%d payout=%s",
            mid, len(merchant_txns), total_net, payout_id,
        )
        details.append({
            "merchant_id": mid,
            "txn_count": len(merchant_txns),
            "amount_cents": total_net,
            "payout_id": payout_id,
        })

    return {
        "merchants_settled": len(details),
        "txn_count": sum(d["txn_count"] for d in details),
        "total_cents": sum(d["amount_cents"] for d in details),
        "details": details,
    }
