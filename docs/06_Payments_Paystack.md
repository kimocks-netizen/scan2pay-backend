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
| `GET /bank/resolve` in test mode | Returns `{ status: false, message: "Please supply one of the following valid currencies: NGN, USD, GHS, KES" }` — ZAR not supported in test mode. Works in prod only. |
| `POST /bank/validate` in test mode | Responds but always returns `verified: false`, `accountHolderMatch: false`, `accountAcceptsCredits: false` regardless of real credentials. Identity verification requires prod mode. |
| `POST /bank/resolve` in test mode | It is actually **GET** with query params: `GET /bank/resolve?account_number=X&bank_code=Y`. Returns HTTP 404 with empty body in test mode — cannot verify real accounts. Works in prod. |
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
GET /bank/resolve?account_number=62845141407&bank_code=250655
```

> ⚠️ It is a **GET** with query params — NOT a POST with a body.

**Request:**
```bash
curl "https://api.paystack.co/bank/resolve?account_number=62845141407&bank_code=250655" \
  -H "Authorization: Bearer $PAYSTACK_SECRET_KEY"
```

**Confirmed prod response:**
```json
{
  "status": true,
  "message": "Account number resolved",
  "data": {
    "account_number": "0022728151",
    "account_name": "WES GIBBONS"
  }
}
```

**Test mode behaviour:** Returns HTTP 404 with empty body — cannot verify real accounts in test. Expected. Works in prod only.

**Our flow:**
- In prod: call this first → show `account_name` to merchant to confirm it’s their account → then save
- In test: skip this call, use `account_holder` name from the request directly
- If 404 in prod → wrong account number or bank code

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

### 5b. Account Validation (full KYC) ✅ confirmed working in test mode

```
POST /bank/validate
```

More powerful than `/bank/resolve` — cross-checks account number against SA ID number and confirms they match. This is automated KYC.

**Request:**
```json
{
  "bank_code": "250655",
  "country_code": "ZA",
  "account_number": "62845141407",
  "account_name": "Demo Merchant",
  "account_type": "personal",
  "document_type": "identityNumber",
  "document_number": "9001015009087"
}
```

`account_type`: `"personal"` or `"business"`
`document_type`: `"identityNumber"` (SA ID) or `"passportNumber"`

**Confirmed response (test mode — mismatched ID, expected false):**
```json
{
  "status": true,
  "message": "Personal Account Verification attempted",
  "data": {
    "verified": false,
    "accountAcceptsDebits": true,
    "accountAcceptsCredits": false,
    "accountOpenForMoreThanThreeMonths": true,
    "accountHolderMatch": false,
    "verificationMessage": "We got account verification result as refuted"
  }
}
```

**Confirmed prod response (matching ID):**
```json
{
  "status": true,
  "message": "Personal Account Verification attempted",
  "data": {
    "accountAcceptsDebits": true,
    "accountAcceptsCredits": true,
    "accountHolderMatch": true,
    "accountOpenForMoreThanThreeMonths": true,
    "accountOpen": true,
    "verified": true,
    "verificationMessage": "Account is verified successfully"
  }
}
```

**What each field means:**
| Field | Meaning |
|---|---|
| `verified` | Overall pass/fail — the only field you need to check |
| `accountHolderMatch` | SA ID number matches the account holder |
| `accountAcceptsCredits` | Account can receive transfers (critical for payouts) |
| `accountAcceptsDebits` | Account can be debited |
| `accountOpen` | Account is active |
| `accountOpenForMoreThanThreeMonths` | Account age check |

**Our flow (replaces manual admin KYC):**
1. Merchant enters bank details + SA ID number on settings page
2. Backend calls `POST /bank/validate`
3. `verified: true` + `accountAcceptsCredits: true` → auto-approve, save `paystack_recipient_code`
4. `verified: false` → return error to merchant with `verificationMessage`
5. `accountAcceptsCredits: false` → block — account cannot receive transfers
6. Admin KYC only needed as fallback for edge cases

**In test mode:** Works but always returns `verified: false` with dummy IDs. Use a real SA ID in prod testing.

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
  "amount": 45000,
  "recipient": "RCP_ag9fgil66ki40vu",
  "reason": "Scan2Pay weekly settlement — WD-ABC123",
  "reference": "WD-ABC123"
}
```

> Note: `currency` is NOT required in the request — Paystack infers it from the recipient.

**Confirmed response:**
```json
{
  "status": true,
  "message": "Transfer has been queued",
  "data": {
    "transfer_code": "TRF_v5tip3zx8nna9o78",
    "reference": "WD-ABC123",
    "amount": 45000,
    "currency": "ZAR",
    "source": "balance",
    "reason": "Scan2Pay weekly settlement — WD-ABC123",
    "status": "success",
    "recipient": 56824902,
    "failures": null,
    "transferred_at": null,
    "transfersessionid": [],
    "createdAt": "2026-09-09T10:32:40.000Z",
    "updatedAt": "2026-09-09T10:32:40.000Z"
  }
}
```

