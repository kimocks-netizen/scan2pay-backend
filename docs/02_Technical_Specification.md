# Scan2Pay — Technical Specification

> Reflects the actual implemented system.

---

## Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 15 App Router · TypeScript · Tailwind v4 · TanStack Query v5 · Zustand |
| Backend | Python 3.13 · FastAPI · Mangum |
| Hosting | AWS Lambda + API Gateway (SAM) · `af-south-1` |
| Database | Supabase (PostgreSQL) |
| Payments | Paystack (ZAR) |
| SMS / OTP | WinSMS |
| File storage | Amazon S3 |
| Background jobs | EventBridge-triggered Lambda |

**Live API:** `https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod`
**Pay page base:** `https://scan2pay.site/pay/{reference}`

---

## The Core Rule

> Every QR code is permanent. No QR is ever created per transaction. The QR encodes a URL that resolves to a `payment_codes` row. What changes is the **configuration** behind that row — not the QR itself.

---

## The Three QR Code Types

---

### Type 1 — Permanent Variable QR (tip / open payment)

**Reference format:** `QR-XXXXXXXX`
**DB:** `mode=variable`, `single_use=false`, `expires_at=null`, `amount_cents=null`, `is_primary=true`
**Created:** Automatically on merchant registration

Customer scans → sees keypad → enters any amount → pays. QR never expires, never deactivates.

```
GET /pay/QR-890E282B
→ { code: { mode: "variable", amount_cents: null }, merchant: {...} }

Customer enters R50

POST /pay/QR-890E282B/initialise { amount_cents: 5000 }
→ { access_code: "..." }

Paystack popup → payment → webhook → transaction success
QR stays active for next customer
```

Additional `variable` or `amount` codes (beyond the primary) can be created from the Payment Codes page — same permanence, `is_primary=false`.

---

### Type 2 — Charge Session on Permanent QR (vendor face-to-face)

**Reference format:** `QR-XXXXXXXX` — the merchant's **permanent primary QR** (same as Type 1)
**DB:** No new `payment_codes` row is created. A `transactions` row is created with `charge_session=true` and `charge_expires_at=now+5min`
**Created:** Merchant via `POST /charges` on the Charge page

The merchant types an amount. A **charge session** is created — a pending transaction linked to the permanent primary QR with the amount and a 5-minute expiry. The QR shown on screen is the same permanent QR the merchant always has. When a customer scans it during the session window, `GET /pay/QR-890E282B` detects the active session and returns `mode=amount` with the session's `amount_cents` — so the customer sees a fixed amount, not a keypad. After payment or expiry, the session is gone and the QR returns to `variable` mode.

```
Merchant types R85

POST /charges { amount_cents: 8500, label: "Amount due" }
→ backend finds primary QR (QR-890E282B)
→ cancels any existing active charge session
→ calls Paystack initialize (creates transaction upfront)
→ inserts transactions row:
   { charge_session: true, charge_expires_at: now+5min, amount_cents: 8500, status: pending }
→ returns { txn_id, access_code, qr_reference: "QR-890E282B", expires_at }

Charge page shows QR for QR-890E282B on screen

Customer scans QR-890E282B

GET /pay/QR-890E282B
→ backend checks: active charge session? YES
→ overrides mode to "amount", amount_cents = 8500
→ { code: { mode: "amount", amount_cents: 8500 }, charge_session: { txn_id, expires_at } }

Customer sees "R85" → taps Pay

POST /pay/QR-890E282B/initialise
→ backend finds active charge session
→ Paystack already initialised — returns existing access_code
→ { txn_id, access_code, amount_cents: 8500 }

Paystack popup → payment → webhook → transaction success
charge_session expires — QR returns to variable mode
```

**Key behaviours:**
- The QR sticker/screen never changes — only the charge session behind it changes
- Starting a new charge cancels the previous session (merchant changed their mind)
- `ExpireChargesFunction` Lambda runs every 1 min — marks sessions with `charge_expires_at < now` as failed
- Charge page polls `GET /payments/:id` every 1.5s — flips to "Paid" when webhook fires
- Recent charges list reads from `GET /merchants/me/transactions?charge_session=true&limit=5`

---

### Type 3 — Permanent Fixed Product QR

**Reference format:** `PRD-XXXXXXXX`
**DB:** `mode=fixed`, `single_use=false`, `expires_at=null`, `amount_cents=null`, `product_id=set`
**Created:** Automatically when merchant creates a product via `POST /merchants/me/products`

