# Scan2Pay — Sprint Planning

> Working backlog. Items move from To Do → In Progress → Done.
> Last updated: September 2026

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
- Security Sprints 1 & 2 — rate limiting, input limits, account lockout, password reset, httpOnly cookies, CSP, S3 CORS, audit log, dependency scanning
- WebSocket real-time payment updates — `useChargeWebSocket` / `usePayWebSocket`, DynamoDB connections table, `$connect`/`$disconnect` Lambdas, `broadcast_to_txn` wired into webhook handler, polling kept as fallback
- Dashboard `refetchOnWindowFocus` — updates on tab switch after payment

---

## 🏃 Current Sprint — Sprint 2: Growth & Payments

### In Progress
- [ ] Catalog page taxi/tip/vendor label adaptation (routes, fares, SKU hidden for taxi)

### To Do

#### 💳 Payment Methods
- [ ] **Capitec Pay** — Paystack supports Capitec Pay as a channel; enable on `POST /charges` and `POST /pay/:reference/initialise` by adding `channels: ["card", "capitec_pay"]` to Paystack initialise calls. No new backend routes needed — Paystack renders the Capitec Pay button in the popup automatically.
- [ ] **Apple Pay** — register `scan2pay.site` domain with Paystack (`POST /apple-pay/domain`). Add `channels: ["card", "apple_pay"]`. Requires HTTPS + domain verification file served at `/.well-known/apple-developer-merchantid-domain-association`.
- [ ] **Google Pay** — add `channels: ["card", "google_pay"]` to Paystack initialise. No domain registration needed. Works in Chrome on Android automatically once channel is enabled.
- [ ] **Paystack production keys** — swap SSM params `PAYSTACK_SECRET_KEY` / `PAYSTACK_PUBLIC_KEY` / `PAYSTACK_WEBHOOK_SECRET` to live keys. Update Paystack dashboard webhook URL to `https://{api}/webhooks/paystack`. Test with a real R1.00 transaction before go-live.

#### 📧 Notifications & Comms
- [ ] **Email notifications** — transactional emails on payment success, KYC decision, withdrawal decision
  - Provider: AWS SES (same region `af-south-1`, already in the AWS account)
  - Verify `noreply@scan2pay.site` (or `noreply@vula-pay.co.za`) as SES sender identity
  - Templates: payment receipt (merchant + customer), KYC approved/rejected, withdrawal approved/rejected
  - Backend: `app/services/email_service.py` — `send_email(to, subject, html_body)`
  - Wire into: `webhooks.py` `_handle_charge_success()`, `admin.py` KYC decision, `admin.py` withdrawal decision
  - Merchant opt-in: read `notification_channel` preference before sending
- [ ] **SMS (WinSMS) — extend coverage**
  - Currently: KYC decision + withdrawal decision only
  - Add: payment success SMS to merchant ("R85.00 received from customer")
  - Merchant opt-in: read `notification_channel` preference
- [ ] **WhatsApp notifications** — future channel, not now
  - Provider: Twilio WhatsApp API or Meta Cloud API — decision needed before building
  - Placeholder: `notification_channel = "whatsapp"` stored but not yet sent
  - Mark as "coming soon" in settings UI
- [ ] **Notification preferences** — merchant chooses preferred channel
  - Add `notification_channel` column on merchants (`sms` default, `email`, `whatsapp` future)
  - Settings page: channel selector (SMS ticked by default, WhatsApp greyed out with "coming soon")
  - Backend: read preference before sending any notification
- [ ] **Custom transactional emails** — branded HTML templates
  - Use AWS SES with HTML templates stored in `app/services/email_service.py`
  - Branding: Scan2Pay / Vula Pay logo, primary colour, footer with unsubscribe link (POPIA)
  - Templates needed: payment receipt, OTP, KYC decision, withdrawal decision, password reset

