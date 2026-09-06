import logging
import random
import secrets
import string
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.core.deps import get_current_user_id
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.connection import get_db
from app.schemas.auth import (
    AuthResponse,
    LoginRequest,
    OtpRequestBody,
    OtpVerifyRequest,
    PublicUser,
    RefreshRequest,
    RegisterRequest,
    normalise_phone,
)
from app.services.sms_service import send_otp

logger = logging.getLogger(__name__)
router = APIRouter()

OTP_TTL_MINUTES = 10
OTP_MAX_ATTEMPTS = 5


# ── helpers ───────────────────────────────────────────────────────────────────

def _get_role(user_id: str, db) -> str:
    res = db.table("user_roles").select("role").eq("user_id", user_id).order("created_at").limit(1).execute()
    return res.data[0]["role"] if res.data else "merchant"


def _user_to_public(row: dict, db, merchant_id: str | None = None) -> PublicUser:
    return PublicUser(
        id=row["id"],
        full_name=row["full_name"],
        phone=row["phone"],
        email=row.get("email"),
        user_type=row.get("user_type"),
        role=_get_role(row["id"], db),
        status=row.get("status", "active"),
        merchant_id=merchant_id or row.get("merchant_id"),
        avatar_initials=row.get("avatar_initials"),
        phone_verified=row.get("phone_verified", False),
        email_verified=row.get("email_verified", False),
        created_at=row["created_at"],
    )


def _make_id(prefix: str, db) -> str:
    """Generate a short sequential-style ID by counting existing rows."""
    table = {"usr": "users", "mch": "merchants", "pc": "payment_codes", "rt": "refresh_tokens", "otp": "otp_codes", "ur": "user_roles"}.get(prefix, prefix)
    try:
        res = db.table(table).select("id", count="exact").execute()
        n = (res.count or 0) + 1
    except Exception:
        n = int(datetime.now(timezone.utc).timestamp() * 1000) % 100000
    return f"{prefix}_{str(n).zfill(3)}"


def _avatar(name: str) -> str:
    parts = name.strip().split()
    return "".join(p[0].upper() for p in parts if p)[:2]


def _caption_for(user_type: str) -> str:
    return {"tip": "Scan to Tip", "taxi": "Scan to Pay Fare"}.get(user_type, "Scan to Pay")


def _category_for(user_type: str) -> str:
    return {"tip": "Tips", "taxi": "Taxi transport"}.get(user_type, "General")


async def _issue_tokens(user_id: str, db, request: Request | None = None) -> tuple[str, str]:
    access = create_access_token(user_id)
    refresh = create_refresh_token(user_id)
    rt_id = _make_id("rt", db)
    expires = datetime.now(timezone.utc) + timedelta(days=30)
    db.table("refresh_tokens").insert({
        "id": rt_id,
        "user_id": user_id,
        "token_hash": hash_token(refresh),
        "expires_at": expires.isoformat(),
        "ip": request.client.host if request and request.client else None,
        "user_agent": request.headers.get("user-agent") if request else None,
    }).execute()
    return access, refresh


# TODO: remove DEV_OTP_BYPASS once WinSMS credits are topped up
DEV_OTP_BYPASS = True
DEV_OTP_CODE = "0000"


async def _send_otp_to(phone: str, db) -> None:
    code = DEV_OTP_CODE if DEV_OTP_BYPASS else "".join(random.choices(string.digits, k=6))
    otp_id = _make_id("otp", db)
    expires = datetime.now(timezone.utc) + timedelta(minutes=OTP_TTL_MINUTES)
    db.table("otp_codes").insert({
        "id": otp_id,
        "phone": phone,
        "code_hash": hash_token(code),
        "expires_at": expires.isoformat(),
    }).execute()
    if DEV_OTP_BYPASS:
        logger.warning("DEV_OTP_BYPASS active — OTP for %s is 0000, no SMS sent", phone)
        return
    sent = await send_otp(phone, code)
    if not sent:
        logger.warning("WinSMS delivery failed for %s", phone)


