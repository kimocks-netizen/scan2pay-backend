with open("app/api/routes/kyc.py", "r") as f:
    content = f.read()

old_sig = 'async def list_kyc_queue(\n    status: str = "pending",\n    staff_id: str = Depends(require_staff),\n):'
new_sig = 'async def list_kyc_queue(\n    status: str = Query("pending"),\n    merchant_id: str | None = Query(None),\n    limit: int = Query(50, ge=1, le=200),\n    offset: int = Query(0, ge=0),\n    staff_id: str = Depends(require_staff),\n):'

old_body = (
    '    db = get_db()\n'
    '    docs = db.table("merchant_documents") \\\n'
    '        .select("id,merchant_id,doc_type,filename,s3_key,status,rejection_reason,uploaded_at") \\\n'
    '        .eq("status", status) \\\n'
    '        .order("uploaded_at") \\\n'
    '        .execute()\n'
    '\n'
    '    rows = docs.data or []\n'
    '    if not rows:\n'
    '        return []\n'
    '\n'
    '    merchant_ids = list({r["merchant_id"] for r in rows})\n'
    '    merchants = db.table("merchants") \\\n'
    '        .select("id,business_name,kyc_status,payout_bank,payout_account_masked,payout_account_name,bank_verified,bank_holder_match,bank_accepts_credits,bank_account_open,bank_open_3_months,bank_verification_msg,bank_validated_at") \\\n'
    '        .in_("id", merchant_ids) \\\n'
    '        .execute()\n'
    '    m_map = {m["id"]: m for m in (merchants.data or [])}\n'
    '\n'
    '    for r in rows:\n'
    '        r["merchant"] = m_map.get(r["merchant_id"])\n'
    '        del r["s3_key"]  # don\'t expose raw key \u2014 use /file endpoint\n'
    '\n'
    '    return rows'
)

new_body = (
    '    db = get_db()\n'
    '    count_q = db.table("merchant_documents").select("id", count="exact").eq("status", status)\n'
    '    data_q = (\n'
    '        db.table("merchant_documents")\n'
    '        .select("id,merchant_id,doc_type,filename,s3_key,status,rejection_reason,uploaded_at")\n'
    '        .eq("status", status)\n'
    '        .order("uploaded_at")\n'
    '        .limit(limit)\n'
    '        .offset(offset)\n'
    '    )\n'
    '    if merchant_id:\n'
    '        count_q = count_q.eq("merchant_id", merchant_id)\n'
    '        data_q = data_q.eq("merchant_id", merchant_id)\n'
    '\n'
    '    count_res = count_q.execute()\n'
    '    total = count_res.count if count_res.count is not None else 0\n'
    '    rows = data_q.execute().data or []\n'
    '\n'
    '    if not rows:\n'
    '        return {"data": [], "total": total, "offset": offset}\n'
    '\n'
    '    merchant_ids = list({r["merchant_id"] for r in rows})\n'
    '    merchants = db.table("merchants") \\\n'
    '        .select("id,business_name,kyc_status,payout_bank,payout_account_masked,payout_account_name,bank_verified,bank_holder_match,bank_accepts_credits,bank_account_open,bank_open_3_months,bank_verification_msg,bank_validated_at") \\\n'
    '        .in_("id", merchant_ids) \\\n'
    '        .execute()\n'
    '    m_map = {m["id"]: m for m in (merchants.data or [])}\n'
    '\n'
    '    for r in rows:\n'
    '        r["merchant"] = m_map.get(r["merchant_id"])\n'
    '        del r["s3_key"]\n'
    '\n'
    '    return {"data": rows, "total": total, "offset": offset}'
)

assert old_sig in content, "sig not found"
assert old_body in content, "body not found"

content = content.replace(old_sig, new_sig)
content = content.replace(old_body, new_body)

# also add Query to the import
content = content.replace(
    "from fastapi import APIRouter, Depends, HTTPException",
    "from fastapi import APIRouter, Depends, HTTPException, Query",
)

with open("app/api/routes/kyc.py", "w") as f:
    f.write(content)

print("done")
