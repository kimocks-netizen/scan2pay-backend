# Scan2Pay — Sprint Planning

> Working backlog. Items move from To Do → In Progress → Done.
> Last updated: September 2026

---

## 🏃 Current Sprint — Sprint 1

### In Progress
- [ ] Catalog page taxi/tip/vendor label adaptation (routes, fares, SKU hidden for taxi)

### To Do
- [ ] **Multiple bank accounts** — up to 2 per merchant, default selection, withdrawal account picker
  - Migration: `merchant_bank_accounts` table
  - Backend: GET/POST/PATCH/DELETE `/merchants/me/bank-accounts`
  - Frontend: settings page list + add/remove + set default
  - Frontend: withdrawal page account selector
  - See `09_Backend_Roadmap.md` for full spec

- [ ] **Support commission — qualify on first transaction, not signup**
  - A referred merchant only counts toward support commission once they make their first successful payment
  - Prevents support agents creating ghost accounts to inflate their numbers
  - Backend: `GET /support/my-stats` — filter `referred_by` merchants where at least 1 `success` transaction exists
  - `recent_signups` table in response: add `first_transaction_at` (null if none yet) and `has_transacted` boolean
  - Frontend: `/admin/my-stats` recent signups table — add "First transaction" column showing date or "Not yet" badge

- [ ] **Notification preferences** — merchant chooses preferred channel
  - Add `notification_channel` column on merchants (`sms` default, `email`/`whatsapp` future)
  - Settings page: channel selector (SMS ticked by default, others greyed out with "coming soon")
  - Backend: read preference before sending WinSMS

- [ ] **Password reset flow**
  - `POST /auth/password-reset/request` — sends OTP to phone
  - `POST /auth/password-reset/confirm` — verifies OTP + sets new password
  - Frontend: "Forgot password?" link on login page
  - on my apple when i click enter Password filed it zooms to enlarge if i click in amy input field why is it doing this lets remove this zoom effect, then where we enter verificication code otp lets use small box when you ebter didgit it will aoutomatically moves to next box, alsoa dd your verification code was send to your number ending *** 84 some thing like this , lastly i ddi not received otp

- [ ] **Security Sprint 1** (see `10_Security.md`)
  - Set `DEV_OTP_BYPASS = False` for prod environment
  - Rate limiting on `/auth/login` + `/auth/otp/verify`
  - Restrict S3 CORS to production domain
  - Confirm `.env` in `.gitignore`

---

## 🔲 Sprint 2 — Production Readiness

- [ ] Paystack live keys (swap SSM params)
- [ ] `POST /apple-pay/domain` — register `scan2pay.site`
- [ ] Custom domain for API Gateway
- [ ] Paystack webhook URL confirmed in Paystack dashboard
- [ ] Wire `GET /cms/homepage` to scan2pay.site marketing site
- [ ] Verify settlement cron running in prod (CloudWatch logs)
- [ ] **Security Sprint 2**
  - Move tokens from localStorage to `httpOnly` cookies
  - WAF — **deferred** (see `10_Security.md`)
  - Input size validation — Pydantic field constraints on all schemas (name max 100, amount max R99,000, etc.)

- [ ] **Password reset**
  - Channel: SMS (default) — email when configured, WhatsApp future
  - `POST /auth/password-reset/request` — accepts phone or email, sends OTP
  - `POST /auth/password-reset/confirm` — verifies OTP + sets new password
  - Frontend: "Forgot password?" link on login page → phone/email input → OTP → new password

- [ ] **Login with Google**
  - OAuth2 flow via Google Identity
  - Post-login: if new user → create account → call `PATCH /merchants/me/referral` if `?ref=` present
  - If existing user → issue JWT same as normal login
  - Add to sprint backlog — design OAuth flow before building
  - Account lockout after 10 failed login attempts
  - Enable CloudTrail in `af-south-1`
  - CSP headers in `next.config.js`

---

## 🔲 Sprint 3 — Post-Launch

- [ ] POPIA compliance — data export + deletion endpoints
- [ ] Extend audit log to cover admin write actions (who approved withdrawal, who changed plan)
- [ ] Merchant plan upgrade flow (self-serve request → support/admin approves)
- [ ] MFA (TOTP) for admin/support roles
- [ ] Dependency scanning in CI/CD (`pip-audit` + `npm audit`)
- [ ] Error monitoring (Sentry or CloudWatch alarms)
- [ ] **Security Sprint 3**
  - Password reset flow
  - POPIA data export + deletion
  - Audit log for admin actions

---

## ✅ Completed

- Phase 1 — Merchant (all routes, charge, QR, catalog, withdrawals, reports)
- Phase 2 — Admin console (all pages, role-based nav, mobile nav)
- Phase 3 — Referral signup flow (QR deep-link, post-registration PATCH)
- Phase 4 — Notifications (WinSMS on KYC decision + withdrawal decision)
- KYC system (S3 upload, staff review, Glacier restore, Paystack bank check)
- CMS system (4 slots, public S3, home page wired)
- Support role (commission tracking, referral QR, my-stats page)
- Admin nav badges (pending KYC + withdrawal counts)
- Mobile responsive tables (dashboard, KYC, people)
- Catalog user-type adaptation (taxi routes, tip options, vendor products)
