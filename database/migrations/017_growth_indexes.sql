-- 017: index created_at on users/merchants
-- Backs the admin growth-analytics endpoint (GET /admin/growth), which
-- filters and sorts both tables by created_at for week/fortnight/month
-- comparisons. Neither column was indexed before this.

create index if not exists idx_users_created_at     on users     (created_at);
create index if not exists idx_merchants_created_at  on merchants (created_at);
