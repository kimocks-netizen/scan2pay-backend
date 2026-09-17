# API reference

Base URL: `https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod`

> All requests and responses are JSON. Authenticated endpoints send
> `Authorization: Bearer <access_token>`. Public endpoints (marked **public**) need no token.

## Error envelope

```json
{ "detail": { "code": "not_found", "message": "Merchant profile not found." } }
```

| HTTP | `code` values |
| --- | --- |
| 400 | `validation_error`, `amount_too_low`, `invalid_mode` |
| 401 | `invalid_credentials`, `token_expired` |
| 404 | `not_found` |
| 410 | `expired` |
| 422 | `amount_required` |
| 500 | `insert_failed`, `qr_failed` |

Minimum amount: **100 cents (R1.00)**. Maximum: **5 000 000 cents (R50 000)**.

---

## 1. Auth ✅ Live

### `POST /auth/register` ✅

```json
{
  "fullName": "Thandi Mokoena",
  "phone": "0821234567",
  "email": "thandi@scanpay.co.za",
  "password": "password123",
  "userType": "vendor",
  "businessName": "Thandi's Spaza & Car Wash"
}
```

`phone` is normalised server-side to E.164 (`0…` → `+27…`).
Side effects: creates `users` + `merchants` + one **primary variable payment
code** (caption defaults by `userType`: `Scan to Pay` / `Scan to Tip` /
`Scan to Pay Fare`).

**201**

```json
{
  "user": { "id": "usr_004", "fullName": "…", "phone": "+27821234567", "email": "…",
            "userType": "vendor", "merchantId": "mch_004", "avatarInitials": "TM",
            "createdAt": "2026-09-04T11:00:00Z", "phoneVerified": false, "emailVerified": false },
  "accessToken": "eyJ…",
  "refreshToken": "eyJ…"
}
```

Errors: `phone_taken` (409), `validation_error` (400).

### `POST /auth/login`

```json
{ "identifier": "0821234567", "password": "password123" }
```

`identifier` is a phone **or** an email. Same 200 body as register.
Errors: `invalid_credentials` (401) — deliberately identical for unknown user
and wrong password in production; the mock distinguishes them.

### `POST /auth/refresh` → `{ "refreshToken": "…" }` → new token pair (rotating).
### `POST /auth/logout` → 204. Revokes the presented refresh token.
### `GET /auth/me` → the `PublicUser` object above.

### Phone verification ✅ Live

- `POST /auth/otp/request` `{ "phone": "+27…" }` → 204
- `POST /auth/otp/verify` `{ "phone": "+27…", "code": "123456" }` → PublicUser

---

## 2. Merchants ✅ Live

### `GET /merchants/me` — authenticated merchant's own profile
### `PATCH /merchants/me` — update own profile (business_name, display_name, trading_category, city, province, settlement_cycle, payout_bank, payout_bank_code, payout_account_masked)
### `GET /merchants/{merchantId}` — public profile (id, business_name, display_name, slug, trading_category, city, status only)

```json
{
  "id": "mch_001", "userId": "usr_001",
  "businessName": "Thandi's Spaza & Car Wash",
  "displayName": "Kasi Fresh Produce",
  "tradingCategory": "Retail & Services",
  "city": "Soweto", "province": "Gauteng",
  "planId": "plan_basic",
  "payoutBank": "Capitec Bank", "payoutAccountMasked": "•••• 4821",
  "settlementCycle": "Daily (T+1)",
  "status": "active", "joinedAt": "2025-11-02T08:12:00Z",
  "slug": "thandis-spaza"
}
```

### `PATCH /merchants/{merchantId}`

Body: any of `displayName`, `city`, `province`, `tradingCategory`. → updated merchant.

### `PUT /merchants/{merchantId}/payout-account`

```json
{ "bankCode": "470010", "accountNumber": "1234564821", "accountHolder": "T Mokoena" }
```

Creates a Paystack transfer recipient, stores `recipient_code`, returns the
merchant with a masked account. Never return the full account number.

