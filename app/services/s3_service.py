import secrets
import boto3
from botocore.exceptions import ClientError

from app.core.config import get_settings

PRESIGN_TTL = 900  # 15 minutes

_s3 = None


def _client():
    global _s3
    if _s3 is None:
        settings = get_settings()
        _s3 = boto3.client("s3", region_name=settings.aws_region)
    return _s3


def _bucket() -> str:
    return get_settings().assets_bucket


def presign_put(s3_key: str, content_type: str = "application/octet-stream") -> str:
    return _client().generate_presigned_url(
        "put_object",
        Params={"Bucket": _bucket(), "Key": s3_key, "ContentType": content_type},
        ExpiresIn=PRESIGN_TTL,
    )


def presign_get(s3_key: str) -> str:
    return _client().generate_presigned_url(
        "get_object",
        Params={"Bucket": _bucket(), "Key": s3_key},
        ExpiresIn=PRESIGN_TTL,
    )


def glacier_status(s3_key: str) -> str:
    """Returns 'available' | 'restoring' | 'in_glacier'."""
    try:
        head = _client().head_object(Bucket=_bucket(), Key=s3_key)
        restore = head.get("Restore", "")
        if not restore:
            return "available"
        if 'ongoing-request="true"' in restore:
            return "restoring"
        if 'ongoing-request="false"' in restore:
            return "available"
        return "in_glacier"
    except ClientError as e:
        if e.response["Error"]["Code"] == "InvalidObjectState":
            return "in_glacier"
        raise


def restore_from_glacier(s3_key: str, days: int = 7) -> None:
    _client().restore_object(
        Bucket=_bucket(),
        Key=s3_key,
        RestoreRequest={"Days": days, "GlacierJobParameters": {"Tier": "Standard"}},
    )


def delete_object(s3_key: str) -> None:
    try:
        _client().delete_object(Bucket=_bucket(), Key=s3_key)
    except ClientError:
        pass  # already gone — not an error


def make_doc_id() -> str:
    return f"doc_{secrets.token_hex(8)}"


def make_cms_id() -> str:
    return f"cms_{secrets.token_hex(6)}"
