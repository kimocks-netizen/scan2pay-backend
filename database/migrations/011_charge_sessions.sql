-- 011_charge_sessions.sql
-- Adds charge session support to transactions table.
-- A charge session is a pending transaction created by the merchant on the
-- Charge page, linked to their permanent primary QR. The QR stays the same;
-- the amount is stored here and surfaced to the customer at scan time.

ALTER TABLE transactions
  ADD COLUMN IF NOT EXISTS charge_session     boolean NOT NULL DEFAULT false,
  ADD COLUMN IF NOT EXISTS charge_expires_at  timestamptz,
  ADD COLUMN IF NOT EXISTS access_code_paystack text;  -- Paystack access_code for the popup

-- index for fast lookup of active charge sessions per payment code
CREATE INDEX IF NOT EXISTS idx_transactions_charge_session
  ON transactions (payment_code_id, status, charge_session, charge_expires_at)
  WHERE charge_session = true;
