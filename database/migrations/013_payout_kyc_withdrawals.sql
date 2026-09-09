-- 013_payout_kyc_withdrawals.sql

-- Merchants: add KYC status + account holder name
ALTER TABLE merchants
  ADD COLUMN IF NOT EXISTS payout_account_name text,
  ADD COLUMN IF NOT EXISTS kyc_status text NOT NULL DEFAULT 'pending'
    CHECK (kyc_status IN ('pending', 'verified', 'failed')),
  ADD COLUMN IF NOT EXISTS kyc_verified_at timestamptz;

-- Withdrawals: add transfer_code + expand status constraint
ALTER TABLE withdrawals
  ADD COLUMN IF NOT EXISTS transfer_code text,
  ADD COLUMN IF NOT EXISTS failure_reason text;

ALTER TABLE withdrawals
  DROP CONSTRAINT IF EXISTS withdrawals_status_check;

ALTER TABLE withdrawals
  ADD CONSTRAINT withdrawals_status_check
    CHECK (status IN ('pending', 'approved', 'paid', 'rejected', 'failed', 'reversed'));
