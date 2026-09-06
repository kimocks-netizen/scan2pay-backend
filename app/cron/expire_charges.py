import json
import logging
from datetime import datetime, timezone

from app.db.connection import get_db

logger = logging.getLogger()


def handler(event, context):
    """Lambda cron — deactivate single-use/timed payment codes past expires_at."""
    db = get_db()
    now = datetime.now(timezone.utc).isoformat()

    res = (
        db.table("payment_codes")
        .update({"active": False})
        .eq("active", True)
        .not_.is_("expires_at", "null")
        .lt("expires_at", now)
        .execute()
    )

    count = len(res.data) if res.data else 0
    logger.info("expire_charges: deactivated %d codes", count)
    return {"statusCode": 200, "body": json.dumps({"job": "expire_charges", "expired": count})}
