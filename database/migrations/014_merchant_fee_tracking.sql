-- 014_merchant_fee_tracking.sql
-- Add monthly fee debt tracking to merchants.
-- pricing_versions table already exists from 002_plans_pricing.sql.

ALTER TABLE merchants
  ADD COLUMN IF NOT EXISTS fee_owed_cents      bigint NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS fee_last_charged_at timestamptz,
  ADD COLUMN IF NOT EXISTS plan                text NOT NULL DEFAULT 'plan_free';
