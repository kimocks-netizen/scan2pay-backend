-- 012_fix_payment_codes_constraints.sql
-- Adds missing constraint and columns to payment_codes that may not exist
-- if the table was created from an earlier version of 004_products_codes.sql.
-- Safe to run multiple times (uses IF NOT EXISTS / DO blocks).

-- ── Add missing columns if they don't exist ───────────────────────────────────
ALTER TABLE payment_codes
  ADD COLUMN IF NOT EXISTS expires_at  timestamptz,
  ADD COLUMN IF NOT EXISTS paid_at     timestamptz,
  ADD COLUMN IF NOT EXISTS single_use  boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS placement   text,
  ADD COLUMN IF NOT EXISTS description text;

-- ── Add single_use_rules constraint if missing ────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'single_use_rules'
      AND conrelid = 'payment_codes'::regclass
  ) THEN
    ALTER TABLE payment_codes
      ADD CONSTRAINT single_use_rules
        CHECK (single_use = false OR (mode = 'amount' AND expires_at IS NOT NULL));
  END IF;
END;
$$;

-- ── Add other missing constraints if not present ──────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'fixed_needs_product'
      AND conrelid = 'payment_codes'::regclass
  ) THEN
    ALTER TABLE payment_codes
      ADD CONSTRAINT fixed_needs_product
        CHECK (mode <> 'fixed' OR (product_id IS NOT NULL AND amount_cents IS NULL));
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'amount_needs_cents'
      AND conrelid = 'payment_codes'::regclass
  ) THEN
    ALTER TABLE payment_codes
      ADD CONSTRAINT amount_needs_cents
        CHECK (mode <> 'amount' OR (amount_cents IS NOT NULL AND product_id IS NULL));
  END IF;
END;
$$;

DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conname = 'variable_no_amount'
      AND conrelid = 'payment_codes'::regclass
  ) THEN
    ALTER TABLE payment_codes
      ADD CONSTRAINT variable_no_amount
        CHECK (mode <> 'variable' OR (amount_cents IS NULL AND product_id IS NULL));
  END IF;
END;
$$;
