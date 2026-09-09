# Scan2Pay — Session Notes

---

## What's done (do not rebuild)

### Merchant — all complete ✅
- `/dashboard`, `/charge`, `/my-code`, `/catalog`, `/transactions`, `/settings`, `/withdrawals`, `/reports`, `/pay/[reference]`
- `/settings` — KYC document upload section (id_document, proof_of_bank, selfie), status badges, rejection reason shown

### Admin console — all complete ✅

**Nav order (money first):**
- Admin: Overview → Revenue → Transactions → Withdrawals → Settlements → People → Pricing → Providers → Audit log → KYC queue → Home page → Support stats
- Support: Overview → People → Transactions → KYC queue → Home page → My stats

**Pages:**
- `/admin/dashboard` — revenue KPIs, merchant growth chart, fees chart, per-merchant revenue table
- `/admin/revenue` — monthly revenue bar (12mo), daily fees + volume area (30d), client growth bar (12mo), txn success vs failed line (12mo)
- `/admin/transactions` — merchant filter, status filter, 10/25/50 page size, consistent pagination
- `/admin/withdrawals` — merchant filter, all statuses (default: all), 10/25/50 page size, pagination
- `/admin/settlements` — pending list + run button
- `/admin/people` — tabbed: Businesses + Users. Both have search, filter pills, server-side pagination (10/25/50)
- `/admin/pricing` — wired to real API
- `/admin/providers` — Paystack balance, success rate, method mix
- `/admin/audit` — webhook_events log
- `/admin/kyc` — KYC review queue, approve/reject with reason modal, Glacier restore notice, status filter
- `/admin/cms` — 4 image slots, local preview before upload, full-screen preview modal, confirm/cancel flow
- `/admin/support-stats` — all agents' commission breakdown, period selector (admin only)
- `/admin/my-stats` — QR code referral card (canvas render, download PNG, share/copy), progress bar, recent signups table

### Role-based access ✅
- Support can access: merchants, users, transactions, KYC, CMS, my-stats (all read endpoints use `require_staff`)
- Support cannot access: withdrawals approve/reject, settlements run, pricing, providers, audit, support-stats
- Financial write endpoints still `require_admin`

### Backend — all deployed ✅
- Auth, merchants, products, payment codes, charges, transactions, webhooks, billing
- `GET /merchants/me/balance`, `PATCH /merchants/me/payout-account`, `GET|POST|DELETE /merchants/me/withdrawals`
- `GET /billing/banks`
- `GET /admin/merchants` + `PATCH /admin/merchants/{id}` (require_staff read, require_admin write)
- `GET /admin/users` + `PATCH /admin/users/{id}`
- `GET /admin/transactions` — paginated, filters: status/method/merchant_id/since
- `GET /admin/balance` — Paystack ZAR balance
- `GET /admin/audit` — webhook_events log
- `GET /admin/settlements/pending` + `POST /admin/settlements/run`
- `GET /admin/withdrawals` — paginated, merchant_id filter, status filter
- `PATCH /admin/withdrawals/{id}/status` — approve/reject
- `GET /admin/pricing` + `POST /admin/pricing` + `GET /admin/plans`
- `GET /merchants/me/documents` + `POST /merchants/me/documents/upload-url` + `POST /merchants/me/documents`
- `GET /admin/kyc` + `GET /admin/kyc/{id}/file` + `PATCH /admin/kyc/{id}`
- `GET /cms/homepage` (public) + `POST /admin/cms/upload-url` + `POST /admin/cms/confirm` + `GET /admin/cms`
- `GET /support/me` + `GET /support/my-stats` + `GET /admin/support-stats`

### Migrations run ✅
- `001` through `015` — all applied
- 015: `referred_by` on merchants, `merchant_documents`, `cms_assets`, `support_commissions`

### S3 bucket ✅
- `scan2pay-assets-dev-542727784619`
- Lifecycle: KYC → GLACIER_IR 90d → GLACIER 365d → delete 730d; CMS → GLACIER_IR 90d
- CORS: GET, PUT, HEAD

---

## Pending / not built yet

### 1. Referral code on signup flow
- Backend: `POST /auth/register` needs optional `referral_code` param → store as `referred_by` on merchant
- Frontend: optional referral code field on signup/register page

### 2. Settlement fee deduction fix
- `settlement_service.py` references `merchant["plan"]` — should be `merchant["plan_id"]`
- One-line fix, then redeploy

### 3. KYC notifications
- No SMS sent when docs approved/rejected
- Add WinSMS call in `PATCH /admin/kyc/{id}` on status change

### 4. Merchant plan upgrade flow
- Currently "contact support" — no self-serve
- Future: merchant requests upgrade, support/admin approves

### 5. CMS → marketing site
- `GET /cms/homepage` is live, nothing consumes it yet
- scan2pay.site needs to call this endpoint

---

## Quick reference

```bash
API=https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod
ASSETS_BUCKET=scan2pay-assets-dev-542727784619

VENDOR_TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" -d '{"identifier":"0821000001","password":"Vendor1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
ADMIN_TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" -d '{"identifier":"0616583827","password":"Admin1234"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
SUPPORT_TOKEN=$(curl -s -X POST $API/auth/login -H "Content-Type: application/json" -d '{"identifier":"0600000001","password":"Support1234!"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

bash scripts/deploy.sh
```

## Test credentials
| Role    | Phone      | Password     | ID                |
|---------|------------|--------------|-------------------|
| Vendor  | 0821000001 | Vendor1234!  | usr_001 / mch_001 |
| Tip     | 0660404333 | 123456       | usr_004 / mch_003 |
| Admin   | 0616583827 | Admin1234    | usr_admin         |
| Support | 0600000001 | Support1234! | usr_support       |

OTP bypass: `0000`

## S3 key structure
```
kyc/{merchant_id}/{doc_type}/{doc_id}/{filename}
cms/homepage/{slot}/{cms_id}/{filename}
```

## Commission logic
- referral_code = support user_id
- Merchants with referral_code → referred_by = support user_id (assigned)
- Merchants without → unassigned pool ÷ active support agents
- Monthly: total = assigned + pool_share + rollover_in
- bonus_units = floor(total / 1000), rollover_out = total % 1000
