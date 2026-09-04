import time
import logging
import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


async def send_sms(to: str, message: str) -> bool:
    """Send a single SMS via WinSMS. Returns True on success."""
    try:
        mobile = to.lstrip("+")  # WinSMS expects number without + prefix
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{settings.winsms_api_url}/sms/outgoing/send",
                headers={"AUTHORIZATION": settings.winsms_api_key, "Content-Type": "application/json"},
                json={
                    "message": message,
                    "recipients": [{"mobileNumber": mobile}],
                },
            )
        data = resp.json()
        accepted = resp.status_code == 200 and data.get("recipients", [{}])[0].get("accepted")
        if not accepted:
            logger.error("WinSMS failed: status=%s body=%s", resp.status_code, data)
        return bool(accepted)
    except Exception as e:
        logger.error("WinSMS exception: %s", e)
        return False


async def send_otp(phone: str, code: str) -> bool:
    message = f"Your Scan2Pay verification code is {code}. Valid for 10 minutes. Do not share this code."
    return await send_sms(phone, message)
