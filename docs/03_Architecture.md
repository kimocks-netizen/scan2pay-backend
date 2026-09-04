# Architecture

## Stack

| Layer | Choice |
| --- | --- |
| Language | Python 3.12 |
| Framework | FastAPI |
| Validation | Pydantic v2 |
| Database | PostgreSQL 16 |
| ORM / migrations | SQLAlchemy 2.x + Alembic |
| Cache / short-lived state | Redis (charge expiry, rate limits, idempotency) |
| Auth | JWT access token (15 min) + refresh token (30 days, rotating) |
| Payments | Paystack |
| Background jobs | Celery + Redis (or APScheduler if you want fewer moving parts) |

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

- `single_use = true`, `expires_at = now + 5 minutes`
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

Secrets held as env vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`,
`PAYSTACK_SECRET_KEY`, `PAYSTACK_PUBLIC_KEY`, `PAYSTACK_WEBHOOK_SECRET`.

## Background jobs

| Job | Schedule | Does |
| --- | --- | --- |
| `expire_charges` | every minute | sets `active = false` on codes past `expires_at` |
| `reconcile_paystack` | every 15 min | verifies `pending` payments older than 10 min against Paystack |
| `build_settlements` | daily 02:00 SAST | groups settled transactions into payout rows |
| `refresh_daily_stats` | hourly | materialised per-merchant totals for the dashboard |

## Cross-cutting

- **Rate limits:** 5/min on login and register per phone+IP; 30/min on
  `resolve`; 10/min on `charges` per merchant.
- **Idempotency:** `POST /payments/initialise` and all webhook handling accept
  an `Idempotency-Key` header; store the key with the response for 24h.
- **Audit:** every write to merchants, payment codes and payouts writes an
  `audit_log` row.
- **Errors** use a single envelope, see `api.md`.
