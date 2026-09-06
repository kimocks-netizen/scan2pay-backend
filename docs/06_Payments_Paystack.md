# Paystack API Reference — Scan2Pay

> Living document. Updated as we integrate each endpoint.
> All amounts are in **cents (ZAR)**. R1.00 = 100 cents.
> All server calls use `Authorization: Bearer <PAYSTACK_SECRET_KEY>`.
> The secret key **never** leaves the server.

---

## Authentication

```
Authorization: Bearer <PAYSTACK_SECRET_KEY>
```

- `PAYSTACK_SECRET_KEY` — server-side only (Lambda env via SSM)
- `PAYSTACK_PUBLIC_KEY` — returned to the browser for Paystack Inline JS
- **Webhook secret** — Paystack does NOT have a separate webhook secret. The `PAYSTACK_SECRET_KEY` itself is used for HMAC-SHA512 webhook signature verification. SSM param `/scan2pay/dev/PAYSTACK_WEBHOOK_SECRET` must be set to the same value as `PAYSTACK_SECRET_KEY`.

---

## Base URL

```
https://api.paystack.co
```

---

## Frontend Integration — Paystack Inline JS

We use **Paystack Inline JS** (popup mode), not a redirect. The backend initializes the transaction and returns `access_code` to the frontend. The frontend resumes the popup using that code.

**Install:**
```bash
npm install @paystack/inline-js
```

**Usage:**
```ts
import PaystackPop from "@paystack/inline-js";

const popup = new PaystackPop();
popup.resumeTransaction(access_code);  // access_code from our backend
```

- The popup handles card entry, Apple Pay, Google Pay automatically based on device/browser
- On success/close, Paystack redirects to `callback_url` — we set this to `/charge?paid=true`
- **Never trust the popup callback as payment confirmation** — only the `charge.success` webhook is authoritative
- Apple Pay and Google Pay surface automatically once the domain is registered (see Apple Pay section)

---

## Pagination — Cursor-Based

All list endpoints that we use are fetched with cursor pagination for infinite scroll on mobile.

**Query params:**
```
?use_cursor=true&perPage=20&next=<cursor>
```

**Response envelope:**
```json
{
  "status": true,
  "data": [...],
  "meta": {
    "next": "cursor_string_here",
    "previous": null,
    "perPage": 20
  }
}
```

| Field | Notes |
|---|---|
| `meta.next` | Cursor for the next page. `null` means end of list |
| `meta.previous` | Cursor for the previous page |
| `perPage` | Always 20 for our use case |

**How we use it:**
- First page: omit `next` param
- Subsequent pages: pass `meta.next` from the previous response as `next=<cursor>`
- Stop fetching when `meta.next === null`

---

## Payment APIs

### 1. Initialize Transaction
**Why we use it:** Kicks off every payment. We call this server-side so we control the final amount — the client never sets the price.

```
POST /transaction/initialize
```

**Request body:**
```json
{
  "email": "customer@example.com",
  "amount": 4500,
  "currency": "ZAR",
  "reference": "STP300001",
  "callback_url": "https://scan2pay.site/charge?paid=true",
  "channels": ["card", "apple_pay", "google_pay"],
  "metadata": {
    "merchant_id": "mch_001",
    "payment_code_id": "pc_001",
    "single_use": false
  }
}
```

> `callback_url` — after the Paystack Inline popup closes, the customer lands back on `/charge?paid=true`. The charge page reads `?paid=true` and shows a success state. **Never trust this redirect as payment confirmation** — only the `charge.success` webhook is authoritative.

> ⚠️ **Channels**: Do not pass `apple_pay` or `google_pay` in the `channels` array — Paystack returns a 500 for unsupported channels on ZAR test accounts. Use `["card"]` only. Apple Pay and Google Pay surface automatically via Paystack Inline JS based on the customer’s device.