### `DELETE /merchants/me` ✅ Live — self-service account deletion (archive, not hard-delete)

Eligibility checked server-side before archiving — 409 with a `reasons` array if blocked. Each
reason is structured, not a pre-formatted sentence — the frontend renders (and colour-codes) the
amount/count itself, which it can only do reliably from typed facts:

```json
{
  "detail": {
    "code": "not_eligible",
    "message": "Your account can't be closed yet.",
    "reasons": [
      { "type": "pending_transactions", "count": 1 },
      { "type": "withdrawal_in_progress", "amount_cents": 5000 },
      { "type": "balance_owed", "amount_cents": 153453 }
    ]
  }
}
```

`type` is one of `pending_transactions` (has `count`), `withdrawal_in_progress` (has
`amount_cents`, an in-flight payout), or `balance_owed` (has `amount_cents`, settled money not
yet withdrawn).

If eligible: deactivates the merchant's payment codes, sets `merchants.status = 'closed'` and
`users.status = 'archived'` (`archived_at`/`archived_by` recorded on both). "The Danger zone" copy
on Settings (web + mobile) explains the flow to the merchant:

> Closing your account deactivates your QR codes and hides your profile. If you register again with
> the same phone or email, we'll reactivate it automatically. If you never do, it's permanently
> deleted after 90 days.

Reactivation is automatic — `POST /auth/register` with the same phone/email while `archived`
reactivates instead of rejecting as "already registered" (phone OTP re-verification is the proof of
ownership). Never reactivated within 90 days → the `PurgeArchivedAccountsFunction` cron anonymises
personal fields (name, phone, email, password, payout bank details) — the row and its transaction
history are kept for accounting/tax retention, only personal data is scrubbed. See migration
`018_account_archival.sql` and `app/cron/purge_archived_accounts.py`.

---

## 3. Products ✅ Live

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/merchants/me/products` | list — includes `qr_reference` and `payments` (sales count) |
| `POST` | `/merchants/me/products` | `{ name, description, price_cents, sku, category }` — auto-creates fixed QR, rolls back on failure |
| `PATCH` | `/merchants/me/products/{id}` | any field; `price_cents` change snapshots old value into `previous_price_cents` |
| `DELETE` | `/merchants/me/products/{id}` | deactivates linked QR, then hard deletes product |
| `POST` | `/merchants/me/products/{id}/regenerate-qr` | issues new `PRD-XXXXXXXX` reference, old sticker stops working |
| `POST` | `/merchants/me/products/{id}/backfill-qr` | creates QR for orphaned product (no existing code) |

Product object:

```json
{ "id": "prd_001", "merchantId": "mch_001", "name": "Washing Powder 2kg",
  "description": "…", "priceCents": 6999, "previousPriceCents": 6499,
  "sku": "SP-WP-2KG", "active": true, "category": "Household",
  "updatedAt": "2026-08-01T09:00:00Z" }
```

---

## 4. Payment codes ✅ Live

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/merchants/me/payment-codes` | excludes product QRs by default; `?include_products=true` for all |
| `POST` | `/merchants/me/payment-codes` | `mode` must be `variable` or `amount` only |
| `PATCH` | `/merchants/me/payment-codes/{id}` | label, caption, placement, active, amount_cents |
| `DELETE` | `/merchants/me/payment-codes/{id}` | blocked on primary code and product-linked codes |

## 5. Charges ✅ Live

### `POST /charges` ✅
```json
{ "amount_cents": 4500, "label": "Groceries" }
```
Creates a charge session on the merchant's **permanent primary QR**. Cancels any existing active session.
Stores `access_code_paystack` on the transaction for reuse when customer scans.
Returns `{ txn_id, reference, access_code, amount_cents, qr_reference, expires_at }`. TTL: 5 minutes.

## 6. Resolve + pay (public) ✅ Live