# ── register ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(body: RegisterRequest, request: Request):
    db = get_db()

    # duplicate phone
    existing = db.table("users").select("id").eq("phone", body.phone).execute()
    if existing.data:
        raise HTTPException(status_code=409, detail={"code": "phone_taken", "message": "That mobile number is already registered."})

    # duplicate email
    if body.email:
        existing_email = db.table("users").select("id").eq("email", body.email.lower()).execute()
        if existing_email.data:
            raise HTTPException(status_code=409, detail={"code": "email_taken", "message": "That email address is already registered."})

    user_id = _make_id("usr", db)
    merchant_id = _make_id("mch", db)
    pc_id = _make_id("pc", db)
    reference = "QR-" + secrets.token_hex(4).upper()

    ur_id = _make_id("ur", db)

    # insert user
    db.table("users").insert({
        "id": user_id,
        "full_name": body.full_name,
        "phone": body.phone,
        "email": body.email.strip().lower() if body.email else None,
        "password_hash": hash_password(body.password),
        "user_type": body.user_type,
        "status": "active",
        "avatar_initials": _avatar(body.full_name),
        "phone_verified": False,
        "email_verified": False,
    }).execute()

    # insert role
    db.table("user_roles").insert({"id": ur_id, "user_id": user_id, "role": "merchant"}).execute()

    # insert merchant
    slug = user_id  # simple unique slug; can be prettified later
    db.table("merchants").insert({
        "id": merchant_id,
        "user_id": user_id,
        "business_name": body.business_name or body.full_name,
        "display_name": body.business_name or body.full_name,
        "slug": slug,
        "trading_category": _category_for(body.user_type),
        "plan_id": "plan_free",
        "settlement_cycle": "Weekly",
        "status": "active",
    }).execute()

    # insert primary payment code
    db.table("payment_codes").insert({
        "id": pc_id,
        "merchant_id": merchant_id,
        "reference": reference,
        "label": _caption_for(body.user_type),
        "caption": _caption_for(body.user_type),
        "mode": "variable",
        "active": True,
        "scans": 0,
        "payments": 0,
        "is_primary": True,
        "placement": "Not set",
    }).execute()

    # send OTP
    await _send_otp_to(body.phone, db)

    access, refresh = await _issue_tokens(user_id, db, request)

    user_row = db.table("users").select("*").eq("id", user_id).single().execute().data
    return AuthResponse(
        user=_user_to_public(user_row, db, merchant_id=merchant_id),
        access_token=access,
        refresh_token=refresh,
    )


# ── login ─────────────────────────────────────────────────────────────────────

@router.post("/login", response_model=AuthResponse)
async def login(body: LoginRequest, request: Request):
    db = get_db()

    # try phone first, then email
    phone = normalise_phone(body.identifier)
    res = db.table("users").select("*").eq("phone", phone).execute()
    if not res.data:
        res = db.table("users").select("*").eq("email", body.identifier.strip().lower()).execute()

    if not res.data:
        raise HTTPException(status_code=401, detail={"code": "invalid_credentials", "message": "No Scan2Pay account found for those details."})

    user = res.data[0]

    if user.get("status") == "suspended":
        raise HTTPException(status_code=403, detail={"code": "account_suspended", "message": "This account has been suspended."})

    if not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail={"code": "invalid_credentials", "message": "That password is incorrect."})

    # get merchant id
    mch = db.table("merchants").select("id").eq("user_id", user["id"]).execute()
    merchant_id = mch.data[0]["id"] if mch.data else None

    # update last_login_at
    db.table("users").update({"last_login_at": datetime.now(timezone.utc).isoformat()}).eq("id", user["id"]).execute()

    # send OTP if phone not yet verified
    if not user.get("phone_verified"):
        await _send_otp_to(user["phone"], db)

    access, refresh = await _issue_tokens(user["id"], db, request)

    return AuthResponse(
        user=_user_to_public(user, db, merchant_id=merchant_id),
        access_token=access,
        refresh_token=refresh,
    )


