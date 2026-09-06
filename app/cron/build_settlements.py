import json
import logging
import secrets
from datetime import datetime, timedelta, timezone

from app.db.connection import get_db

logger = logging.getLogger()


def _week_bounds() -> tuple[str, str]:
    """Return ISO strings for start/end of the previous calendar week (Mon–Sun)."""
    today = datetime.now(timezone.utc).date()
    # last Monday
    start = today - timedelta(days=today.weekday() + 7)
    end = start + timedelta(days=6)
    return start.isoformat(), end.isoformat()


def _make_payout_id(db) -> str:
    try:
        n = (db.table("payouts").select("id", count="exact").execute().count or 0) + 1
    except Exception:
        n = int(secrets.token_hex(3), 16) % 100000
    return f"pout_{str(n).zfill(5)}"


def handler(event, context):
    """Lambda cron — group last week's settled transactions into payout rows."""
    db = get_db()
    period_start, period_end = _week_bounds()

    # find all success + unsettled transactions in the period
    res = (
        db.table("transactions")
        .select("id, merchant_id, net_cents")
        .eq("status", "success")
        .eq("settlement_status", "pending")
        .gte("paid_at", period_start)
        .lte("paid_at", period_end)
        .execute()
    )

    rows = res.data or []
    if not rows:
        logger.info("build_settlements: no unsettled transactions for %s–%s", period_start, period_end)
        return {"statusCode": 200, "body": json.dumps({"job": "build_settlements", "payouts_created": 0})}

    # group by merchant
    by_merchant: dict[str, list] = {}
    for row in rows:
        by_merchant.setdefault(row["merchant_id"], []).append(row)

    payouts_created = 0
    for merchant_id, txns in by_merchant.items():
        total_net = sum(t["net_cents"] for t in txns)
        txn_ids = [t["id"] for t in txns]

        payout_id = _make_payout_id(db)
        db.table("payouts").insert({
            "id": payout_id,
            "merchant_id": merchant_id,
            "amount_cents": total_net,
            "transaction_count": len(txns),
            "period_start": period_start,
            "period_end": period_end,
            "status": "pending",
        }).execute()

        # mark transactions as settled
        db.table("transactions").update({
            "settlement_status": "settled",
            "payout_id": payout_id,
        }).in_("id", txn_ids).execute()

        payouts_created += 1
        logger.info("build_settlements: payout %s for merchant %s — %d txns, %d cents", payout_id, merchant_id, len(txns), total_net)

    logger.info("build_settlements complete: %d payouts created for %s–%s", payouts_created, period_start, period_end)
    return {"statusCode": 200, "body": json.dumps({"job": "build_settlements", "payouts_created": payouts_created, "period_start": period_start, "period_end": period_end})}
