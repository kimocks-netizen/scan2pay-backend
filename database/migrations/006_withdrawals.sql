-- 006_withdrawals.sql

CREATE TABLE withdrawals (
  id              text PRIMARY KEY,                -- 'wd_...'
  reference       text NOT NULL,                  -- 'WD-XXXXXX' shown to merchant
  merchant_id     text NOT NULL REFERENCES merchants(id),
  amount_cents    bigint NOT NULL CHECK (amount_cents >= 5000),
  bank            text NOT NULL,
  account_masked  text NOT NULL,
  status          text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'paid', 'rejected')),
  note            text,
  requested_at    timestamptz NOT NULL DEFAULT now(),
  decided_at      timestamptz,
  decided_by      text REFERENCES users(id),
  paid_at         timestamptz,

  CONSTRAINT withdrawals_reference_unique UNIQUE (reference)
);

CREATE INDEX ON withdrawals (status, requested_at DESC);
CREATE INDEX ON withdrawals (merchant_id, requested_at DESC);
