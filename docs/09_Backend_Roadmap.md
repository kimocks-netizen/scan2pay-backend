# scan2pay-backend — Build Roadmap

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

## Phase 2 — Database
- [ ] `database/migrations/001_enums.sql` — user_type, code_mode, txn_status, etc.
- [ ] `database/migrations/002_plans_pricing.sql` — plans + pricing_versions seed
- [ ] `database/migrations/003_users_merchants.sql`
- [ ] `database/migrations/004_products_codes.sql`
- [ ] `database/migrations/005_transactions_payouts.sql`
- [ ] `database/migrations/006_withdrawals.sql`
- [ ] `database/migrations/007_auth_tables.sql` — refresh_tokens, otp_codes
- [ ] `database/migrations/008_webhooks_audit.sql`
- [ ] Run migrations against Supabase (paste into SQL editor)

---

## Phase 3 — Schemas (Pydantic)
- [ ] `app/schemas/auth.py` — RegisterRequest, LoginRequest, TokenResponse
- [ ] `app/schemas/merchant.py` — MerchantOut, MerchantUpdate
- [ ] `app/schemas/product.py` — ProductOut, ProductCreate, ProductUpdate
- [ ] `app/schemas/payment_code.py` — PaymentCodeOut, PaymentCodeCreate
- [ ] `app/schemas/charge.py` — ChargeCreate, ChargeOut
- [ ] `app/schemas/payment.py` — PaymentInitRequest, PaymentInitResponse, PaymentOut
- [ ] `app/schemas/transaction.py` — TransactionOut, TransactionList
- [ ] `app/schemas/withdrawal.py` — WithdrawalCreate, WithdrawalOut
- [ ] `app/schemas/admin.py` — AdminStats, SettlementRow, PricingVersionCreate

---

## Phase 4 — Repositories (DB layer)
- [ ] `app/db/repositories/users.py`
- [ ] `app/db/repositories/merchants.py`
- [ ] `app/db/repositories/products.py`
- [ ] `app/db/repositories/payment_codes.py`
- [ ] `app/db/repositories/transactions.py`
- [ ] `app/db/repositories/withdrawals.py`
- [ ] `app/db/repositories/pricing.py`
- [ ] `app/db/repositories/audit.py`

---

## Phase 5 — Services
- [x] `app/services/sms_service.py` — WinSMS OTP ✅
- [ ] `app/services/paystack_service.py` — init transaction, verify, transfer, webhook
- [ ] `app/services/settlement_service.py` — balance calc, payout grouping

---

## Phase 6 — Routes (implement each stub)
- [ ] `app/api/routes/health.py` ✅ basic version done
- [ ] `app/api/routes/auth.py` — register, login, refresh, logout, me, OTP
- [ ] `app/api/routes/merchants.py` — GET/PATCH merchant, payout account
- [ ] `app/api/routes/products.py` — CRUD products
- [ ] `app/api/routes/payment_codes.py` — list, create, get, patch, delete
- [ ] `app/api/routes/charges.py` — create charge, list, get, cancel, SSE
- [ ] `app/api/routes/payments.py` — initialise, get status
- [ ] `app/api/routes/webhooks.py` — Paystack webhook (signature verified)
- [ ] `app/api/routes/transactions.py` — list, stats, CSV export, payouts
- [ ] `app/api/routes/withdrawals.py` — balance, list, create, cancel
- [ ] `app/api/routes/billing.py` — plans, pricing
- [ ] `app/api/routes/admin.py` — all admin endpoints

---

## Phase 7 — Cron Lambdas (implement)
- [ ] `app/cron/expire_charges.py` — query `active=true AND expires_at < now()`, bulk update
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

## Phase 9 — Deploy
- [ ] Store all secrets in SSM Parameter Store under `/scan2pay/{env}/`
- [ ] `sam build`
- [ ] `sam deploy --guided` (first time)
- [ ] Point `scan2pay-web` `NEXT_PUBLIC_API_URL` at the API Gateway URL
- [ ] Swap `src/lib/mock-client.ts` → real `api-client.ts` calls

---

## SSM Parameters Required
```
/scan2pay/dev/SUPABASE_URL
/scan2pay/dev/SUPABASE_SERVICE_ROLE_KEY
/scan2pay/dev/JWT_SECRET
/scan2pay/dev/WINSMS_API_KEY
/scan2pay/dev/PAYSTACK_SECRET_KEY
/scan2pay/dev/PAYSTACK_PUBLIC_KEY
/scan2pay/dev/PAYSTACK_WEBHOOK_SECRET
```

## Build Order
1. Supabase keys → copy `.env.example` → `.env` → fill in keys
2. Run DB migrations in Supabase SQL editor
3. Implement schemas → repositories → services → routes (in that order)
4. Test locally with `uvicorn app.main:app --reload`
5. Implement + test cron handlers
6. `sam build && sam deploy`
