# S3 Presigned URL + Glacier Archiving Pattern

File uploads never pass through your backend server. The backend only generates short-lived signed URLs and stores file metadata in the database. S3 handles the file and automatically moves it to cheaper storage tiers over time.

---

## AWS Resources Required

### S3 Bucket (CloudFormation / SAM)

```yaml
MyDocumentsBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: my-app-documents
    BucketEncryption:
      ServerSideEncryptionConfiguration:
        - ServerSideEncryptionByDefault:
            SSEAlgorithm: AES256
    CorsConfiguration:
      CorsRules:
        - AllowedMethods: [GET, PUT, HEAD]
          AllowedOrigins: ['*']
          AllowedHeaders: ['*', 'content-type', 'x-amz-*']
          ExposedHeaders: [ETag]
          MaxAge: 3600
    LifecycleConfiguration:
      Rules:
        - Id: ArchiveAndExpire
          Status: Enabled
          Transitions:
            - TransitionInDays: 90
              StorageClass: GLACIER_IR   # Instant retrieval, ~80% cheaper than Standard
            - TransitionInDays: 365
              StorageClass: GLACIER      # Deep archive, ~96% cheaper, 3-5h restore
          ExpirationInDays: 730          # Auto-delete after 2 years
```

**Storage cost tiers:**

| Days | Storage Class | Cost/GB | Retrieval Speed |
|------|--------------|---------|-----------------|
| 0–90 | S3 Standard | ~$0.023 | Instant |
| 90–365 | GLACIER_IR | ~$0.004 | Instant |
| 365–730 | GLACIER | ~$0.00099 | 3–5 hours |
| 730+ | Deleted | — | — |

---

## Supabase Table

```sql
create table documents (
  id           text primary key,          -- e.g. "doc_01HXYZ123" (ULID)
  user_id      uuid references auth.users not null,
  period       text,                       -- e.g. "2024-01", or any grouping key
  s3_key       text not null,             -- full S3 object key, used to generate retrieval URL
  filename     text not null,             -- original filename for display
  status       text default 'PENDING',    -- PENDING | APPROVED | REJECTED
  uploaded_by  text,
  uploaded_at  timestamptz default now(),
  approved_by  text,
  approved_at  timestamptz,
  notes        text
);
```

> The file itself is never stored in Supabase — only the `s3_key` that points to it in S3.

---

## S3 Key Naming Convention

```
{user_or_tenant_id}/documents/{period}/{document_id}/{original_filename}

Example:
  user123/documents/2024-01/doc_01HXYZ123/invoice.pdf
```

- `user_or_tenant_id` — scopes files per user/org
- `documents/` — separates from other bucket contents
- `period/` — groups by billing period, month, or any logical grouping
- `document_id/` — unique folder per upload, prevents filename collisions
- `original_filename` — preserved for display

---

## Upload Flow

```
Client                    Backend                        S3
  |                          |                            |
  |-- POST /documents/upload-url -->                      |
  |   { period, filename }   |                            |
  |                          | generate_presigned_url()   |
  |                          |--------------------------->|
  |                          |<-- signed PUT URL (15 min)-|
  |<-- { upload_url, s3_key, document_id } --------------|
  |                          |                            |
  |-- PUT file bytes directly to upload_url ------------>|
  |<-- 200 OK -------------------------------------------|
  |                          |                            |
  |-- POST /documents ------->                            |
  |   { document_id,         |                            |
  |     s3_key, filename }   |                            |
  |                   save metadata to Supabase           |
  |<-- 201 Created ----------|                            |
```

**Step 1 — Backend generates presigned PUT URL:**
```python
PRESIGN_TTL = 900  # 15 minutes

def get_upload_url(period: str, filename: str, user_id: str):
    document_id = f"doc_{ULID()}"
    s3_key = f"{user_id}/documents/{period}/{document_id}/{filename}"

    url = s3_client.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET_NAME, "Key": s3_key},
        ExpiresIn=PRESIGN_TTL,
    )
    return {"upload_url": url, "s3_key": s3_key, "document_id": document_id}
```

**Step 2 — Client uploads directly to S3** (frontend, not backend):
```javascript
const { upload_url, s3_key, document_id } = await api.post('/documents/upload-url', { period, filename })
await fetch(upload_url, { method: 'PUT', body: file })
await api.post('/documents', { document_id, s3_key, filename, period })
```

**Step 3 — Backend saves metadata to Supabase:**
```python
def save_document(user_id: str, document_id: str, s3_key: str, filename: str, period: str):
    supabase.table("documents").insert({
        "id": document_id,
        "user_id": user_id,
        "period": period,
        "s3_key": s3_key,
        "filename": filename,
        "status": "PENDING",
        "uploaded_by": user_email,
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
    }).execute()
```

---

## Retrieval Flow

