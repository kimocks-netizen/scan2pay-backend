# API reference

Base URL: `https://api.scan2pay.co.za/v1`

All requests and responses are JSON. Authenticated endpoints send
`Authorization: Bearer <access_token>`. Public endpoints (marked **public**) are
what a scanning customer hits and need no token.

## Error envelope

Every non-2xx response:

```json
{
  "error": {
    "code": "code_expired",
    "message": "This payment request has expired. Ask for a new one.",
    "field": null
  }
}
```

| HTTP | `code` values |
| --- | --- |
| 400 | `validation_error`, `amount_too_low`, `amount_too_high` |
| 401 | `invalid_credentials`, `token_expired`, `token_invalid` |
| 403 | `not_your_resource`, `plan_limit_reached` |
| 404 | `not_found` |
| 409 | `phone_taken`, `email_taken`, `already_paid` |
| 410 | `code_expired`, `code_inactive` |
| 422 | `payment_failed` |
| 429 | `rate_limited` |
| 500 | `internal_error` |

Minimum amount is **100 cents (R1.00)**; maximum is **5 000 000 cents (R50 000)**.

---

## 1. Auth

### `POST /auth/register`

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

### Phone verification (phase 2)

- `POST /auth/otp/request` `{ "phone": "+27…" }` → 204
- `POST /auth/otp/verify` `{ "phone": "+27…", "code": "123456" }` → token pair

---

## 2. Merchants

### `GET /merchants/{merchantId}`

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

---

## 3. Products

Only relevant to merchants who want product-linked (`fixed`) codes. Vendors
using the till-charge flow never touch this.

| Method | Path | Notes |
| --- | --- | --- |
| `GET` | `/merchants/{id}/products` | list |
| `POST` | `/merchants/{id}/products` | `{ name, description, priceCents, sku, category }` |
| `PATCH` | `/products/{productId}` | any field; changing `priceCents` copies the old value into `previousPriceCents` |
| `DELETE` | `/products/{productId}` | soft delete (`active = false`) |

Product object:

```json
{ "id": "prd_001", "merchantId": "mch_001", "name": "Washing Powder 2kg",
  "description": "…", "priceCents": 6999, "previousPriceCents": 6499,
  "sku": "SP-WP-2KG", "active": true, "category": "Household",
  "updatedAt": "2026-08-01T09:00:00Z" }
```

---

## 4. Payment codes (permanent, printable)

### `GET /merchants/{id}/payment-codes`
Returns the merchant's printable codes. **Excludes `singleUse` charges.**

### `GET /merchants/{id}/payment-codes/primary`
The permanent code minted at signup (`isPrimary = true`), else the oldest.

### `POST /merchants/{id}/payment-codes`

```json
{ "label": "Full Car Wash", "mode": "fixed", "productId": "prd_003",
  "amountCents": null, "placement": "Wash bay board", "description": "…",
  "caption": "Scan to Pay" }
```

Validation: `mode=fixed` requires `productId` and `amountCents = null`;
`mode=amount` requires `amountCents` and `productId = null`; `mode=variable`
requires both null. Free plan is capped at 1 code → `plan_limit_reached`.

### `GET /payment-codes/{id}` · `PATCH /payment-codes/{id}` (`label`, `caption`, `placement`, `active`) · `DELETE /payment-codes/{id}` (soft)

Payment code object:

```json
{ "id": "pc_002", "merchantId": "mch_001", "reference": "QR-2B41C77",
  "label": "Full Car Wash", "mode": "fixed", "productId": "prd_003",
  "amountCents": null, "description": "…", "active": true,
  "scans": 689, "payments": 501, "createdAt": "2025-11-05T07:34:00Z",
  "placement": "Wash bay board", "isPrimary": false, "caption": "Scan to Pay",
  "singleUse": false, "expiresAt": null, "paidAt": null }
```

---

## 5. Till charges (single-use)

### `POST /merchants/{id}/charges`

```json
{ "amountCents": 4500, "note": "Groceries" }
```

**201** → a payment code with `singleUse: true`, `mode: "amount"`,
`reference: "PAY-8BEB644"`, `expiresAt = now + 5 min`, `paidAt: null`.
`note` is a free-text label only — **we never record what was sold.**
Errors: `amount_too_low` (400).

### `GET /merchants/{id}/charges?limit=8`
Most recent charges, newest first. Used by "Recent requests".

### `GET /charges/{chargeId}`
Polled by the merchant screen every 1.5s. Watch `paidAt` and `active`.

### `POST /charges/{chargeId}/cancel`
Sets `active = false`, `expiresAt = now`. → the updated charge.

### `GET /charges/{chargeId}/events` *(optional, SSE)*
Emits `{"status":"paid","transactionId":"txn_…"}` — replaces polling later.

---

