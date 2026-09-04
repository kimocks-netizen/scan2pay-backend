# Admin system

The admin console manages the *platform*, not one merchant's trading. Everything here
sits behind a staff role check on the server — never on the client.

Conventions follow `docs/README.md`: money in cents (ZAR), timestamps ISO-8601 UTC.

## 1. Access control

- `users.role` is `merchant` (default) or `admin`.
- Admin endpoints live under `/api/admin/*` and require `role = admin`; every mutating
  call writes an `audit_logs` row.
- Admin accounts have no merchant, no QR codes and cannot take payments.

Demo login in the prototype: `087 000 1234` / `admin123`.

## 2. Console sections

| Section | Route | What it does |
|---|---|---|
| Overview | `/admin` | Volume, platform revenue, provider fees, pending settlement, account counts |
| Users | `/admin/users` | Search all accounts (business, tip earner, taxi), verification state, suspend/reactivate |
| Businesses | `/admin/merchants` | Plan, payout bank, QR code count, lifetime volume, suspend/reactivate |
| Transactions | `/admin/transactions` | Every payment with fees, method, settlement state and the pricing version used |
| Settlements | `/admin/settlements` | Per-business pending vs settled, cycle, last payment |
| Pricing | `/admin/pricing` | Publish pricing versions, view full history |
| Provider | `/admin/providers` | Paystack success rate, failures, method mix, fee totals |
| Audit log | `/admin/audit` | Who changed what, when, from where |

Refunds/disputes, WhatsApp monitoring, notifications and system configuration reuse the
same shape: a read list plus a small number of audited mutations.

## 3. Pricing configuration (database-driven)

Pricing is data. Changing a fee is an `INSERT` into `pricing_versions`, never a deploy.

```sql
create table pricing_versions (
  id                       uuid primary key default gen_random_uuid(),
  version                  integer not null unique,      -- monotonic, human-facing
  name                     text not null,
  plan_id                  uuid not null references plans(id),
  monthly_subscription_cents integer not null default 0,
  platform_fee_percent     numeric(5,2) not null,        -- e.g. 1.50
  platform_fixed_fee_cents integer not null default 0,
  provider_percent         numeric(5,2) not null,        -- assumption used in estimates
  provider_fixed_cents     integer not null default 0,
  fee_bearer               text not null check (fee_bearer in ('merchant','customer','split')),
  effective_from           timestamptz not null,
  status                   text not null check (status in ('published','scheduled','retired')),
  note                     text not null default '',
  created_by               uuid not null references users(id),
  created_at               timestamptz not null default now()
);
create index on pricing_versions (plan_id, status, effective_from desc);
```

Rules:

1. Publishing a row whose `effective_from <= now()` retires the previous published row
   for that plan; a future date is stored as `scheduled` and flips over by a nightly job.
2. Rows are immutable once published — corrections are new versions.
3. The active row for a plan is the highest `version` that is `published` and whose
   `effective_from <= now()`.

Admin endpoints:

| Method | Path | Body / notes |
|---|---|---|
| GET | `/api/admin/pricing-versions` | Full history, newest first |
| POST | `/api/admin/pricing-versions` | `name, plan_id, monthly_subscription_cents, platform_fee_percent, platform_fixed_fee_cents, provider_percent, provider_fixed_cents, fee_bearer, effective_from, note` |
| GET | `/api/admin/pricing-versions/active?plan_id=` | The row a new payment would use right now |

## 4. Pricing snapshot on every transaction

When a transaction is created the resolved pricing is **copied onto the row**. Later
pricing changes never rewrite history.

```sql
alter table transactions
  add column pricing_version           integer not null,
  add column pricing_platform_percent  numeric(5,2) not null,
  add column pricing_platform_fixed_cents integer not null default 0,
  add column pricing_provider_percent  numeric(5,2) not null,
  add column pricing_provider_fixed_cents integer not null default 0,
  add column pricing_fee_bearer        text not null;
```

Worked example:

```
Transaction:          TXN123
Pricing version:      5
Platform fee:         1.5%
Platform fee amount:  R3.00
Provider fee:         R6.80
```

If the platform fee later becomes 2%, TXN123 still reports 1.5% / R3.00. Reports,
settlements and merchant statements all read the snapshot columns, never the live
pricing table.

Fee maths at capture time:

