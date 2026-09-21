-- Google sign-in support: code at app/api/routes/auth.py (google_auth) was
-- referencing users.google_sub and inserting NULL phone/password_hash for
-- Google-only signups, but no migration ever added the column or relaxed
-- these NOT NULL constraints — every /auth/google call failed in prod.
alter table users add column if not exists google_sub text;
create unique index if not exists users_google_sub_unique on users (google_sub) where google_sub is not null;

alter table users alter column phone drop not null;
alter table users alter column password_hash drop not null;
