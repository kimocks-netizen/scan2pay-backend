-- Audit trail for admin write actions (suspend, archive, KYC review, withdrawal
-- decisions, pricing changes, manual settlements) — previously only Paystack
-- webhook events were logged, not who-did-what on the admin side.
create table if not exists admin_audit_log (
  id uuid primary key default gen_random_uuid(),
  admin_id text not null references users(id),
  action text not null,
  target_type text not null,
  target_id text not null,
  detail jsonb,
  created_at timestamptz not null default now()
);

create index if not exists idx_admin_audit_log_created_at on admin_audit_log(created_at desc);
create index if not exists idx_admin_audit_log_target on admin_audit_log(target_type, target_id);
