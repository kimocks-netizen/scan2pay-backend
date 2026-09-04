import httpx
from app.core.config import get_settings

settings = get_settings()


async def send_sms(to: str, message: str) -> bool:
    """Send a single SMS via WinSMS. Returns True on success."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{settings.winsms_api_url}/sms/outgoing/send",
                headers={"AUTHORIZATION": settings.winsms_api_key, "Content-Type": "application/json"},
                json={"messages": [{"clientMessageId": 1, "mobileNumber": to, "messageText": message}]},
                timeout=10,
            )
        return resp.status_code == 200
    except Exception:
        return False


async def send_otp(phone: str, code: str) -> bool:
    message = f"Your Scan2Pay verification code is {code}. Valid for 10 minutes. Do not share this code."
    return await send_sms(phone, message)
