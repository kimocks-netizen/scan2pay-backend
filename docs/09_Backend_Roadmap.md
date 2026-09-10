# scan2pay-backend — Backend Roadmap

> Single source of truth for backend state, endpoints, and pending work.
> Last updated: September 2026

## Working Rules
1. **Third-party APIs** — if unsure about exact payload, auth format, or endpoint behaviour (WinSMS, Paystack, etc.), ask the user first. Do not guess.
2. **Unclear requirements** — if scope is ambiguous, ask before writing code.
3. **Scope** — only build what was explicitly asked for in the current session.
4. **Existing patterns** — check how it's already done before implementing anything new.

---

## Stack
Python 3.13 · FastAPI · Mangum · Supabase (Postgres) · Paystack · WinSMS · AWS SAM · S3

## Deployment
- Stack: `scan2pay-backend` · Region: `af-south-1` · Account: `542727784619` (profile: `predictiq`)
- API: `https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod`
- Deploy: `bash scripts/deploy.sh`

## Quick Tokens
```bash
API=https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod

VENDOR_TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" \
  -d '{"identifier":"0821000001","password":"Vendor1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

ADMIN_TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" \
  -d '{"identifier":"0616583827","password":"Admin1234"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

SUPPORT_TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" \
  -d '{"identifier":"0600000001","password":"Support1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
```

## Test Credentials
| Role    | Phone      | Password     |
|---------|------------|--------------|
| Vendor  | 0821000001 | Vendor1234!  |
| Tip     | 0660404333 | 123456       |
| Admin   | 0616583827 | Admin1234    |
| Support | 0600000001 | Support1234! |

OTP bypass: `0000`

---

## Lambda Architecture
| Lambda | Trigger | Purpose |
|---|---|---|
| `Scan2PayApiFunction` | API Gateway `/{proxy+}` | Entire FastAPI app via Mangum |
| `ExpireChargesFunction` | EventBridge every 1 min | Set `active=false` on codes past `expires_at` |
| `ReconcilePaystackFunction` | EventBridge every 15 min | Verify `pending` payments older than 10 min |
| `BuildSettlementsFunction` | EventBridge daily 18:00 UTC (20:00 SAST) | Settle eligible transactions (T+2 clearing) |

---

## ✅ Phase 1 — Merchant (COMPLETE)

### Routes
| File | Endpoints |
|---|---|
| `health.py` | `GET /health` |
| `auth.py` | register, login, refresh, logout, me, otp/request, otp/verify |
| `merchants.py` | `GET/PATCH /merchants/me`, `PATCH /me/payout-account`, `GET /me/balance`, `GET /:id` |
| `products.py` | CRUD `/merchants/me/products`, regenerate-qr |
| `payment_codes.py` | CRUD `/merchants/me/payment-codes` |
| `charges.py` | `POST /charges`, charge session flow |
| `payments.py` | `POST /payments/initialise`, `GET /payments/:id` |
| `transactions.py` | Paginated + filters (status/method/type/settlement) |
| `withdrawals.py` | `GET/POST/DELETE /merchants/me/withdrawals` |
| `billing.py` | `GET /billing/banks` — 33 SA banks proxy |
| `webhooks.py` | charge.success, transfer.success/failed/reversed |

### Migrations
- `001` through `013` ✅ — includes payout_account_name, kyc_status, transfer_code, failure_reason, expanded withdrawal status

---

## ✅ Phase 2 — Admin Console (COMPLETE)

### Routes
| File | Endpoints |
|---|---|
| `admin.py` | `GET /admin/merchants` + `PATCH /admin/merchants/{id}` |
| | `GET /admin/users` + `PATCH /admin/users/{id}` |
| | `GET /admin/transactions` (paginated, filters: status/method/merchant_id/since) |
| | `GET /admin/balance` — Paystack ZAR balance |
| | `GET /admin/audit` — webhook_events log |
| | `GET /admin/settlements/pending` + `POST /admin/settlements/run` |
| | `GET /admin/withdrawals` (paginated, merchant_id + status filter) + `PATCH /admin/withdrawals/{id}/status` |
| | `GET /admin/pricing` + `POST /admin/pricing` + `GET /admin/plans` |
| | `GET /admin/support-stats` |
| `kyc.py` | `POST /merchants/me/documents/upload-url` + `POST /merchants/me/documents` |
| | `GET /merchants/me/documents` + `GET /merchants/me/documents/{doc_id}/file` |
| | `GET /admin/kyc` + `GET /admin/kyc/{doc_id}/file` + `PATCH /admin/kyc/{doc_id}` |
| `cms.py` | `GET /cms/homepage` (public) |
| | `POST /admin/cms/upload-url` + `POST /admin/cms/confirm` + `GET /admin/cms` |
| `support.py` | `GET /support/me` + `GET /support/my-stats` |

### Access control
- `require_staff` — admin or support. Used on all read endpoints.
- `require_admin` — admin only. Used on all write/financial endpoints.