# ── refresh ───────────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=AuthResponse)
async def refresh_tokens(body: RefreshRequest, request: Request):
    db = get_db()
    payload = decode_token(body.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail={"code": "token_invalid", "message": "Invalid refresh token."})

    token_hash = hash_token(body.refresh_token)
    rt = db.table("refresh_tokens").select("*").eq("token_hash", token_hash).execute()
    if not rt.data or rt.data[0].get("revoked_at"):
        raise HTTPException(status_code=401, detail={"code": "token_invalid", "message": "Refresh token has been revoked."})

    # revoke old token
    db.table("refresh_tokens").update({"revoked_at": datetime.now(timezone.utc).isoformat()}).eq("token_hash", token_hash).execute()

    user_id = payload["sub"]
    user = db.table("users").select("*").eq("id", user_id).single().execute().data
    mch = db.table("merchants").select("id").eq("user_id", user_id).execute()
    merchant_id = mch.data[0]["id"] if mch.data else None

    access, new_refresh = await _issue_tokens(user_id, db, request)
    return AuthResponse(
        user=_user_to_public(user, db, merchant_id=merchant_id),
        access_token=access,
        refresh_token=new_refresh,
    )


# ── logout ────────────────────────────────────────────────────────────────────

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(body: RefreshRequest):
    db = get_db()
    token_hash = hash_token(body.refresh_token)
    db.table("refresh_tokens").update({"revoked_at": datetime.now(timezone.utc).isoformat()}).eq("token_hash", token_hash).execute()


# ── me ────────────────────────────────────────────────────────────────────────

@router.get("/me", response_model=PublicUser)
async def me(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    user = db.table("users").select("*").eq("id", user_id).single().execute().data
    if not user:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "User not found."})
    mch = db.table("merchants").select("id").eq("user_id", user_id).execute()
    merchant_id = mch.data[0]["id"] if mch.data else None
    return _user_to_public(user, db, merchant_id=merchant_id)


# ── OTP request ───────────────────────────────────────────────────────────────

@router.post("/otp/request", status_code=status.HTTP_204_NO_CONTENT)
async def otp_request(body: OtpRequestBody):
    db = get_db()
    user = db.table("users").select("id").eq("phone", body.phone).execute()
    if not user.data:
        # don't reveal whether the phone exists
        return
    await _send_otp_to(body.phone, db)


# ── OTP verify ────────────────────────────────────────────────────────────────

@router.post("/otp/verify", response_model=PublicUser)
async def otp_verify(body: OtpVerifyRequest, user_id: str = Depends(get_current_user_id)):
    db = get_db()

    # find the latest unconsumed OTP for this phone
    otps = (
        db.table("otp_codes")
        .select("*")
        .eq("phone", body.phone)
        .is_("consumed_at", "null")
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if not otps.data:
        raise HTTPException(status_code=400, detail={"code": "validation_error", "message": "No active OTP found. Request a new one."})

    otp = otps.data[0]

    # check expiry
    expires = datetime.fromisoformat(otp["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires:
        raise HTTPException(status_code=400, detail={"code": "validation_error", "message": "OTP has expired. Request a new one."})

    # check attempts
    if otp["attempts"] >= OTP_MAX_ATTEMPTS:
        raise HTTPException(status_code=400, detail={"code": "validation_error", "message": "Too many incorrect attempts. Request a new OTP."})

    # verify code
    if hash_token(body.code) != otp["code_hash"]:
        db.table("otp_codes").update({"attempts": otp["attempts"] + 1}).eq("id", otp["id"]).execute()
        raise HTTPException(status_code=400, detail={"code": "validation_error", "message": "Incorrect verification code."})

    # consume OTP + mark phone verified
    db.table("otp_codes").update({"consumed_at": datetime.now(timezone.utc).isoformat()}).eq("id", otp["id"]).execute()
    db.table("users").update({"phone_verified": True}).eq("id", user_id).execute()

    user = db.table("users").select("*").eq("id", user_id).single().execute().data
    mch = db.table("merchants").select("id").eq("user_id", user_id).execute()
    merchant_id = mch.data[0]["id"] if mch.data else None
    return _user_to_public(user, merchant_id=merchant_id)
