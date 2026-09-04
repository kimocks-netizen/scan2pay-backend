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
- [ ] `app/schemas/withdrawal.py` — WithdrawalCreate, WithdrawalOut
- [ ] `app/schemas/admin.py` — AdminStats, SettlementRow, PricingVersionCreate

---

## Phase 4 — Repositories (DB layer)
- [ ] Skipped — queries are inline in routes (supabase-py is thin enough; repos added if complexity grows)

---

## Phase 5 — Services
- [x] `app/services/sms_service.py` — WinSMS OTP, unique clientMessageId ✅
- [ ] `app/services/paystack_service.py` — init transaction, verify, transfer, webhook ← **next**
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
- [ ] `app/api/routes/payments.py` — POST /payments/initialise, GET /payments/{id} ← **next**
- [ ] `app/api/routes/webhooks.py` — Paystack webhook (HMAC-SHA512 verified) ← **next**
- [ ] `app/api/routes/withdrawals.py` — balance, list, create, cancel
- [ ] `app/api/routes/billing.py` — plans, pricing
- [ ] `app/api/routes/admin.py` — all admin endpoints

---

## Phase 7 — Cron Lambdas (implement)
- [ ] `app/cron/expire_charges.py` — query `active=true AND expires_at < now()`, bulk update ← **next after payments**
- [ ] `app/cron/reconcile_paystack.py` — verify `pending` txns > 10 min old via Paystack API
- [ ] `app/cron/build_settlements.py` — group `success + settlement_status=pending` by merchant + cycle

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
- `POST /transaction/initialize` ✅ tested
- `GET /transaction/verify/:ref` ✅ tested
- `POST /transferrecipient` ✅ tested (Absa `632005` resolves correctly)
- Webhook secret: pending — get from Paystack dashboard → Settings → API Keys

## What's Next
1. `app/services/paystack_service.py` — initialize, verify, create recipient
2. `app/api/routes/payments.py` — POST /payments/initialise, GET /payments/{id}
3. `app/api/routes/webhooks.py` — charge.success handler
4. `app/cron/expire_charges.py` — implement
5. Withdrawals, billing, admin routes
