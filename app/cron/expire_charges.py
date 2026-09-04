import json
import logging

logger = logging.getLogger()


def handler(event, context):
    """Lambda cron handler — expire_charges"""
    logger.info("Running expire_charges")
    # TODO: implement
    return {"statusCode": 200, "body": json.dumps({"job": "expire_charges", "status": "ok"})}