**Key fields:**
| Field | Notes |
|---|---|
| `email` | Customer email — use `"anonymous@scan2pay.co.za"` if not provided |
| `amount` | In cents. We validate: `variable` ≥ 100, ≤ 5,000,000 |
| `reference` | Our `STP…` reference — must be unique per transaction |
| `channels` | Paystack surfaces Apple Pay / Google Pay automatically based on device |
| `metadata` | Stored on the Paystack transaction, echoed back in webhook |

**Response:**
```json
{
  "status": true,
  "data": {
    "authorization_url": "https://checkout.paystack.com/abc123",
    "access_code": "abc123",
    "reference": "STP300001"
  }
}
```

**What we do with it:**
- Persist a `pending` transaction row in our DB **before** returning to the client
- Return `access_code` to the browser → frontend calls `popup.resumeTransaction(access_code)`
- Never mark a payment successful from the client callback — only from the webhook

---

### 2. Verify Transaction
**Why we use it:** (1) `reconcile_paystack` cron checks `pending` transactions older than 10 min in case the webhook was missed. (2) Belt-and-braces check after customer returns from Paystack.

```
GET /transaction/verify/:reference
```

> ⚠️ Mixed casing confirmed from live test: both `paid_at` (snake_case) AND `paidAt` (camelCase) are present in the response — use `paid_at`. `authorization` is `{}` empty object when transaction not yet paid — always guard before reading fields.

**Response (success):**
```json
{
  "status": true,
  "data": {
    "status": "success",
    "reference": "STP300001",
    "amount": 4500,
    "currency": "ZAR",
    "paid_at": "2026-09-06T09:00:00.000Z",
    "created_at": "2026-09-06T09:00:00.000Z",
    "channel": "card",
    "authorization": {
      "authorization_code": "AUTH_abc123",
      "card_type": "visa",
      "last4": "4081",
      "bank": "Test Bank",
      "reusable": true
    },
    "customer": {
      "id": 396619944,
      "email": "customer@example.com",
      "customer_code": "CUS_tx7tyx4z2gfftp4"
    },
    "metadata": {
      "merchant_id": "mch_001",
      "payment_code_id": "pc_001"
    }
  }
}
```

**Possible `data.status` values:** `success`, `failed`, `abandoned`, `pending`

**What we do with it:**
- `success` → mark transaction `success`, update `paid_at`, store `authorization_code`
- `failed` / `abandoned` → mark transaction `failed`
- `pending` → leave it, cron will retry

---

### 3. List Transactions
**Why we use it:** Merchant dashboard transaction history — infinite scroll, cursor-based.

```
GET /transaction?use_cursor=true&perPage=20&next=<cursor>
```

> ✅ Cursor pagination confirmed from live test. `meta.next` is `null` when no more pages.

**Response:**
```json
{
  "status": true,
  "data": [
    {
      "id": 6531530437,
      "domain": "test",
      "status": "abandoned",
      "reference": "STP300001",
      "amount": 4500,
      "currency": "ZAR",
      "paid_at": null,
      "created_at": "2026-09-06T10:48:51.000Z",
      "channel": "card",
      "gateway_response": "The transaction was not completed",
      "customer": {
        "id": 396619944,
        "email": "customer@example.com",
        "customer_code": "CUS_tx7tyx4z2gfftp4"
      },
      "authorization": {
        "authorization_code": null,
        "card_type": null,
        "last4": null,
        "bank": null,
        "reusable": false
      },
      "metadata": {
        "merchant_id": "mch_001",
        "payment_code_id": "pc_001"
      }
    }
  ],
  "meta": {
    "next": null,
    "previous": null,
    "perPage": 20
  }
}
```

**What we do with it:**
- Filter by `merchant_id` from our own DB — we don't pass merchant filter to Paystack, we store all transactions ourselves and query our DB for the merchant view
- `meta.next === null` → end of list, stop fetching

---

### 4. Charge Authorization (Returning Customers)
**Why we use it:** Once a customer has paid once, we store their `authorization_code`. Future payments skip card entry.

