from pydantic import BaseModel, Field, field_validator
import re

USER_TYPES = {"vendor", "tip", "taxi"}


def normalise_phone(raw: str) -> str:
    digits = re.sub(r"[^\d+]", "", raw)
    if digits.startswith("+"):
        return digits
    if digits.startswith("0"):
        return f"+27{digits[1:]}"
    if digits.startswith("27"):
        return f"+{digits}"
    return digits


class RegisterRequest(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=100)
    phone: str = Field(..., max_length=20)
    email: str = Field(..., max_length=254)
    password: str = Field(..., min_length=6, max_length=128)
    user_type: str
    business_name: str = Field(..., min_length=2, max_length=100)

    @field_validator("phone")
    @classmethod
    def normalise(cls, v: str) -> str:
        return normalise_phone(v)

    @field_validator("user_type")
    @classmethod
    def valid_type(cls, v: str) -> str:
        if v not in USER_TYPES:
            raise ValueError(f"user_type must be one of {USER_TYPES}")
        return v


class LoginRequest(BaseModel):
    identifier: str = Field(..., max_length=254)
    password: str = Field(..., max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., max_length=512)


class LogoutRequest(BaseModel):
    # Optional — the proxy injects this from its own httpOnly cookie when
    # present, but that cookie may already be gone (expired/cleared) by the
    # time logout fires. A missing token here is a no-op, not an error.
    refresh_token: str | None = Field(None, max_length=512)


class OtpRequestBody(BaseModel):
    phone: str = Field(..., max_length=20)

    @field_validator("phone")
    @classmethod
    def normalise(cls, v: str) -> str:
        return normalise_phone(v)


class OtpVerifyRequest(BaseModel):
    phone: str = Field(..., max_length=20)
    code: str = Field(..., max_length=64)

    @field_validator("phone")
    @classmethod
    def normalise(cls, v: str) -> str:
        return normalise_phone(v)


class PublicUser(BaseModel):
    id: str
    full_name: str
    phone: str
    email: str | None
    user_type: str | None
    role: str
    status: str
    merchant_id: str | None
    avatar_initials: str | None
    phone_verified: bool
    email_verified: bool
    created_at: str


class AuthResponse(BaseModel):
    user: PublicUser
    access_token: str
    refresh_token: str


class PasswordResetRequestBody(BaseModel):
    identifier: str = Field(..., max_length=254)

class PasswordResetConfirmBody(BaseModel):
    identifier: str = Field(..., max_length=254)
    code: str = Field(..., max_length=64)
    new_password: str = Field(..., min_length=6, max_length=128)
