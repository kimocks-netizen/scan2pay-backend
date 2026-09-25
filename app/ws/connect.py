import time
import logging

import boto3

from app.core.config import get_settings
from app.core.security import decode_token

logger = logging.getLogger(__name__)

TTL_SECONDS = 6 * 60  # 6 minutes


def _table():
    settings = get_settings()
    return boto3.resource("dynamodb", region_name="af-south-1").Table(
        settings.ws_connections_table
    )


def handler(event: dict, context) -> dict:
    connection_id = event["requestContext"]["connectionId"]
    params = event.get("queryStringParameters") or {}
    txn_id = params.get("txn_id")  # optional — charge page connections
    token = params.get("token")

    # token is required for merchant-scoped connections
    if not token and not txn_id:
        return {"statusCode": 400}

    merchant_id = None
    if token:
        payload = decode_token(token)
        if not payload or payload.get("type") != "access":
            return {"statusCode": 401}
        merchant_id = payload.get("sub")

    # txn_id-only connections (charge page, no auth) are still allowed
    if not txn_id and not merchant_id:
        return {"statusCode": 400}

    try:
        _table().put_item(Item={
            "connectionId": connection_id,
            "txn_id": txn_id or "__merchant__",  # GSI requires a value
            "merchant_id": merchant_id or "",
            "connected_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "ttl": int(time.time()) + TTL_SECONDS,
        })
    except Exception as e:
        logger.error("ws connect: failed to write connection: %s", e)
        return {"statusCode": 500}

    return {"statusCode": 200}