```
Client                    Backend                        S3
  |                          |                            |
  |-- GET /documents/{id}/file -->                        |
  |                          |                            |
  |                   1. fetch s3_key from Supabase       |
  |                   2. generate_presigned_url()         |
  |                          |--------------------------->|
  |                          |<-- signed GET URL (15 min)-|
  |<-- { url, expires_in } --|                            |
  |                          |                            |
  |-- GET url directly ------------------------------------->
  |<-- file bytes ----------------------------------------|
```

**Backend generates presigned GET URL:**
```python
def get_document_url(document_id: str, user_id: str):
    record = supabase.table("documents") \
        .select("s3_key") \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .single() \
        .execute()

    if not record.data:
        raise HTTPException(status_code=404)

    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": BUCKET_NAME, "Key": record.data["s3_key"]},
        ExpiresIn=PRESIGN_TTL,
    )
    return {"url": url, "expires_in": PRESIGN_TTL}
```

---

## Glacier Caveat — Files Older Than 1 Year

Presigned GET URLs work for S3 Standard and GLACIER_IR. Once a file transitions to GLACIER (after 365 days), S3 returns an error — the object must be restored first.

```python
def restore_from_glacier(s3_key: str, days: int = 7):
    s3_client.restore_object(
        Bucket=BUCKET_NAME,
        Key=s3_key,
        RestoreRequest={
            "Days": days,
            "GlacierJobParameters": {"Tier": "Standard"},  # 3-5h, cheapest
        },
    )
    # Returns immediately — restore happens async in background

def check_restore_status(s3_key: str) -> str:
    head = s3_client.head_object(Bucket=BUCKET_NAME, Key=s3_key)
    restore = head.get("Restore", "")
    if 'ongoing-request="true"' in restore:
        return "RESTORING"       # still in progress
    if 'ongoing-request="false"' in restore:
        return "READY"           # can now generate presigned URL
    return "IN_GLACIER"          # restore not started yet
```

**Recommended retrieval endpoint logic for files that may be in Glacier:**
```python
def get_document_url_safe(document_id: str, user_id: str):
    record = ...  # fetch from Supabase

    status = check_restore_status(record["s3_key"])

    if status == "READY" or status not in ("RESTORING", "IN_GLACIER"):
        url = s3_client.generate_presigned_url("get_object", ...)
        return {"url": url}

    if status == "IN_GLACIER":
        restore_from_glacier(record["s3_key"])
        return {"url": None, "status": "RESTORING", "message": "File is being restored, check back in 3-5 hours"}

    if status == "RESTORING":
        return {"url": None, "status": "RESTORING", "message": "Restore in progress, check back soon"}
```

> If files older than 1 year will be accessed regularly, remove the GLACIER transition and keep only GLACIER_IR — still 80% cheaper than Standard with no restore delay.

---

## Lambda IAM Policy

```yaml
Policies:
  - S3CrudPolicy:
      BucketName: !Ref MyDocumentsBucket
```

Or as an inline statement if not using SAM:
```yaml
- Effect: Allow
  Action:
    - s3:GetObject
    - s3:PutObject
    - s3:DeleteObject
    - s3:RestoreObject
    - s3:GetObjectAttributes
  Resource: !Sub "arn:aws:s3:::my-app-documents/*"
```

---

## Delete Flow

When deleting a record, always delete from both S3 and Supabase:

```python
def delete_document(document_id: str, user_id: str):
    record = ...  # fetch s3_key from Supabase first

    s3_client.delete_object(Bucket=BUCKET_NAME, Key=record["s3_key"])

    supabase.table("documents") \
        .delete() \
        .eq("id", document_id) \
        .eq("user_id", user_id) \
        .execute()
```

---

## Prompt for AI

> Implement a file upload system using S3 presigned URLs, Supabase (PostgreSQL) for metadata, and S3 Glacier lifecycle archiving for cost savings.
>
> **Upload:** `POST /documents/upload-url` — backend generates a presigned PUT URL (15 min TTL) and returns `{ upload_url, s3_key, document_id }`. The file never passes through the backend. Client uploads directly to S3, then calls `POST /documents` with `{ document_id, s3_key, filename, period }` to save metadata to Supabase.
>
> **Retrieval:** `GET /documents/{id}/file` — backend fetches `s3_key` from Supabase, generates a presigned GET URL (15 min TTL), returns it. Client fetches the file directly from S3.
>
> **S3 key format:** `{user_id}/documents/{period}/{document_id}/{filename}`
>
> **Supabase table:** `documents` with columns `id, user_id, period, s3_key, filename, status, uploaded_by, uploaded_at, approved_by, approved_at, notes`.
>
> **S3 lifecycle:** GLACIER_IR at 90 days, GLACIER at 365 days, delete at 730 days. For files in GLACIER, implement a `restore_object` flow that returns `{ status: "RESTORING" }` and a `check_restore_status` helper before generating the presigned URL.
>
> **Delete:** remove from both S3 and Supabase.
