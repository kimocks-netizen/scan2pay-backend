-- 009_seed_admin.sql
-- Admin user seed — run once after all migrations
-- Password: Admin1234
-- Phone: +27616583827
-- Safe to re-run: ON CONFLICT DO NOTHING

INSERT INTO users (id, full_name, phone, email, password_hash, user_type, status, avatar_initials, phone_verified, email_verified)
VALUES (
  'usr_admin',
  'Admin User',
  '+27616583827',
  'admin@scan2pay.co.za',
  '$2b$12$4y4MVCiYQ85GIgjoyTueqOy2jtH82dwd8te1VbKRsJAMqa8S86ayq',  -- Admin1234
  NULL,
  'active',
  'AU',
  true,
  false
) ON CONFLICT (id) DO NOTHING;

INSERT INTO user_roles (id, user_id, role)
VALUES ('ur_admin', 'usr_admin', 'admin')
ON CONFLICT DO NOTHING;
