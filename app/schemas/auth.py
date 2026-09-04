from pydantic import BaseModel, field_validator
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
    full_name: str
    phone: str
    email: str
    password: str
    user_type: str
    business_name: str

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

    @field_validator("password")
    @classmethod
    def min_length(cls, v: str) -> str:
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    identifier: str   # phone or email
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class OtpRequestBody(BaseModel):
    phone: str

    @field_validator("phone")
    @classmethod
    def normalise(cls, v: str) -> str:
        return normalise_phone(v)


class OtpVerifyRequest(BaseModel):
    phone: str
    code: str

    @field_validator("phone")
    @classmethod
    def normalise(cls, v: str) -> str:
        return normalise_phone(v)


class PublicUser(BaseModel):
    id: str
    full_name: str
    phone: str
    email: str | None
    user_type: str
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
