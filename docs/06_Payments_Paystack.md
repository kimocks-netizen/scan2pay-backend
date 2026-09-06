# Paystack API Reference — Scan2Pay

> Living document. Updated as we integrate each endpoint.
> All amounts are in **cents (ZAR)**. R1.00 = 100 cents.
> All server calls use `Authorization: Bearer <PAYSTACK_SECRET_KEY>`.
> The secret key **never** leaves the server.

---

## Authentication

```
Authorization: Bearer sk_test_5007f89004bd371737871acffe64a98fd2ec3a36
```

- `PAYSTACK_SECRET_KEY` — server-side only (Lambda env via SSM)
- `PAYSTACK_PUBLIC_KEY` — returned to the browser for Paystack Inline JS
- `PAYSTACK_WEBHOOK_SECRET` — HMAC-SHA512 signature verification on incoming webhooks

---

## Base URL

```
https://api.paystack.co
```

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
  "channels": ["card", "apple_pay", "google_pay"],
  "metadata": {
    "merchant_id": "mch_001",
    "payment_code_id": "pc_001",
    "single_use": false
  }
}
```

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
- Return `authorization_url` to the browser → customer is redirected to Paystack checkout
- Never mark a payment successful from the client callback — only from the webhook

---

### 2. Verify Transaction
**Why we use it:** Two places — (1) the `reconcile_paystack` cron job checks `pending` transactions older than 10 min in case the webhook was missed, (2) optionally after the customer returns from the Paystack redirect as a belt-and-braces check.

```
GET /transaction/verify/:reference
```

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
    "authorization": {
      "authorization_code": "AUTH_abc123",
      "card_type": "visa",
      "last4": "4081",
      "bank": "Test Bank"
    },
    "customer": {
      "email": "customer@example.com"
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
- If `success` → mark our transaction `success`, update `paid_at`, store `authorization_code` for future charges
- If `failed` / `abandoned` → mark our transaction `failed`
- If still `pending` → leave it, cron will retry

---

### 3. Charge Authorization (Returning Customers)
**Why we use it:** Once a customer has paid once, we store their `authorization_code`. Future payments can be charged without them re-entering card details — useful for repeat taxi fares or regular customers.

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

### 4. Account Validation
**Why we use it:** Before storing a merchant's bank account, we validate it against Paystack to confirm the account number and name are correct. Prevents failed payouts.

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
- Display `account_name` to the merchant to confirm it's their account
- Store only the last 4 digits of `account_number` (masked) in our DB
- Only proceed to create a transfer recipient if validation passes

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

### 5. Create Transfer Recipient
**Why we use it:** Paystack requires a `recipient_code` to initiate a transfer. We create one per merchant bank account and store it — we never re-create it for the same account.

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

**Response:**
```json
{
  "status": true,
  "data": {
    "recipient_code": "RCP_abc123xyz",
    "type": "nuban",
    "name": "Thandi Mokoena",
    "details": {
      "account_number": "0123456789",
      "account_name": "THANDI MOKOENA",
      "bank_code": "632005",
      "bank_name": "Absa"
    }
  }
}
```

**What we do with it:**
- Store `recipient_code` in `merchant_bank_accounts.recipient_code`
- This code is used in every future transfer to this account
- Never expose `recipient_code` to the frontend

---

### 6. Initiate Transfer
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
| `recipient` | The `recipient_code` from step 5 |
| `reason` | Shown on the merchant's bank statement |
| `reference` | Our withdrawal reference `WD-…` — must be unique |

**Response:**
```json
{
  "status": true,
  "data": {
    "transfer_code": "TRF_abc123",
    "status": "pending",
    "amount": 420100,
    "recipient": "RCP_abc123xyz"
  }
}
```

**What we do with it:**
- Store `transfer_code` on the withdrawal row
- Status starts as `pending` — final status comes via webhook
- ⚠️ Test mode may require OTP confirmation — check Paystack dashboard settings

---

### 7. Fetch Transfer
**Why we use it:** Poll the status of a transfer if the webhook was missed, or for admin visibility.

```
GET /transfer/:transfer_code
```

**Response `data.status` values:** `pending`, `success`, `failed`, `reversed`

**Status:** Used by admin routes and the `build_settlements` cron. Not yet implemented.

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
Every incoming webhook must be verified before processing:

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

- Return `200` immediately after verification — Paystack retries if it doesn't get a fast response
- Insert into `webhook_events` first — the `UNIQUE(provider, event_type, provider_reference)` index makes replays no-ops
- Process the business logic after acknowledging

### `charge.success` Payload Shape
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

### `transfer.success` / `transfer.failed` Payload Shape
```json
{
  "event": "transfer.success",
  "data": {
    "transfer_code": "TRF_abc123",
    "reference": "WD-ABC123",
    "amount": 420100,
    "currency": "ZAR",
    "status": "success",
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

This means a missed webhook is caught within 15 minutes at most.

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
| Refunds | `POST /refund` | Phase 2 |
