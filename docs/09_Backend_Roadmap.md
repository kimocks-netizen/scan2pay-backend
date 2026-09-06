# scan2pay-backend — Build Roadmap

---

## ⚠️ Working Rules

1. **Third-party APIs** — if unsure about the exact payload, auth format, or endpoint behaviour of any external API (WinSMS, Paystack, WhatsApp, etc.), **ask the user first**. Do not guess. The WinSMS incident (`messages[].messageText` instead of `message` + `recipients[]`) is a direct example of what happens when this rule is broken.
2. **Unclear requirements** — if the scope of a feature is ambiguous, **ask before writing any code**. Do not assume what endpoints, fields, or behaviours are needed.
3. **Scope** — only build what was explicitly asked for in the current session. No extra endpoints or logic that were not requested.
4. **Existing patterns** — before implementing anything new, check how it is already done in the codebase (e.g. check PredictIQ for WinSMS format, check existing routes for DB query patterns).

---

## Stack
Python 3.13 · FastAPI · Mangum · Supabase (Postgres) · Paystack · WinSMS · AWS SAM · S3

## Lambda Architecture
| Lambda | Trigger | Purpose |
|---|---|---|
| `Scan2PayApiFunction` | API Gateway `/{proxy+}` | Entire FastAPI app via Mangum |
| `ExpireChargesFunction` | EventBridge every 1 min | Set `active=false` on codes past `expires_at` |
| `ReconcilePaystackFunction` | EventBridge every 15 min | Verify `pending` payments older than 10 min |
| `BuildSettlementsFunction` | EventBridge daily 02:00 SAST | Group settled transactions into payout rows |

---

## Phase 1 — Foundation ✅ Scaffolded
- [x] Project structure created
- [x] `requirements.txt`
- [x] `app/core/config.py` — all settings (Supabase, JWT, WinSMS, Paystack, AWS)
- [x] `app/core/security.py` — JWT, bcrypt, Paystack HMAC
- [x] `app/core/deps.py` — FastAPI auth dependency
- [x] `app/db/connection.py` — Supabase client singleton
- [x] `app/main.py` — FastAPI app + all routers registered + Mangum handler
- [x] `app/services/sms_service.py` — WinSMS OTP (same keys as PredictIQ)
- [x] `app/cron/expire_charges.py` — stub
- [x] `app/cron/reconcile_paystack.py` — stub
- [x] `app/cron/build_settlements.py` — stub
- [x] `template.yaml` — SAM: 1 API Lambda + 3 cron Lambdas + S3 bucket
- [x] `.env.example`

---

## Phase 2 — Database ✅ Complete
- [x] `database/migrations/001_enums.sql` — user_type, user_role, user_status, code_mode, txn_status, payment_method, settlement_state, payout_status, merchant_status, pricing_status, fee_bearer
- [x] `database/migrations/002_plans_pricing.sql` — plans + pricing_versions + seed data (3 plans, 3 initial pricing rows)
- [x] `database/migrations/003_users_merchants.sql` — users (role, status) + merchants
- [x] `database/migrations/004_products_codes.sql` — products + payment_codes (constraints + indexes)
- [x] `database/migrations/005_transactions_payouts.sql` — payouts + transactions (pricing jsonb snapshot, paid_at) — fixed constraint name clash with 004
- [x] `database/migrations/006_withdrawals.sql`
- [x] `database/migrations/007_auth_tables.sql` — refresh_tokens, otp_codes
- [x] `database/migrations/008_webhooks_audit.sql` — webhook_events, scan_events, audit_log
- [ ] `database/migrations/009_merchant_bank_accounts.sql` — merchant_bank_accounts (id, merchant_id, recipient_code, bank_name, account_number masked, account_name, is_default, created_at) ← **needed for withdrawals**
- [x] All migrations run against Supabase ✅
- [x] `database/migrations/seed.sql` — plans already in 002; test user, merchant, products, payment codes, transactions seeded ✅

---

## Phase 3 — Schemas (Pydantic)
- [x] `app/schemas/auth.py` — RegisterRequest, LoginRequest, OtpRequestBody, OtpVerifyRequest, PublicUser, AuthResponse, normalise_phone() ✅
- [ ] `app/schemas/merchant.py` — inline in route (MerchantUpdate)
- [ ] `app/schemas/product.py` — inline in route (ProductCreate, ProductUpdate)
- [ ] `app/schemas/payment_code.py` — inline in route (CodeCreate, CodeUpdate)
- [ ] `app/schemas/charge.py` — inline in route (ChargeCreate)
- [ ] `app/schemas/payment.py` — PaymentInitRequest, PaymentInitResponse, PaymentOut
- [ ] `app/schemas/transaction.py` — TransactionOut, TransactionList
- [ ] `app/schemas/bank_account.py` — BankAccountCreate, BankAccountOut
- [ ] `app/schemas/withdrawal.py` — WithdrawalCreate, WithdrawalOut
- [ ] `app/schemas/admin.py` — AdminStats, SettlementRow, PricingVersionCreate

