# Scan2Pay — Security Reference

> Living document. Updated as security posture changes.
> Last updated: 18 September 2026

---

## Current Posture — What's Already Done ✅

### Authentication
- JWT access tokens (short-lived) + refresh tokens (30-day, stored hashed in DB)
- Refresh token rotation — old token revoked on every refresh
- OTP verification on registration and login (phone not yet verified)
- OTP brute force protection — max 5 attempts, 10-minute TTL
- Passwords hashed with bcrypt
- OTP bypass is a master code stored in SSM (`master_otp`), not a hardcoded dev flag — empty in prod means bypass is off
- Password reset flow — `POST /auth/password-reset/request` → OTP → `POST /auth/password-reset/confirm`
- **Account lockout** — 5 failed login attempts locks the account for 5 minutes (`app/core/rate_limit.py` handles the per-IP side, `users.failed_login_attempts`/`locked_until` handle the per-account side)

### API
- All secrets in AWS SSM Parameter Store — never in code or env files
- Pydantic request validation on all endpoints — malformed input rejected before handler runs
- **Input size limits** — `Field(min_length=..., max_length=...)` on all text fields (names/emails 100–254 chars, descriptions 500), amount ceilings on all money fields (`le=9_900_000` cents / R99,000)
- **Rate limiting** — in-memory per-Lambda-instance limiter (`app/core/rate_limit.py`) on `register`, `login`, `otp_request`, `otp_verify`, `password-reset/request`, `password-reset/confirm`, `pay_init` (5/min for auth endpoints, 3/min for OTP/reset sends, 10/min for public pay init)
- Supabase client uses parameterised queries — no raw SQL string interpolation
- `require_admin` / `require_staff` dependency guards on all sensitive endpoints
- Webhook HMAC-SHA512 signature verification on every Paystack webhook

### Data
- Full bank account numbers never stored — only masked (`**** 1407`)
- KYC documents stored in private S3 bucket — no public access on `kyc/` prefix
- CMS images publicly readable (`cms/` prefix only) — intentional
- Presigned URLs for KYC access — 15-minute expiry, scoped to specific object
- Merchant can only view their own documents (ownership check on `merchant_id`)
- Bank validation result stored (verified/not) — raw ID number discarded after Paystack call

### Payments
- Paystack handles all card data — we are out of PCI-DSS scope for card storage
- Webhook idempotency — `UNIQUE(provider, event_type, provider_reference)` prevents replay attacks
- Transfer recipient codes stored server-side only — never exposed to frontend

### Infrastructure
- S3 bucket: `BlockPublicAcls`, `IgnorePublicAcls` enabled; `kyc/` prefix fully private
- S3 KYC lifecycle: GLACIER_IR after 90 days, deleted after 730 days
- CloudWatch logs on all Lambda functions
- API Gateway with IAM execution role — least privilege

---

## Known Risks & Backlog 🔲

### High Priority

| Risk | Detail | Fix |
|---|---|---|
| **Tokens in localStorage** | `accessToken` + `refreshToken` stored in localStorage — vulnerable to XSS. Cookie-only would be safer. | Move to `httpOnly` cookies server-side. Requires a Next.js API route as token proxy. |

### Medium Priority

| Risk | Detail | Fix |
|---|---|---|
| **No CSP headers** | No Content-Security-Policy on Next.js responses — XSS impact higher | Add CSP via `next.config.js` headers |
| **Refresh token in localStorage** | Even if access token moves to cookie, refresh token in localStorage is still XSS-exposed | Store refresh token in `httpOnly` cookie too |
| **Audit log gaps** | `webhook_events` logs Paystack events but no audit trail for admin actions (who approved withdrawal, who changed plan) | Extend audit log to cover admin write actions |
| **S3 CORS `AllowedOrigins: ['*']`** | Overly permissive — any origin can PUT to the bucket with a valid presigned URL | Restrict to `scan2pay.site` and `localhost:3000` in prod |
| **No CloudTrail** | No AWS CloudTrail — no record of who called which AWS API (S3, SSM, Lambda) | Enable CloudTrail in `af-south-1` |

