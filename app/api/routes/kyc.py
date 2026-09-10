from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.core.deps import get_current_user_id, require_staff
from app.db.connection import get_db
from app.services.s3_service import (
    presign_put, presign_get, glacier_status, restore_from_glacier,
    delete_object, make_doc_id,
)
from app.services.sms_service import send_sms

router = APIRouter()

VALID_DOC_TYPES = ("id_document", "proof_of_bank", "selfie")


class UploadUrlRequest(BaseModel):
    doc_type: str
    filename: str
    content_type: str = "application/octet-stream"


class ConfirmUploadRequest(BaseModel):
    doc_id: str
    s3_key: str
    filename: str
    doc_type: str


class ReviewRequest(BaseModel):
    status: str          # 'approved' | 'rejected'
    rejection_reason: str | None = None


# ── Merchant: request presigned PUT URL ──────────────────────────────────────

@router.post("/merchants/me/documents/upload-url")
async def get_kyc_upload_url(
    body: UploadUrlRequest,
    user_id: str = Depends(get_current_user_id),
):
    if body.doc_type not in VALID_DOC_TYPES:
        raise HTTPException(status_code=422, detail={"code": "invalid_doc_type", "message": f"doc_type must be one of {VALID_DOC_TYPES}"})

    db = get_db()
    merchant_res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not merchant_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found"})
    merchant_id = merchant_res.data[0]["id"]

    doc_id = make_doc_id()
    s3_key = f"kyc/{merchant_id}/{body.doc_type}/{doc_id}/{body.filename}"
    upload_url = presign_put(s3_key, body.content_type)

    return {"upload_url": upload_url, "s3_key": s3_key, "doc_id": doc_id}


# ── Merchant: confirm upload (save metadata) ─────────────────────────────────

@router.post("/merchants/me/documents")
async def confirm_kyc_upload(
    body: ConfirmUploadRequest,
    user_id: str = Depends(get_current_user_id),
):
    if body.doc_type not in VALID_DOC_TYPES:
        raise HTTPException(status_code=422, detail={"code": "invalid_doc_type", "message": "Invalid doc_type"})

    db = get_db()
    merchant_res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not merchant_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found"})
    merchant_id = merchant_res.data[0]["id"]

    # Upsert — replace previous doc of same type
    existing = db.table("merchant_documents").select("s3_key").eq("merchant_id", merchant_id).eq("doc_type", body.doc_type).execute()
    if existing.data:
        delete_object(existing.data[0]["s3_key"])
        db.table("merchant_documents").delete().eq("merchant_id", merchant_id).eq("doc_type", body.doc_type).execute()

    res = db.table("merchant_documents").insert({
        "id": body.doc_id,
        "merchant_id": merchant_id,
        "doc_type": body.doc_type,
        "s3_key": body.s3_key,
        "filename": body.filename,
        "status": "pending",
    }).execute()

    # Reset merchant kyc_status to pending when new docs uploaded
    db.table("merchants").update({"kyc_status": "pending"}).eq("id", merchant_id).execute()

    return res.data[0]


# ── Merchant: list own documents ─────────────────────────────────────────────

@router.get("/merchants/me/documents")
async def list_kyc_documents(user_id: str = Depends(get_current_user_id)):
    db = get_db()
    merchant_res = db.table("merchants").select("id,kyc_status").eq("user_id", user_id).execute()
    if not merchant_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found"})
    merchant = merchant_res.data[0]

    docs = db.table("merchant_documents") \
        .select("id,doc_type,filename,status,rejection_reason,uploaded_at,reviewed_at") \
        .eq("merchant_id", merchant["id"]) \
        .execute()

    return {"kyc_status": merchant["kyc_status"], "documents": docs.data or []}


# ── Merchant: get presigned view URL for own document ───────────────────────

@router.get("/merchants/me/documents/{doc_id}/file")
async def get_merchant_kyc_file_url(
    doc_id: str,
    user_id: str = Depends(get_current_user_id),
):
    db = get_db()
    merchant_res = db.table("merchants").select("id").eq("user_id", user_id).execute()
    if not merchant_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Merchant not found"})
    merchant_id = merchant_res.data[0]["id"]

    res = db.table("merchant_documents").select("s3_key").eq("id", doc_id).eq("merchant_id", merchant_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})

    return {"url": presign_get(res.data[0]["s3_key"]), "expires_in": 900}


