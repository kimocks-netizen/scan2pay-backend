-- 023: push notifications + notification prefs

-- merchants: push token + enabled flag
ALTER TABLE merchants
  ADD COLUMN IF NOT EXISTS expo_push_token  text,
  ADD COLUMN IF NOT EXISTS push_enabled     boolean NOT NULL DEFAULT true;

-- notifications table (bell)
CREATE TABLE IF NOT EXISTS notifications (
  id           text PRIMARY KEY,
  merchant_id  text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
  type         text NOT NULL,
  title        text NOT NULL,
  body         text NOT NULL,
  data         jsonb NOT NULL DEFAULT '{}',
  read_at      timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS notifications_merchant_created
  ON notifications (merchant_id, created_at DESC);

CREATE INDEX IF NOT EXISTS notifications_merchant_unread
  ON notifications (merchant_id, read_at)
  WHERE read_at IS NULL;

-- notification_prefs table
CREATE TABLE IF NOT EXISTS notification_prefs (
  merchant_id           text PRIMARY KEY REFERENCES merchants(id) ON DELETE CASCADE,
  payments_push         boolean NOT NULL DEFAULT true,
  payments_sms          boolean NOT NULL DEFAULT true,
  payments_sms_mode     text NOT NULL DEFAULT 'instant' CHECK (payments_sms_mode IN ('instant', 'digest')),
  events_push           boolean NOT NULL DEFAULT true,
  events_sms            boolean NOT NULL DEFAULT true,
  updated_at            timestamptz NOT NULL DEFAULT now()
);
