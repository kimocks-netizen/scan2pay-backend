# Database schema (PostgreSQL)

Conventions:

- IDs are `text` primary keys with a type prefix (`usr_`, `mch_`, …). Generate
  with a ULID/nanoid so they sort by creation time.
- Money columns are `bigint` **cents (ZAR)**, never `numeric`, never floats.
- Timestamps are `timestamptz`, always stored in UTC.
- Every table has `created_at` and (where mutable) `updated_at`.
- Soft delete via `active boolean` — we never hard-delete anything financial.

## Enums

```sql
CREATE TYPE user_type        AS ENUM ('vendor', 'tip', 'taxi');
CREATE TYPE user_role        AS ENUM ('merchant', 'admin');
CREATE TYPE user_status      AS ENUM ('active', 'suspended');
CREATE TYPE code_mode        AS ENUM ('fixed', 'amount', 'variable');
CREATE TYPE txn_status       AS ENUM ('pending', 'success', 'failed');
CREATE TYPE payment_method   AS ENUM ('card', 'apple_pay', 'google_pay');
CREATE TYPE settlement_state AS ENUM ('pending', 'settled', 'failed');
CREATE TYPE payout_status    AS ENUM ('pending', 'processing', 'paid', 'failed');
CREATE TYPE merchant_status  AS ENUM ('active', 'suspended', 'closed');
CREATE TYPE pricing_status   AS ENUM ('published', 'scheduled', 'retired');
CREATE TYPE fee_bearer       AS ENUM ('merchant', 'customer', 'split');
```

---

## `users`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `usr_…` |
| `full_name` | text NOT NULL | |
| `phone` | text NOT NULL UNIQUE | E.164, primary login identifier |
| `email` | citext UNIQUE | secondary login identifier |
| `password_hash` | text NOT NULL | bcrypt; never store plaintext |
| `user_type` | user_type NOT NULL | wording/defaults only |
| `role` | user_role NOT NULL DEFAULT 'merchant' | `merchant` \| `admin` |
| `status` | user_status NOT NULL DEFAULT 'active' | `active` \| `suspended` |
| `avatar_initials` | text | derived at signup |
| `phone_verified` | boolean NOT NULL DEFAULT false | |
| `email_verified` | boolean NOT NULL DEFAULT false | |
| `last_login_at` | timestamptz | |
| `created_at` / `updated_at` | timestamptz NOT NULL | |

Indexes: `UNIQUE(phone)`, `UNIQUE(lower(email))`.

## `merchants`

One per user today; the column layout already allows many-per-user later.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `mch_…` |
| `user_id` | text NOT NULL REFERENCES users(id) ON DELETE RESTRICT | owner |
| `business_name` | text NOT NULL | legal / registered name |
| `display_name` | text NOT NULL | shown on the QR poster |
| `slug` | text NOT NULL UNIQUE | url-safe |
| `trading_category` | text | "Retail & Services", "Tips", "Taxi transport" |
| `city` / `province` | text | |
| `plan_id` | text NOT NULL REFERENCES plans(id) DEFAULT 'plan_free' | |
| `payout_bank` | text | display name |
| `payout_bank_code` | text | Paystack bank code |
| `payout_account_masked` | text | last 4 digits shown in UI |
| `payout_account_enc` | bytea | full number, encrypted at rest (pgcrypto) |
| `paystack_recipient_code` | text | for transfers |
| `settlement_cycle` | text NOT NULL DEFAULT 'Weekly' | 'Daily (T+1)' \| 'Weekly' |
| `status` | merchant_status NOT NULL DEFAULT 'active' | |
| `joined_at` | timestamptz NOT NULL | |
| `created_at` / `updated_at` | timestamptz NOT NULL | |

Indexes: `UNIQUE(slug)`, `INDEX(user_id)`.

## `products`

