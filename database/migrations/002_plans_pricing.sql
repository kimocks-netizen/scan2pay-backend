-- 002_plans_pricing.sql
-- Seed reference data. plans must exist before merchants (FK plan_id).

CREATE EXTENSION IF NOT EXISTS citext;

-- ── plans ────────────────────────────────────────────────────────────────────
CREATE TABLE plans (
  id                    text PRIMARY KEY,          -- 'plan_free' | 'plan_basic' | 'plan_pro'
  name                  text NOT NULL,
  monthly_price_cents   bigint NOT NULL,
  platform_fee_percent  numeric(5,2) NOT NULL,
  max_codes             integer,                   -- NULL = unlimited; free = 1
  features              jsonb NOT NULL DEFAULT '[]',
  recommended           boolean NOT NULL DEFAULT false,
  active                boolean NOT NULL DEFAULT true
);

INSERT INTO plans (id, name, monthly_price_cents, platform_fee_percent, max_codes, features, recommended) VALUES
  ('plan_free',  'Free',  0,     2.50, 1,    '["1 payment code","Basic analytics","WinSMS notifications"]', false),
  ('plan_basic', 'Basic', 10000, 1.50, 10,   '["10 payment codes","Full analytics","Priority support","CSV export"]', true),
  ('plan_pro',   'Pro',   29900, 1.00, NULL, '["Unlimited codes","Advanced analytics","API access","Dedicated support"]', false);

-- ── pricing_versions ─────────────────────────────────────────────────────────
-- One row per pricing snapshot. Transactions snapshot the version at pay time.
CREATE TABLE pricing_versions (
  id                        text PRIMARY KEY,       -- 'pv_...'
  version                   integer NOT NULL,       -- monotonic int, e.g. 1, 2, 3
  name                      text NOT NULL,
  plan_id                   text NOT NULL REFERENCES plans(id),
  monthly_subscription_cents bigint NOT NULL,
  platform_fee_percent      numeric(5,2) NOT NULL,
  platform_fixed_fee_cents  bigint NOT NULL DEFAULT 0,
  provider_percent          numeric(5,2) NOT NULL DEFAULT 2.90,
  provider_fixed_cents      bigint NOT NULL DEFAULT 100,
  fee_bearer                fee_bearer NOT NULL DEFAULT 'merchant',
  effective_from            timestamptz NOT NULL,
  status                    pricing_status NOT NULL DEFAULT 'published',
  created_by                text NOT NULL DEFAULT 'system',
  note                      text NOT NULL DEFAULT '',
  created_at                timestamptz NOT NULL DEFAULT now()
);

-- Seed initial pricing versions (one per plan)
INSERT INTO pricing_versions
  (id, version, name, plan_id, monthly_subscription_cents, platform_fee_percent, platform_fixed_fee_cents, provider_percent, provider_fixed_cents, fee_bearer, effective_from, status, created_by, note)
VALUES
  ('pv_001', 1, 'Launch pricing – Free',  'plan_free',  0,     2.50, 0, 2.90, 100, 'merchant', '2026-07-01T00:00:00Z', 'published', 'system', 'Initial launch pricing'),
  ('pv_002', 1, 'Launch pricing – Basic', 'plan_basic', 10000, 1.50, 0, 2.90, 100, 'merchant', '2026-07-01T00:00:00Z', 'published', 'system', 'Initial launch pricing'),
  ('pv_003', 1, 'Launch pricing – Pro',   'plan_pro',   29900, 1.00, 0, 2.90, 100, 'merchant', '2026-07-01T00:00:00Z', 'published', 'system', 'Initial launch pricing');
