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
- `PAYSTACK_PUBLIC_KEY` — used in the browser for Paystack Inline JS
- **Webhook secret** — Paystack does NOT have a separate webhook secret. `PAYSTACK_SECRET_KEY` IS the HMAC-SHA512 key. SSM param `PAYSTACK_WEBHOOK_SECRET` must equal `PAYSTACK_SECRET_KEY`.

---

## Base URL

```
https://api.paystack.co
```

---

## Frontend Integration — Paystack Inline JS

We use **Paystack Inline JS** (popup mode). The backend initializes the transaction and returns `access_code`. The frontend opens the popup using `newTransaction`.

```ts
// Dynamic import required — @paystack/inline-js accesses window at module level (SSR crash)
const { default: PaystackPop } = await import("@paystack/inline-js");
const popup = new PaystackPop();
popup.newTransaction({
  access_code: "abc123",   // from our backend
  onSuccess: () => { /* mark paid */ },
  onClose: () => { /* back to enter screen */ },
});
```

**Key rules:**
- Always dynamically import — never static import (crashes Next.js SSR)
- Use `newTransaction({ access_code })` not `resumeTransaction(code)` — only `newTransaction` supports `onSuccess`/`onClose` callbacks
- **Never trust the popup `onSuccess` as payment confirmation** — it fires client-side and can be faked. Only the `charge.success` webhook is authoritative. `onSuccess` is used only for immediate UI feedback.
- The 1.5s poll on `GET /payments/:id` is the fallback for QR-scan payments (customer pays on their own device)

---

## ⚠️ Known Gotchas (confirmed from live testing)

| Issue | Detail |
|---|---|
| `apple_pay` / `google_pay` in `channels` | Paystack returns **500** on ZAR test accounts. Use `["card"]` only. Apple/Google Pay surface automatically via Inline JS on supported devices once account is verified. |
| Boolean values in `metadata` | Paystack returns **500**. All metadata values must be strings — use `"true"`/`"false"` not `true`/`false`. |
| `metadata` field in webhook | Can be `0`, `null`, or an object. Always guard: `metadata = data.get("metadata") or {}` |
| Mixed casing in verify response | Both `paid_at` (snake) and `paidAt` (camel) present — use `paid_at` |
| `authorization` when not paid | Returns `{}` empty object — always guard before reading fields |
| `type` in transfer recipient | Echoed back as `"basa"` not `"nuban"` for SA accounts |
| `POST /bank/resolve` in test mode | Returns HTTP 404 with empty body — cannot verify real accounts in test. Expected behaviour. Works in prod. |
| `account_name` in transfer recipient | `null` in test mode — use name from `POST /bank/resolve` in prod instead |
| `POST /transfer` | Blocked on starter/test accounts with `transfer_unavailable`. Prod account only. |
| Webhook `charge.success` reference | `data.reference` = our `STP…` reference (what we passed to initialize). We store this as `paystack_reference` on the transaction and look it up by that column. |

---

## Payment APIs

### 1. Initialize Transaction ✅ implemented

```
POST /transaction/initialize
```

**Request:**
```json
{
  "email": "customer@example.com",
  "amount": 4500,
  "currency": "ZAR",
  "reference": "STP000021",
  "callback_url": "https://scan2pay.site/charge?paid=true",
  "channels": ["card"],
  "metadata": {
    "merchant_id": "mch_001",
    "payment_code_id": "pc_001",
    "single_use": "true",
    "txn_id": "txn_000021"
  }
}
```

**Response:**
```json
{
  "status": true,
  "data": {
    "authorization_url": "https://checkout.paystack.com/abc123",
    "access_code": "abc123",
    "reference": "STP000021"
  }
}
```

**Our flow:**
1. Insert `pending` transaction in DB **before** calling Paystack
2. Call Paystack → get `access_code`
3. Store `paystack_reference = result["reference"]` on the transaction
4. Return `access_code` to frontend
5. Frontend calls `popup.newTransaction({ access_code })`

---

### 2. Verify Transaction ✅ used by reconcile cron

```
GET /transaction/verify/:reference
```

