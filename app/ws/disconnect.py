import logging

import boto3

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def handler(event: dict, context) -> dict:
    connection_id = event["requestContext"]["connectionId"]
    settings = get_settings()
    try:
        boto3.resource("dynamodb", region_name="af-south-1").Table(
            settings.ws_connections_table
        ).delete_item(Key={"connectionId": connection_id})
    except Exception as e:
        logger.error("ws disconnect: failed to delete connection: %s", e)
    return {"statusCode": 200}
