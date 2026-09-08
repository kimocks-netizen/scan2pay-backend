# scan2pay-backend — Build Roadmap

---

## ⚠️ Working Rules

1. **Third-party APIs** — if unsure about the exact payload, auth format, or endpoint behaviour of any external API (WinSMS, Paystack, etc.), **ask the user first**. Do not guess.
2. **Unclear requirements** — if the scope of a feature is ambiguous, **ask before writing any code**.
3. **Scope** — only build what was explicitly asked for in the current session.
4. **Existing patterns** — before implementing anything new, check how it is already done in the codebase.

---

## Stack
Python 3.13 · FastAPI · Mangum · Supabase (Postgres) · Paystack · WinSMS · AWS SAM · S3

## Deployment
- Stack: `scan2pay-backend` · Region: `af-south-1` · Account: `542727784619` (profile: `predictiq`)
- API: `https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod`
- Deploy: `sam build --no-cached && sam deploy --profile predictiq --config-file samconfig.toml --parameter-overrides "Environment=dev" --force-upload`

## Lambda Architecture
| Lambda | Trigger | Purpose |
|---|---|---|
| `Scan2PayApiFunction` | API Gateway `/{proxy+}` | Entire FastAPI app via Mangum |
| `ExpireChargesFunction` | EventBridge every 1 min | Set `active=false` on codes past `expires_at` |
| `ReconcilePaystackFunction` | EventBridge every 15 min | Verify `pending` payments older than 10 min |
| `BuildSettlementsFunction` | EventBridge daily 02:00 SAST | Group settled transactions into payout rows |

---

## Phase 1 — Foundation ✅
- [x] Project structure, `requirements.txt`, SAM template
- [x] `app/core/config.py`, `security.py`, `deps.py`
- [x] `app/db/connection.py` — Supabase client singleton
- [x] `app/main.py` — FastAPI + all routers + Mangum + global exception handler
- [x] `app/services/sms_service.py` — WinSMS OTP
- [x] All 3 cron Lambdas implemented

## Phase 2 — Database ✅
- [x] `001_enums.sql` through `008_webhooks_audit.sql` — all run ✅
- [x] `009_merchant_bank_accounts.sql` — **not yet run** (needed for withdrawals)
- [x] `010_txn_authorization_code.sql` — `ALTER TABLE transactions ADD COLUMN authorization_code text` ✅ run manually
- [x] `seed.sql` — test user `+27820000099` / `Test1234!`, merchant `mch_004`, payment code `QR-890E282B` ✅

## Phase 3–5 — Schemas / Services ✅
- [x] `app/services/paystack_service.py` — initialize, verify, list, create_recipient, initiate/finalize/fetch transfer
- [x] All schemas inline in routes (sufficient for current complexity)

## Phase 6 — Routes ✅ (all live)

| Route file | Endpoints | Status |
|---|---|---|
| `health.py` | `GET /health` | ✅ |
| `auth.py` | register, login, refresh, logout, me, otp/request, otp/verify | ✅ |
| `merchants.py` | `GET/PATCH /merchants/me`, `GET /merchants/:id` | ✅ |
| `products.py` | CRUD `/merchants/me/products` | ✅ |
| `payment_codes.py` | CRUD `/merchants/me/payment-codes`, `GET /pay/:reference` | ✅ |
| `charges.py` | `POST /charges`, `GET /charges/:reference`, `POST /pay/:reference/initialise` (public) | ✅ |
| `payments.py` | `POST /payments/initialise`, `GET /payments/:id` | ✅ |
| `transactions.py` | `GET /merchants/me/transactions` (pagination + filters), `GET /:id` | ✅ |
| `webhooks.py` | `POST /webhooks/paystack` — charge.success, transfer.* | ✅ |
| `withdrawals.py` | stub | 🔴 needs implementation |
| `bank_accounts.py` | **not yet created** | ❌ |
| `billing.py` | stub | 🔴 |
| `admin.py` | stub | 🔴 |

