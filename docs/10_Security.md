# Scan2Pay — Security Reference

> Living document. Updated as security posture changes.
> Last updated: September 2026

---

## Current Posture — What's Already Done ✅

### Authentication
- JWT access tokens (short-lived) + refresh tokens (30-day, stored hashed in DB)
- Refresh token rotation — old token revoked on every refresh
- OTP verification on registration and login (phone not yet verified)
- OTP brute force protection — max 5 attempts, 10-minute TTL
- Passwords hashed with bcrypt
- OTP bypass (`0000`) is dev-only — controlled by `DEV_OTP_BYPASS` flag, must be `False` in prod

### API
- All secrets in AWS SSM Parameter Store — never in code or env files
- Pydantic request validation on all endpoints — malformed input rejected before handler runs
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
| **No rate limiting** | API Gateway has no usage plans — brute force on `/auth/login` and `/auth/otp/verify` is possible | API Gateway usage plans + WAF rule on login endpoints |
| **No input size limits** | No max length on text fields or max value on amounts — oversized payloads could cause slow DB queries or unexpected behaviour. Practice OWASP Top 10. | Add Pydantic field constraints: name/email max 100 chars, amount max 9,900,000 cents (R99,000), description max 500 chars |
| **No WAF** | $5/month fixed cost not justified at current scale (~11k req/month). Pydantic + input validation covers the main risks. | Defer — revisit when prod traffic exceeds 500k req/month |
| **OTP bypass in prod** | `DEV_OTP_BYPASS = True` in `auth.py` — must be `False` before go-live | Set `DEV_OTP_BYPASS = False` and remove `DEV_OTP_CODE` constant |
| **Password reset** | No password reset flow — user has no way to recover account if they forget password | `POST /auth/password-reset/request` → OTP → `POST /auth/password-reset/confirm` |

### Medium Priority

| Risk | Detail | Fix |
|---|---|---|
| **No CSP headers** | No Content-Security-Policy on Next.js responses — XSS impact higher | Add CSP via `next.config.js` headers |
| **Refresh token in localStorage** | Even if access token moves to cookie, refresh token in localStorage is still XSS-exposed | Store refresh token in `httpOnly` cookie too |
| **No account lockout** | Login has no lockout after N failed attempts — only OTP has attempt limits | Add failed login counter + temporary lockout (e.g. 10 attempts → 15 min lockout) |
| **Audit log gaps** | `webhook_events` logs Paystack events but no audit trail for admin actions (who approved withdrawal, who changed plan) | Extend audit log to cover admin write actions |
| **S3 CORS `AllowedOrigins: ['*']`** | Overly permissive — any origin can PUT to the bucket with a valid presigned URL | Restrict to `scan2pay.site` and `localhost:3000` in prod |
| **No CloudTrail** | No AWS CloudTrail — no record of who called which AWS API (S3, SSM, Lambda) | Enable CloudTrail in `af-south-1` |

### Low Priority / Future

| Risk | Detail | Fix |
|---|---|---|
| **JWT secret rotation** | `JWT_SECRET` in SSM has never been rotated — all tokens would be invalidated on rotation | Document rotation procedure; rotate before go-live |
| **No MFA for admin** | Admin login is phone OTP only — no second factor for high-privilege accounts | TOTP (Google Authenticator) as optional second factor for admin/support roles |
| **Merchant data export** | No POPIA-compliant data export or deletion flow | `GET /merchants/me/export` + `DELETE /merchants/me` (soft delete) |
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
| Data subject rights (access/deletion) | 🔲 | No export or deletion endpoint |
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
- [ ] Set `DEV_OTP_BYPASS = False` in prod environment
- [ ] Add rate limiting on `/auth/login` and `/auth/otp/verify` (API Gateway usage plan)
- [ ] Restrict S3 CORS `AllowedOrigins` to production domain
- [ ] Confirm `.env` files are in `.gitignore` and never committed

### Sprint 2 (before go-live)
- [ ] Move tokens from localStorage to `httpOnly` cookies
- [ ] Add WAF WebACL with `AWSManagedRulesCommonRuleSet`
- [ ] Add account lockout after 10 failed login attempts
- [ ] Enable CloudTrail in `af-south-1`
- [ ] Add CSP headers in `next.config.js`

### Sprint 3 (post-launch)
- [ ] Password reset flow (`POST /auth/password-reset/request` + confirm)
- [ ] POPIA data export + deletion endpoints
- [ ] Extend audit log to cover admin write actions
- [ ] Dependency scanning in CI/CD (`pip-audit` + `npm audit`)
- [ ] MFA (TOTP) for admin/support roles