#### 📊 Analytics & Ads
- [ ] **Google Analytics 4** — add `gtag.js` to `scan2pay-web` and `vula-pay-home`
  - Add `NEXT_PUBLIC_GA_MEASUREMENT_ID` env var
  - Track: page views (automatic), charge created, payment success, QR scan
  - Add to CSP `connect-src` and `script-src`
- [ ] **Google Ads conversion tracking** — fire conversion event on payment success on `/pay/[reference]`
  - Add `NEXT_PUBLIC_GADS_CONVERSION_ID` + `NEXT_PUBLIC_GADS_CONVERSION_LABEL` env vars
  - Fire `gtag('event', 'conversion', {...})` in `usePayWebSocket` `onPaymentSuccess` callback
- [ ] **Google Search Console** — verify `scan2pay.site` and `vula-pay.co.za` ownership
  - Add verification meta tag to `<head>` in `layout.tsx`

#### 🔐 Auth
- [ ] **Google Sign-In fix** — current web flow uses `access_token` via tokeninfo endpoint; confirm it works end-to-end in prod with the live Google client ID. Known issue: `azp` vs `aud` mismatch on some token types — may need to switch to `id_token` flow via `@react-oauth/google` on web.
- [ ] **Remove polling fallback** — `useChargeWebSocket` polling fallback (1.5s `refetchInterval`) confirmed stable in prod; remove the `useQuery` + `useEffect` polling block from `/charge` page.

#### 🏗️ Infrastructure
- [ ] **Custom domain for API Gateway** — map `api.scan2pay.site` to the API Gateway endpoint via Route 53 + ACM certificate
- [ ] **Paystack webhook URL** — confirm `https://api.scan2pay.site/webhooks/paystack` is set in Paystack dashboard
- [ ] **Error monitoring** — CloudWatch alarms on Lambda error rate > 1% + p99 duration > 5s. Optional: Sentry for frontend.

---

## 🔲 Sprint 3 — Mobile Push Notifications

- [ ] **Firebase Cloud Messaging (FCM) — Android push notifications**
  - Add `@react-native-firebase/messaging` to `scan2pay-app`
  - Request notification permission on app launch
  - Register FCM token on login → `POST /merchants/me/push-token` (new endpoint)
  - Backend: store `fcm_token` on merchants table
  - Trigger: payment success → `firebase-admin` SDK → `send()` to merchant's FCM token
  - Lambda: add `firebase-admin` to `requirements.txt`, initialise with service account from SSM
- [ ] **Apple Push Notification Service (APNs) — iOS push notifications**
  - Same `@react-native-firebase/messaging` package handles APNs via FCM on iOS
  - Requires: APNs key (`.p8`) uploaded to Firebase console, Apple Developer team ID + key ID
  - Add APNs auth key to Firebase project settings — no code change needed beyond FCM setup
  - Test on physical iOS device (APNs does not work on simulator)
- [ ] **Push notification types**
  - `PAYMENT_RECEIVED` — "R85.00 received" — fires from `_handle_charge_success()` alongside WebSocket broadcast
  - `KYC_DECISION` — "Your KYC has been approved" — fires from admin KYC endpoint
  - `WITHDRAWAL_DECISION` — "Your withdrawal of R500 has been approved" — fires from admin withdrawal endpoint
- [ ] **`POST /merchants/me/push-token`** — upsert FCM token for logged-in merchant
- [ ] **`DELETE /merchants/me/push-token`** — remove on logout
- [ ] **Notification permission UI** — prompt on first launch, respect OS-level permission

---

## 🔲 Sprint 4 — Post-Launch

- [ ] POPIA compliance — data export + deletion endpoints
- [ ] Multiple bank accounts (up to 2 per merchant, default selection, withdrawal account picker)
- [ ] Merchant plan upgrade flow (self-serve request → support/admin approves)
- [ ] MFA (TOTP) for admin/support roles
- [ ] WhatsApp notifications (Twilio or Meta Cloud API — provider decision first)
- [ ] Account status history (`account_status_events` table, admin timeline view)
- [ ] Support commission — qualify on first transaction, not signup