---

## Phase 4 — Repositories (DB layer)
- [ ] Skipped — queries are inline in routes (supabase-py is thin enough; repos added if complexity grows)

---

## Phase 5 — Services
- [x] `app/services/sms_service.py` — WinSMS OTP, unique clientMessageId ✅
- [x] `app/services/paystack_service.py` — init transaction, verify, list transactions, create recipient, initiate/finalize/fetch transfer ✅
- [ ] `app/services/settlement_service.py` — balance calc, payout grouping

---

## Phase 6 — Routes (implement each stub)
- [x] `app/api/routes/health.py` — GET /health → `{status, db}` ✅
- [x] `app/api/routes/auth.py` — POST /register, /login, /refresh, /logout, GET /me, POST /otp/request, /otp/verify ✅
- [x] `app/api/routes/merchants.py` — GET /merchants/me, PATCH /merchants/me, GET /merchants/{id} ✅
- [x] `app/api/routes/products.py` — GET/POST /merchants/me/products, PATCH/DELETE /merchants/me/products/{id} ✅
- [x] `app/api/routes/payment_codes.py` — GET/POST /merchants/me/payment-codes, PATCH/DELETE /{id}, GET /pay/{reference} ✅
- [x] `app/api/routes/charges.py` — POST /charges (single-use 5-min QR), GET /charges/{reference} ✅
- [x] `app/api/routes/transactions.py` — GET /merchants/me/transactions (filter + pagination), GET /{id} ✅
- [x] `app/api/routes/payments.py` — POST /payments/initialise, GET /payments/{id} ✅
- [x] `app/api/routes/webhooks.py` — charge.success, transfer.success/failed/reversed ✅
- [ ] `app/api/routes/bank_accounts.py` — POST /merchants/me/bank-accounts, GET /merchants/me/bank-accounts, DELETE /{id}, PATCH /{id}/set-default
- [ ] `app/api/routes/withdrawals.py` — balance, list, create, cancel
- [ ] `app/api/routes/billing.py` — plans, pricing
- [ ] `app/api/routes/admin.py` — all admin endpoints

---

## Phase 7 — Cron Lambdas (implement)
- [x] `app/cron/expire_charges.py` — bulk deactivate codes past `expires_at` ✅
- [x] `app/cron/reconcile_paystack.py` — verify `pending` txns > 10 min old via Paystack API ✅
- [x] `app/cron/build_settlements.py` — group last week's settled txns into payout rows per merchant ✅

---

## Phase 8 — Tests
- [ ] `tests/unit/test_security.py`
- [ ] `tests/unit/test_fee_calc.py`
- [ ] `tests/integration/test_auth.py`
- [ ] `tests/integration/test_payments.py`
- [ ] `tests/integration/test_webhooks.py`

---

## Phase 9 — Deploy ✅ Live
- [x] All secrets stored in SSM Parameter Store under `/scan2pay/dev/` (8 params) ✅
- [x] `sam build` ✅
- [x] `sam deploy` — stack `scan2pay-dev` live in `af-south-1` on account `542727784619` ✅
- [x] API endpoint: `https://xuwz8h1y4f.execute-api.af-south-1.amazonaws.com/Prod` ✅
- [x] Health check: `GET /health` → `{"status":"ok","db":"ok"}` ✅
- [ ] Point `scan2pay-web` `NEXT_PUBLIC_API_URL` at the API Gateway URL
- [ ] Swap `src/lib/mock-client.ts` → real `api-client.ts` calls

---

## SSM Parameters (all stored ✅)
```
/scan2pay/dev/SUPABASE_URL           → String
/scan2pay/dev/SUPABASE_ANON_KEY      → String
/scan2pay/dev/SUPABASE_SERVICE_ROLE_KEY → String
/scan2pay/dev/JWT_SECRET             → String
/scan2pay/dev/WINSMS_API_KEY         → String  (80EE00F5-...)
/scan2pay/dev/PAYSTACK_SECRET_KEY    → String  (sk_test_5007...)
/scan2pay/dev/PAYSTACK_PUBLIC_KEY    → String  (pk_test_23c7...)
/scan2pay/dev/PAYSTACK_WEBHOOK_SECRET → String (placeholder — update when Paystack dashboard provides it)
```

