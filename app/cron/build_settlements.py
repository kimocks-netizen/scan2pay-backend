import json
import logging

logger = logging.getLogger()


def handler(event, context):
    """Lambda cron handler — build_settlements"""
    logger.info("Running build_settlements")
    # TODO: implement
    return {"statusCode": 200, "body": json.dumps({"job": "build_settlements", "status": "ok"})}
