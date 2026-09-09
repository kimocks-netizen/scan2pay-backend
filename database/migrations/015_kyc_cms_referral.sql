-- 015_kyc_cms_referral.sql

-- ── Referral tracking on merchants ───────────────────────────────────────────
ALTER TABLE merchants
  ADD COLUMN IF NOT EXISTS referred_by text REFERENCES users(id);  -- support user_id

CREATE INDEX IF NOT EXISTS merchants_referred_by_idx ON merchants (referred_by);

-- ── KYC documents ─────────────────────────────────────────────────────────────
-- Files live in S3. Only metadata stored here.
CREATE TABLE merchant_documents (
  id            text PRIMARY KEY,                  -- 'doc_...'
  merchant_id   text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
  doc_type      text NOT NULL                      -- 'id_document' | 'proof_of_bank' | 'selfie'
    CHECK (doc_type IN ('id_document', 'proof_of_bank', 'selfie')),
  s3_key        text NOT NULL,
  filename      text NOT NULL,
  status        text NOT NULL DEFAULT 'pending'
    CHECK (status IN ('pending', 'approved', 'rejected')),
  rejection_reason text,
  uploaded_at   timestamptz NOT NULL DEFAULT now(),
  reviewed_by   text REFERENCES users(id),
  reviewed_at   timestamptz,
  CONSTRAINT merchant_documents_merchant_type_unique UNIQUE (merchant_id, doc_type)
);

CREATE INDEX IF NOT EXISTS merchant_documents_status_idx ON merchant_documents (status, uploaded_at DESC);
CREATE INDEX IF NOT EXISTS merchant_documents_merchant_idx ON merchant_documents (merchant_id);

-- ── CMS assets (home page images) ────────────────────────────────────────────
CREATE TABLE cms_assets (
  id          text PRIMARY KEY,                    -- 'cms_...'
  slot        text NOT NULL                        -- 'hero' | 'feature_1' | 'feature_2' | 'banner'
    CHECK (slot IN ('hero', 'feature_1', 'feature_2', 'banner')),
  s3_key      text NOT NULL,
  filename    text NOT NULL,
  alt_text    text,
  active      boolean NOT NULL DEFAULT true,
  uploaded_by text REFERENCES users(id),
  uploaded_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT cms_assets_slot_unique UNIQUE (slot)   -- one active image per slot
);

-- ── Support commission snapshots ──────────────────────────────────────────────
-- Written by a monthly cron or manually by admin. Read-only for support.
CREATE TABLE support_commissions (
  id              text PRIMARY KEY,                -- 'sc_...'
  support_user_id text NOT NULL REFERENCES users(id),
  period          text NOT NULL,                   -- 'YYYY-MM'
  assigned_count  integer NOT NULL DEFAULT 0,      -- merchants referred_by = this support
  unassigned_share integer NOT NULL DEFAULT 0,     -- their share of unassigned pool
  total_count     integer NOT NULL DEFAULT 0,      -- assigned + unassigned_share
  threshold       integer NOT NULL DEFAULT 1000,   -- bonus threshold for this period
  bonus_units     integer NOT NULL DEFAULT 0,      -- floor(total_count / threshold)
  rollover        integer NOT NULL DEFAULT 0,      -- total_count mod threshold → carries forward
  notes           text,
  created_at      timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT support_commissions_user_period_unique UNIQUE (support_user_id, period)
);

CREATE INDEX IF NOT EXISTS support_commissions_period_idx ON support_commissions (period DESC);
