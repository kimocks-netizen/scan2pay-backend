-- 018: account archival (soft delete) + reactivation tracking
--
-- Merchant-initiated or admin-forced account closure. We never hard-delete a
-- row on request — transactions/withdrawals reference merchant_id and must be
-- kept for accounting/tax retention regardless of what happens to the account.
-- "Permanent deletion" after the 90-day window (see purge_archived_accounts
-- cron) means anonymising personal fields on an already-archived, never-
-- reactivated account — the row shell and its financial history stay intact.
--
-- merchant_status already has 'closed' (unused until now) — reused here.
-- user_status only has active/suspended, so we add 'archived'.

alter type user_status add value if not exists 'archived';

alter table users
  add column if not exists archived_at         timestamptz,
  add column if not exists archived_by         text references users(id),
  add column if not exists archive_reason      text,
  add column if not exists reactivated_at      timestamptz,
  add column if not exists reactivation_count  integer not null default 0,
  add column if not exists anonymized_at       timestamptz;

alter table merchants
  add column if not exists archived_at    timestamptz,
  add column if not exists archived_by    text references users(id),
  add column if not exists archive_reason text;

-- No partial index on status = 'archived' here: a freshly-added enum value
-- can't be referenced until it's committed, and this whole file runs as one
-- transaction in the Supabase SQL editor. Plain index instead — still helps
-- the purge cron's `WHERE status = 'archived' AND archived_at < cutoff` scan
-- without needing the new value at creation time.
create index if not exists idx_users_status_archived_at on users (status, archived_at);
