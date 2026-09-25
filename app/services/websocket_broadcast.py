import json
import logging

import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

_dynamodb = None
_apigw = None


def _get_dynamodb():
    global _dynamodb
    if _dynamodb is None:
        _dynamodb = boto3.resource("dynamodb", region_name="af-south-1")
    return _dynamodb


def _get_apigw():
    global _apigw
    if _apigw is None:
        settings = get_settings()
        _apigw = boto3.client(
            "apigatewaymanagementapi",
            endpoint_url=settings.websocket_endpoint,
            region_name="af-south-1",
        )
    return _apigw


def broadcast_to_merchant(merchant_id: str, message: dict) -> None:
    """Push a message to all WebSocket connections for a merchant."""
    settings = get_settings()
    if not settings.websocket_endpoint or not settings.ws_connections_table:
        return
    try:
        table = _get_dynamodb().Table(settings.ws_connections_table)
        result = table.query(
            IndexName="merchant_id-index",
            KeyConditionExpression="merchant_id = :mid",
            ExpressionAttributeValues={":mid": merchant_id},
        )
        connections = result.get("Items", [])
        if not connections:
            return
        payload = json.dumps(message).encode()
        apigw = _get_apigw()
        for conn in connections:
            connection_id = conn["connectionId"]
            try:
                apigw.post_to_connection(ConnectionId=connection_id, Data=payload)
            except ClientError as e:
                if e.response["Error"]["Code"] == "GoneException":
                    table.delete_item(Key={"connectionId": connection_id})
                else:
                    logger.warning("ws: post_to_connection error: %s", e)
    except Exception as e:
        logger.error("ws: broadcast_to_merchant failed: %s", e)


def broadcast_to_txn(txn_id: str, message: dict) -> None:
    """Push a message to all WebSocket connections waiting on txn_id."""
    settings = get_settings()
    if not settings.websocket_endpoint or not settings.ws_connections_table:
        return  # not configured — skip silently (local dev without WS)

    try:
        table = _get_dynamodb().Table(settings.ws_connections_table)
        result = table.query(
            IndexName="txn_id-index",
            KeyConditionExpression="txn_id = :tid",
            ExpressionAttributeValues={":tid": txn_id},
        )
        connections = result.get("Items", [])
        if not connections:
            return

        payload = json.dumps(message).encode()
        apigw = _get_apigw()

        for conn in connections:
            connection_id = conn["connectionId"]
            try:
                apigw.post_to_connection(ConnectionId=connection_id, Data=payload)
                logger.info("ws: pushed %s to %s", message.get("type"), connection_id)
            except ClientError as e:
                if e.response["Error"]["Code"] == "GoneException":
                    table.delete_item(Key={"connectionId": connection_id})
                    logger.info("ws: removed stale connection %s", connection_id)
                else:
                    logger.warning("ws: post_to_connection error: %s", e)
    except Exception as e:
        logger.error("ws: broadcast_to_txn failed: %s", e)
        # never raise — a failed push must not break the webhook response
