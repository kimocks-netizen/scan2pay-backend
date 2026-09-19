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
NEXT_PUBLIC_PAY_BASE_URL=https://vula-pay.co.za/pay
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_test_23c73dd403061843824f61e3cb4cd96bd5220110
NEXT_PUBLIC_WS_URL=wss://hd4o0s91g8.execute-api.af-south-1.amazonaws.com/Prod
NEXT_PUBLIC_GA_MEASUREMENT_ID=          # Sprint 2 — Google Analytics 4
NEXT_PUBLIC_GADS_CONVERSION_ID=         # Sprint 2 — Google Ads
NEXT_PUBLIC_GADS_CONVERSION_LABEL=      # Sprint 2 — Google Ads
```

---

## ✅ Phase 1 — Merchant (COMPLETE)

| Route | Description |
|---|---|
| `/dashboard` | Stats, 30-day chart, top codes/tips, recent payments. Tip vs vendor layout. `refetchOnWindowFocus` enabled — updates on tab switch after payment |
| `/charge` | Charge session, QR countdown, live per-row expiry badge. WebSocket via `useChargeWebSocket`, polling kept as fallback |
| `/my-code` | Primary QR poster, print/download/share buttons |
| `/catalog` | Product CRUD, QR poster modal/drawer, regenerate QR |
| `/transactions` | Paginated, status/method/type/settlement filters |
| `/settings` | Business profile, payout account (modal + mobile drawer), plan card, KYC document upload (id_document, proof_of_bank, selfie with status badges + view button). Approved docs cannot be replaced. |
| `/withdrawals` | Balance cards, request form, history, cancel with confirmation modal |
| `/reports` | Period selector, gross/fees/net cards, charts, CSV export |
| `/pay/[reference]` | Public pay page, all three modes, charge session overlay. WebSocket via `usePayWebSocket` |

---

## ✅ Phase 2 — Admin Console (COMPLETE)

### Navigation (role-based)
- **Admin:** Overview → Revenue → Transactions → Payouts → People → Pricing → Providers → Audit log → KYC queue → CMS → Support stats
- **Support:** Overview → People → Transactions → KYC queue → CMS → My stats

### Pages

| Route | Description |
|---|---|
| `/admin/dashboard` | Revenue KPIs, Paystack balance, merchant KPIs, fees chart, merchant growth chart, per-merchant revenue table |
| `/admin/revenue` | Monthly revenue bar (12mo), daily fees + volume area (30d), client growth bar (12mo), txn success vs failed line (12mo) |
| `/admin/transactions` | Platform-wide, merchant filter dropdown, status filter, 10/25/50 page size, pagination |
| `/admin/withdrawals` | Combined Payouts page — Withdrawals + Settlements tabs. Merchant filter, status filter, approve/reject actions |
| `/admin/settlements` | Redirects to `/admin/withdrawals` |
| `/admin/people` | Tabbed Businesses + Users. Search, filter pills, server-side pagination |
| `/admin/pricing` | Pricing versions history, publish new version form |
| `/admin/providers` | Paystack balance, success rate, method mix table, recent failures |
| `/admin/audit` | webhook_events log, status filter |
| `/admin/kyc` | Grouped by merchant. Status filter, view doc, approve, reject with reason modal |
| `/admin/cms` | 4 image slots. Local preview before upload, confirm/cancel, full-screen preview modal |
| `/admin/support-stats` | All agents' commission breakdown, period selector (admin only) |
| `/admin/my-stats` | QR encodes full signup URL. Progress bar, rollover display, recent signups table (support only) |

---

## ✅ Home / Marketing Pages (COMPLETE)

| Route | Description |
|---|---|
| `/` | Placeholder with header + hero |
| `/home` | Full marketing page. Fetches `GET /cms/homepage` server-side (`force-dynamic`, `no-store`) |

---

## ✅ Phase 3 — Referral Signup Flow (COMPLETE)

- [x] `?ref=<support_user_id>` pre-read from URL on register page, passed silently through mutation
- [x] QR deep-link encodes full URL: `/login?mode=register&ref=<code>`

---

## ✅ Phase 4 — Notifications & Security (COMPLETE)

- [x] WinSMS on KYC approval/rejection
- [x] WinSMS on withdrawal approved/rejected
- [x] Tokens moved to httpOnly cookies — BFF proxy at `/api/proxy/[...path]/route.ts`
- [x] CSP headers in `next.config.ts`
- [x] WebSocket real-time updates — `useChargeWebSocket` / `usePayWebSocket` hooks
- [x] Dashboard `refetchOnWindowFocus` — updates on tab switch after payment

---

## 🔲 Sprint 2 — Growth & Payments (see `SPRINT.md`)

- [ ] Google Analytics 4 — `gtag.js`, page views + payment success events
- [ ] Google Ads conversion tracking — fire on `PAYMENT_SUCCESS` in `usePayWebSocket`
- [ ] Google Search Console — verification meta tag in `layout.tsx`
- [ ] Google Sign-In fix — confirm `id_token` vs `access_token` flow in prod
- [ ] Remove polling fallback from `/charge` page once WS confirmed stable
- [ ] Notification preferences — channel selector in settings (SMS default, WhatsApp "coming soon")

---

## 🔲 Future — Multiple Bank Accounts

- [ ] Settings page: list accounts with default badge, add/remove, set default
- [ ] Withdrawal page: account selector when requesting payout
- [ ] See `09_Backend_Roadmap.md` for full API spec

---

## API Wiring Status

### Auth ✅
`POST /auth/register` · `POST /auth/login` · `POST /auth/refresh` · `POST /auth/logout` · `GET /auth/me` · `POST /auth/otp/request` · `POST /auth/otp/verify` · `POST /auth/ws-token`

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
