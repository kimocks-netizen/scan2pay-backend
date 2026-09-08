import json
import logging
from datetime import datetime, timezone

from app.db.connection import get_db

logger = logging.getLogger()


def handler(event, context):
    """
    Lambda cron — expire stale charge sessions.
    Marks pending charge_session transactions past charge_expires_at as failed.
    These are Type 2 vendor charges where nobody paid within 5 minutes.
    """
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    res = (
        db.table("transactions")
        .update({"status": "failed", "failure_reason": "charge_session_expired"})
        .eq("status", "pending")
        .eq("charge_session", True)
        .not_.is_("charge_expires_at", "null")
        .lt("charge_expires_at", now)
        .execute()
    )

    count = len(res.data) if res.data else 0
    logger.info("expire_charges: expired %d charge sessions", count)
    return {"statusCode": 200, "body": json.dumps({"job": "expire_charges", "expired": count})}
