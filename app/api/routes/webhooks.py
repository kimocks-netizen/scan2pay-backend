import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from app.core.security import verify_paystack_signature
from app.db.connection import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/paystack", status_code=200)
async def paystack_webhook(request: Request):
    raw_body = await request.body()
    signature = request.headers.get("x-paystack-signature", "")

    if not verify_paystack_signature(raw_body, signature):
        raise HTTPException(status_code=401, detail={"code": "invalid_signature", "message": "Webhook signature invalid."})

    payload = await request.json()
    event = payload.get("event")
    data = payload.get("data", {})

    # idempotency key — provider_reference is the Paystack transaction/transfer reference
    provider_reference = data.get("reference") or data.get("transfer_code", "")

    db = get_db()

    # insert webhook event — UNIQUE(provider, event_type, provider_reference) makes replays no-ops
    import secrets as _secrets
    try:
        db.table("webhook_events").insert({
            "id": _secrets.token_hex(16),
            "provider": "paystack",
            "event_type": event,
            "provider_reference": provider_reference,
            "payload": payload,
            "signature_valid": True,
        }).execute()
    except Exception:
        # duplicate — already processed, return 200 immediately
        logger.info("Duplicate webhook ignored: %s %s", event, provider_reference)
        return {"received": True}

    # ── charge.success ────────────────────────────────────────────────────────
    if event == "charge.success":
        try:
            await _handle_charge_success(data, db)
        except Exception:
            logger.exception("Error handling charge.success for ref %s", provider_reference)

    # ── transfer events ───────────────────────────────────────────────────────
    elif event in ("transfer.success", "transfer.failed", "transfer.reversed"):
        try:
            _handle_transfer_event(event, data, db)
        except Exception:
            logger.exception("Error handling %s for ref %s", event, provider_reference)

    else:
        logger.info("Unhandled Paystack event: %s", event)

    return {"received": True}


async def _handle_charge_success(data: dict, db) -> None:
    reference = data.get("reference")
    if not reference:
        logger.warning("charge.success missing reference")
        return

    txn_res = db.table("transactions").select("id, status, payment_code_id, merchant_id").eq("paystack_reference", reference).execute()
    if not txn_res.data:
        logger.warning("charge.success: no transaction found for reference %s", reference)
        return

    txn = txn_res.data[0]
    if txn["status"] == "success":
        return  # already processed

    now = datetime.now(timezone.utc).isoformat()

    # extract authorization — may be {} when not a card payment
    auth = data.get("authorization") or {}
    authorization_code = auth.get("authorization_code")

    # metadata can be 0, null, or object
    metadata = data.get("metadata") or {}
    single_use = metadata.get("single_use") in (True, "true", "True", 1)

    updates: dict = {
        "status": "success",
        "paid_at": data.get("paid_at") or now,
        "method": data.get("channel", "card"),
    }
    if authorization_code:
        updates["authorization_code"] = authorization_code

    db.table("transactions").update(updates).eq("id", txn["id"]).execute()

    # push real-time update to any waiting WebSocket connection
    from app.services.websocket_broadcast import broadcast_to_txn, broadcast_to_merchant
    broadcast_to_txn(txn["id"], {
        "type": "PAYMENT_SUCCESS",
        "txn_id": txn["id"],
        "amount_cents": data.get("amount"),
        "paid_at": updates.get("paid_at"),
    })

    # notify merchant — bell + push + SMS
    await _notify_payment(txn, data, db)

    # deactivate single-use payment code
    if single_use:
        db.table("payment_codes").update({"active": False, "paid_at": now}).eq("id", txn["payment_code_id"]).execute()

    # increment payment code payments counter
    pc_res = db.table("payment_codes").select("payments").eq("id", txn["payment_code_id"]).execute()
    current = (pc_res.data[0].get("payments", 0) if pc_res.data else 0)
    db.table("payment_codes").update({"payments": current + 1}).eq("id", txn["payment_code_id"]).execute()

    logger.info("charge.success processed: txn=%s reference=%s", txn["id"], reference)


async def _notify_payment(txn: dict, data: dict, db) -> None:
    """Bell + push + SMS for payment_received. Non-fatal — never raises."""
    try:
        amount_cents = data.get("amount", 0)
        amount_str = f"R{amount_cents / 100:.2f}"
        title = "Payment received"
        body = f"{amount_str} received"

        # look up merchant
        m_res = db.table("merchants").select("id,user_id,expo_push_token,push_enabled").eq("id", txn.get("merchant_id", "")).execute()
        if not m_res.data:
            return
        merchant = m_res.data[0]
        mid = merchant["id"]

        # bell — write notification row
        import secrets as _s
        from datetime import datetime, timezone
        db.table("notifications").insert({
            "id": f"notif_{_s.token_hex(8)}",
            "merchant_id": mid,
            "type": "payment_received",
            "title": title,
            "body": body,
            "data": {"txn_id": txn["id"], "amount_cents": amount_cents},
        }).execute()

        # bell — WebSocket broadcast
        from app.services.websocket_broadcast import broadcast_to_merchant
        broadcast_to_merchant(mid, {
            "type": "NOTIFICATION",
            "notification": {"type": "payment_received", "title": title, "body": body,
                             "data": {"txn_id": txn["id"], "amount_cents": amount_cents},
                             "created_at": datetime.now(timezone.utc).isoformat()},
        })

        # check prefs
        prefs_res = db.table("notification_prefs").select("payments_push,payments_sms,payments_sms_mode").eq("merchant_id", mid).execute()
        prefs = prefs_res.data[0] if prefs_res.data else {}
        push_on = prefs.get("payments_push", True)
        sms_on = prefs.get("payments_sms", True)
        sms_mode = prefs.get("payments_sms_mode", "instant")

        # push — all devices
        if push_on:
            from app.services.push_service import send_push_to_merchant
            await send_push_to_merchant(mid, title, body, {"txn_id": txn["id"], "amount_cents": amount_cents}, db)

        # SMS — only if instant mode
        if sms_on and sms_mode == "instant":
            usr = db.table("users").select("phone").eq("id", merchant["user_id"]).execute()
            if usr.data:
                from app.services.sms_service import send_sms
                await send_sms(usr.data[0]["phone"], f"VulaPay: {body}")
    except Exception as e:
        logger.error("_notify_payment failed: %s", e)


def _handle_transfer_event(event: str, data: dict, db) -> None:
    transfer_code = data.get("transfer_code")
    reference = data.get("reference")
    if not reference:
        logger.warning("%s missing reference", event)
        return

    status_map = {
        "transfer.success": "paid",
        "transfer.failed": "failed",
        "transfer.reversed": "reversed",
    }
    new_status = status_map[event]
    now = datetime.now(timezone.utc).isoformat()

    updates: dict = {"status": new_status}
    if new_status == "paid":
        updates["paid_at"] = now
    elif new_status == "failed":
        updates["failure_reason"] = data.get("reason") or "Transfer failed"

    db.table("withdrawals").update(updates).eq("reference", reference).execute()
    logger.info("%s processed: transfer_code=%s reference=%s", event, transfer_code, reference)
