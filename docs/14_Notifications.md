# VulaPay — Notifications System

> Covers all notification channels across `scan2pay-app` (Expo/React Native),
> `scan2pay-web` (Next.js), and `scan2pay-backend` (FastAPI/SAM).
> Last updated: 2026

---

## Overview

Merchants need to know when things happen to their account — payments received,
withdrawals decided, KYC outcomes. This document defines every notification
channel, what triggers each one, how preferences work, and the full
implementation plan.

---

## Channels

| Channel | Delivery | Who controls it | Per-event or digest |
|---|---|---|---|
| In-app bell (web + app) | Real-time via WebSocket + DB | Always on | Per-event |
| Push notifications (app) | Expo Push / APNs / FCM | Merchant can disable | Per-event |
| SMS | WinSMS | Merchant: per-event or daily digest | Per-event or 19:00 digest |
| WhatsApp | Meta Cloud API | Merchant: per-event or daily digest | Per-event or 19:00 digest |
| Email | SES | Always on | Daily digest only (19:00) |

---

## Notification Events

These are the events that trigger notifications. Not every channel fires for
every event — see the matrix below.

| Event | Bell | Push | SMS | WhatsApp | Email |
|---|---|---|---|---|---|
| Payment received | ✅ | ✅ | ✅ (pref) | ✅ (pref) | digest |
| Withdrawal approved | ✅ | ✅ | ✅ always | ✅ always | digest |
| Withdrawal rejected | ✅ | ✅ | ✅ always | ✅ always | digest |
| KYC approved | ✅ | ✅ | ✅ always | ✅ always | digest |
| KYC rejected | ✅ | ✅ | ✅ always | ✅ always | digest |

**"always"** = sent regardless of digest preference — these are high-importance
events the merchant must not miss.

**"pref"** = controlled by `notification_prefs.payments_sms` /
`notification_prefs.payments_whatsapp` — merchant can choose per-event or
daily digest.

---

## Bell Notification (In-App)

### Why it matters

The bell is the only channel that works without any external service. It is
always on, costs nothing, and gives merchants a history of events they can
scroll through. It is the fallback when push/SMS/WhatsApp are disabled or
fail.

Users are not always in the app — but when they open it, the bell badge tells
them immediately what they missed. This is important.

### How it works

1. Backend writes a row to `notifications` table on every event.
2. If the merchant has an active WebSocket connection (app or web), the backend
   also pushes a real-time `NOTIFICATION` message via the existing
   `websocket_broadcast` service.
3. The app/web bell icon shows an unread count badge. Tapping it opens a
   notification drawer/panel.
4. Marking as read updates `notifications.read_at`.

### `notifications` table (new)

```sql
CREATE TABLE notifications (
  id           text PRIMARY KEY,          -- notif_…
  merchant_id  text NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
  type         text NOT NULL,             -- 'payment_received' | 'withdrawal_approved' | etc.
  title        text NOT NULL,
  body         text NOT NULL,
  data         jsonb NOT NULL DEFAULT '{}', -- txn_id, amount_cents, reference, etc.
  read_at      timestamptz,
  created_at   timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX ON notifications (merchant_id, created_at DESC);
CREATE INDEX ON notifications (merchant_id, read_at) WHERE read_at IS NULL;
```

### Backend API endpoints (new)

```
GET  /merchants/me/notifications          → list (limit 50, unread first)
POST /merchants/me/notifications/read-all → mark all read
PATCH /merchants/me/notifications/{id}    → mark single read
```

### WebSocket push (existing infrastructure)

The existing `websocket_broadcast.broadcast_to_txn()` targets a specific
`txn_id`. For notifications we need to broadcast to a merchant's open
connections. The `WebSocketConnectionsTable` already has a `merchant_id-index`
GSI — use it.

Add `broadcast_to_merchant(merchant_id, message)` to
`app/services/websocket_broadcast.py`:

```python
def broadcast_to_merchant(merchant_id: str, message: dict) -> None:
    """Push a message to all WebSocket connections for a merchant."""
    # query merchant_id-index GSI — same pattern as broadcast_to_txn
```

Message shape:
```json
{
  "type": "NOTIFICATION",
  "notification": {
    "id": "notif_abc123",
    "type": "payment_received",
    "title": "Payment received",
    "body": "R85.00 from Anonymous",
    "data": { "txn_id": "txn_…", "amount_cents": 8500 },
    "created_at": "2026-09-19T14:32:00Z"
  }
}
```