```
platform_fee = round(amount * platform_fee_percent / 100) + platform_fixed_fee_cents
provider_fee = round(amount * provider_percent / 100) + provider_fixed_cents
net          = amount - platform_fee - provider_fee      (fee_bearer = 'merchant')
```

With `fee_bearer = 'customer'` the fees are added on top of the basket amount before the
provider is called; with `split` each side carries half of the platform fee.

## 5. Audit log

```sql
create table audit_logs (
  id          uuid primary key default gen_random_uuid(),
  actor_id    uuid references users(id),      -- null for system jobs
  actor_name  text not null,
  actor_role  text not null check (actor_role in ('admin','merchant','system')),
  action      text not null,                  -- pricing.published, user.suspended, …
  target      text not null,
  detail      text not null default '',
  ip          inet,
  created_at  timestamptz not null default now()
);
create index on audit_logs (created_at desc);
```

Every admin mutation and every settlement batch writes one row. Audit rows are
append-only — no updates, no deletes.

## 6. Admin API summary

| Method | Path | Returns |
|---|---|---|
| GET | `/api/admin/stats` | Platform totals for the overview cards |
| GET | `/api/admin/users` | All accounts (no password hashes) |
| PATCH | `/api/admin/users/:id/status` | `{ status: 'active' \| 'suspended' }` |
| GET | `/api/admin/merchants` | All businesses |
| PATCH | `/api/admin/merchants/:id/status` | Suspend / reactivate |
| PATCH | `/api/admin/merchants/:id/plan` | Move a business between plans |
| GET | `/api/admin/payment-codes` | Every QR/payment code, newest first |
| GET | `/api/admin/transactions` | Platform-wide payments, with pricing snapshot |
| GET | `/api/admin/settlements` | Pending vs settled per business |
| GET | `/api/admin/provider/health` | Success rate, failures, method mix |
| GET | `/api/admin/audit-logs` | Audit trail |

The prototype implements all of these against mock data in `src/lib/api/client.ts`
(`adminStats`, `adminListUsers`, `adminSetUserStatus`, `adminListMerchants`,
`adminSetMerchantStatus`, `adminSetMerchantPlan`, `adminListTransactions`,
`adminListCodes`, `adminSettlements`, `adminListPricingVersions`,
`adminPublishPricing`, `adminActivePricing`, `adminListAudit`) — swapping to real
endpoints is a one-file change.

## Withdrawals

Merchants request a payout of their **settled** balance; the Scan2Pay team approves and pays it.

Available balance = settled successful `net_cents` − paid withdrawals − withdrawals in flight
(`pending` + `approved`). Unsettled payments show as "still clearing" and cannot be withdrawn.

### `withdrawals`

| column | type | notes |
| --- | --- | --- |
| id | uuid pk | |
| reference | text unique | `WD-XXXXXX`, shown to the merchant |
| merchant_id | uuid ref merchants | indexed |
| amount_cents | integer | check `>= 5000` (R50 minimum) |
| bank | text | copied from the merchant at request time |
| account_masked | text | copied at request time |
| status | text | check `pending` \| `approved` \| `paid` \| `rejected` |
| note | text | merchant reason, or rejection reason |
| requested_at | timestamptz | default now() |
| decided_at | timestamptz null | set on approve/reject |
| decided_by | uuid null ref users | admin who acted |
| paid_at | timestamptz null | set when the bank transfer goes out |

Index on `(status, requested_at desc)` for the admin queue and `(merchant_id, requested_at desc)`
for the merchant list.

State machine: `pending → approved → paid`, `pending → rejected`. A merchant may cancel only while
`pending`. `paid` is only reachable from `approved`. Every transition writes an `audit_logs` row
(`withdrawal.requested`, `withdrawal.approved`, `withdrawal.paid`, `withdrawal.rejected`).

### Endpoints

| method | path | who | notes |
| --- | --- | --- | --- |
| GET | `/api/merchants/:id/balance` | merchant | available, on hold, in flight, paid to date |
| GET | `/api/merchants/:id/withdrawals` | merchant | history |
| POST | `/api/merchants/:id/withdrawals` | merchant | `{ amountCents, note }`, re-checks the balance server-side |
| POST | `/api/withdrawals/:id/cancel` | merchant | pending only |
| GET | `/api/admin/withdrawals?status=` | admin | queue, defaults to `pending` |
| POST | `/api/admin/withdrawals/:id/status` | admin | `{ status, reason }` |

The balance must be recomputed inside the same transaction that inserts the request, so two
concurrent requests cannot overdraw the account.