```
POST /transaction/charge_authorization
```

**Request body:**
```json
{
  "email": "customer@example.com",
  "amount": 4500,
  "authorization_code": "AUTH_abc123",
  "reference": "STP300002",
  "currency": "ZAR",
  "metadata": {
    "merchant_id": "mch_001",
    "payment_code_id": "pc_001"
  }
}
```

**Status:** Planned — Phase 2. Not yet implemented.

---

## Transfer APIs (Merchant Payouts)

### 5. Account Validation
**Why we use it:** Validate merchant bank account before storing. Prevents failed payouts.

```
POST /bank/resolve
```

**Request body:**
```json
{
  "account_number": "0123456789",
  "bank_code": "632005"
}
```

**Response:**
```json
{
  "status": true,
  "data": {
    "account_number": "0123456789",
    "account_name": "THANDI MOKOENA"
  }
}
```

**What we do with it:**
- Display `account_name` to merchant to confirm it's their account
- Store only last 4 digits of `account_number` (masked) in our DB
- Only create a transfer recipient if validation passes

**Common SA bank codes:**
| Bank | Code |
|---|---|
| Absa | 632005 |
| FNB | 250655 |
| Standard Bank | 051001 |
| Nedbank | 198765 |
| Capitec | 470010 |
| TymeBank | 678910 |
| African Bank | 430000 |

---

### 6. Create Transfer Recipient
**Why we use it:** Paystack requires a `recipient_code` to initiate a transfer. Created once per merchant bank account, stored permanently.

```
POST /transferrecipient
```

**Request body:**
```json
{
  "type": "nuban",
  "name": "Thandi Mokoena",
  "account_number": "0123456789",
  "bank_code": "632005",
  "currency": "ZAR"
}
```

> ⚠️ Live test findings: `type` is echoed back as `"basa"` (not `"nuban"`) for SA accounts. `details.account_name` is `null` in test mode — do not rely on it for display, use the name from `POST /bank/resolve` instead. Response uses camelCase for timestamps (`createdAt`, `updatedAt`).

**Response:**
```json
{
  "status": true,
  "data": {
    "recipient_code": "RCP_32cx31lv0eet4xh",
    "type": "basa",
    "name": "Thandi Mokoena",
    "active": true,
    "createdAt": "2026-09-04T20:58:40.000Z",
    "updatedAt": "2026-09-06T10:46:55.000Z",
    "details": {
      "account_number": "0123456789",
      "account_name": null,
      "bank_code": "632005",
      "bank_name": "Absa Bank Limited, South Africa"
    }
  }
}
```

**What we do with it:**
- Store `recipient_code` in `merchant_bank_accounts.recipient_code`
- Store `bank_name` from `details.bank_name` (full name e.g. `"Absa Bank Limited, South Africa"`)
- Never re-create for the same account — reuse the stored code
- Never expose `recipient_code` to the frontend

---

### 7. Initiate Transfer
**Why we use it:** Pay out a merchant's settled balance to their bank account.

```
POST /transfer
```

**Request body:**
```json
{
  "source": "balance",
  "amount": 420100,
  "recipient": "RCP_abc123xyz",
  "reason": "Scan2Pay weekly settlement — WD-ABC123",
  "currency": "ZAR",
  "reference": "WD-ABC123"
}
```

**Key fields:**
| Field | Notes |
|---|---|
| `source` | Always `"balance"` — transfers from our Paystack balance |
| `amount` | In cents |
| `recipient` | The `recipient_code` from step 6 |
| `reason` | Shown on the merchant's bank statement |
| `reference` | Our withdrawal reference `WD-…` — must be unique |

**Response:**
```json
{
  "status": true,
  "data": {
    "transfer_code": "TRF_abc123",
    "status": "otp",
    "amount": 420100,
    "recipient": "RCP_abc123xyz"
  }
}
```