## Phase 7 — Cron Lambdas ✅
- [x] `expire_charges.py` — bulk deactivate codes past `expires_at`
- [x] `reconcile_paystack.py` — verify `pending` txns > 10 min old
- [x] `build_settlements.py` — group settled txns into payout rows per merchant

---

## What's Next — Priority Order

### 1. 🔴 Bank Accounts route (needed before withdrawals)
**File:** `app/api/routes/bank_accounts.py`

Endpoints:
- `POST /merchants/me/bank-accounts` — validate via `POST /bank/resolve`, create Paystack recipient, store masked account
- `GET /merchants/me/bank-accounts` — list merchant's accounts
- `PATCH /merchants/me/bank-accounts/:id/set-default` — flip default
- `DELETE /merchants/me/bank-accounts/:id` — block if only/default account

Migration `009_merchant_bank_accounts.sql` must be run first.

### 2. 🔴 Withdrawals route (depends on bank accounts)
**File:** `app/api/routes/withdrawals.py`

Endpoints:
- `GET /merchants/me/balance` — sum of `net_cents` where `settlement_status=settled` and no `payout_id`, minus pending withdrawals
- `GET /merchants/me/withdrawals` — list with status
- `POST /merchants/me/withdrawals` — create withdrawal → `POST /transfer` (prod only)
- `DELETE /merchants/me/withdrawals/:id` — cancel if still `pending`

Note: `POST /transfer` is blocked on Paystack test/starter accounts. Build the route, test the DB logic, but Paystack call will only work on prod account.

### 3. 🔴 Settings page backend (already live — just needs frontend wiring)
`GET/PATCH /merchants/me` already works. Frontend settings page still on mockApi.

### 4. 🔴 Admin routes
**File:** `app/api/routes/admin.py`

Needs: merchant list, transaction list, settlement management, pricing version management, manual reconcile trigger.

### 5. 🔴 Charge authorization (returning customers)
`POST /transaction/charge_authorization` — skip card entry for customers who've paid before.
Requires storing `authorization_code` per customer email (already have the column).

---

## Bugs Fixed (session log)

| Bug | Fix |
|---|---|
| `.single()` on Supabase throws if row exists | Replaced all `.single()` with `.execute()` + index `[0]` |
| Boolean metadata causes Paystack 500 | Convert to strings `"true"`/`"false"` |
| `apple_pay`/`google_pay` channels cause Paystack 500 on ZAR test | Use `["card"]` only |
| Global exception handler swallowing HTTPException | Added isinstance check in handler |
| Webhook `.single()` on payment_codes throws, swallows charge.success | Fixed + wrapped handlers in try/except |
| STP000021 stuck pending (webhook fired before fix deployed) | Manually patched via Supabase REST API |
| `transactions` endpoint returning `count` not `total` | Fixed — now returns `total` from `count="exact"` |

---

## SSM Parameters (all stored ✅)
```
/scan2pay/dev/SUPABASE_URL
/scan2pay/dev/SUPABASE_ANON_KEY
/scan2pay/dev/SUPABASE_SERVICE_ROLE_KEY
/scan2pay/dev/JWT_SECRET
/scan2pay/dev/WINSMS_API_KEY
/scan2pay/dev/PAYSTACK_SECRET_KEY        → sk_test_5007f89004bd371737871acffe64a98fd2ec3a36
/scan2pay/dev/PAYSTACK_PUBLIC_KEY        → pk_test_23c73dd403061843824f61e3cb4cd96bd5220110
/scan2pay/dev/PAYSTACK_WEBHOOK_SECRET    → same value as PAYSTACK_SECRET_KEY ✅
```

## Test Credentials
- Phone: `+27820000099` · Password: `Test1234!`
- `user_id=usr_005` · `merchant_id=mch_004`
- Primary payment code: `QR-890E282B`
- Test card (success): `4084 0840 8408 4081` · any future expiry · CVV `408`
