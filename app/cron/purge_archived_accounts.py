import json
import logging
from datetime import datetime, timedelta, timezone

from app.db.connection import get_db
from app.services.s3_service import delete_object

logger = logging.getLogger()

PURGE_AFTER_DAYS = 90


def handler(event, context):
    """
    Lambda cron — POPIA-driven permanent deletion of archived accounts.

    "Permanently delete" here means anonymising personal fields, not
    dropping the row: transactions/withdrawals reference merchant_id and
    must survive for accounting/tax retention regardless of what happens
    to the account. This satisfies the right-to-erasure on personal data
    while keeping financial history intact.

    Only accounts that have been archived for 90+ days AND were never
    reactivated since that archival run (reactivated_at null, or older
    than archived_at — a since-reactivated-then-re-archived account gets
    a fresh 90-day clock).
    """
    db = get_db()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=PURGE_AFTER_DAYS)).isoformat()

    candidates = (
        db.table("users")
        .select("id,archived_at,reactivated_at")
        .eq("status", "archived")
        .lt("archived_at", cutoff)
        .execute()
    )

    purged = 0
    for row in candidates.data or []:
        if row["reactivated_at"] and row["reactivated_at"] >= row["archived_at"]:
            continue  # reactivated after this archival — not eligible

        user_id = row["id"]
        now = datetime.now(timezone.utc).isoformat()

        db.table("users").update({
            "full_name": "Deleted user",
            "phone": f"deleted-{user_id}",
            "email": None,
            "password_hash": "",
            "avatar_initials": None,
            "anonymized_at": now,
        }).eq("id", user_id).execute()

        merchant_res = db.table("merchants").select("id").eq("user_id", user_id).execute()
        if merchant_res.data:
            merchant_id = merchant_res.data[0]["id"]
            db.table("merchants").update({
                "business_name": "Deleted business",
                "display_name": "Deleted business",
                "payout_bank": None,
                "payout_bank_code": None,
                "payout_account_masked": None,
                "payout_account_enc": None,
                "paystack_recipient_code": None,
            }).eq("id", merchant_id).execute()

            # KYC documents (ID document, proof of bank, selfie) are the most
            # sensitive personal data on the whole platform — an ID photo and
            # a selfie left behind after "permanent deletion" would defeat the
            # point. Unlike transactions/withdrawals these carry no accounting
            # retention requirement, so they're hard-deleted, not anonymised:
            # both the S3 object and the metadata row.
            docs_res = db.table("merchant_documents").select("id,s3_key").eq("merchant_id", merchant_id).execute()
            for doc in (docs_res.data or []):
                delete_object(doc["s3_key"])
            db.table("merchant_documents").delete().eq("merchant_id", merchant_id).execute()

        purged += 1

    logger.info("purge_archived_accounts: anonymised %d account(s)", purged)
    return {"statusCode": 200, "body": json.dumps({"job": "purge_archived_accounts", "anonymised": purged})}
