from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.deps import require_staff
from app.db.connection import get_db
from app.services.s3_service import presign_put, delete_object, make_cms_id

router = APIRouter()

VALID_SLOTS = ("hero", "feature_1", "feature_2", "banner", "feature_3", "feature_4", "feature_5")


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
    focal_x: float = 50
    focal_y: float = 50


class CmsFocalRequest(BaseModel):
    focal_x: float
    focal_y: float


class CmsVisibilityRequest(BaseModel):
    visible: bool


# ── Public: get current home page assets (visible only) ──────────────────────

@router.get("/cms/homepage")
async def get_homepage_assets():
    settings = get_settings()
    db = get_db()
    rows = db.table("cms_assets").select("slot,s3_key,filename,alt_text,focal_x,focal_y,uploaded_at") \
        .eq("active", True).eq("visible", True).execute()
    result = {}
    for row in (rows.data or []):
        url = f"https://s3.af-south-1.amazonaws.com/{settings.assets_bucket}/{row['s3_key']}"
        result[row["slot"]] = {
            "url": url,
            "filename": row["filename"],
            "alt_text": row["alt_text"],
            "focal_x": row.get("focal_x") or 50,
            "focal_y": row.get("focal_y") or 50,
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
        "focal_x": body.focal_x,
        "focal_y": body.focal_y,
        "active": True,
        "visible": True,
        "uploaded_by": staff_id,
    }).execute()
    return res.data[0]


# ── Staff: toggle visibility ──────────────────────────────────────────────────

@router.patch("/admin/cms/{slot}/visibility")
async def set_visibility(
    slot: str,
    body: CmsVisibilityRequest,
    staff_id: str = Depends(require_staff),
):
    if slot not in VALID_SLOTS:
        raise HTTPException(status_code=422, detail={"code": "invalid_slot", "message": "Invalid slot"})
    db = get_db()
    db.table("cms_assets").update({"visible": body.visible}).eq("slot", slot).eq("active", True).execute()
    return {"ok": True}


# ── Staff: update focal point ─────────────────────────────────────────────────

@router.patch("/admin/cms/{slot}/focal")
async def update_focal_point(
    slot: str,
    body: CmsFocalRequest,
    staff_id: str = Depends(require_staff),
):
    if slot not in VALID_SLOTS:
        raise HTTPException(status_code=422, detail={"code": "invalid_slot", "message": "Invalid slot"})
    db = get_db()
    db.table("cms_assets").update({"focal_x": body.focal_x, "focal_y": body.focal_y}).eq("slot", slot).eq("active", True).execute()
    return {"ok": True}


# ── Staff: list all CMS assets (admin view, includes hidden) ──────────────────

@router.get("/admin/cms")
async def list_cms_assets(staff_id: str = Depends(require_staff)):
    settings = get_settings()
    db = get_db()
    rows = db.table("cms_assets").select("id,slot,s3_key,filename,alt_text,focal_x,focal_y,visible,active,uploaded_by,uploaded_at").execute()
    result = []
    for row in (rows.data or []):
        url = f"https://s3.af-south-1.amazonaws.com/{settings.assets_bucket}/{row['s3_key']}"
        result.append({**row, "url": url})
    return result
