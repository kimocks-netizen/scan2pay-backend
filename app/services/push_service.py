import logging
import httpx

logger = logging.getLogger(__name__)

EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


async def send_push(token: str, title: str, body: str, data: dict | None = None) -> bool:
    """Send a push notification via Expo Push API. Returns True on success."""
    if not token or not token.startswith("ExponentPushToken["):
        return False
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                EXPO_PUSH_URL,
                json={
                    "to": token,
                    "title": title,
                    "body": body,
                    "data": data or {},
                    "sound": "default",
                    "priority": "high",
                },
                headers={"Content-Type": "application/json", "Accept": "application/json"},
            )
        result = resp.json()
        status = result.get("data", {}).get("status")
        if status != "ok":
            logger.error("Expo push failed: %s", result)
            return False
        return True
    except Exception as e:
        logger.error("Expo push exception: %s", e)
        return False


async def send_push_to_merchant(merchant_id: str, title: str, body: str, data: dict | None = None, db=None) -> None:
    """Send push to ALL registered devices for a merchant. Cleans up stale tokens."""
    if db is None:
        return
    try:
        res = db.table("push_tokens").select("id,token").eq("merchant_id", merchant_id).execute()
        tokens = res.data or []
        if not tokens:
            return

        stale_ids = []
        for row in tokens:
            success = await send_push(row["token"], title, body, data)
            if not success:
                stale_ids.append(row["id"])

        # remove tokens that Expo rejected (device uninstalled app, etc.)
        if stale_ids:
            db.table("push_tokens").delete().in_("id", stale_ids).execute()
    except Exception as e:
        logger.error("send_push_to_merchant failed: %s", e)
