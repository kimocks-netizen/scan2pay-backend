import json
import logging

logger = logging.getLogger()


def handler(event, context):
    """Lambda cron handler — reconcile_paystack"""
    logger.info("Running reconcile_paystack")
    # TODO: implement
    return {"statusCode": 200, "body": json.dumps({"job": "reconcile_paystack", "status": "ok"})}
