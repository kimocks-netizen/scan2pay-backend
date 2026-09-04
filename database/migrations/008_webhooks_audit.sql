-- 008_webhooks_audit.sql

-- ── webhook_events ────────────────────────────────────────────────────────────
-- Idempotency guard + replay debugging for Paystack webhooks.
CREATE TABLE webhook_events (
  id                 text PRIMARY KEY,
  provider           text NOT NULL DEFAULT 'paystack',
  event_type         text NOT NULL,
  provider_reference text NOT NULL,
  payload            jsonb NOT NULL,
  signature_valid    boolean NOT NULL,
  processed_at       timestamptz,
  error              text,
  created_at         timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT webhook_idempotency UNIQUE (provider, event_type, provider_reference)
);

-- ── scan_events ───────────────────────────────────────────────────────────────
-- Optional time-series analytics. payment_codes.scans stays as a fast counter.
CREATE TABLE scan_events (
  id              bigserial PRIMARY KEY,
  payment_code_id text NOT NULL REFERENCES payment_codes(id) ON DELETE CASCADE,
  scanned_at      timestamptz NOT NULL DEFAULT now(),
  user_agent      text,
  ip_hash         text                                -- hashed, never raw IP
);

-- ── audit_log ─────────────────────────────────────────────────────────────────
-- Free-text actor so system/cron jobs can log without a user FK.
CREATE TABLE audit_log (
  id          bigserial PRIMARY KEY,
  actor       text NOT NULL,                         -- display name or 'system'
  actor_role  text NOT NULL,                         -- 'admin' | 'merchant' | 'system'
  action      text NOT NULL,                         -- e.g. 'user.suspended'
  target      text NOT NULL,                         -- display name of affected entity
  detail      text NOT NULL,
  ip          text,
  before      jsonb,
  after       jsonb,
  created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON audit_log (created_at DESC);
CREATE INDEX ON audit_log (actor_role, created_at DESC);