---

## Push Notifications (scan2pay-app only)

### Why it matters

Push is the only way to reach a merchant when the app is closed. A merchant
running a busy stall cannot keep the app open — they need a tap on the shoulder
when a payment lands.

### Stack

- **Expo Push Notifications** (`expo-notifications`) — single SDK for both
  APNs (iOS) and FCM (Android).
- **Expo Push Service** — Expo's free relay. We send one HTTP request to
  `https://exp.host/--/api/v2/push/send`, Expo handles APNs/FCM routing.
- No direct APNs/FCM credentials needed in the backend — Expo manages them.

### Token registration flow

1. On app launch (after auth), call `Notifications.getExpoPushTokenAsync()`.
2. POST the token to `PATCH /merchants/me/push-token` (new endpoint).
3. Backend stores it in `merchants.expo_push_token`.
4. On logout / account deletion, DELETE the token.

### `merchants` table additions

```sql
ALTER TABLE merchants ADD COLUMN expo_push_token text;
ALTER TABLE merchants ADD COLUMN push_enabled    boolean NOT NULL DEFAULT true;
```

### Backend: send push

New `app/services/push_service.py`:

```python
async def send_push(token: str, title: str, body: str, data: dict = {}) -> bool:
    """Send via Expo Push API. Returns True on success."""
    # POST https://exp.host/--/api/v2/push/send
    # { "to": token, "title": title, "body": body, "data": data, "sound": "default" }
```

### Permissions (app)

- Request permission on first launch after login (not on cold start before auth).
- iOS: `Notifications.requestPermissionsAsync()` — shows system prompt.
- Android 13+: `POST_NOTIFICATIONS` permission — handled by `expo-notifications`.
- Store permission status in Zustand; don't re-prompt if denied.

### app.json additions needed

```json
{
  "expo": {
    "plugins": [
      ["expo-notifications", {
        "icon": "./assets/images/notification-icon.png",
        "color": "#0E6BE1",
        "sounds": []
      }]
    ]
  }
}
```

---

## SMS Notifications

### Current state

`app/services/sms_service.py` already has `send_sms(to, message)` via WinSMS.
It is already wired into:
- `admin.py` → `_notify_merchant()` for withdrawal approved/rejected
- `kyc.py` → KYC approved/rejected

Payment received SMS does **not** exist yet — it needs to be added to
`webhooks.py → _handle_charge_success()`.

### Preference: per-event vs daily digest

Merchants can choose:
- **Per-event** (default): SMS sent immediately on every payment.
- **Daily digest**: No per-payment SMS. One summary SMS at 19:00 SAST.

Withdrawal and KYC notifications are always sent immediately regardless of
this preference — they are too important to batch.

### Daily digest SMS format

```
VulaPay Daily Summary — 19 Sep 2026

Payments today: 6
Total received: R610.00
Fees: R36.60
Net earned: R573.40

View transactions: vula-pay.co.za/transactions
```

---

## WhatsApp Notifications

### Current state

`whatsapp_templates.md` defines 5 approved templates. `13_VulaPay_WhatsApp_Integration_Plan.md`
covers the full bot and outbound notification architecture.

**This document does not change any of that.** The WhatsApp integration plan
stands as-is. What this document adds is:

1. The `notification_prefs` table (which WhatsApp reads from).
2. The daily digest WhatsApp template (new — needs Meta approval).
3. The 19:00 cron that sends digests.

### Preference: per-event vs daily digest

Same as SMS — merchants choose per-event or daily digest for payment
notifications. Withdrawal and KYC are always immediate.

### New WhatsApp template: daily digest

**Template name:** `vulapay_daily_summary`
**Category:** UTILITY
**Language:** en_US

**Header:** `Your VulaPay daily summary`