**Response (success):**
```json
{
  "status": true,
  "data": {
    "status": "success",
    "reference": "STP000021",
    "amount": 4500,
    "paid_at": "2026-09-06T12:55:15.000Z",
    "channel": "card",
    "authorization": {
      "authorization_code": "AUTH_abc123",
      "card_type": "visa",
      "last4": "4081",
      "reusable": true
    },
    "metadata": { "merchant_id": "mch_001", "txn_id": "txn_000021" }
  }
}
```

**`data.status` values:** `success`, `failed`, `abandoned`, `pending`

---

### 3. List Transactions ✅ used by reconcile cron

```
GET /transaction?use_cursor=true&perPage=20&next=<cursor>
```

`meta.next === null` means end of list.

---

### 4. Charge Authorization — planned (Phase 2)

```
POST /transaction/charge_authorization
```

Skip card entry for returning customers using stored `authorization_code`.
Column `authorization_code` already exists on `transactions` table (migration 010).
Not yet implemented.

---

## Transfer APIs (Merchant Payouts)

### 5. Account Validation ⚠️ test mode returns 404

```
POST /bank/resolve
```

**Request:**
```json
{ "account_number": "62845141407", "bank_code": "250655" }
```

**Test mode behaviour:** Returns HTTP 404 with empty body — Paystack cannot verify real accounts in test mode. This is expected. In production this returns the account holder name.

**Production response:**
```json
{ "status": true, "data": { "account_number": "62845141407", "account_name": "ACCOUNT HOLDER NAME" } }
```

**Our flow:** Call this before saving bank details. Show `account_name` to merchant to confirm it's their account. If 404 in prod → account number or bank code is wrong.

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

### 6. Create Transfer Recipient ✅ confirmed working in test mode

```
POST /transferrecipient
```

**Request:**
```json
{ "type": "nuban", "name": "Demo Merchant", "account_number": "62845141407", "bank_code": "250655", "currency": "ZAR" }
```

**Confirmed response (test mode, FNB account):**
```json
{
  "status": true,
  "message": "Transfer recipient created successfully",
  "data": {
    "active": true,
    "currency": "ZAR",
    "domain": "test",
    "name": "Demo Merchant",
    "recipient_code": "RCP_ag9fgil66ki40vu",
    "type": "basa",
    "details": {
      "account_number": "62845141407",
      "account_name": null,
      "bank_code": "250655",
      "bank_name": "First National Bank"
    }
  }
}
```

**Key observations from live test:**
- `type` is echoed back as `"basa"` not `"nuban"` for SA accounts — this is correct, do not treat as an error
- `account_name` is `null` in test mode — in prod use `POST /bank/resolve` name instead
- `recipient_code` (`RCP_...`) is what we store and use for all future transfers to this merchant
- Works fully in test mode — no prod account needed

Store `recipient_code` on the merchant record. Never expose to frontend.

---

### 7. Initiate Transfer ⛔ prod only

```
POST /transfer
```

**Request:**
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

**Response:**
```json
{ "status": true, "data": { "transfer_code": "TRF_abc123", "status": "otp" } }
```

Initial status is `"otp"` — requires OTP finalization in prod. Disable OTP in Paystack dashboard for dev testing.

---

### 8. Finalize Transfer (OTP) — prod only

```
POST /transfer/finalize_transfer
```

```json
{ "transfer_code": "TRF_abc123", "otp": "123456" }
```

After finalization, status moves to `pending`. Final outcome via webhook.

---

### 9. Fetch Transfer ✅ implemented in service

```
GET /transfer/:transfer_code
```

Status values: `pending`, `otp`, `success`, `failed`, `reversed`

---

## Platform Balance ✅ confirmed working in test mode

```
GET /balance
```

**Confirmed response (test mode):**
```json
{
  "status": true,
  "message": "Balances retrieved",
  "data": [{ "currency": "ZAR", "balance": 59987 }]
}
```

`balance` is in **cents**. R599.87 in the example above.
This is the **platform's** Paystack balance — what Scan2Pay has available to pay out to merchants.
Used by the admin dashboard to show available settlement funds.
Not exposed to merchants — admin only.

---

## Webhooks ✅ implemented

### Handler: `POST /webhooks/paystack`

