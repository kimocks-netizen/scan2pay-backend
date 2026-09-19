# Scan2Pay — Security Reference

> Living document. Updated as security posture changes.
> Last updated: 19 September 2026 — added WebSocket real-time payment updates

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
- **`.env` never committed** — confirmed gitignored in all three repos (`scan2pay-backend`, `scan2pay-web`, `scan2pay-app`); only `.env.example` (no real values) is tracked
- Pydantic request validation on all endpoints — malformed input rejected before handler runs
- **Input size limits** — `Field(min_length=..., max_length=...)` on all text fields (names/emails 100–254 chars, descriptions 500), amount ceilings on all money fields (`le=9_900_000` cents / R99,000)
- **Rate limiting** — in-memory per-Lambda-instance limiter (`app/core/rate_limit.py`) on `register`, `login`, `otp_request`, `otp_verify`, `password-reset/request`, `password-reset/confirm`, `pay_init` (5/min for auth endpoints, 3/min for OTP/reset sends, 10/min for public pay init)
- Supabase client uses parameterised queries — no raw SQL string interpolation
- `require_admin` / `require_staff` dependency guards on all sensitive endpoints
- Webhook HMAC-SHA512 signature verification on every Paystack webhook
- **Admin action audit trail** — `admin_audit_log` table + `log_admin_action()` (`app/core/audit.py`) records every admin write (merchant/user status changes, archive/reactivate, KYC approve/reject, withdrawal approve/reject, pricing publish, manual settlement run), viewable on the web Admin → Audit log page (`GET /admin/audit-log`)
- **Dependency scanning in CI** — `pip-audit` (backend) and `npm audit --audit-level=high` (web + app) run on every push/PR via GitHub Actions (`.github/workflows/dependency-scan.yml` in each repo). Caught and fixed real CVEs in `python-jose`, `requests`, `python-multipart`, `pyasn1` on first run — see the `starlette`/`ecdsa` rows in Known Risks for the two that are explicitly ignored (documented, not silent)

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
- **S3 CORS restricted** — `AllowedOrigins` limited to `scan2pay.site`, `vula-pay.site`, `vula-pay.co.za`, `vula-pay.xyz`, `localhost:3000` (was `['*']`)
- S3 KYC lifecycle: GLACIER_IR after 90 days, deleted after 730 days
- CloudWatch logs on all Lambda functions
- API Gateway with IAM execution role — least privilege

### Frontend (scan2pay-web)
- **CSP headers** — `Content-Security-Policy` set via `next.config.ts` `headers()`, scoped to what the app actually loads (self + Google OAuth + Paystack checkout); `object-src 'none'`, `frame-ancestors 'self'`, `base-uri 'self'`; `'unsafe-eval'` only added in dev (Turbopack/React dev tooling needs it), never in production builds
- `Cross-Origin-Opener-Policy: same-origin-allow-popups` (needed for the Google OAuth popup flow)
- **Tokens moved to httpOnly cookies** — `src/app/api/proxy/[...path]/route.ts` is a same-origin BFF proxy: the browser only ever calls `/api/proxy/*` (never the API Gateway URL directly — removed from CSP `connect-src`), the proxy holds the real backend URL and attaches `Authorization: Bearer` server-side. `access_token`/`refresh_token` are stripped out of `/auth/login|register|google|refresh` JSON responses and re-issued as `httpOnly` cookies instead; `localStorage` no longer holds anything sensitive. Refresh-and-retry-once on an expired access token happens transparently inside the proxy, server-side. `middleware.ts` reads the same (now genuinely httpOnly) cookie for its login-gate redirect.