Optional — only merchants who use `fixed` codes populate this.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `prd_…` |
| `merchant_id` | text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE | |
| `name` | text NOT NULL | |
| `description` | text | |
| `price_cents` | bigint NOT NULL CHECK (price_cents >= 0) | |
| `previous_price_cents` | bigint | set automatically on price change |
| `sku` | text | |
| `category` | text | |
| `active` | boolean NOT NULL DEFAULT true | |
| `created_at` / `updated_at` | timestamptz NOT NULL | |

Indexes: `INDEX(merchant_id, active)`, `UNIQUE(merchant_id, sku) WHERE sku IS NOT NULL`.

## `payment_codes`

The core table. Holds **both** permanent printable codes and one-off till
charges — they differ only by `single_use`.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `pc_…` |
| `merchant_id` | text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE | |
| `reference` | text NOT NULL UNIQUE | what the QR encodes: `QR-…` permanent, `PAY-…` charge |
| `label` | text NOT NULL | "Full Car Wash", "Amount due" |
| `caption` | text | poster headline: "Scan to Pay" / "Scan to Tip" / "Scan to Pay Fare" |
| `mode` | code_mode NOT NULL | fixed \| amount \| variable |
| `product_id` | text REFERENCES products(id) ON DELETE SET NULL | only when `mode = 'fixed'` |
| `amount_cents` | bigint | only when `mode = 'amount'` |
| `description` | text | |
| `placement` | text | "Shop counter", "Inside taxi" |
| `active` | boolean NOT NULL DEFAULT true | |
| `is_primary` | boolean NOT NULL DEFAULT false | the code minted at signup |
| `single_use` | boolean NOT NULL DEFAULT false | till charge |
| `expires_at` | timestamptz | set for till charges (`now() + 5 min`) |
| `paid_at` | timestamptz | set when the charge is paid |
| `scans` | integer NOT NULL DEFAULT 0 | |
| `payments` | integer NOT NULL DEFAULT 0 | |
| `created_at` / `updated_at` | timestamptz NOT NULL | |

Constraints:

```sql
CHECK (mode <> 'fixed'    OR (product_id IS NOT NULL AND amount_cents IS NULL)),
CHECK (mode <> 'amount'   OR (amount_cents IS NOT NULL AND product_id IS NULL)),
CHECK (mode <> 'variable' OR (amount_cents IS NULL AND product_id IS NULL)),
CHECK (amount_cents IS NULL OR amount_cents >= 100),
CHECK (single_use = false OR (mode = 'amount' AND expires_at IS NOT NULL))
```

Indexes:

```sql
UNIQUE (reference);
CREATE UNIQUE INDEX one_primary_per_merchant
  ON payment_codes (merchant_id) WHERE is_primary;
CREATE INDEX ON payment_codes (merchant_id, single_use, created_at DESC);
CREATE INDEX ON payment_codes (expires_at) WHERE single_use AND active;
```

## `transactions`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `txn_…` |
| `reference` | text NOT NULL UNIQUE | our customer-facing ref, `STP300100` |
| `paystack_reference` | text UNIQUE | provider ref, used for idempotency |
| `merchant_id` | text NOT NULL REFERENCES merchants(id) | |
| `payment_code_id` | text NOT NULL REFERENCES payment_codes(id) | |
| `product_id` | text REFERENCES products(id) | nullable |
| `item` | text NOT NULL | snapshot of the code label at pay time |
| `amount_cents` | bigint NOT NULL CHECK (amount_cents >= 100) | what the customer paid |
| `platform_fee_cents` | bigint NOT NULL DEFAULT 0 | our cut, by plan |
| `provider_fee_cents` | bigint NOT NULL DEFAULT 0 | Paystack's cut |
| `net_cents` | bigint NOT NULL | amount − platform − provider |
| `status` | txn_status NOT NULL DEFAULT 'pending' | |
| `failure_reason` | text | |
| `method` | payment_method NOT NULL | |
| `customer_label` | text NOT NULL DEFAULT 'Anonymous' | |
| `customer_email` | citext | Paystack requires one; never shown to merchant |
| `settlement_status` | settlement_state NOT NULL DEFAULT 'pending' | |
| `payout_id` | text REFERENCES payouts(id) | filled when settled |
| `pricing` | jsonb NOT NULL DEFAULT '{}' | full snapshot at pay time |
| `plan_id_at_time` | text NOT NULL | fee snapshot |
| `pricing_version` | text NOT NULL | e.g. `pv_001` |
| `created_at` | timestamptz NOT NULL | |
| `paid_at` | timestamptz | webhook time |

