-- 016: store Paystack bank validation result on merchants
-- Captured once when merchant saves payout account (prod only)
-- Surfaced to admin during KYC review — no sensitive data stored

alter table merchants
  add column if not exists bank_verified            boolean   default null,
  add column if not exists bank_holder_match        boolean   default null,
  add column if not exists bank_accepts_credits     boolean   default null,
  add column if not exists bank_account_open        boolean   default null,
  add column if not exists bank_open_3_months       boolean   default null,
  add column if not exists bank_verification_msg    text      default null,
  add column if not exists bank_validated_at        timestamptz default null;
