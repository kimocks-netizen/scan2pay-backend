-- 010_txn_authorization_code.sql
-- Stores Paystack authorization_code on successful card transactions.
-- Used in Phase 2 for charge_authorization (repeat payments without card re-entry).

ALTER TABLE transactions
  ADD COLUMN IF NOT EXISTS authorization_code text;