**Key observations:**
- `message` is `"Transfer has been queued"` — not `"otp"` as previously assumed. OTP only applies when OTP is enabled on the Paystack account. Disable OTP in Paystack dashboard Settings → Preferences for automated payouts.
- `status` in `data` can be `"success"`, `"pending"`, or `"otp"` depending on account settings
- `transfer_code` (`TRF_...`) is what we store on the withdrawal row and use to look up status
- `reference` echoes back our `WD-...` reference — use this in webhook to find the withdrawal
- `recipient` in response is Paystack's internal integer ID, not our `RCP_...` code — store `transfer_code` not `recipient`
- `transferred_at` is `null` at creation — set by Paystack when money actually moves

**What to store on withdrawal row after this call:**
```python
db.table("withdrawals").update({
    "transfer_code": result["transfer_code"],
    "status": "approved",
}).eq("id", withdrawal_id).execute()
```
Webhook `transfer.success` will flip it to `paid`.

---

### 8. Finalize Transfer (OTP) — only needed if OTP enabled on Paystack account

```
POST /transfer/finalize_transfer
```

> Disable OTP in Paystack dashboard → Settings → Preferences to avoid needing this for automated payouts.

**Request:**
```json
{ "transfer_code": "TRF_vsyqdmlzble3uii", "otp": "928783" }
```

