# Next Session — Admin Console

> Pick up from: Phase 1 (merchant) is 100% complete. Moving to Phase 2 (admin).

---

## What's done (do not rebuild)

### Merchant — all complete ✅
- `/dashboard`, `/charge`, `/my-code`, `/catalog`, `/transactions`, `/settings`, `/withdrawals`, `/reports`, `/pay/[reference]`
- All wired to real API. No mockApi remaining on merchant pages.

### Backend — all deployed ✅
- Auth, merchants, products, payment codes, charges, transactions, webhooks
- `GET /merchants/me/balance` — available / clearing / in-flight / withdrawn
- `PATCH /merchants/me/payout-account` — KYC (prod) + Paystack recipient + SA ID / Passport `document_type`
- `GET|POST|DELETE /merchants/me/withdrawals`
- `GET /billing/banks` — 33 SA banks proxy
- `GET /admin/settlements/pending` + `POST /admin/settlements/run`
- `GET|PATCH /admin/withdrawals` — approve (SIMULATED in dev) / reject
- Settlement cron — EventBridge daily at **18:00 UTC (20:00 SAST)**, T+2 clearing window
- Transactions `settlement_status` filter

### Migration run ✅
- `013_payout_kyc_withdrawals.sql` — `payout_account_name`, `kyc_status`, `kyc_verified_at` on merchants; `transfer_code`, `failure_reason`, expanded status on withdrawals

---

## Session Goals — Admin Console

### 1. Backend endpoints needed

| Endpoint | Notes |
|----------|-------|
| `GET /admin/merchants` | list all merchants with plan, status, joined_at |
| `PATCH /admin/merchants/{id}` | suspend/activate + plan change |
| `GET /admin/users` | list all users with role, status |
| `PATCH /admin/users/{id}` | suspend/activate |
| `GET /admin/transactions` | platform-wide, all merchants, same filters as merchant version |
| `GET /admin/balance` | calls Paystack `GET /balance` → returns ZAR cents |
| `GET /admin/audit` | list `webhook_events` table, newest first, paginated |

### 2. Frontend pages to wire (all currently mockApi)

| Page | What to build |
|------|---------------|
| `/admin/dashboard` | Real stats (total merchants, total txns, platform revenue) + Paystack balance card |
| `/admin/merchants` | Real list, suspend button, plan badge |
| `/admin/users` | Real list, suspend button, role badge |
| `/admin/transactions` | Platform-wide paginated list, same filter bar as merchant transactions |
| `/admin/withdrawals` | Real approve/reject queue — already has backend ✅ just needs frontend wired |
| `/admin/settlements` | Pending list + run button — partially wired ✅ |
| `/admin/audit` | webhook_events log — event type, reference, timestamp |
| `/admin/providers` | Paystack balance card |

### 3. Order to build
1. Backend: `GET /admin/merchants`, `PATCH /admin/merchants/{id}`, `GET /admin/users`, `PATCH /admin/users/{id}`, `GET /admin/transactions`, `GET /admin/balance`, `GET /admin/audit`
2. Deploy
3. Frontend: wire each admin page in order above

---

## Quick reference

```bash
API=https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod
PAYSTACK=sk_test_5007f89004bd371737871acffe64a98fd2ec3a36

# Fresh vendor token
VENDOR_TOKEN=$(curl -s -X POST $API/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"0821000001","password":"Vendor1234!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Fresh admin token
ADMIN_TOKEN=$(curl -s -X POST $API/auth/login \
  -H "Content-Type: application/json" \
  -d '{"identifier":"0616583827","password":"Admin1234"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Deploy
bash scripts/deploy.sh
```

## Test credentials
| Role | Phone | Password | ID |
|------|-------|----------|----|
| Vendor | 0821000001 | Vendor1234! | usr_001 / mch_001 |
| Tip | 0660404333 | 123456 | usr_004 / mch_003 |
| Admin | 0616583827 | Admin1234 | usr_admin |
| Support | 0600000001 | Support1234! | usr_support |

OTP bypass: `0000`

## Test bank account (already saved on mch_001)
| Field | Value |
|-------|-------|
| Bank | FNB |
| Account | 62845141407 |
| Paystack code | 250655 |
| Recipient code | RCP_ag9fgil66ki40vu |

## Paystack test limitations
| Endpoint | Test mode |
|----------|-----------|
| `POST /transferrecipient` | ✅ works |
| `GET /balance` | ✅ works — returns 59987 cents |
| `GET /bank` (list) | ✅ works — 33 SA banks |
| `GET /bank/resolve` | ⛔ ZAR unsupported |
| `POST /bank/validate` | ⚠️ always returns verified=false |
| `POST /transfer` | ⛔ blocked — `SIMULATE_TRANSFERS=true` in dev |

## Settlement cron
- Runs daily at **18:00 UTC = 20:00 SAST** via EventBridge
- Finds all `status='success'` + `settlement_status='pending'` + `paid_at <= now - 2 days`
- Groups by merchant → creates payout row → flips to `settled`
- Manual trigger: `POST /admin/settlements/run`
- To run for one merchant: `POST /admin/settlements/run?merchant_id=mch_001`