Indexes:

```sql
CREATE INDEX ON transactions (merchant_id, created_at DESC);
CREATE INDEX ON transactions (merchant_id, status, created_at DESC);
CREATE INDEX ON transactions (payment_code_id);
CREATE INDEX ON transactions (settlement_status) WHERE status = 'success';
UNIQUE (paystack_reference);
```

**Fee formulas** (snapshot the inputs, never recompute historic rows):

```text
platform_fee_cents = round(amount_cents * platform_fee_percent_for_plan / 100)
provider_fee_cents = round(amount_cents * 2.9 / 100) + 100
net_cents          = amount_cents - platform_fee_cents - provider_fee_cents
```

## `payouts`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `pout_…` |
| `merchant_id` | text NOT NULL REFERENCES merchants(id) | |
| `amount_cents` | bigint NOT NULL | sum of `net_cents` in the period |
| `transaction_count` | integer NOT NULL | |
| `period_start` / `period_end` | timestamptz NOT NULL | |
| `status` | payout_status NOT NULL DEFAULT 'pending' | |
| `bank_reference` | text | Paystack transfer code |
| `failure_reason` | text | |
| `paid_at` | timestamptz | |
| `created_at` / `updated_at` | timestamptz NOT NULL | |

Index: `INDEX(merchant_id, period_start DESC)`.

## `plans`

Seeded reference data.

| Column | Type |
| --- | --- |
| `id` | text PK (`plan_free`, `plan_basic`, `plan_pro`) |
| `name` | text NOT NULL |
| `monthly_price_cents` | bigint NOT NULL |
| `platform_fee_percent` | numeric(5,2) NOT NULL |
| `max_codes` | integer (NULL = unlimited; free = 1) |
| `features` | jsonb NOT NULL |
| `recommended` | boolean NOT NULL DEFAULT false |
| `active` | boolean NOT NULL DEFAULT true |

Seed: free R0 / 2.5%, basic R100 / 1.5%, pro / 1.0%.

## `pricing_versions`

Fees change; historic transactions must not. One row per plan per version.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `pv_…` |
| `version` | integer NOT NULL | monotonic int, e.g. 1, 2, 3 |
| `name` | text NOT NULL | display label |
| `plan_id` | text NOT NULL REFERENCES plans(id) | |
| `monthly_subscription_cents` | bigint NOT NULL | |
| `platform_fee_percent` | numeric(5,2) NOT NULL | |
| `platform_fixed_fee_cents` | bigint NOT NULL DEFAULT 0 | |
| `provider_percent` | numeric(5,2) NOT NULL DEFAULT 2.90 | |
| `provider_fixed_cents` | bigint NOT NULL DEFAULT 100 | |
| `fee_bearer` | fee_bearer NOT NULL DEFAULT 'merchant' | who pays fees |
| `effective_from` | timestamptz NOT NULL | |
| `status` | pricing_status NOT NULL DEFAULT 'published' | |
| `created_by` | text NOT NULL DEFAULT 'system' | |
| `note` | text NOT NULL DEFAULT '' | |
| `created_at` | timestamptz NOT NULL DEFAULT now() | |

## `withdrawals`

