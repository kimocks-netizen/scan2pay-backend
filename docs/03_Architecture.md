# Architecture

## Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.13 |
| Framework | FastAPI + Mangum (Lambda adapter) |
| Validation | Pydantic v2 |
| Database | Supabase (PostgreSQL 16) |
| DB client | `supabase-py` (no ORM — raw Supabase queries) |
| Migrations | Plain SQL files run in Supabase SQL editor |
| Auth | JWT access token (15 min) + refresh token (30 days, rotating) |
| Payments | Paystack |
| SMS / OTP | WinSMS |
| Hosting | AWS Lambda + API Gateway (SAM) |
| Background jobs | EventBridge-triggered Lambda functions (no Redis, no Celery) |

## Request flow

```text
Customer phone                 Scan2Pay API                 Paystack
     |                              |                          |
  scan QR  -->  GET /codes/resolve/{reference}                 |
     |          <-- merchant, label, amount (or null)          |
     |                              |                          |
  tap Pay -->  POST /payments/initialise  -->  init transaction|
     |          <-- authorization_url / access_code            |
  pay on Paystack checkout  ------------------------------->   |
     |                              |  <-- POST /webhooks/paystack
     |                              |      (charge.success, signed)
  poll GET /payments/{id}  <-- status: success                 |
```

Two rules follow from this:

1. **The webhook is the source of truth.** A payment is only `success` after a
   verified `charge.success` webhook (or an explicit server-side verify call).
   Never trust the browser redirect.
2. **The merchant screen polls**, it does not wait. `GET /charges/{id}` is
   called every ~1.5s by the Charge page until `paid_at` is set. (Optional
   upgrade: SSE at `GET /charges/{id}/events`.)

## The three code modes

| Mode | Amount comes from | Typical use |
| --- | --- | --- |
| `fixed` | the linked product's current price | barber "Cut R80", shelf item |
| `amount` | `amount_cents` on the code itself | taxi route fare |
| `variable` | the paying customer types it | tips, mixed baskets |

Because `fixed` resolves the product price **at scan time**, a merchant changes
a price in the app and every printed poster is correct instantly. No reprints.

## Till charges (single-use codes)

The vendor flow the product is built around: the merchant types **one total**
on a keypad, the API mints a throwaway code.

- `single_use = true`, `expires_at = now + 5 minutes` (`CHARGE_TTL_MS = 300 000 ms` in the frontend constant)
- Dies on payment (`paid_at` set, `active = false`) or on expiry
- Never appears in the printable-codes list
- **No inventory is captured** — we never store what was sold, only the amount

Expiry must be enforced **server-side** in `resolve` and in `initialise`; the
countdown in the UI is cosmetic.

## Environments

| Env | API | Paystack keys |
| --- | --- | --- |
| local | `http://localhost:8000` | test |
| staging | `https://api-staging.scan2pay.co.za` | test |
| production | `https://api.scan2pay.co.za` | live |

Secrets held in SSM Parameter Store under `/scan2pay/{env}/` and loaded at
Lambda cold-start via `app/core/config.py` (Pydantic Settings). Local dev uses
`.env` (gitignored). Keys: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
`SUPABASE_ANON_KEY`, `JWT_SECRET`, `PAYSTACK_SECRET_KEY`,
`PAYSTACK_PUBLIC_KEY`, `PAYSTACK_WEBHOOK_SECRET`, `WINSMS_API_KEY`.

## Background jobs

| Job | Schedule | Does |
| --- | --- | --- |
| `expire_charges` | every 1 min | sets `active = false` on codes past `expires_at` |
| `reconcile_paystack` | every 15 min | verifies `pending` payments older than 10 min against Paystack |
| `build_settlements` | daily 02:00 SAST | groups settled transactions into payout rows |

No Redis or Celery — all scheduling is EventBridge rules in `template.yaml`.

## Cross-cutting

- **Rate limits:** 5/min on login and register per phone+IP; 30/min on
  `resolve`; 10/min on `charges` per merchant.
- **Idempotency:** `POST /payments/initialise` and all webhook handling accept
  an `Idempotency-Key` header; store the key with the response for 24h.
- **Audit:** every write to merchants, payment codes and payouts writes an
  `audit_log` row.
- **Errors** use a single envelope, see `api.md`.
