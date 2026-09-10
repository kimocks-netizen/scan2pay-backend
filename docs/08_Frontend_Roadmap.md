# scan2pay-web — Frontend Roadmap

> Single source of truth for frontend state, routes, and pending work.
> Last updated: September 2026

## Stack
Next.js 15 App Router · TypeScript · Tailwind v4 · shadcn/ui · TanStack Query v5 · Zustand · Recharts · qrcode · @paystack/inline-js

## Live API
`https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod`
AWS account: `542727784619` · profile: `predictiq` · region: `af-south-1`
Deploy: `bash scripts/deploy.sh` from `scan2pay-backend/`

## Environment Variables
```env
NEXT_PUBLIC_API_URL=https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod
NEXT_PUBLIC_PAY_BASE_URL=https://scan2pay.site/pay
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_test_23c73dd403061843824f61e3cb4cd96bd5220110
```

---

## ✅ Phase 1 — Merchant (COMPLETE)

| Route | Description |
|---|---|
| `/dashboard` | Stats, 30-day chart, top codes/tips, recent payments. Tip vs vendor layout |
| `/charge` | Charge session, QR countdown, live per-row expiry badge |
| `/my-code` | Primary QR poster, print/download/share buttons |
| `/catalog` | Product CRUD, QR poster modal/drawer, regenerate QR |
| `/transactions` | Paginated, status/method/type/settlement filters |
| `/settings` | Business profile, payout account (modal + mobile drawer), plan card, KYC document upload (id_document, proof_of_bank, selfie with status badges + view button). Approved docs cannot be replaced. |
| `/withdrawals` | Balance cards, request form, history, cancel with confirmation modal |
| `/reports` | Period selector, gross/fees/net cards, charts, CSV export |
| `/pay/[reference]` | Public pay page, all three modes, charge session overlay |

---

## ✅ Phase 2 — Admin Console (COMPLETE)

### Navigation (role-based)
- **Admin:** Overview → Revenue → Transactions → Payouts → People → Pricing → Providers → Audit log → KYC queue → CMS → Support stats
- **Support:** Overview → People → Transactions → KYC queue → CMS → My stats

### Mobile nav
Both admin and support use the same bottom-bar + More sheet pattern as the merchant shell (first 4 items in bar, rest in sheet with logout).

### Pages

| Route | Description |
|---|---|
| `/admin/dashboard` | Revenue KPIs, Paystack balance, merchant KPIs, fees chart, merchant growth chart, per-merchant revenue table. Mobile: card view for recent transactions |
| `/admin/revenue` | Monthly revenue bar (12mo), daily fees + volume area (30d), client growth bar (12mo), txn success vs failed line (12mo). Colour-coded stat chips per chart |
| `/admin/transactions` | Platform-wide, merchant filter dropdown, status filter, 10/25/50 page size, pagination |
| `/admin/withdrawals` | Combined Payouts page — Withdrawals + Settlements tabs. Merchant filter, status filter, 10/25/50 page size, approve/reject actions |
| `/admin/settlements` | Redirects to `/admin/withdrawals` |
| `/admin/people` | Tabbed Businesses + Users. Search, filter pills, server-side pagination (10/25/50). Users show user_type pill |
| `/admin/pricing` | Pricing versions history, publish new version form |
| `/admin/providers` | Paystack balance, success rate, method mix table, recent failures |
| `/admin/audit` | webhook_events log, status filter |
| `/admin/kyc` | Grouped by merchant (one card per merchant, docs as rows inside). Status filter, view doc (presigned GET + Glacier restore notice), approve, reject with reason modal |
| `/admin/cms` | 4 image slots (hero, feature_1, feature_2, banner). Local preview before upload, confirm/cancel, full-screen preview modal, alt text input |
| `/admin/support-stats` | All agents' commission breakdown, period selector (admin only) |
| `/admin/my-stats` | QR encodes full signup URL with `?ref=<code>`. Full-width QR card with logo + URL printed below. Full-width buttons on mobile. Progress bar, rollover display, recent signups table (support only) |

### Key component notes
- `AdminShell` — desktop sidebar + mobile bottom nav (same pattern as `AppShell`)
- `ChartPanel` — accepts `stat` prop with `color` for colour-coded top-right values
- `PaginationBar` — inline in withdrawals page, reusable pattern

---

## ✅ Home / Marketing Pages

| Route | Description |
|---|---|
| `/` | Placeholder with header + hero (CMS hero slot as background overlay if available) |
| `/home` | Full marketing page. Fetches `GET /cms/homepage` server-side (`force-dynamic`, `no-store`). CMS slots: hero → hero image, feature_1/2/banner → story cards. Falls back to static assets |

CMS images use `force-dynamic` + `cache: "no-store"` so new uploads appear immediately.

---

## ✅ Phase 3 — Referral Signup Flow (COMPLETE)

- [x] Backend: `POST /auth/register` accepts optional `referral_code` → stores `referred_by` on merchant (validated against existing users)
- [x] Frontend: `?ref=<support_user_id>` pre-read from URL on register page, passed silently through mutation
- [x] QR deep-link encodes full URL: `/login?mode=register&ref=<code>`

---

## 🔲 Phase 4 — Notifications & Automation

- [ ] WinSMS on KYC approval/rejection (`PATCH /admin/kyc/{id}`)
- [ ] WinSMS on withdrawal approved
- [ ] Fix `settlement_service.py` — uses `merchant["plan"]`, should be `merchant["plan_id"]`
- [ ] Merchant plan upgrade flow (self-serve request → support/admin approves)
- [ ] Wire `GET /cms/homepage` to scan2pay.site marketing site

---

## 🔲 Phase 5 — Production Readiness

- [ ] Paystack live keys
- [ ] `POST /apple-pay/domain` — register `scan2pay.site`
- [ ] Custom domain for API Gateway
- [ ] Error monitoring (Sentry or CloudWatch alarms)
- [ ] Rate limiting (API Gateway usage plans)
- [ ] Paystack webhook URL confirmed in Paystack dashboard
- [ ] Verify settlement cron running in prod (CloudWatch logs)
- [ ] KYC bank validation in prod (test mode always returns `verified=false`)

---

## 🔲 Future — Multiple Bank Accounts

- [ ] Up to 2 bank accounts per merchant with a default
- [ ] Settings page: list accounts, add/remove, set default
- [ ] Withdrawal page: account selector when requesting payout
- [ ] See `09_Backend_Roadmap.md` for full API spec

---

## API Wiring Status

### Auth ✅
`POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` · `POST /auth/otp/request` · `POST /auth/otp/verify`

### Merchant ✅
`GET/PATCH /merchants/me` · `PATCH /merchants/me/payout-account` · `GET /merchants/me/balance`

### KYC ✅
`POST /merchants/me/documents/upload-url` · `POST /merchants/me/documents` · `GET /merchants/me/documents` · `GET /merchants/me/documents/{doc_id}/file`

### Payment Codes ✅
`GET/POST/PATCH/DELETE /merchants/me/payment-codes` · `GET /pay/:reference`

### Charges & Payments ✅
`POST /charges` · `POST /payments/initialise` · `GET /payments/:id` · `POST /pay/:reference/initialise`

### Transactions ✅
`GET /merchants/me/transactions` (paginated, filters)

### Products ✅
`GET/POST/PATCH/DELETE /merchants/me/products`

### Withdrawals ✅
`GET/POST/DELETE /merchants/me/withdrawals` · `GET /billing/banks`

### Admin ✅
All endpoints — see `09_Backend_Roadmap.md` for full list