## 6. Resolve + pay (public, no auth)

### `GET /codes/resolve/{reference}` **public**

The single endpoint a scanning phone hits. Increments `scans`.

**200**

```json
{
  "code": { "id": "pc_chg_1757…", "reference": "PAY-8BEB644", "label": "Groceries",
            "mode": "amount", "singleUse": true, "expiresAt": "2026-09-04T11:10:00Z" },
  "merchant": { "id": "mch_001", "displayName": "Kasi Fresh Produce", "slug": "thandis-spaza" },
  "product": null,
  "amountCents": 4500,
  "expiresAt": "2026-09-04T11:10:00Z"
}
```

`amountCents` is `null` when `mode = variable` — the customer types it.
Return only the public merchant fields (id, displayName, slug, tradingCategory).
Never leak payout details, phone or email here.
Errors: `not_found` (404), `code_inactive` / `code_expired` (410).

### `POST /payments/initialise` **public**

```json
{ "reference": "PAY-8BEB644", "amountCents": 4500, "method": "card", "email": "customer@example.com" }
```

Server re-resolves the code and **re-validates the amount** (must equal the
resolved amount for `fixed`/`amount`; must be ≥ 100 cents for `variable`).
Creates a `pending` transaction and a Paystack transaction.

**201**

```json
{ "paymentId": "pay_01J…", "reference": "STP300123",
  "authorizationUrl": "https://checkout.paystack.com/…",
  "accessCode": "0peioxfhpn", "publicKey": "pk_live_…" }
```

Errors: `code_expired` (410), `already_paid` (409), `amount_too_low` (400).

### `GET /payments/{paymentId}` **public**

```json
{ "id": "pay_01J…", "status": "pending", "transaction": null }
```

Once the webhook lands, `status` is `success` and `transaction` is a full
transaction object (the customer's receipt).

### `POST /webhooks/paystack` **public, signature-verified**

Verify `x-paystack-signature` = HMAC-SHA512 of the **raw** body with
`PAYSTACK_WEBHOOK_SECRET`, timing-safe compare, before parsing anything.
Handled events: `charge.success`, `charge.failed`, `transfer.success`,
`transfer.failed`. Always return 200 quickly; process idempotently by
`paystack_reference`.

On `charge.success`:
1. mark the transaction `success`, compute fees, set `net_cents`
2. if the code is `singleUse` → `paid_at = now`, `active = false`
3. increment `payments` on the code
4. write a `webhook_events` row

---

## 7. Transactions & reports

### `GET /merchants/{id}/transactions`
Query: `?from=&to=&status=&method=&codeId=&cursor=&limit=50`.

```json
{ "items": [ { "id": "txn_90000", "reference": "STP300100", "merchantId": "mch_003",
               "paymentCodeId": "pc_008", "productId": null,
               "item": "Taxi Fare — Soweto to Johannesburg CBD",
               "amountCents": 2500, "platformFeeCents": 62, "providerFeeCents": 172,
               "netCents": 2266, "status": "success", "method": "card",
               "customerLabel": "Anonymous", "settlementStatus": "pending",
               "createdAt": "2026-09-04T05:12:00Z" } ],
  "nextCursor": null }
```

### `GET /merchants/{id}/stats?period=today|7d|30d|mtd`

```json
{ "grossCents": 128400, "netCents": 121030, "feesCents": 7370,
  "count": 46, "successRate": 0.94,
  "byDay": [ { "date": "2026-09-01", "grossCents": 18200, "count": 7 } ],
  "byMethod": { "card": 30, "apple_pay": 9, "google_pay": 7 },
  "topCodes": [ { "codeId": "pc_008", "label": "…", "count": 21, "grossCents": 52500 } ] }
```

### `GET /merchants/{id}/transactions.csv` → CSV export (same filters).

### `GET /merchants/{id}/payouts`

```json
[ { "id": "pout_001", "merchantId": "mch_003", "amountCents": 226600,
    "status": "paid", "bankReference": "TRF_9x…",
    "periodStart": "2026-09-01T00:00:00Z", "periodEnd": "2026-09-02T00:00:00Z",
    "paidAt": "2026-09-02T09:14:00Z", "transactionCount": 41 } ]
```

Taxi associations settle to the **association's** account. We do not split to
individual drivers.

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

### `GET /health` → `{ "status": "ok", "db": "ok", "redis": "ok" }`

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
| GET | `/admin/transactions` | every payment with its pricing snapshot |
| GET | `/admin/payment-codes` | code management |
| GET | `/admin/settlements` | pending vs settled per business |
| GET | `/admin/withdrawals?status=` · POST `/admin/withdrawals/{id}/status` | payout queue |
| GET | `/admin/pricing/versions` · POST `/admin/pricing/versions` | publish a pricing version |
| GET | `/admin/audit` | audit log |

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