**Body:**
```
📊 Hi {{1}}, here's your summary for {{2}}:

Payments: {{3}}
Total received: R{{4}}
Fees: R{{5}}
Net earned: R{{6}}

View transactions: vula-pay.co.za/transactions
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | first name | `Bryne` |
| `{{2}}` | date | `19 Sep 2026` |
| `{{3}}` | transaction count | `6` |
| `{{4}}` | total amount / 100 | `610.00` |
| `{{5}}` | total fees / 100 | `36.60` |
| `{{6}}` | net earned / 100 | `573.40` |

> Submit this template to Meta alongside the existing 5. Category: UTILITY.

---

## Email Notifications

### Why digest-only

Sending an email for every payment would be spam for a busy merchant. Email is
a lower-urgency channel — a daily summary is appropriate. Withdrawal and KYC
decisions are included in the digest (not sent as separate emails) because SMS
and WhatsApp already cover those immediately.

### Stack

**Amazon SES** (Simple Email Service) — already in the AWS account, same
`af-south-1` region. No new vendor needed.

### Daily digest email

Sent at 19:00 SAST (17:00 UTC) by the `SendDailyDigestFunction` cron Lambda.

Subject: `VulaPay — Your daily summary for {date}`

Content (HTML + plain text):
- Today's payment count, total received, fees, net earned
- Last 5 transactions (amount + time)
- Any withdrawal decisions today
- Any KYC decisions today
- Link to dashboard

### SES setup required

1. Verify sending domain `vula-pay.co.za` in SES (DNS TXT + DKIM records).
2. Move out of SES sandbox (submit production access request to AWS).
3. From address: `notifications@vula-pay.co.za`
4. Add `SES_FROM_EMAIL` to SSM and config.

### `users` table addition

```sql
ALTER TABLE users ADD COLUMN email_notifications boolean NOT NULL DEFAULT true;
```

Merchants can opt out of email entirely in notification preferences.

---

## Notification Preferences

### `notification_prefs` table (new)

One row per merchant. Created with defaults on merchant signup.

```sql
CREATE TABLE notification_prefs (
  merchant_id              text PRIMARY KEY REFERENCES merchants(id) ON DELETE CASCADE,

  -- Payment received channel preferences
  payments_push            boolean NOT NULL DEFAULT true,
  payments_sms             boolean NOT NULL DEFAULT true,
  payments_whatsapp        boolean NOT NULL DEFAULT true,
  payments_email           boolean NOT NULL DEFAULT true,  -- always digest

  -- SMS/WhatsApp delivery mode for payments
  payments_sms_mode        text NOT NULL DEFAULT 'instant'  CHECK (payments_sms_mode IN ('instant', 'digest')),
  payments_whatsapp_mode   text NOT NULL DEFAULT 'instant'  CHECK (payments_whatsapp_mode IN ('instant', 'digest')),

  -- Withdrawal + KYC: channel on/off only (always instant — no digest option)
  events_push              boolean NOT NULL DEFAULT true,
  events_sms               boolean NOT NULL DEFAULT true,
  events_whatsapp          boolean NOT NULL DEFAULT true,

  updated_at               timestamptz NOT NULL DEFAULT now()
);
```

### API endpoints (new)

```
GET  /merchants/me/notification-prefs   → return current prefs
PATCH /merchants/me/notification-prefs  → update prefs (partial update)
```

### WhatsApp STOP/START global toggle

The existing `merchants.notification_channel` field (from the WhatsApp plan)
acts as a global WhatsApp toggle:
- `STOP` → sets `notification_channel = 'sms'` (WhatsApp off globally)
- `START` → sets `notification_channel = 'whatsapp'`

This is a blunt override that takes precedence over `notification_prefs`.
Granular per-event WhatsApp prefs are managed via the preferences page.

---

## The 19:00 Digest Cron

### Why a fixed time

A fixed daily time (19:00 SAST = 17:00 UTC) means:
- One Lambda invocation covers all merchants — no per-merchant scheduling.
- Merchants know when to expect their summary.
- No cron jobs running at different times for different merchants.
- 19:00 is after typical trading hours — the day is complete.

### What it does

1. Query all merchants where `notification_prefs.payments_sms_mode = 'digest'`
   OR `payments_whatsapp_mode = 'digest'` OR `payments_email = true`.
2. For each merchant, aggregate today's transactions (00:00–19:00 SAST).
3. Send the appropriate channels based on their prefs.
4. Log each send to `notification_log` (see below).

### `notification_log` table (new)

Prevents duplicate sends if the cron retries.

```sql
CREATE TABLE notification_log (
  id           text PRIMARY KEY,
  merchant_id  text NOT NULL REFERENCES merchants(id),
  channel      text NOT NULL,   -- 'sms' | 'whatsapp' | 'email' | 'push'
  type         text NOT NULL,   -- 'digest' | 'payment_received' | 'withdrawal_approved' | etc.
  sent_at      timestamptz NOT NULL DEFAULT now(),
  digest_date  date,            -- for digest deduplication: one per merchant per channel per day
  success      boolean NOT NULL DEFAULT true,
  error        text
);

