import json
import logging
from datetime import datetime, timedelta, timezone

from app.db.connection import get_db
from app.services.paystack_service import PaystackError, verify_transaction

logger = logging.getLogger()

STALE_MINUTES = 10


def handler(event, context):
    """Lambda cron — verify pending transactions older than 10 min via Paystack."""
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(minutes=STALE_MINUTES)).isoformat()

    res = (
        db.table("transactions")
        .select("id, paystack_reference, payment_code_id")
        .eq("status", "pending")
        .not_.is_("paystack_reference", "null")
        .lt("created_at", cutoff)
        .execute()
    )

    rows = res.data or []
    results = {"verified": 0, "failed": 0, "still_pending": 0, "errors": 0}

    for txn in rows:
        ref = txn["paystack_reference"]
        try:
            data = verify_transaction(ref)
            ps_status = data.get("status")

            if ps_status == "success":
                auth = data.get("authorization") or {}
                updates = {
                    "status": "success",
                    "paid_at": data.get("paid_at") or datetime.now(timezone.utc).isoformat(),
                    "method": data.get("channel", "card"),
                }
                if auth.get("authorization_code"):
                    updates["authorization_code"] = auth["authorization_code"]
                db.table("transactions").update(updates).eq("id", txn["id"]).execute()

                metadata = data.get("metadata") or {}
                if metadata.get("single_use"):
                    db.table("payment_codes").update({"active": False}).eq("id", txn["payment_code_id"]).execute()

                results["verified"] += 1
                logger.info("reconcile: marked success txn=%s ref=%s", txn["id"], ref)

            elif ps_status in ("failed", "abandoned"):
                db.table("transactions").update({"status": "failed", "failure_reason": ps_status}).eq("id", txn["id"]).execute()
                results["failed"] += 1
                logger.info("reconcile: marked failed txn=%s ref=%s status=%s", txn["id"], ref, ps_status)

            else:
                results["still_pending"] += 1

        except PaystackError as e:
            logger.warning("reconcile: Paystack error for ref=%s: %s", ref, e.message)
            results["errors"] += 1

    logger.info("reconcile_paystack complete: %s", results)
    return {"statusCode": 200, "body": json.dumps({"job": "reconcile_paystack", **results})}
