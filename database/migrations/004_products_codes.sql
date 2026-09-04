-- 004_products_codes.sql

-- ── products ──────────────────────────────────────────────────────────────────
CREATE TABLE products (
  id                    text PRIMARY KEY,           -- 'prd_...'
  merchant_id           text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
  name                  text NOT NULL,
  description           text,
  price_cents           bigint NOT NULL CHECK (price_cents >= 0),
  previous_price_cents  bigint,
  sku                   text,
  category              text,
  active                boolean NOT NULL DEFAULT true,
  created_at            timestamptz NOT NULL DEFAULT now(),
  updated_at            timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON products (merchant_id, active);
CREATE UNIQUE INDEX ON products (merchant_id, sku) WHERE sku IS NOT NULL;

-- ── payment_codes ─────────────────────────────────────────────────────────────
CREATE TABLE payment_codes (
  id          text PRIMARY KEY,                     -- 'pc_...'
  merchant_id text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
  reference   text NOT NULL,                        -- QR-... permanent | PAY-... charge
  label       text NOT NULL,
  caption     text,                                 -- poster headline
  mode        code_mode NOT NULL,
  product_id  text REFERENCES products(id) ON DELETE SET NULL,
  amount_cents bigint,
  description text,
  placement   text,
  active      boolean NOT NULL DEFAULT true,
  is_primary  boolean NOT NULL DEFAULT false,
  single_use  boolean NOT NULL DEFAULT false,
  expires_at  timestamptz,
  paid_at     timestamptz,
  scans       integer NOT NULL DEFAULT 0,
  payments    integer NOT NULL DEFAULT 0,
  created_at  timestamptz NOT NULL DEFAULT now(),
  updated_at  timestamptz NOT NULL DEFAULT now(),

  CONSTRAINT reference_unique UNIQUE (reference),
  CONSTRAINT fixed_needs_product
    CHECK (mode <> 'fixed'    OR (product_id IS NOT NULL AND amount_cents IS NULL)),
  CONSTRAINT amount_needs_cents
    CHECK (mode <> 'amount'   OR (amount_cents IS NOT NULL AND product_id IS NULL)),
  CONSTRAINT variable_no_amount
    CHECK (mode <> 'variable' OR (amount_cents IS NULL AND product_id IS NULL)),
  CONSTRAINT min_amount
    CHECK (amount_cents IS NULL OR amount_cents >= 100),
  CONSTRAINT single_use_rules
    CHECK (single_use = false OR (mode = 'amount' AND expires_at IS NOT NULL))
);

CREATE UNIQUE INDEX one_primary_per_merchant
  ON payment_codes (merchant_id) WHERE is_primary;
CREATE INDEX ON payment_codes (merchant_id, single_use, created_at DESC);
CREATE INDEX ON payment_codes (expires_at) WHERE single_use AND active;
