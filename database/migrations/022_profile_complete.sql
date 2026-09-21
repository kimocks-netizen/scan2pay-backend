-- Google sign-up creates a user without a phone number, a default "vendor"
-- type and a placeholder business name. This flags those accounts so the
-- frontend can force a "finish your profile" step before anything else —
-- existing (phone-registered) users are already complete by definition.
alter table users add column if not exists profile_complete boolean not null default true;
