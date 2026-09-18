-- Account lockout after repeated failed login attempts.
alter table users add column if not exists failed_login_attempts int not null default 0;
alter table users add column if not exists locked_until timestamptz null;
