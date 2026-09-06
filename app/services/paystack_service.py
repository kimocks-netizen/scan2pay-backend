import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_BASE = settings.paystack_base_url
_HEADERS = {
    "Authorization": f"Bearer {settings.paystack_secret_key}",
    "Content-Type": "application/json",
}


def _client() -> httpx.Client:
    return httpx.Client(base_url=_BASE, headers=_HEADERS, timeout=30)


class PaystackError(Exception):
    def __init__(self, message: str, code: str = "paystack_error"):
        self.message = message
        self.code = code
        super().__init__(message)


def _raise(res: httpx.Response) -> dict:
    try:
        data = res.json()
    except Exception:
        raise PaystackError(f"Invalid JSON response from Paystack (status {res.status_code})")
    if not data.get("status"):
        raise PaystackError(data.get("message", "Paystack error"), data.get("code", "paystack_error"))
    return data["data"]


# ── Transactions ──────────────────────────────────────────────────────────────

def initialize_transaction(
    email: str,
    amount_cents: int,
    reference: str,
    metadata: dict[str, Any],
) -> dict:
    """Returns {authorization_url, access_code, reference}."""
    try:
        with _client() as c:
            res = c.post("/transaction/initialize", json={
                "email": email,
                "amount": amount_cents,
                "currency": "ZAR",
                "reference": reference,
                "callback_url": "https://scan2pay.site/charge?paid=true",
                # TODO: add "apple_pay", "google_pay", "capitec_pay" once configured:
                #   - Apple Pay: register scan2pay.site domain via POST /apple-pay/domain before go-live
                #   - Google Pay: enabled automatically by Paystack once account is verified
                #   - Capitec Pay: confirm channel name with Paystack support before adding
                #   All three surface automatically in Paystack Inline JS once registered
                "channels": ["card"],
                "metadata": metadata,
            })
    except httpx.HTTPError as e:
        raise PaystackError(f"Network error contacting Paystack: {e}", "network_error")
    logger.info("Paystack initialize response: status=%s body=%s", res.status_code, res.text[:500])
    return _raise(res)


def verify_transaction(reference: str) -> dict:
    """Returns full transaction data dict. Raises PaystackError if not found."""
    with _client() as c:
        res = c.get(f"/transaction/verify/{reference}")
    return _raise(res)


def list_transactions(per_page: int = 20, next_cursor: str | None = None) -> dict:
    """Returns {data: [...], meta: {next, previous, perPage}}."""
    params: dict[str, Any] = {"use_cursor": "true", "perPage": per_page}
    if next_cursor:
        params["next"] = next_cursor
    with _client() as c:
        res = c.get("/transaction", params=params)
    raw = res.json()
    if not raw.get("status"):
        raise PaystackError(raw.get("message", "Paystack error"))
    return {"data": raw["data"], "meta": raw.get("meta", {})}


# ── Transfer Recipients ───────────────────────────────────────────────────────

def create_transfer_recipient(name: str, account_number: str, bank_code: str) -> dict:
    """Returns {recipient_code, details.bank_name, ...}."""
    with _client() as c:
        res = c.post("/transferrecipient", json={
            "type": "nuban",
            "name": name,
            "account_number": account_number,
            "bank_code": bank_code,
            "currency": "ZAR",
        })
    return _raise(res)


# ── Transfers (prod-only — blocked on starter/test accounts) ─────────────────

def initiate_transfer(amount_cents: int, recipient_code: str, reference: str, reason: str) -> dict:
    """Returns {transfer_code, status}. Status may be 'otp' or 'pending'."""
    with _client() as c:
        res = c.post("/transfer", json={
            "source": "balance",
            "amount": amount_cents,
            "recipient": recipient_code,
            "reason": reason,
            "currency": "ZAR",
            "reference": reference,
        })
    return _raise(res)


def finalize_transfer(transfer_code: str, otp: str) -> dict:
    """Required in prod when transfer status is 'otp'."""
    with _client() as c:
        res = c.post("/transfer/finalize_transfer", json={
            "transfer_code": transfer_code,
            "otp": otp,
        })
    return _raise(res)


def fetch_transfer(transfer_code: str) -> dict:
    with _client() as c:
        res = c.get(f"/transfer/{transfer_code}")
    return _raise(res)