### Migrations
- `014` ✅ — `fee_owed_cents`, `fee_last_charged_at`, `plan` columns on merchants
- `015` ✅ — `referred_by` on merchants, `merchant_documents`, `cms_assets`, `support_commissions`

### S3 Bucket
- Name: `scan2pay-assets-dev-542727784619`
- Key structure: `kyc/{merchant_id}/{doc_type}/{doc_id}/{filename}` · `cms/homepage/{slot}/{cms_id}/{filename}`
- CORS: GET, PUT, HEAD · `AllowedOrigins: ['*']`
- Lifecycle: KYC → GLACIER_IR 90d → GLACIER 365d → delete 730d; CMS → GLACIER_IR 90d
- Presigned URLs use regional endpoint `https://s3.af-south-1.amazonaws.com` (required for opt-in regions)
- `presign_put` signs `ContentType` — frontend must send matching `Content-Type` header

### Commission logic
- `referral_code` = support user_id
- Merchants with `referred_by` → assigned to that support agent
- Merchants without → unassigned pool ÷ active support agents
- Monthly: `total = assigned + pool_share + rollover_in`
- `bonus_units = floor(total / 1000)`, `rollover_out = total % 1000`

---

## ✅ Phase 3 — Referral Signup Flow (COMPLETE)

- [x] `POST /auth/register` — accepts optional `referral_code`, validates it exists as a user, stores as `referred_by` on merchant
- [x] Signup URL format: `/login?mode=register&ref=<support_user_id>`

---

## ✅ Phase 4 — Notifications & Automation (COMPLETE)

- [x] **WinSMS on KYC decision** — SMS sent in `PATCH /admin/kyc/{doc_id}` when status → verified or failed
- [x] **WinSMS on withdrawal decision** — SMS sent in `PATCH /admin/withdrawals/{id}/status` when approved or rejected
- [x] **Settlement fee fix** — `settlement_service.py` already uses `plan_id` correctly
- [x] **OTP during registration** — built and wired end-to-end (bypass: `0000` in dev)
- [ ] Merchant notification preferences (SMS default, email/WhatsApp future) — settings page
- [ ] Merchant plan upgrade flow (self-serve request → support/admin approves)

---

## 🔲 Phase 5 — Production Readiness

- [ ] Paystack live keys (swap SSM params)
- [ ] `POST /apple-pay/domain` — register `scan2pay.site`
- [ ] Custom domain for API Gateway
- [ ] Paystack webhook URL confirmed in Paystack dashboard
- [ ] Verify settlement cron running in prod (CloudWatch logs)
- [ ] KYC bank validation — test mode always returns `verified=false`
- [ ] Rate limiting (API Gateway usage plans)
- [ ] Error monitoring (CloudWatch alarms or Sentry)

---

## SSM Parameters
```
/scan2pay/dev/SUPABASE_URL
/scan2pay/dev/SUPABASE_ANON_KEY
/scan2pay/dev/SUPABASE_SERVICE_ROLE_KEY
/scan2pay/dev/JWT_SECRET
/scan2pay/dev/WINSMS_API_KEY
/scan2pay/dev/PAYSTACK_SECRET_KEY     → sk_test_5007f89004bd371737871acffe64a98fd2ec3a36
/scan2pay/dev/PAYSTACK_PUBLIC_KEY     → pk_test_23c73dd403061843824f61e3cb4cd96bd5220110
/scan2pay/dev/PAYSTACK_WEBHOOK_SECRET → same as PAYSTACK_SECRET_KEY
```

---

## DB Column Notes
- `transactions.platform_fee_cents` (not `fee_cents`)
- `merchants.plan_id` (not `plan`)
- `webhook_events.provider_reference` (not `reference`)

---

## Bugs Fixed
| Bug | Fix |
|---|---|
| `.single()` on Supabase throws if row exists | Replaced all with `.execute()` + index `[0]` |
| Boolean metadata causes Paystack 500 | Convert to strings `"true"`/`"false"` |
| `apple_pay`/`google_pay` channels cause Paystack 500 on ZAR test | Use `["card"]` only |
| Global exception handler swallowing HTTPException | Added isinstance check |
| Webhook `.single()` on payment_codes swallows charge.success | Fixed + wrapped in try/except |
| `transactions` endpoint returning `count` not `total` | Fixed — returns `total` from `count="exact"` |
| Duplicate `GET /pay/{reference}` route | Removed from payment_codes.py |
| `/merchants/me` 404 — wildcard catching `/me` | Fixed route order |
| `document_type` hardcoded as `identityNumber` | Now driven by frontend toggle |
| S3 presigned PUT 400 — `ContentType` not signed | `presign_put` now signs `ContentType` |
| S3 `IllegalLocationConstraintException` | S3 client uses regional endpoint `s3.af-south-1.amazonaws.com` |
| CMS images not updating after upload | `force-dynamic` + `cache: "no-store"` on home pages |
