-- 024: multi-device push tokens
-- Replace single expo_push_token column with a dedicated table
-- so a merchant logged in on 2 phones both receive push notifications.

CREATE TABLE IF NOT EXISTS push_tokens (
  id          text PRIMARY KEY,           -- pt_<hex>
  merchant_id text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
  token       text NOT NULL,
  created_at  timestamptz NOT NULL DEFAULT now(),
  UNIQUE (merchant_id, token)             -- no duplicates per merchant
);

CREATE INDEX IF NOT EXISTS push_tokens_merchant ON push_tokens (merchant_id);

-- keep expo_push_token column for now (nullable) — will drop in a later migration
-- once all push sends are reading from push_tokens table