### `GET /pay/{reference}` **public** ✅
Resolves any QR reference. For the primary QR, checks for an active charge session:
- Active session found → returns `mode: "amount"` with the charge amount
- No session → returns `mode: "variable"` (tip/open payment)
- Product QR → returns `mode: "fixed"` with live `price_cents` from products table

Response includes `charge_session: { txn_id, amount_cents, expires_at, access_code }` when applicable.

### `POST /pay/{reference}/initialise` **public** ✅
```json
{ "amount_cents": 4500, "customer_email": "optional@example.com" }
```
For primary QR with active charge session: reuses stored `access_code_paystack`.
For product/variable: creates new transaction + Paystack initialisation.
Returns `{ txn_id, access_code, amount_cents }`.

### `POST /webhooks/paystack` **public, HMAC-SHA512 verified** ✅
Handles `charge.success` → marks transaction `success`, increments `payment_codes.payments`.
Idempotent by `paystack_reference`.

---

## 7. Transactions ✅ Live

### `GET /merchants/me/transactions` ✅
Query params:
- `status=success|pending|failed`
- `method=card|apple_pay|google_pay`
- `txn_type=charge|product|scan` — charge session / product QR / direct primary scan
- `charge_session=true|false`
- `q=` — search by reference (ilike)
- `limit=10` (max 200), `offset=0`

Returns `{ "data": [...], "total": N, "offset": N }`.

### `GET /merchants/me/transactions/{txn_id}` ✅
### `GET /payments/{txn_id}` ✅ — polled by charge page every 1.5s

---

## 8. Platform

### `GET /billing/plans` **public**

```json
[ { "id": "plan_free", "name": "Free", "monthlyPriceCents": 0,
    "platformFeePercent": 2.5, "features": ["…"], "recommended": false } ]
```

### `GET /platform/pricing` **public**

```json
{ "currency": "ZAR", "provider": "Paystack", "providerPercent": 2.9,
  "providerFixedCents": 100,
  "platformFeePercentByPlan": { "plan_free": 2.5, "plan_basic": 1.5, "plan_pro": 1.0 },
  "version": "2026-07-01", "effectiveFrom": "2026-07-01T00:00:00Z" }
```

### `POST /merchants/{id}/plan` `{ "planId": "plan_basic" }` → updated merchant.

### `GET /health` → `{ "status": "ok", "db": "ok" }` ✅ live

---

## 9. Withdrawals

| method | path | who | notes |
| --- | --- | --- | --- |
| GET | `/merchants/{id}/balance` | merchant | `{ availableCents, onHoldCents, inFlightCents, paidToDateCents }` |
| GET | `/merchants/{id}/withdrawals` | merchant | history, newest first |
| POST | `/merchants/{id}/withdrawals` | merchant | `{ amountCents, note }` — server re-checks the balance |
| POST | `/withdrawals/{id}/cancel` | merchant | `pending` only |

Available = settled successful `net_cents` − paid − in flight (`pending` + `approved`).
Minimum request R50 (`5000` cents). Errors: `422 amount_below_minimum`,
`422 insufficient_balance`, `409 withdrawal_not_pending`.

---

## 10. Admin (staff only)

All under `/admin/*` and gated on the `admin` role. Full request/response detail,
pricing versioning rules and the audit-log contract live in `docs/admin.md`.

| method | path | notes |
| --- | --- | --- |
| GET | `/admin/stats` | platform totals |
| GET | `/admin/users` · POST `/admin/users/{id}/status` | user management |
| GET | `/admin/merchants` · POST `/admin/merchants/{id}/status` · `/plan` | business management |
| POST | `/admin/merchants/{id}/archive` ✅ Live | admin-forced archive — bypasses the eligibility checks `DELETE /merchants/me` enforces (e.g. closing a fraudulent account). Body: `{ "reason": "..." }` |
| POST | `/admin/merchants/{id}/reactivate` ✅ Live | manual reactivation without waiting for the merchant to re-register. Sets `merchants.status = 'active'`, `users.status = 'active'`, bumps `reactivation_count` |
| GET | `/admin/merchants?status=closed` · `/admin/users?status=archived` ✅ Live | already-supported status filter now also surfaces archived accounts — no new endpoint needed |
| GET | `/admin/growth` ✅ Live | People page growth analytics — see below |
| GET | `/admin/transactions` | every payment with its pricing snapshot |
| GET | `/admin/payment-codes` | code management |
| GET | `/admin/settlements` | pending vs settled per business |
| GET | `/admin/withdrawals?status=` · POST `/admin/withdrawals/{id}/status` | payout queue |
| GET | `/admin/pricing/versions` · POST `/admin/pricing/versions` | publish a pricing version |
| GET | `/admin/audit` | audit log |