CREATE UNIQUE INDEX ON notification_log (merchant_id, channel, digest_date)
  WHERE type = 'digest';  -- one digest per merchant per channel per day
```

### `template.yaml` addition

```yaml
SendDailyDigestFunction:
  Type: AWS::Serverless::Function
  Properties:
    Handler: app.cron.send_daily_digest.handler
    CodeUri: .
    Description: Send daily payment summary via SMS, WhatsApp, and email at 19:00 SAST
    Timeout: 300
    Policies:
      - SSMParameterReadPolicy:
          ParameterName: !Sub 'scan2pay/${Environment}/*'
      - Statement:
          - Effect: Allow
            Action: ses:SendEmail
            Resource: '*'
    Environment:
      Variables:
        META_WHATSAPP_PHONE_NUMBER_ID: !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_PHONE_NUMBER_ID}}'
        META_WHATSAPP_ACCESS_TOKEN:    !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_ACCESS_TOKEN}}'
        SES_FROM_EMAIL:                !Sub '{{resolve:ssm:/scan2pay/${Environment}/SES_FROM_EMAIL}}'
    Events:
      Schedule:
        Type: Schedule
        Properties:
          Schedule: cron(0 17 * * ? *)
          Description: Daily digest at 17:00 UTC (19:00 SAST)
```

---

## Notification Preferences UI

### scan2pay-app: Settings screen

Add a "Notifications" section to `src/app/(merchant)/settings.tsx`:

- Push notifications toggle (calls `PATCH /merchants/me/push-token` to
  register/deregister)
- SMS: per-event / daily digest / off
- WhatsApp: per-event / daily digest / off
- Email digest: on / off

### scan2pay-web: Settings page

Add `/settings/notifications` page under `src/app/(merchant)/settings/`:

Same controls as the app. This is also the page linked from the WhatsApp bot's
`🔔 Notifications` menu item (already defined in `13_VulaPay_WhatsApp_Integration_Plan.md`).

---

## Notification Helper: `app/services/notification_service.py` (new)

Central dispatcher. All event handlers call this instead of calling
`send_sms`, `send_push`, `send_whatsapp_template` directly.

```python
async def notify_merchant(
    merchant_id: str,
    event_type: str,          # 'payment_received' | 'withdrawal_approved' | etc.
    title: str,
    body: str,
    data: dict,               # stored in notifications table + push payload
    db,
    # optional overrides for template variables
    sms_message: str | None = None,
    whatsapp_template: str | None = None,
    whatsapp_components: list | None = None,
) -> None:
    """
    1. Write to notifications table (bell — always)
    2. Broadcast via WebSocket if merchant is connected
    3. Send push if push_enabled and events_push (or payments_push)
    4. Send SMS based on prefs (instant or skip for digest)
    5. Send WhatsApp based on prefs (instant or skip for digest)
    Email is digest-only — never sent here, only by the cron.
    """
