-- 003_users_merchants.sql

-- ── users ─────────────────────────────────────────────────────────────────────
CREATE TABLE users (
  id               text PRIMARY KEY,               -- 'usr_...'
  full_name        text NOT NULL,
  phone            text NOT NULL,
  email            citext,
  password_hash    text NOT NULL,
  user_type        user_type NOT NULL,
  role             user_role NOT NULL DEFAULT 'merchant',
  status           user_status NOT NULL DEFAULT 'active',
  avatar_initials  text,
  phone_verified   boolean NOT NULL DEFAULT false,
  email_verified   boolean NOT NULL DEFAULT false,
  last_login_at    timestamptz,
  created_at       timestamptz NOT NULL DEFAULT now(),
  updated_at       timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT users_phone_unique UNIQUE (phone),
  CONSTRAINT users_email_unique UNIQUE (email)
);

CREATE INDEX ON users (lower(email::text));

-- ── merchants ─────────────────────────────────────────────────────────────────
CREATE TABLE merchants (
  id                       text PRIMARY KEY,       -- 'mch_...'
  user_id                  text NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
  business_name            text NOT NULL,
  display_name             text NOT NULL,
  slug                     text NOT NULL,
  trading_category         text,
  city                     text,
  province                 text,
  plan_id                  text NOT NULL REFERENCES plans(id) DEFAULT 'plan_free',
  payout_bank              text,
  payout_bank_code         text,
  payout_account_masked    text,                   -- last 4 digits shown in UI
  payout_account_enc       bytea,                  -- full number, encrypted at rest
  paystack_recipient_code  text,
  settlement_cycle         text NOT NULL DEFAULT 'Weekly',
  status                   merchant_status NOT NULL DEFAULT 'active',
  joined_at                timestamptz NOT NULL DEFAULT now(),
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT merchants_slug_unique UNIQUE (slug)
);

CREATE INDEX ON merchants (user_id);
