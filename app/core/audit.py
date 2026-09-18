"""Admin action audit trail — who did what to which resource, when."""

import logging

from app.db.connection import get_db

logger = logging.getLogger(__name__)


def log_admin_action(admin_id: str, action: str, target_type: str, target_id: str, detail: dict | None = None) -> None:
    """
    Record an admin write action. Best-effort — a logging failure should
    never break the admin action itself, so errors are swallowed and logged.
    """
    try:
        get_db().table("admin_audit_log").insert({
            "admin_id": admin_id,
            "action": action,
            "target_type": target_type,
            "target_id": target_id,
            "detail": detail,
        }).execute()
    except Exception:
        logger.exception("Failed to write admin audit log entry: %s %s/%s", action, target_type, target_id)