```

This replaces the scattered `send_sms()` calls in `admin.py`, `kyc.py`, and
`webhooks.py`. Those files will call `notify_merchant()` instead.

---

## Implementation Plan

### Phase 1 — Bell + Push (highest value, no external dependencies)

**Backend:**
- [ ] `notifications` table migration
- [ ] `notification_prefs` table migration (with defaults)
- [ ] `notification_log` table migration
- [ ] `broadcast_to_merchant()` in `websocket_broadcast.py`
- [ ] `GET/PATCH /merchants/me/notifications` endpoints
- [ ] `GET/PATCH /merchants/me/notification-prefs` endpoints
- [ ] `PATCH /merchants/me/push-token` endpoint
- [ ] `app/services/push_service.py` — Expo Push API
- [ ] `app/services/notification_service.py` — central dispatcher
- [ ] Wire `notify_merchant()` into `webhooks.py`, `admin.py`, `kyc.py`
- [ ] `merchants` table: add `expo_push_token`, `push_enabled` columns

**scan2pay-app:**
- [ ] `expo-notifications` plugin in `app.json`
- [ ] Permission request flow (post-login, not cold start)
- [ ] Push token registration on login, deregistration on logout
- [ ] Bell icon with unread badge in `AppShell.tsx`
- [ ] Notification drawer/panel component
- [ ] Notification preferences section in `settings.tsx`
- [ ] WebSocket handler for `NOTIFICATION` message type

**scan2pay-web:**
- [ ] Bell icon with unread badge in `AppShell.tsx`
- [ ] Notification panel component
- [ ] `/settings/notifications` page
- [ ] WebSocket handler for `NOTIFICATION` message type

---

### Phase 2 — SMS digest + WhatsApp digest

**Backend:**
- [ ] `app/cron/send_daily_digest.py` — Lambda handler
- [ ] `template.yaml` — `SendDailyDigestFunction` at `cron(0 17 * * ? *)`
- [ ] `template.yaml` — SES IAM permission on digest function
- [ ] SSM: `/scan2pay/prod/SES_FROM_EMAIL`
- [ ] `app/core/config.py` — `ses_from_email` setting
- [ ] Digest logic: aggregate today's txns per merchant, send SMS/WhatsApp/email
- [ ] `notification_log` deduplication check before each send
- [ ] Update `notify_merchant()` to skip SMS/WhatsApp for digest-mode merchants

**Meta:**
- [ ] Submit `vulapay_daily_summary` template for approval

**AWS SES:**
- [ ] Verify `vula-pay.co.za` domain in SES
- [ ] Request SES production access (out of sandbox)
- [ ] Add DKIM DNS records

---

### Phase 3 — Email digest

**Backend:**
- [ ] `app/services/email_service.py` — SES send via `boto3`
- [ ] HTML email template for daily digest
- [ ] Wire email into `send_daily_digest.py`

**scan2pay-app / scan2pay-web:**
- [ ] Email digest toggle in notification preferences UI

---

## What is NOT in scope

- Email for individual events (payment received, withdrawal, KYC) — digest only.
- WhatsApp OTP — stays on WinSMS (existing behaviour).
- Admin notifications — admins use the web dashboard directly.
- Customer (payer) notifications — out of scope; customers are anonymous.

---

## SSM Parameters (new)

```
/scan2pay/prod/SES_FROM_EMAIL          → notifications@vula-pay.co.za
```

WhatsApp SSM params are already defined in `13_VulaPay_WhatsApp_Integration_Plan.md`.

---

## Config additions (`app/core/config.py`)

```python
# ── SES ───────────────────────────────────────────────────────────────────────
ses_from_email: str = ""

# ── WhatsApp (already in Sprint 1 plan — listed here for completeness) ────────
meta_whatsapp_phone_number_id: str = ""
meta_whatsapp_access_token: str = ""
meta_whatsapp_webhook_verify_token: str = ""
meta_whatsapp_app_secret: str = ""
```

---

## Answers to Design Questions

**Q: Is the bell notification important if users aren't always in the app?**

Yes — it is the most important channel for in-app context. When a merchant
opens the app or web dashboard, the bell badge immediately shows what happened
while they were away. It also provides a persistent history that SMS/WhatsApp
do not. It costs nothing and has no external dependencies. Always implement it.

**Q: Fixed 19:00 digest time vs per-merchant scheduled times?**

Fixed 19:00 SAST is the right call:
- One Lambda invocation, one cron expression, zero per-merchant scheduling.
- Merchants know when to expect their summary.
- 19:00 is after typical trading hours — the day is complete.
- EventBridge Scheduler (per-merchant cron) would cost more and add complexity
  for no meaningful benefit.

**Q: Does the WhatsApp integration plan need to change?**

No. `12_Whatsapp_Integration.md`, `13_VulaPay_WhatsApp_Integration_Plan.md`,
and `whatsapp_templates.md` are unchanged. This document adds:
1. The `notification_prefs` table that WhatsApp reads from.
2. The `vulapay_daily_summary` template (new — needs Meta approval).
3. The 19:00 digest cron that sends WhatsApp digests.
The existing 5 templates, the bot flow, and the Sprint 1/2 plan are unaffected.