### `GET /admin/growth` ✅ Live

Powers the "Compare by" (Week / Fortnight / Month) cards and the three trend charts on
`/admin/people`. All bucketing happens server-side in `admin.py` — the frontend never fetches raw
merchant/user rows for this.

```json
{
  "week":      { "current": { "start": "2026-09-13", "end": "2026-09-17", "merchants": 5, "users": 12 },
                 "previous": { "start": "2026-09-06", "end": "2026-09-10", "merchants": 3, "users": 9 },
                 "elapsed_days": 5 },
  "fortnight": { "current": {...}, "previous": {...}, "elapsed_days": 12 },
  "month":     { "current": { "label": "Aug 2026", "merchants": 40, "users": 90, ... },
                 "previous": { "label": "Jul 2026", "merchants": 35, "users": 80, ... } },
  "daily_30":   [ { "label": "20 Aug", "merchants": 2, "users": 5 }, ... ],
  "weekly_12":  [ { "label": "23 Aug", "merchants": 9, "users": 20 }, ... ],
  "monthly_12": [ { "label": "Aug 26", "merchants": 40, "users": 90, "cum_merchants": 812, "cum_users": 1904 }, ... ],
  "totals":     { "merchants": 812, "users": 1904 }
}
```

Two deliberate framing choices, not obvious from the shape alone:

- **Week/fortnight are elapsed-day-matched.** `previous` is truncated to the same number of days
  as `current` (`elapsed_days`) — a partial current week is never compared against a full prior
  week, which would always look like a decline regardless of actual performance.
- **Month always compares the last two *complete* calendar months** (e.g. August vs July), never
  the current partial month against a complete one — that comparison is simply not offered until
  the month ends. The current partial month still appears as the newest bar in `monthly_12`.

---

## Mapping from the current mock client

| `src/lib/api/client.ts` | Endpoint |
| --- | --- |
| `login` | `POST /auth/login` |
| `register` | `POST /auth/register` |
| `getUser` | `GET /auth/me` |
| `getMerchant` / `updateMerchant` | `GET` / `PATCH /merchants/{id}` |
| `listProducts` / `updateProductPrice` | `GET /merchants/{id}/products` / `PATCH /products/{id}` |
| `listPaymentCodes` / `createPaymentCode` | `GET` / `POST /merchants/{id}/payment-codes` |
| `getPaymentCode` / `updatePaymentCode` | `GET` / `PATCH /payment-codes/{id}` |
| `getPrimaryCode` | `GET /merchants/{id}/payment-codes/primary` |
| `createCharge` / `listCharges` / `cancelCharge` | `POST` / `GET /merchants/{id}/charges`, `POST /charges/{id}/cancel` |
| `resolveCode` | `GET /codes/resolve/{reference}` |
| `payCode` | `POST /payments/initialise` + poll `GET /payments/{id}` |
| `listTransactions` | `GET /merchants/{id}/transactions` |
| `listPlans` / `getPricing` | `GET /billing/plans` / `GET /platform/pricing` |
| `getBalance` / `listWithdrawals` / `requestWithdrawal` / `cancelWithdrawal` | `GET /merchants/{id}/balance`, `GET` / `POST /merchants/{id}/withdrawals`, `POST /withdrawals/{id}/cancel` |
| `admin*` (see `docs/admin.md`) | `GET`/`POST /admin/*` |