# ── Staff: KYC review queue ───────────────────────────────────────────────────

@router.get("/admin/kyc")
async def list_kyc_queue(
    status: str = "pending",
    staff_id: str = Depends(require_staff),
):
    db = get_db()
    docs = db.table("merchant_documents") \
        .select("id,merchant_id,doc_type,filename,s3_key,status,rejection_reason,uploaded_at") \
        .eq("status", status) \
        .order("uploaded_at") \
        .execute()

    rows = docs.data or []
    if not rows:
        return []

    merchant_ids = list({r["merchant_id"] for r in rows})
    merchants = db.table("merchants") \
        .select("id,business_name,kyc_status") \
        .in_("id", merchant_ids) \
        .execute()
    m_map = {m["id"]: m for m in (merchants.data or [])}

    for r in rows:
        r["merchant"] = m_map.get(r["merchant_id"])
        del r["s3_key"]  # don't expose raw key — use /file endpoint

    return rows


# ── Staff: get presigned view URL for a document ─────────────────────────────

@router.get("/admin/kyc/{doc_id}/file")
async def get_kyc_file_url(
    doc_id: str,
    staff_id: str = Depends(require_staff),
):
    db = get_db()
    res = db.table("merchant_documents").select("s3_key,status").eq("id", doc_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})

    s3_key = res.data[0]["s3_key"]
    gstatus = glacier_status(s3_key)

    if gstatus == "in_glacier":
        restore_from_glacier(s3_key)
        return {"url": None, "status": "restoring", "message": "File is being restored from archive, check back in 3–5 hours"}

    if gstatus == "restoring":
        return {"url": None, "status": "restoring", "message": "Restore in progress, check back soon"}

    return {"url": presign_get(s3_key), "status": "available", "expires_in": 900}


# ── Staff: approve or reject a document ──────────────────────────────────────

@router.patch("/admin/kyc/{doc_id}")
async def review_kyc_document(
    doc_id: str,
    body: ReviewRequest,
    staff_id: str = Depends(require_staff),
):
    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=422, detail={"code": "invalid_status", "message": "status must be approved or rejected"})
    if body.status == "rejected" and not body.rejection_reason:
        raise HTTPException(status_code=422, detail={"code": "reason_required", "message": "rejection_reason is required when rejecting"})

    db = get_db()
    doc_res = db.table("merchant_documents").select("merchant_id").eq("id", doc_id).execute()
    if not doc_res.data:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Document not found"})
    merchant_id = doc_res.data[0]["merchant_id"]

    now = datetime.now(timezone.utc).isoformat()
    db.table("merchant_documents").update({
        "status": body.status,
        "rejection_reason": body.rejection_reason,
        "reviewed_by": staff_id,
        "reviewed_at": now,
    }).eq("id", doc_id).execute()

    # Recompute merchant kyc_status from all docs
    all_docs = db.table("merchant_documents") \
        .select("status") \
        .eq("merchant_id", merchant_id) \
        .execute()
    statuses = [d["status"] for d in (all_docs.data or [])]

    if any(s == "rejected" for s in statuses):
        kyc_status = "failed"
    elif all(s == "approved" for s in statuses) and len(statuses) == len(VALID_DOC_TYPES):
        kyc_status = "verified"
    else:
        kyc_status = "pending"

    db.table("merchants").update({
        "kyc_status": kyc_status,
        "kyc_verified_at": now if kyc_status == "verified" else None,
    }).eq("id", merchant_id).execute()

    # SMS notification to merchant
    user_res = db.table("users").select("phone").eq(
        "id",
        db.table("merchants").select("user_id").eq("id", merchant_id).execute().data[0]["user_id"]
    ).execute()
    if user_res.data:
        phone = user_res.data[0]["phone"]
        if kyc_status == "verified":
            msg = "Your Scan2Pay KYC verification is complete. Your account is now fully verified and withdrawal limits have been lifted."
        elif kyc_status == "failed":
            reason = body.rejection_reason or "Please resubmit the required documents."
            msg = f"Your Scan2Pay KYC document was rejected. Reason: {reason} Please log in to resubmit."
        else:
            msg = None
        if msg:
            await send_sms(phone, msg)

    return {"doc_id": doc_id, "status": body.status, "merchant_kyc_status": kyc_status}