Each product gets its own permanent QR. `amount_cents` is `null` on the code — price is always read live from `products.price_cents` at scan time.

```
POST /merchants/me/products { name: "Haircut", price_cents: 8000 }
→ products row: { id: "prd_001", price_cents: 8000 }
→ payment_codes row: { reference: "PRD-A3F2C1B4", mode: "fixed", product_id: "prd_001" }

Customer scans PRD-A3F2C1B4

GET /pay/PRD-A3F2C1B4
→ joins product → code.amount_cents = 8000
→ { code: { mode: "fixed", amount_cents: 8000 }, product: { name: "Haircut" } }

PATCH /merchants/me/products/prd_001 { price_cents: 10000 }
→ same QR sticker → next customer sees R100
```

---

## QR Reference Prefixes

| Prefix | Type | Permanent? | Created by |
|---|---|---|---|
| `QR-` | Type 1 primary or additional | ✅ | Auto on registration / Payment Codes page |
| `QR-` | Type 2 charge (reuses primary) | ✅ | Charge page (session on existing QR) |
| `PRD-` | Type 3 product | ✅ | Auto when product created |

> There is no `PAY-` prefix anymore. The old single-use charge code model has been replaced by charge sessions on the permanent primary QR.

---

## `GET /pay/:reference` Resolution Logic

```
GET /pay/QR-890E282B
        |
        v
Fetch payment_codes row (active=true)
        |
        v
Is mode=fixed and product_id set?
  YES → join products.price_cents → set code.amount_cents
        |
        v
Is is_primary=true and no product_id?
  YES → check for active charge session:
        SELECT * FROM transactions
        WHERE payment_code_id = pc.id
          AND status = 'pending'
          AND charge_session = true
          AND charge_expires_at > now()
        ORDER BY created_at DESC LIMIT 1
        |
        v
  Session found?
    YES → override code.mode = "amount"
          override code.amount_cents = session.amount_cents
          include charge_session in response
    NO  → return as-is (variable mode, customer enters amount)
        |
        v
Return { code, merchant, product?, charge_session? }
```

---

## `POST /pay/:reference/initialise` Logic

```
Is is_primary=true?
  YES → check for active charge session
        Session found?
          YES → Paystack already initialised — return existing access_code
                (no double-charge, no new Paystack transaction)
          NO  → fall through to normal variable flow

Normal flow:
  mode=variable → amount from request body
  mode=amount   → amount from payment_codes.amount_cents
  mode=fixed    → amount from products.price_cents (live read)
  → create transaction → call Paystack → return access_code
```

---

## Database Schema (key tables)

### payment_codes
```sql
id              text PK
merchant_id     text FK → merchants
reference       text UNIQUE      -- QR-... | PRD-...
label           text
caption         text
mode            code_mode        -- variable | amount | fixed
product_id      text FK → products  -- only for mode=fixed
amount_cents    bigint           -- null for variable+fixed, set for amount
active          bool
is_primary      bool
single_use      bool             -- always false now (charge sessions use transactions)
expires_at      timestamptz      -- null for all permanent codes
scans           int
payments        int
```

### transactions
```sql
id                    text PK    -- txn_000001
reference             text       -- STP000001
paystack_reference    text
merchant_id           text FK
payment_code_id       text FK
item                  text
amount_cents          int
platform_fee_cents    int
provider_fee_cents    int
net_cents             int
status                txn_status -- pending | success | failed
authorization_code    text
settlement_status     text
paid_at               timestamptz
charge_session        bool       -- true for Type 2 charge page transactions
charge_expires_at     timestamptz -- 5min TTL for charge sessions
access_code_paystack  text       -- stored so customer can resume without re-initialising
pricing               jsonb      -- fee snapshot at creation time
```

### products
```sql
id                    text PK    -- prd_001
merchant_id           text FK
name                  text
price_cents           bigint     -- live price — read at every scan
previous_price_cents  bigint     -- snapshotted on price change
sku                   text
category              text
active                bool
```

---

## Fee Calculation

```python
platform_fee_cents = round(amount_cents * plan_percent / 100)
provider_fee_cents = round(amount_cents * 2.9 / 100) + 100
net_cents          = amount_cents - platform_fee_cents - provider_fee_cents
```

Snapshotted on the transaction at creation. Never recalculated.

---

## Background Jobs

| Lambda | Schedule | Purpose |
|---|---|---|
| `ExpireChargesFunction` | Every 1 min | Marks charge sessions with `charge_expires_at < now` as `failed` |
| `ReconcilePaystackFunction` | Every 15 min | Verifies `pending` transactions >10 min via Paystack API |
| `BuildSettlementsFunction` | Daily 02:00 SAST | Groups settled transactions into payout rows per merchant |