**Transfer OTP:**
- Paystack requires OTP confirmation for transfers by default — initial status is `"otp"` not `"pending"`
- Production: call `POST /transfer/finalize_transfer` with the OTP sent to the Paystack account owner
- **Dev/test**: disable in Paystack dashboard under *Settings → Transfers → Require OTP for transfers*. Controlled via `DEV_TRANSFER_OTP=False` env var — when false, skip finalize and treat `pending` as initial status

**What we do with it:**
- Store `transfer_code` on the withdrawal row
- If `status == "otp"` and `DEV_TRANSFER_OTP=True` → call finalize endpoint below
- Final status comes via webhook

---

### 8. Finalize Transfer (OTP)
**Why we use it:** Required in production to confirm a transfer after OTP is received.

```
POST /transfer/finalize_transfer
```

**Request body:**
```json
{
  "transfer_code": "TRF_abc123",
  "otp": "123456"
}
```

**Response:**
```json
{
  "status": true,
  "data": {
    "transfer_code": "TRF_abc123",
    "status": "pending",
    "amount": 420100
  }
}
```

After finalization, status moves to `pending` and final outcome arrives via `transfer.success` / `transfer.failed` webhook.

---

### 9. Fetch Transfer
**Why we use it:** Poll transfer status if webhook was missed, or for admin visibility.

```
GET /transfer/:transfer_code
```

**Response `data.status` values:** `pending`, `otp`, `success`, `failed`, `reversed`

**Error shape (confirmed from live test):**
```json
{
  "status": false,
  "message": "Transfer ID/code specified is invalid",
  "type": "validation_error",
  "code": "invalid_params"
}
```

> ⚠️ `POST /transfer` is blocked on Paystack starter/test accounts with error `transfer_unavailable`. Transfer endpoints can only be fully tested against a registered business (production) account.

Used by admin routes and the `build_settlements` cron. Not yet implemented.

---

## Webhooks

### Incoming Events We Handle

| Event | Trigger | Our Action |
|---|---|---|
| `charge.success` | Customer payment confirmed | Mark transaction `success`, update `paid_at`, set single-use code `active=false` |
| `transfer.success` | Payout to merchant completed | Mark withdrawal `paid`, stamp `paid_at` |
| `transfer.failed` | Payout failed | Mark withdrawal `failed`, alert admin |
| `transfer.reversed` | Payout reversed by bank | Mark withdrawal `reversed`, alert admin |

### Signature Verification

Every incoming webhook must be verified before processing. The `PAYSTACK_SECRET_KEY` is the HMAC key — there is no separate webhook secret.

```python
import hmac, hashlib

def verify_webhook(raw_body: bytes, signature_header: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        raw_body,           # RAW bytes — before any JSON parsing
        hashlib.sha512,
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)
```

- Signature is in the `x-paystack-signature` request header
- Return `200` immediately after verification — Paystack retries if it doesn't get a fast response
- Insert into `webhook_events` first — the `UNIQUE(provider, event_type, provider_reference)` index makes replays no-ops
- Process business logic after acknowledging

### `charge.success` Payload Shape

> ⚠️ `metadata` can be `0`, `null`, or an object — always guard: `metadata = data.get("metadata") or {}`

```json
{
  "event": "charge.success",
  "data": {
    "id": 123456,
    "reference": "STP300001",
    "amount": 4500,
    "currency": "ZAR",
    "status": "success",
    "paid_at": "2026-09-06T09:00:00.000Z",
    "channel": "card",
    "authorization": {
      "authorization_code": "AUTH_abc123",
      "card_type": "visa",
      "last4": "4081",
      "bank": "Test Bank",
      "reusable": true
    },
    "customer": {
      "email": "customer@example.com",
      "customer_code": "CUS_abc123"
    },
    "metadata": {
      "merchant_id": "mch_001",
      "payment_code_id": "pc_001",
      "single_use": false
    }
  }
}
```

