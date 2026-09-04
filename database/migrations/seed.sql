-- seed.sql — run AFTER all migrations (001→008)
-- Safe to re-run: uses INSERT ... ON CONFLICT DO NOTHING

-- ── Plans already seeded in 002_plans_pricing.sql — skip ───────────────────

-- ── Test user ─────────────────────────────────────────────────────────────────
-- password: Test1234  (bcrypt hash)
INSERT INTO users (id, full_name, phone, email, password_hash, user_type, role, status, avatar_initials, phone_verified, email_verified)
VALUES (
  'usr_001',
  'Demo Merchant',
  '+27821000001',
  'demo@scan2pay.co.za',
  '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMlJbekRSm6E6YkFqhZ9Aq5K2.',
  'vendor',
  'merchant',
  'active',
  'DM',
  true,
  false
) ON CONFLICT (id) DO NOTHING;

-- ── Test merchant ─────────────────────────────────────────────────────────────
INSERT INTO merchants (id, user_id, business_name, display_name, slug, trading_category, city, province, plan_id, settlement_cycle, status)
VALUES (
  'mch_001',
  'usr_001',
  'Demo Store',
  'Demo Store',
  'usr_001',
  'General',
  'Cape Town',
  'Western Cape',
  'plan_free',
  'Weekly',
  'active'
) ON CONFLICT (id) DO NOTHING;

-- ── Primary payment code ──────────────────────────────────────────────────────
INSERT INTO payment_codes (id, merchant_id, reference, label, caption, mode, active, is_primary, single_use, scans, payments, placement)
VALUES (
  'pc_001',
  'mch_001',
  'QR-DEMO0001',
  'Scan to Pay',
  'Scan to Pay',
  'variable',
  true,
  true,
  false,
  0,
  0,
  'Counter'
) ON CONFLICT (id) DO NOTHING;

-- ── Sample products ───────────────────────────────────────────────────────────
INSERT INTO products (id, merchant_id, name, description, price_cents, category, active)
VALUES
  ('prd_001', 'mch_001', 'Coffee',       'Freshly brewed',    3500,  'Beverages', true),
  ('prd_002', 'mch_001', 'Sandwich',     'Toasted chicken',   6500,  'Food',      true),
  ('prd_003', 'mch_001', 'Juice',        'Fresh orange',      2500,  'Beverages', true)
ON CONFLICT (id) DO NOTHING;

-- ── Fixed payment code linked to a product ────────────────────────────────────
INSERT INTO payment_codes (id, merchant_id, reference, label, caption, mode, product_id, active, is_primary, single_use, scans, payments, placement)
VALUES (
  'pc_002',
  'mch_001',
  'QR-COFFEE01',
  'Coffee — R35',
  'Tap to pay for your coffee',
  'fixed',
  'prd_001',
  true,
  false,
  false,
  0,
  0,
  'Coffee station'
) ON CONFLICT (id) DO NOTHING;

-- ── Sample transactions ───────────────────────────────────────────────────────
INSERT INTO transactions (
  id, reference, merchant_id, payment_code_id, item,
  amount_cents, platform_fee_cents, provider_fee_cents, net_cents,
  status, method, customer_label, customer_email,
  settlement_status, pricing, plan_id_at_time, pricing_version, paid_at
)
VALUES
  (
    'txn_001', 'STP300001', 'mch_001', 'pc_001', 'Scan to Pay',
    15000, 375, 225, 14400,
    'success', 'card', 'Anonymous', null,
    'settled', '{"platform_pct":250,"provider_pct":150}', 'plan_free', 'v1',
    now() - interval '2 days'
  ),
  (
    'txn_002', 'STP300002', 'mch_001', 'pc_001', 'Scan to Pay',
    8500, 213, 128, 8159,
    'success', 'card', 'Jane D', 'jane@example.com',
    'pending', '{"platform_pct":250,"provider_pct":150}', 'plan_free', 'v1',
    now() - interval '1 day'
  ),
  (
    'txn_003', 'STP300003', 'mch_001', 'pc_002', 'Coffee — R35',
    3500, 88, 53, 3359,
    'success', 'card', 'Anonymous', null,
    'pending', '{"platform_pct":250,"provider_pct":150}', 'plan_free', 'v1',
    now() - interval '3 hours'
  ),
  (
    'txn_004', 'STP300004', 'mch_001', 'pc_001', 'Scan to Pay',
    20000, 500, 300, 19200,
    'pending', 'card', 'Anonymous', null,
    'pending', '{"platform_pct":250,"provider_pct":150}', 'plan_free', 'v1',
    null
  )
ON CONFLICT (id) DO NOTHING;
