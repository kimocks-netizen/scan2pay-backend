"""
In-memory rate limiter for Lambda.

Lambda runs many concurrent instances — each instance has its own memory,
so this is per-instance, not global. That is acceptable here:
- Auth endpoints: 5 attempts/min per IP. With 10 Lambda instances, worst
  case is 50 attempts/min before a lockout — still a meaningful brake on
  brute force without needing Redis or DynamoDB.
- The reconcile cron and WAF (when added) provide the global safety net.

Key format: "{route_key}:{identifier}"
  route_key  — short string identifying the endpoint group (e.g. "login")
  identifier — client IP address extracted from the request
"""

import time
from collections import defaultdict
from fastapi import HTTPException, Request

# { key: [timestamp, timestamp, ...] }
_buckets: dict[str, list[float]] = defaultdict(list)

# Route limits: (max_requests, window_seconds)
LIMITS: dict[str, tuple[int, int]] = {
    "login":       (5,  60),   # 5 attempts per minute per IP
    "register":    (5,  60),   # 5 registrations per minute per IP
    "otp_request": (3,  60),   # 3 OTP sends per minute per IP
    "otp_verify":  (5,  60),   # 5 verify attempts per minute per IP
    "pay_init":    (10, 60),   # 10 payment initialisations per minute per IP (public)
    "password_reset_request": (3, 60),  # 3 reset OTPs per minute per IP
    "password_reset_confirm": (5, 60),  # 5 confirm attempts per minute per IP
}


def _client_ip(request: Request) -> str:
    """Extract real client IP, respecting X-Forwarded-For from API Gateway."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def check_rate_limit(route_key: str, request: Request) -> None:
    """
    Raises HTTP 429 if the client has exceeded the limit for this route.
    Call at the top of any endpoint that needs rate limiting.
    """
    if route_key not in LIMITS:
        return

    max_requests, window = LIMITS[route_key]
    ip = _client_ip(request)
    key = f"{route_key}:{ip}"
    now = time.time()
    cutoff = now - window

    # drop timestamps outside the window
    _buckets[key] = [t for t in _buckets[key] if t > cutoff]

    if len(_buckets[key]) >= max_requests:
        retry_after = max(1, int(_buckets[key][0] + window - now))
        raise HTTPException(
            status_code=429,
            headers={"Retry-After": str(retry_after)},
            detail={
                "code": "rate_limit_exceeded",
                "message": f"Too many requests. Try again in {retry_after} second(s).",
                "retry_after": retry_after,
            },
        )

    _buckets[key].append(now)
