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
| `BuildSettlementsFunction` | EventBridge daily **18:00 UTC (20:00 SAST)** | Settle eligible transactions (T+2 clearing) |

---

## Phase 1 — Merchant ✅ COMPLETE

### Routes (all live)
| Route file | Endpoints | Status |
|---|---|---|
| `health.py` | `GET /health` | ✅ |
| `auth.py` | register, login, refresh, logout, me, otp | ✅ |
| `merchants.py` | `GET/PATCH /merchants/me`, `PATCH /me/payout-account`, `GET /me/balance`, `GET /:id` | ✅ |
| `products.py` | CRUD `/merchants/me/products`, regenerate-qr | ✅ |
| `payment_codes.py` | CRUD `/merchants/me/payment-codes` | ✅ |
| `charges.py` | `POST /charges`, charge session flow | ✅ |
| `payments.py` | `POST /payments/initialise`, `GET /payments/:id` | ✅ |
| `transactions.py` | paginated + filters (status/method/type/settlement) | ✅ |
| `withdrawals.py` | `GET/POST/DELETE /merchants/me/withdrawals` | ✅ |
| `billing.py` | `GET /billing/banks` — 33 SA banks proxy | ✅ |
| `webhooks.py` | charge.success, transfer.success/failed/reversed | ✅ |
| `admin.py` | settlements pending/run, withdrawals approve/reject | ✅ partial |

### Migrations run
- `001` through `012` ✅
- `013_payout_kyc_withdrawals.sql` ✅ — payout_account_name, kyc_status, transfer_code, failure_reason, expanded withdrawal status

### Cron Lambdas
- `expire_charges.py` ✅
- `reconcile_paystack.py` ✅
- `build_settlements.py` ✅ — simplified, uses `settlement_service.run_settlements()`, T+2 clearing

---

## Phase 2 — Admin Console 🔴 NEXT

### Backend needed
| Endpoint | Notes |
|---|---|
| `GET /admin/merchants` | list all, plan + status |
| `PATCH /admin/merchants/{id}` | suspend/activate + plan change |
| `GET /admin/users` | list all users with role |
| `PATCH /admin/users/{id}` | suspend/activate |
| `GET /admin/transactions` | platform-wide, all merchants, same filters |
| `GET /admin/balance` | Paystack `GET /balance` → ZAR cents |
| `GET /admin/audit` | `webhook_events` table, paginated |

### Frontend pages to wire
| Page | Status |
|------|--------|
| `/admin/dashboard` | mockApi → real stats + Paystack balance card |
| `/admin/merchants` | mockApi → real list, suspend, plan |
| `/admin/users` | mockApi → real list, suspend |
| `/admin/transactions` | mockApi → platform-wide list |
| `/admin/withdrawals` | mockApi → approve/reject queue (backend ✅) |
| `/admin/settlements` | partially wired ✅ |
| `/admin/audit` | mockApi → webhook_events log |
| `/admin/providers` | mockApi → Paystack balance |

---

## Phase 3 — Support role 🔲
- Read-only: transactions, merchants, users
- No financial actions
- Route guard already in `MERCHANT_ROUTES_BY_TYPE`

## Phase 4 — Production readiness 🔲
- Paystack live keys
- `POST /apple-pay/domain` — register scan2pay.site
- Verify webhook URL in Paystack dashboard
- Verify `build_settlements` cron running in prod (CloudWatch logs)
- Custom domain for API Gateway

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
| Duplicate `GET /pay/{reference}` route in payment_codes.py | Removed — charges.py version has charge session logic |
| `/merchants/me` 404 — wildcard `/{merchant_id}` catching `/me` | Fixed route order — `/me` routes registered before wildcard |
| `document_type` hardcoded as `identityNumber` in KYC | Now driven by frontend toggle (SA ID / Passport) |

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