### Low Priority / Future

| Risk | Detail | Fix |
|---|---|---|
| **JWT secret rotation** | `JWT_SECRET` in SSM has never been rotated — all tokens would be invalidated on rotation | Document rotation procedure; rotate before go-live |
| **No MFA for admin** | Admin login is phone OTP only — no second factor for high-privilege accounts | TOTP (Google Authenticator) as optional second factor for admin/support roles |
| **Merchant data export** | `DELETE /merchants/me` (archive, POPIA-anonymise after 90 days) is done. No self-service data export endpoint yet. | `GET /merchants/me/export` |
| **Dependency scanning** | No automated CVE scanning on Python or npm dependencies | Add `pip-audit` + `npm audit` to CI/CD |
| **Secrets in `.env`** | Local `.env` files contain real Paystack test keys — should not be committed | Confirm `.env` is in `.gitignore`; rotate keys if ever committed |

---

## POPIA Compliance (SA Data Protection)

South Africa's Protection of Personal Information Act applies to all personal data we process.

| Requirement | Status | Notes |
|---|---|---|
| Lawful basis for processing | ✅ | Contract (payment processing) |
| Data minimisation | ✅ | No full account numbers, ID numbers discarded after validation |
| Storage limitation | ✅ | KYC docs auto-deleted from S3 after 730 days |
| Access controls | ✅ | Role-based access, merchant can only see own data |
| Breach notification | 🔲 | No incident response plan documented |
| Data subject rights (access/deletion) | 🟡 | `DELETE /merchants/me` (archive → anonymise after 90 days) done; data export endpoint still missing |
| Privacy policy | 🔲 | Not written yet |
| Information officer registration | 🔲 | Required for SA businesses processing personal info |

---

## PCI-DSS Scope

**We are out of scope for card data storage** — Paystack handles all card processing via their hosted checkout. We never see, transmit, or store card numbers, CVVs, or full PANs.

What we do store:
- `authorization_code` on transactions (Paystack token for recurring charges) — this is a Paystack reference, not a card number
- `last4` + `card_type` on transactions — explicitly allowed under PCI-DSS

**Maintain scope reduction by:**
- Never logging raw Paystack webhook payloads that contain card data
- Never passing card data through our API
- Keeping Paystack Inline JS as the only card entry point

---

## Sprint Backlog — Security Items

### Sprint 1 (before beta)
- [x] OTP bypass is SSM-controlled (`master_otp`), not a hardcoded flag — empty in prod disables it
- [x] Add rate limiting on `/auth/login`, `/auth/otp/verify`, `/auth/register`, `/auth/otp/request`, password-reset endpoints, and public `pay_init`
- [x] Add input size limits (Pydantic `Field` constraints) across all request schemas
- [x] Add account lockout after 5 failed login attempts (5-minute lock)
- [x] Password reset flow (`POST /auth/password-reset/request` + confirm)
- [ ] Restrict S3 CORS `AllowedOrigins` to production domain
- [ ] Confirm `.env` files are in `.gitignore` and never committed

### Sprint 2 (before go-live)
- [ ] Move tokens from localStorage to `httpOnly` cookies
- [ ] Enable CloudTrail in `af-south-1`
- [ ] Add CSP headers in `next.config.js`

### Sprint 3 (post-launch)
- [ ] POPIA data export + deletion endpoints
- [ ] Extend audit log to cover admin write actions
- [ ] Dependency scanning in CI/CD (`pip-audit` + `npm audit`)
- [ ] MFA (TOTP) for admin/support roles

### Won't do (cost vs. benefit)
- **WAF WebACL** — ~$5/month fixed cost not justified at current scale (~11k req/month). Rate limiting + Pydantic input validation cover the realistic risk at this traffic level. Revisit only if prod traffic exceeds ~500k req/month or we see actual abuse patterns in CloudWatch logs.
