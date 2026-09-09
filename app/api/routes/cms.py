from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import require_staff
from app.db.connection import get_db
from app.services.s3_service import presign_put, presign_get, delete_object, make_cms_id

router = APIRouter()

VALID_SLOTS = ("hero", "feature_1", "feature_2", "banner")


class CmsUploadUrlRequest(BaseModel):
    slot: str
    filename: str
    content_type: str = "application/octet-stream"
    alt_text: str = ""


class CmsConfirmRequest(BaseModel):
    cms_id: str
    slot: str
    s3_key: str
    filename: str
    alt_text: str = ""


# ── Public: get current home page assets ─────────────────────────────────────

@router.get("/cms/homepage")
async def get_homepage_assets():
    db = get_db()
    res = db.table("cms_assets").select("slot,filename,alt_text,uploaded_at").eq("active", True).execute()
    assets = {row["slot"]: row for row in (res.data or [])}

    # Generate fresh presigned GET URLs for each active asset
    full_res = db.table("cms_assets").select("slot,s3_key,filename,alt_text,uploaded_at").eq("active", True).execute()
    result = {}
    for row in (full_res.data or []):
        try:
            url = presign_get(row["s3_key"])
        except Exception:
            url = None
        result[row["slot"]] = {
            "url": url,
            "filename": row["filename"],
            "alt_text": row["alt_text"],
            "uploaded_at": row["uploaded_at"],
        }
    return result


# ── Staff: request presigned PUT URL ─────────────────────────────────────────

@router.post("/admin/cms/upload-url")
async def get_cms_upload_url(
    body: CmsUploadUrlRequest,
    staff_id: str = Depends(require_staff),
):
    if body.slot not in VALID_SLOTS:
        raise HTTPException(status_code=422, detail={"code": "invalid_slot", "message": f"slot must be one of {VALID_SLOTS}"})

    cms_id = make_cms_id()
    s3_key = f"cms/homepage/{body.slot}/{cms_id}/{body.filename}"
    upload_url = presign_put(s3_key, body.content_type)

    return {"upload_url": upload_url, "s3_key": s3_key, "cms_id": cms_id}


# ── Staff: confirm upload ─────────────────────────────────────────────────────

@router.post("/admin/cms/confirm")
async def confirm_cms_upload(
    body: CmsConfirmRequest,
    staff_id: str = Depends(require_staff),
):
    if body.slot not in VALID_SLOTS:
        raise HTTPException(status_code=422, detail={"code": "invalid_slot", "message": "Invalid slot"})

    db = get_db()

    # Delete old S3 object + DB row for this slot
    existing = db.table("cms_assets").select("s3_key").eq("slot", body.slot).execute()
    if existing.data:
        delete_object(existing.data[0]["s3_key"])
        db.table("cms_assets").delete().eq("slot", body.slot).execute()

    res = db.table("cms_assets").insert({
        "id": body.cms_id,
        "slot": body.slot,
        "s3_key": body.s3_key,
        "filename": body.filename,
        "alt_text": body.alt_text,
        "active": True,
        "uploaded_by": staff_id,
    }).execute()

    return res.data[0]


# ── Staff: list all CMS assets ────────────────────────────────────────────────

@router.get("/admin/cms")
async def list_cms_assets(staff_id: str = Depends(require_staff)):
    db = get_db()
    res = db.table("cms_assets").select("id,slot,filename,alt_text,active,uploaded_by,uploaded_at").execute()
    return res.data or []
