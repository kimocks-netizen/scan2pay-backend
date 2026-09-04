# Payments (Paystack)

Paystack is the **only** provider. Supported methods: `card`, `apple_pay`,
`google_pay`. Everything is ZAR.

## Keys

| Env var | Used for |
| --- | --- |
| `PAYSTACK_PUBLIC_KEY` | returned to the browser for Paystack Inline |
| `PAYSTACK_SECRET_KEY` | server-side initialise / verify / transfer |
| `PAYSTACK_WEBHOOK_SECRET` | HMAC-SHA512 signature verification |

The secret key never leaves the server. The public key may be returned in
`POST /payments/initialise`.

## Charge lifecycle

1. **Resolve** — `GET /codes/resolve/{reference}` returns the amount (or `null`
   for `variable`). Server checks `active` and `expires_at`.
2. **Initialise** — `POST /payments/initialise`. The server, *not the client*,
   decides the final amount:
   - `fixed` → the product's current `price_cents`
   - `amount` → the code's `amount_cents`
   - `variable` → the client's amount, validated `>= 100` and `<= 5_000_000`

   Then calls Paystack `POST /transaction/initialize` with
   `amount` (cents), `email`, `reference` (our `STP…`), `currency: "ZAR"`,
   `channels`, and `metadata: { merchant_id, payment_code_id, single_use }`.
   Persist a `pending` transaction row **before** returning.
3. **Customer pays** on Paystack checkout (Inline or hosted).
4. **Webhook** `charge.success` arrives → the transaction becomes `success`.
5. **Merchant screen** polling `GET /charges/{id}` sees `paid_at` and flips to
   the paid state.

The browser redirect is a UX convenience only — never mark a payment successful
from a client callback.

## Webhook verification

```python
expected = hmac.new(
    settings.PAYSTACK_WEBHOOK_SECRET.encode(),
    raw_body,                       # the RAW bytes, before JSON parsing
    hashlib.sha512,
).hexdigest()
if not hmac.compare_digest(expected, request.headers.get("x-paystack-signature", "")):
    return Response(status_code=401)
```

Then:

- Insert into `webhook_events`; the `UNIQUE(provider, event_type,
  provider_reference)` index makes replays no-ops.
- Process inside one DB transaction; return `200` fast (< 5s) so Paystack does
  not retry.
- Reconcile anything missed with the `reconcile_paystack` job, which calls
  `GET /transaction/verify/{reference}` for `pending` rows older than 10 min.

## Fees

Snapshot `plan_id_at_time` and `pricing_version` on every transaction so old
receipts never change when pricing does.

```text
platform_fee_cents = round(amount_cents * plan_percent / 100)   # 2.5 / 1.5 / 1.0
provider_fee_cents = round(amount_cents * 2.9 / 100) + 100      # Paystack ZAR
net_cents          = amount_cents - platform_fee_cents - provider_fee_cents
```

Worked example — R45.00 charge on `plan_basic` (1.5%):

```text
amount   4500
platform   68   (4500 * 1.5%)
provider  231   (4500 * 2.9% = 131, + 100 fixed)
net      4201
```

## Single-use till charges

- `expires_at = created_at + 5 minutes`, enforced in `resolve` **and** in
  `initialise` (a customer can sit on the pay screen past expiry).
- On `charge.success`: `paid_at = now()`, `active = false`, `payments += 1`.
- Concurrency: `SELECT … FOR UPDATE` the code row inside the webhook
  transaction and reject a second success with `already_paid`.
- A charge that expires while a Paystack session is open and then succeeds
  anyway must be **honoured and refunded-or-credited manually** — flag it
  `settlement_status = 'pending'` and alert; do not silently keep the money.

## Refunds

Phase 2. `POST /transactions/{id}/refund` → Paystack `POST /refund`. Store the
refund as a linked negative transaction rather than mutating the original row.

## Settlement / payouts

- Paystack settles to the platform account; Scan2Pay pays merchants out via
  Paystack Transfers to a stored `paystack_recipient_code`.
- `build_settlements` groups `success` + `settlement_status = 'pending'`
  transactions by merchant and cycle (`Daily (T+1)` or `Weekly`), creates a
  `payouts` row of `sum(net_cents)`, then stamps the transactions
  `settled` with `payout_id`.
- Taxi associations settle **to the association**. We never split to individual
  drivers.
- Minimum payout R50; anything below rolls into the next cycle.

## Testing

| Scenario | How |
| --- | --- |
| success | Paystack test card `4084 0840 8408 4081`, any future expiry, CVV `408` |
| failure | test card `4084 0800 0000 5408` |
| webhook replay | POST the same payload twice — the second must be a no-op |
| expiry | create a charge, freeze/advance the clock past 5 min, initialise → `code_expired` |
| double pay | two concurrent initialise calls on one single-use code → one `already_paid` |
