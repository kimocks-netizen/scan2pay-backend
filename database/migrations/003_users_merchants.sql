-- 003_users_merchants.sql

-- ── users ─────────────────────────────────────────────────────────────────────
CREATE TABLE users (
  id               text PRIMARY KEY,               -- 'usr_...'
  full_name        text NOT NULL,
  phone            text NOT NULL,
  email            citext,
  password_hash    text NOT NULL,
  user_type        user_type,                       -- NULL for admin/staff users
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

-- ── user_roles ────────────────────────────────────────────────────────────────
-- One row per role per user. Roles: merchant | admin | support
CREATE TABLE user_roles (
  id         text PRIMARY KEY,
  user_id    text NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  role       text NOT NULL CHECK (role IN ('merchant', 'admin', 'support')),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT user_roles_user_role_unique UNIQUE (user_id, role)
);

CREATE INDEX ON user_roles (user_id);

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
  payout_account_masked    text,
  payout_account_enc       bytea,
  paystack_recipient_code  text,
  settlement_cycle         text NOT NULL DEFAULT 'Weekly',
  status                   merchant_status NOT NULL DEFAULT 'active',
  joined_at                timestamptz NOT NULL DEFAULT now(),
  created_at               timestamptz NOT NULL DEFAULT now(),
  updated_at               timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT merchants_slug_unique UNIQUE (slug)
);

CREATE INDEX ON merchants (user_id);