**OTP is sent to the business phone number registered on the Paystack account (your phone, not the merchant's).**

**Confirmed response:**
```json
{
  "status": true,
  "message": "Transfer has been queued",
  "data": {
    "transfer_code": "TRF_zuirlnr9qblgfko",
    "reference": "WD-ABC123",
    "amount": 45000,
    "status": "success",
    "source": "balance",
    "failures": null,
    "transferred_at": null,
    "createdAt": "2026-09-09T10:02:55.000Z",
    "updatedAt": "2026-09-09T10:12:05.000Z"
  }
}
```

Same shape as `POST /transfer` response. After finalization, final outcome via `transfer.success` or `transfer.failed` webhook.

---

### 9. Fetch Transfer ✅ confirmed response

```
GET /transfer/:transfer_code
```

**Confirmed response:**
```json
{
  "status": true,
  "message": "Transfer retrieved",
  "data": {
    "transfer_code": "TRF_fpmd0l8uta8upow7",
    "reference": "WD-ABC123",
    "amount": 45000,
    "currency": "ZAR",
    "status": "success",
    "reason": "Scan2Pay weekly settlement — WD-ABC123",
    "failures": null,
    "transferred_at": null,
    "fee_charged": 0,
    "fees_breakdown": null,
    "gateway_response": null,
    "recipient": {
      "recipient_code": "RCP_ag9fgil66ki40vu",
      "name": "Demo Merchant",
      "details": {
        "account_number": "62845141407",
        "account_name": "Demo Merchant",
        "bank_code": "250655",
        "bank_name": "First National Bank"
      }
    },
    "session": { "provider": null, "id": null },
    "createdAt": "2026-09-09T08:32:21.000Z",
    "updatedAt": "2026-09-09T08:34:07.000Z"
  }
}
```

Status values: `pending`, `otp`, `success`, `failed`, `reversed`
Used by the reconcile cron to check status of `approved` withdrawals that haven't received a webhook.

---

### 10. Verify Transfer ✅ confirmed response

```
GET /transfer/verify/:reference
```

Look up a transfer by **our reference** (`WD-...`) instead of Paystack's `transfer_code`. Useful for reconciliation.

**Confirmed response:** Same shape as `GET /transfer/:transfer_code` above.

---

### 11. List Transfers ✅ confirmed response

```
GET /transfer?page=1&perPage=50
```

**Confirmed response:**
```json
{
  "status": true,
  "message": "Transfers retrieved",
  "data": [
    {
      "transfer_code": "TRF_1ptvuv321ahaa7q",
      "reference": "WD-ABC123",
      "amount": 45000,
      "currency": "ZAR",
      "status": "success",
      "reason": "Scan2Pay weekly settlement",
      "recipient": {
        "recipient_code": "RCP_ag9fgil66ki40vu",
        "name": "Demo Merchant",
        "details": { "account_number": "62845141407", "bank_name": "First National Bank" }
      },
      "createdAt": "2026-09-09T17:21:54.000Z",
      "updatedAt": "2026-09-09T17:21:54.000Z"
    }
  ],
  "meta": { "total": 1, "skipped": 0, "perPage": 50, "page": 1, "pageCount": 1 }
}
```

Used by admin dashboard to show all outgoing transfers. Paginated.

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

### Webhook payloads — confirmed

#### `transfer.success`
```json
{
  "event": "transfer.success",
  "data": {
    "transfer_code": "TRF_v5tip3zx8nna9o78",
    "reference": "WD-ABC123",
    "amount": 45000,
    "currency": "ZAR",
    "status": "success",
    "reason": "Scan2Pay weekly settlement — WD-ABC123",
    "failures": null,
    "transferred_at": null,
    "fee_charged": 0,
    "gateway_response": null,
    "recipient": {
      "recipient_code": "RCP_ag9fgil66ki40vu",
      "name": "Demo Merchant",
      "details": {
        "account_number": "62845141407",
        "account_name": null,
        "bank_code": "250655",
        "bank_name": "First National Bank"
      }
    },
    "session": { "provider": null, "id": null },
    "createdAt": "2026-09-09T10:32:40.000Z",
    "updatedAt": "2026-09-09T10:32:40.000Z"
  }
}
```

**How we handle it:**
```python
reference = data["reference"]   # our WD-... reference
transfer_code = data["transfer_code"]
db.table("withdrawals").update({"status": "paid", "paid_at": now}).eq("reference", reference).execute()
```

---

#### `transfer.failed`
```json
{
  "event": "transfer.failed",
  "data": {
    "transfer_code": "TRF_chs98y5rykjb47w",
    "reference": "WD-ABC123",
    "amount": 45000,
    "currency": "ZAR",
    "status": "failed",
    "failures": null,
    "transferred_at": null,
    "recipient": {
      "recipient_code": "RCP_ag9fgil66ki40vu",
      "name": "Demo Merchant",
      "details": {
        "account_number": "62845141407",
        "account_name": "Demo Merchant",
        "bank_code": "250655",
        "bank_name": "First National Bank"
      }
    },
    "session": { "provider": "nip", "id": "74849400998877667" },
    "created_at": "2026-09-09T10:32:15.000Z",
    "updated_at": "2026-09-09T10:41:21.000Z"
  }
}
```

**Key observation:** `failures` is `null` even on failed transfers — do not rely on it for failure reason. Use `status: "failed"` only.

**How we handle it:**
```python
reference = data["reference"]
db.table("withdrawals").update({"status": "failed"}).eq("reference", reference).execute()
# alert admin — money stays in Paystack balance, needs manual retry
```

---

#### `transfer.reversed`
```json
{
  "event": "transfer.reversed",
  "data": {
    "transfer_code": "TRF_js075pj9u07f34l",
    "reference": "WD-ABC123",
    "amount": 45000,
    "currency": "ZAR",
    "status": "reversed",
    "failures": null,
    "transferred_at": "2026-09-09T07:14:00.000Z",
    "recipient": {
      "recipient_code": "RCP_ag9fgil66ki40vu",
      "name": "Demo Merchant"
    },
    "session": { "provider": "nip", "id": "110006200324071331002061586801" },
    "created_at": "2026-09-09T07:13:31.000Z",
    "updated_at": "2026-09-09T07:14:55.000Z"
  }
}
```

**Reversed = money was sent but bounced back** (wrong account, account closed, etc.). Money returns to Paystack balance.

**How we handle it:**
```python
reference = data["reference"]
db.table("withdrawals").update({"status": "reversed"}).eq("reference", reference).execute()
# alert admin — money is back in Paystack balance, merchant needs to update bank details
```

**Important:** Add `reversed` to the withdrawals status check constraint:
```sql
CHECK (status IN ('pending', 'approved', 'paid', 'rejected', 'failed', 'reversed'))
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
| Bank account validation | `GET /bank/resolve` | ⚠️ ZAR unsupported in test | Next — settings page |
| Full KYC validation | `POST /bank/validate` | ⚠️ always false in test | Next — settings page |
| Save bank details + create recipient | `PATCH /merchants/me/payout-account` | ✅ recipient works in test | Next |
| Merchant balance | `GET /merchants/me/balance` | ✅ can build now | Next |
| Withdrawal request | `POST /merchants/me/withdrawals` | ✅ can build now | Next |
| Platform balance (admin) | `GET /balance` | ✅ confirmed working | Next — admin dashboard |
| Initiate transfer | `POST /transfer` | ⛔ blocked in test | Build now, test on prod |
| Finalize transfer OTP | `POST /transfer/finalize_transfer` | ⛔ blocked in test | Only if OTP enabled — disable in Paystack dashboard |
| Verify transfer by reference | `GET /transfer/verify/:reference` | ✅ | Reconcile cron |
| List transfers | `GET /transfer` | ✅ | Admin dashboard |
| Apple Pay domain registration | `POST /apple-pay/domain` | N/A | Before go-live |
| Charge authorization (returning customers) | `POST /transaction/charge_authorization` | ✅ | Phase 2 — not in Paystack ZA docs, confirm availability |
| Refunds | `POST /refund` | ✅ | Phase 2 |
| Paystack Billing Plans (merchant subscriptions) | `POST /plan` + `POST /subscription` | ✅ | Phase 2 |
