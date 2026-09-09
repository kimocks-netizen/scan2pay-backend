import json
import logging

from app.db.connection import get_db
from app.services.settlement_service import run_settlements

logger = logging.getLogger()


def handler(event, context):
    """Lambda cron — settle all eligible transactions across all merchants."""
    db = get_db()
    result = run_settlements(db)
    logger.info(
        "build_settlements: merchants=%d txns=%d total=%d cents",
        result["merchants_settled"], result["txn_count"], result["total_cents"],
    )
    return {"statusCode": 200, "body": json.dumps({"job": "build_settlements", **result})}