> Note: `ExpireChargesFunction` previously set `payment_codes.active=false` on `PAY-` codes. Now it marks `transactions.status=failed` where `charge_session=true AND charge_expires_at < now AND status=pending`.

---

## Frontend Pages

| Route | Auth | Type served |
|---|---|---|
| `/charge` | Yes | Type 2 — sets charge session on permanent QR, shows same QR on screen |
| `/my-code` | Yes | Type 1 — primary QR poster, print/share/customise |
| `/payment-codes` | Yes | Type 1 — additional permanent variable/amount codes |
| `/products` | Yes | Type 3 — product CRUD, auto-creates PRD- QR per product |
| `/pay/[reference]` | No | All types — customer payment page |
| `/transactions` | Yes | All types — transaction history |
| `/dashboard` | Yes | All types — overview |

---

## API Routes

### Public (no auth)
| Method | Path | Notes |
|---|---|---|
| GET | `/pay/:reference` | Resolves QR. Checks charge session for primary QR. Joins product price for fixed mode. |
| POST | `/pay/:reference/initialise` | Customer payment init. Returns existing access_code if charge session active. |

### Merchant (JWT required)
| Method | Path | Notes |
|---|---|---|
| POST | `/charges` | Creates charge session on primary QR. Calls Paystack upfront. Returns `qr_reference` (permanent). |
| GET | `/payments/:id` | Poll transaction status (1.5s poll on Charge page) |
| GET/POST/PATCH/DELETE | `/merchants/me/payment-codes` | Type 1 permanent codes (excludes product codes) |
| GET/POST/PATCH/DELETE | `/merchants/me/products` | Type 3 — POST auto-creates PRD- code |
| GET/PATCH | `/merchants/me` | Merchant profile |
| GET | `/merchants/me/transactions` | Paginated + filtered. Supports `?charge_session=true` for recent charges list. |

---

## Auth

- JWT access token (short-lived) + refresh token (30 days)
- `api-client.ts`: on 401 → `POST /auth/refresh` → retry once → on failure clear auth + redirect `/login`
- Token in `localStorage` + cookie (cookie used by Next.js middleware for SSR route protection)

---

## Webhook Security

```python
expected = hmac.new(PAYSTACK_SECRET_KEY.encode(), raw_body, hashlib.sha512).hexdigest()
hmac.compare_digest(expected, x_paystack_signature_header)
```

- `PAYSTACK_SECRET_KEY` is the HMAC key — no separate webhook secret
- `webhook_events` UNIQUE constraint makes replays no-ops
- Handlers in try/except — bugs never return non-200 to Paystack

---

## Pending Migration

Run in Supabase SQL editor before testing Type 2 charges:

```sql
ALTER TABLE transactions
  ADD COLUMN IF NOT EXISTS charge_session boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS charge_expires_at timestamptz,
  ADD COLUMN IF NOT EXISTS access_code_paystack text;

CREATE INDEX IF NOT EXISTS idx_transactions_charge_session
  ON transactions (payment_code_id, status, charge_session, charge_expires_at)
  WHERE charge_session = true;
```

---

## Paystack Gotchas

| Issue | Detail |
|---|---|
| `channels: ["apple_pay"]` | 500 on ZAR test accounts — use `["card"]` only |
| Boolean metadata | 500 — all metadata values must be strings |
| `resumeTransaction` | No callbacks — use `newTransaction({ access_code })` |
| `@paystack/inline-js` | Dynamic import only — crashes SSR if statically imported |
| `POST /transfer` | Blocked on test/starter accounts — prod only |

---

## What's Not Yet Built

| Feature | Notes |
|---|---|
| Bank accounts | `POST/GET /merchants/me/bank-accounts` — needed before withdrawals |
| Withdrawals | Depends on bank accounts + prod Paystack account |
| Admin pages | All stubs |
| Apple Pay | Register `scan2pay.site` via `POST /apple-pay/domain` before go-live |
| Google Pay | Auto on verified Paystack account |
| Capitec Pay | Confirm channel name with Paystack support first |
| SMS notifications | WinSMS wired for OTP only — not yet on payment events |
| Charge authorization | Returning customers skip card entry — Phase 2 |
| `ExpireChargesFunction` update | Needs updating to mark `charge_session` transactions as failed instead of deactivating payment codes |