### WebSocket real-time payment updates (`11_WebSocket_RealTime.md`)
- **No raw JWT in the WebSocket URL** — the original design doc's `?token=<full access token>` approach was replaced with a short-lived ticket: `POST /auth/ws-token` (authenticated via the httpOnly cookie, through the proxy) mints a **60-second** token purpose-built for the `$connect` handshake, distinct from the real 7-day access token. Even if API Gateway/CloudWatch access logs ever captured the query string, the ticket is worthless within a minute. The real long-lived tokens never appear in a URL, ever.
- **Merchant (charge page) connections are authenticated** — `app/ws/connect.py` decodes the ticket and rejects (`401`) anything that isn't a valid, unexpired `type: "access"` token before writing the connection to DynamoDB.
- **Customer (pay page) connections are intentionally unauthenticated** — scoped only by an unguessable, server-issued `txn_id` and a 6-minute DynamoDB TTL; the only thing a connection can ever see is "did this one transaction succeed," no sensitive data.
- **Connections are ephemeral, not business data** — `websocket_connections` DynamoDB table auto-expires rows via TTL (6 minutes), fully decoupled from Supabase.
- **Least-privilege IAM** — `WebSocketConnectFunction`/`WebSocketDisconnectFunction` each get `DynamoDBCrudPolicy` scoped to just that one table; the main API Lambda gets read-only `DynamoDBReadPolicy` + `execute-api:ManageConnections` (needed to push `PAYMENT_SUCCESS`), nothing broader.
- **Known accepted trade-off**: the 60-second ws-token is a real (if extremely short-lived) bearer token — technically usable against any authenticated endpoint, not just the WebSocket handshake, within that window. Not worth the added complexity of a purpose-scoped token type at this scale; revisit if that ever changes.

---

## Known Risks & Backlog 🔲

### Low Priority / Future

| Risk | Detail | Fix |
|---|---|---|
| **No MFA for admin** | Admin login is phone OTP only — no second factor for high-privilege accounts | TOTP (Google Authenticator) as optional second factor for admin/support roles — not now |
| **`starlette` CVEs (transitive)** | Pinned at 0.38.6 via `fastapi==0.115.0`, which caps `starlette<0.39.0` — every fixed version (0.40.0+) is outside that range. `pip-audit` explicitly ignores these IDs (`PYSEC-2026-1943/1941/161/2281/2280/249/248`) in CI with a comment, not silently. | Requires a `fastapi` major-version upgrade — bigger, riskier change on a payments backend, needs its own review before doing it |
| **`ecdsa` CVE (transitive, no fix)** | Pulled in by `python-jose`; `PYSEC-2026-1325` (timing side-channel in EC operations) has no patched version. Not exploitable here — our JWTs use `HS256` only (`app/core/security.py`), never an elliptic-curve algorithm. Ignored in CI with a comment. | None needed while `jwt_algorithm` stays `HS256`; revisit only if the app ever adopts an EC-based JWT algorithm |

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
| Data subject rights (access/deletion) | ✅ | `DELETE /merchants/me` (archive → anonymise after 90 days). Self-service export endpoint deliberately not built — see Won't do. |
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
- [x] Confirm `.env` files are in `.gitignore` and never committed

### Sprint 2 (before go-live)
- [x] Move tokens from localStorage to `httpOnly` cookies (BFF proxy at `/api/proxy`)
- [x] Add CSP headers in `next.config.ts`
- [x] Restrict S3 CORS `AllowedOrigins` to production domains
- [x] Extend audit log to cover admin write actions (`admin_audit_log` table + `/admin/audit-log`)

### Sprint 3 (post-launch)
- [x] Dependency scanning in CI/CD (`pip-audit` + `npm audit`)
- [ ] MFA (TOTP) for admin/support roles — not now

### Won't do (cost vs. benefit)
- **WAF WebACL** — ~$5/month fixed cost not justified at current scale (~11k req/month). Rate limiting + Pydantic input validation cover the realistic risk at this traffic level. Revisit only if prod traffic exceeds ~500k req/month or we see actual abuse patterns in CloudWatch logs.
- **CloudTrail** — adds ongoing per-event storage/ingestion cost for AWS API call logging we don't need at this scale. CloudWatch logs on every Lambda already cover application-level activity; CloudTrail would only add infra-level API call tracing. Deferred while cost control is the priority.
- **Merchant self-service data export** (`GET /merchants/me/export`) — decided not to build this. The deletion/anonymisation side of POPIA data-subject rights is already covered by `DELETE /merchants/me`; a self-service export endpoint isn't being added on top of it.
- **JWT secret rotation** — not doing a rotation procedure/schedule for `JWT_SECRET`. Accepted as-is.
