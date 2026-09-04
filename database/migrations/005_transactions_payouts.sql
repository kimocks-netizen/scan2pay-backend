-- 005_transactions_payouts.sql
-- payouts first — transactions has a nullable FK to payouts.

-- ── payouts ───────────────────────────────────────────────────────────────────
CREATE TABLE payouts (
  id                text PRIMARY KEY,              -- 'pout_...'
  merchant_id       text NOT NULL REFERENCES merchants(id),
  amount_cents      bigint NOT NULL,
  transaction_count integer NOT NULL,
  period_start      timestamptz NOT NULL,
  period_end        timestamptz NOT NULL,
  status            payout_status NOT NULL DEFAULT 'pending',
  bank_reference    text,
  failure_reason    text,
  paid_at           timestamptz,
  created_at        timestamptz NOT NULL DEFAULT now(),
  updated_at        timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON payouts (merchant_id, period_start DESC);

-- ── transactions ──────────────────────────────────────────────────────────────
CREATE TABLE transactions (
  id                   text PRIMARY KEY,           -- 'txn_...'
  reference            text NOT NULL,              -- 'STP300100' customer-facing
  paystack_reference   text,
  merchant_id          text NOT NULL REFERENCES merchants(id),
  payment_code_id      text NOT NULL REFERENCES payment_codes(id),
  product_id           text REFERENCES products(id),
  item                 text NOT NULL,              -- label snapshot at pay time
  amount_cents         bigint NOT NULL CHECK (amount_cents >= 100),
  platform_fee_cents   bigint NOT NULL DEFAULT 0,
  provider_fee_cents   bigint NOT NULL DEFAULT 0,
  net_cents            bigint NOT NULL,
  status               txn_status NOT NULL DEFAULT 'pending',
  failure_reason       text,
  method               payment_method NOT NULL,
  customer_label       text NOT NULL DEFAULT 'Anonymous',
  customer_email       citext,
  settlement_status    settlement_state NOT NULL DEFAULT 'pending',
  payout_id            text REFERENCES payouts(id),
  -- Pricing snapshot — never recompute historic rows
  pricing              jsonb NOT NULL DEFAULT '{}',
  plan_id_at_time      text NOT NULL,
  pricing_version      text NOT NULL,
  created_at           timestamptz NOT NULL DEFAULT now(),
  paid_at              timestamptz,

  CONSTRAINT reference_unique UNIQUE (reference),
  CONSTRAINT paystack_reference_unique UNIQUE (paystack_reference)
);

CREATE INDEX ON transactions (merchant_id, created_at DESC);
CREATE INDEX ON transactions (merchant_id, status, created_at DESC);
CREATE INDEX ON transactions (payment_code_id);
CREATE INDEX ON transactions (settlement_status) WHERE status = 'success';