### `transfer.success` / `transfer.failed` / `transfer.reversed` Payload Shape

> ⚠️ Mixed casing in transfer webhooks: `createdAt`/`updatedAt` are camelCase, `transfer_code`/`recipient_code` are snake_case. Handle both.

```json
{
  "event": "transfer.success",
  "data": {
    "transfer_code": "TRF_abc123",
    "reference": "WD-ABC123",
    "amount": 420100,
    "currency": "ZAR",
    "status": "success",
    "createdAt": "2026-09-06T09:00:00.000Z",
    "updatedAt": "2026-09-06T09:05:00.000Z",
    "recipient": {
      "recipient_code": "RCP_abc123xyz",
      "name": "Thandi Mokoena",
      "details": {
        "account_number": "0123456789",
        "bank_name": "Absa"
      }
    }
  }
}
```

---

## Apple Pay

### Domain Registration
Must register `scan2pay.site` with Paystack before going live. Only needs to be done once.

```
POST /apple-pay/domain
```

**Request body:**
```json
{
  "domainName": "scan2pay.site"
}
```

**Response:**
```json
{
  "status": true,
  "message": "Domain registered successfully"
}
```

- After registration, Apple Pay surfaces automatically in Paystack Inline when the customer is on a supported Apple device/browser
- No additional frontend code needed — Paystack handles it via the `channels` array in initialize

---

## Capitec Pay

### Requery
Used to check the status of a Capitec Pay transaction if the webhook was missed.

```
GET /charge/:reference
```

**Response:**
```json
{
  "status": true,
  "data": {
    "reference": "STP300001",
    "status": "success",
    "amount": 4500,
    "currency": "ZAR"
  }
}
```

- Same `GET /charge/:reference` endpoint used for all channel types
- Capitec Pay is surfaced automatically by Paystack Inline — no separate integration needed
- Status values same as card: `success`, `failed`, `abandoned`, `pending`

---

## Fee Calculation

Snapshot pricing on every transaction — old receipts never change when pricing does.

```
platform_fee_cents = round(amount_cents * plan_percent / 100)
provider_fee_cents = round(amount_cents * 2.9 / 100) + 100   # Paystack ZAR rate
net_cents          = amount_cents - platform_fee_cents - provider_fee_cents
```

**Worked example — R45.00 on plan_free (2.5%):**
```
amount        4500
platform       113   (4500 × 2.5%)
provider       231   (4500 × 2.9% = 131 + 100 fixed)
net           4156
```

---

## Test Cards (ZAR)

| Scenario | Card number | Expiry | CVV |
|---|---|---|---|
| Success | 4084 0840 8408 4081 | Any future | 408 |
| Failure | 4084 0800 0000 5408 | Any future | 408 |
| Insufficient funds | 4084 0840 8408 4081 | Any future | 000 |

---

## Reconciliation Strategy

1. **Primary** — `charge.success` webhook marks transaction `success` in real time
2. **Fallback** — `reconcile_paystack` cron runs every 15 min, calls `GET /transaction/verify/:reference` for any `pending` transaction older than 10 min
3. **Manual** — admin can trigger a verify from the admin panel (Phase 2)

Missed webhook is caught within 15 minutes at most.

---

## What's Not Yet Implemented

| Feature | Endpoint | Priority |
|---|---|---|
| Payment initialise route | `POST /payments/initialise` | **Next** |
| Webhook handler | `POST /webhooks/paystack` | **Next** |
| Bank account validation | `POST /bank/resolve` | Withdrawals phase |
| Create transfer recipient | `POST /transferrecipient` | Withdrawals phase |
| Initiate transfer | `POST /transfer` | Withdrawals phase |
| Charge authorization | `POST /transaction/charge_authorization` | Phase 2 |
| Apple Pay domain registration | `POST /apple-pay/domain` | Before go-live |
| Refunds | `POST /refund` | Phase 2 |