## Paystack Status
- Keys: `sk_test_5007f89...` / `pk_test_23c73dd...` ✅ active
- `POST /transaction/initialize` ✅ tested — returns `authorization_url`, `access_code`, `reference`
- `GET /transaction/verify/:ref` ✅ tested — mixed casing: `paid_at` (snake) AND `paidAt` (camel) both present, `authorization: {}` when not paid
- `GET /transaction?use_cursor=true&perPage=N` ✅ tested — `meta.next` is `null` when no more pages
- `POST /transferrecipient` ✅ tested — `type` echoed as `"basa"` (not `"nuban"`), `details.account_name` is `null` in test mode
- `POST /transfer` ⛔ blocked — `transfer_unavailable` error on starter business. Implement against prod account
- `GET /transfer/:code` ✅ error shape confirmed — `{status: false, message, type: "validation_error", code: "invalid_params"}`
- Webhook secret: ✅ confirmed — `PAYSTACK_SECRET_KEY` IS the HMAC key, no separate secret. Update SSM `/scan2pay/dev/PAYSTACK_WEBHOOK_SECRET` to match `PAYSTACK_SECRET_KEY`

## What's Next
1. Wire `scan2pay-web` charge page — call `POST /payments/initialise`, invoke `popup.resumeTransaction(access_code)`
2. `expire_charges.py` cron — already implemented ✅
3. Withdrawals, billing, admin routes
4. **Before go-live — payment method configuration:**
   - Apple Pay: register `scan2pay.site` via `POST /apple-pay/domain`
   - Google Pay: enabled automatically once Paystack account is verified
   - Capitec Pay: confirm exact channel name with Paystack support before adding to `channels` array

---

## Tomorrow's Session — Paystack Integration Plan

### Payment Flow
1. Customer scans QR → app calls `POST /payments/initialise`
2. Backend calls Paystack `POST /transaction/initialize` → returns `authorization_url`
3. Customer is redirected to Paystack hosted page (handles **card, Apple Pay, Google Pay** automatically — no separate APIs needed)
4. Paystack fires `charge.success` webhook → backend verifies HMAC-SHA512, marks transaction `success`
5. Merchant gets notified (SMS / push)

### Paystack APIs Needed
| Endpoint | Purpose | Confidence |
|---|---|---|
| `POST /transaction/initialize` | Create payment link | ✅ tested |
| `GET /transaction/verify/:reference` | Verify after callback | ✅ tested — full shape confirmed, mixed `paid_at`/`paidAt` casing |
| `GET /transaction?use_cursor=true` | List transactions | ✅ tested — cursor pagination confirmed, `meta.next=null` when end |
| `POST /transferrecipient` | Create payout recipient | ✅ tested — `type` returns `"basa"` not `"nuban"`, `account_name` is `null` in test |
| `POST /transfer` | Initiate payout to merchant | ⛔ blocked — starter business account cannot initiate transfers. Shape documented from Paystack docs, implement and test in prod |
| `GET /transfer/:code` | Check transfer status | ✅ error shape confirmed — `{status: false, message, type, code}` |
| Webhook `charge.success` | Payment confirmed | ✅ shape confirmed in `06_Payments_Paystack.md` |
| Webhook `transfer.success` | Payout confirmed | ✅ shape confirmed in `06_Payments_Paystack.md` |
| Webhook `transfer.failed` | Payout failed | ✅ shape confirmed in `06_Payments_Paystack.md` |

### Apple Pay & Google Pay
- **No separate integration needed** — Paystack's hosted checkout page surfaces Apple Pay / Google Pay automatically based on customer's device/browser
- The `authorization_url` from `POST /transaction/initialize` is all we need
- Decision needed: **hosted page** (redirect) vs **Paystack Inline** (custom page, more control) — confirm before building

### Merchant Bank Accounts & Withdrawal Flow
1. Merchant adds bank account → `POST /merchants/me/bank-accounts` (bank_name + account_number)
2. Backend calls Paystack `POST /transferrecipient` → validates account, returns `recipient_code`
3. Store in `merchant_bank_accounts` table — first account auto-set as `is_default`
4. Merchant can add more accounts and switch default via `PATCH /{id}/set-default`
5. On withdrawal request → use `is_default` account's `recipient_code` with `POST /transfer`

**Rules:**
- Multiple accounts allowed, one `is_default = true` at a time
- Switching default flips previous default to `false`
- Cannot delete the default account if it's the only one — must set another as default first
- `account_number` stored masked (last 4 digits only) after Paystack resolves it

### All Blockers Resolved ✅
- Webhook secret = `PAYSTACK_SECRET_KEY` (no separate secret)
- `callback_url` = `https://scan2pay.site/charge?paid=true`
- Transfer OTP = enabled by default, `DEV_TRANSFER_OTP=False` skips finalize in dev
- Payment method = Paystack Inline JS (`popup.resumeTransaction(access_code)`)
- All API shapes confirmed and documented in `06_Payments_Paystack.md`
- `POST /transfer` blocked on starter account — implement and test against prod account only