1. Verify HMAC-SHA512 signature (`x-paystack-signature` header, key = `PAYSTACK_SECRET_KEY`)
2. Insert into `webhook_events` — `UNIQUE(provider, event_type, provider_reference)` makes replays no-ops
3. Handle event — wrapped in try/except so bugs never return non-200 to Paystack

### Events handled

| Event | Action |
|---|---|
| `charge.success` | Mark transaction `success`, store `paid_at` + `authorization_code`, deactivate single-use codes, increment `payments` counter |
| `transfer.success` | Mark withdrawal `paid` |
| `transfer.failed` | Mark withdrawal `failed` |
| `transfer.reversed` | Mark withdrawal `reversed` |

### Signature verification

```python
import hmac, hashlib

expected = hmac.new(
    secret.encode(),
    raw_body,        # RAW bytes — before any JSON parsing
    hashlib.sha512,
).hexdigest()
return hmac.compare_digest(expected, signature_header)
```

### `charge.success` payload

```json
{
  "event": "charge.success",
  "data": {
    "reference": "STP000021",
    "amount": 3500,
    "paid_at": "2026-09-06T12:55:15.000Z",
    "channel": "card",
    "authorization": { "authorization_code": "AUTH_abc123", "card_type": "visa", "last4": "4081" },
    "customer": { "email": "customer@example.com" },
    "metadata": { "merchant_id": "mch_004", "payment_code_id": "pc_006", "single_use": "true", "txn_id": "txn_000021" }
  }
}
```

### `transfer.*` payload

```json
{
  "event": "transfer.success",
  "data": {
    "transfer_code": "TRF_abc123",
    "reference": "WD-ABC123",
    "amount": 420100,
    "status": "success",
    "recipient": { "recipient_code": "RCP_abc123xyz", "name": "Thandi Mokoena" }
  }
}
```

---

## Apple Pay

Register domain once before go-live:

```
POST /apple-pay/domain
{ "domainName": "scan2pay.site" }
```

After registration, Apple Pay surfaces automatically in Paystack Inline JS on supported devices. No additional frontend code needed.

---

## Capitec Pay

Surfaces automatically via Paystack Inline JS. Confirm exact channel name with Paystack support before adding to `channels` array. Do not guess.

---

## Fee Calculation

```python
platform_fee_cents = round(amount_cents * plan_percent / 100)
provider_fee_cents = round(amount_cents * 2.9 / 100) + 100   # Paystack ZAR rate
net_cents          = amount_cents - platform_fee_cents - provider_fee_cents
```

**Example — R35.00 on plan_free (2.5%):**
```
amount        3500
platform        88   (3500 × 2.5%)
provider       202   (3500 × 2.9% = 102 + 100 fixed)
net           3210
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
3. **Manual** — admin can trigger verify from admin panel (not yet built)

Missed webhook is caught within 15 minutes at most.

---

## What's Not Yet Implemented

| Feature | Endpoint | Test mode | Priority |
|---|---|---|---|
| Bank account validation | `POST /bank/resolve` | ⚠️ 404 in test, works in prod | Next — settings page |
| Save bank details + create recipient | `PATCH /merchants/me` + `POST /transferrecipient` | ✅ recipient works in test | Next — settings page |
| Merchant balance | `GET /merchants/me/balance` | ✅ can build now | Next — withdrawals page |
| Withdrawal request | `POST /merchants/me/withdrawals` | ✅ can build now | Next |
| Platform balance (admin) | `GET /balance` | ✅ confirmed working | Next — admin dashboard |
| Initiate transfer (admin approves) | `POST /transfer` | ⛔ blocked in test | Build now, test on prod |
| Finalize transfer OTP | `POST /transfer/finalize_transfer` | ⛔ blocked in test | Build now, test on prod |
| Apple Pay domain registration | `POST /apple-pay/domain` | N/A | Before go-live |
| Charge authorization (returning customers) | `POST /transaction/charge_authorization` | ✅ works in test | Phase 2 |
| Refunds | `POST /refund` | ✅ works in test | Phase 2 |
| Paystack Billing Plans (merchant subscriptions) | `POST /plan` + `POST /subscription` | ✅ works in test | Phase 2 |