Merchant payout requests against the **settled** balance. Approved and paid by the
Scan2Pay team — see `docs/admin.md` for the balance formula and state machine.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | `wd_…` |
| `reference` | text NOT NULL UNIQUE | `WD-XXXXXX`, shown to the merchant |
| `merchant_id` | text NOT NULL REFERENCES merchants(id) | |
| `amount_cents` | bigint NOT NULL CHECK (amount_cents >= 5000) | R50 minimum |
| `bank` / `account_masked` | text NOT NULL | copied from the merchant at request time |
| `status` | text NOT NULL CHECK (status IN ('pending','approved','paid','rejected')) | |
| `note` | text | merchant reason, or rejection reason |
| `requested_at` | timestamptz NOT NULL DEFAULT now() | |
| `decided_at` | timestamptz | approve/reject time |
| `decided_by` | text REFERENCES users(id) | admin who acted |
| `paid_at` | timestamptz | bank transfer sent |

```sql
CREATE INDEX ON withdrawals (status, requested_at DESC);
CREATE INDEX ON withdrawals (merchant_id, requested_at DESC);
```

The available balance MUST be recomputed inside the same transaction that inserts the
request, so two concurrent requests cannot overdraw the account.

## `refresh_tokens`

| Column | Type | Notes |
| --- | --- | --- |
| `id` | text PK | |
| `user_id` | text NOT NULL REFERENCES users(id) ON DELETE CASCADE | |
| `token_hash` | text NOT NULL UNIQUE | sha256 of the token |
| `expires_at` | timestamptz NOT NULL | |
| `revoked_at` | timestamptz | |
| `user_agent` / `ip` | text | |
| `created_at` | timestamptz NOT NULL | |

## `otp_codes`

| Column | Type |
| --- | --- |
| `id` | text PK |
| `phone` | text NOT NULL |
| `code_hash` | text NOT NULL |
| `expires_at` | timestamptz NOT NULL (now + 10 min) |
| `attempts` | integer NOT NULL DEFAULT 0 |
| `consumed_at` | timestamptz |
| `created_at` | timestamptz NOT NULL |

Index: `INDEX(phone, created_at DESC)`.

## `webhook_events`

Idempotency + replay debugging.

| Column | Type |
| --- | --- |
| `id` | text PK |
| `provider` | text NOT NULL DEFAULT 'paystack' |
| `event_type` | text NOT NULL |
| `provider_reference` | text NOT NULL |
| `payload` | jsonb NOT NULL |
| `signature_valid` | boolean NOT NULL |
| `processed_at` | timestamptz |
| `error` | text |
| `created_at` | timestamptz NOT NULL |

Index: `UNIQUE(provider, event_type, provider_reference)` — the idempotency guard.

## `scan_events` (optional analytics)

| Column | Type |
| --- | --- |
| `id` | bigserial PK |
| `payment_code_id` | text NOT NULL REFERENCES payment_codes(id) ON DELETE CASCADE |
| `scanned_at` | timestamptz NOT NULL DEFAULT now() |
| `user_agent` | text |
| `ip_hash` | text (hashed, never raw IP) |

`payment_codes.scans` stays as a fast counter; this table gives the time series.

## `audit_log`

Free-text `actor` so system/cron jobs can log without a user FK.

| Column | Type | Notes |
| --- | --- | --- |
| `id` | bigserial PK | |
| `actor` | text NOT NULL | display name or `'system'` |
| `actor_role` | text NOT NULL | `'admin'` \| `'merchant'` \| `'system'` |
| `action` | text NOT NULL | e.g. `'user.suspended'` |
| `target` | text NOT NULL | display name of affected entity |
| `detail` | text NOT NULL | human-readable description |
| `ip` | text | |
| `before` / `after` | jsonb | |
| `created_at` | timestamptz NOT NULL DEFAULT now() | |

---

## Relationship map

```text
users 1──1 merchants 1──* products
                      1──* payment_codes ──* transactions ──? payouts
plans 1──* merchants
merchants 1──* withdrawals
pricing_versions ──(snapshot)── transactions
```

## Migration order

1. enums → `plans`, `pricing_versions` (seed data)
2. `users` → `merchants` → `products` → `payment_codes`
3. `payouts` → `transactions` (FK to payouts)
4. `withdrawals`
5. `refresh_tokens`, `otp_codes`, `webhook_events`, `scan_events`, `audit_log`
