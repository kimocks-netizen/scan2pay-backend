# Scan2Pay — WhatsApp Integration Plan

> Based on the actual Scan2Pay backend (FastAPI · Supabase · AWS SAM · af-south-1).
> Button-based UI for Sprint 1 & 2. Bedrock natural language as MVP 2.
> Last updated: September 2026

---

## Credentials & Meta Assets

| Item | Value |
|---|---|
| Phone Number ID | `1379297795259081` |
| Business Account ID | `1095598982856337` |
| Phone number | `+1 (555) 147-8233` (Meta test number) |
| Template confirmed working | `jaspers_market_plain_text_v1` (en_US) — Meta demo template |
| Token in use | Temporary 24-hour token — **must be replaced with System User long-lived token before Sprint 1 build** |

### SSM Parameters (to be added)
```
/scan2pay/prod/META_WHATSAPP_PHONE_NUMBER_ID
/scan2pay/prod/META_WHATSAPP_ACCESS_TOKEN          ← long-lived System User token
/scan2pay/prod/META_WHATSAPP_WEBHOOK_VERIFY_TOKEN  ← random string you choose
/scan2pay/prod/META_WHATSAPP_APP_SECRET            ← from Meta App dashboard, for HMAC validation
```

---

## What WhatsApp is used for

WhatsApp is the merchant's day-to-day channel. They should be able to do everything they need without opening the app or website, except for sensitive financial actions.

| Action | Via WhatsApp | Via Website |
|---|---|---|
| Check available balance | ✅ | ✅ |
| Check today's earnings | ✅ | ✅ |
| View last 10 transactions | ✅ | ✅ |
| Check if latest payment went through | ✅ | ✅ |
| Check withdrawal-ready amount | ✅ | ✅ |
| Request a withdrawal | ❌ redirect to website | ✅ |
| KYC document upload | ❌ redirect to website | ✅ |
| Payout account changes | ❌ redirect to website | ✅ |
| Speak to an agent | ✅ (HELP → agent handoff) | ✅ |
| Receive payment notification | ✅ (automatic) | — |
| Receive KYC decision | ✅ (automatic) | — |
| Receive withdrawal decision | ✅ (automatic) | — |

---

## Conversation UI — Full Flow

### Main menu

Shown on any first message, "hi", "menu", "0", or unrecognised input.

Because Meta limits interactive buttons to 3 per message, the menu is split across two messages sent back-to-back:

**Message 1 (3 buttons):**
```
👋 Welcome to VulaPay

What would you like to do?

[💰 Check Balance]  [📜 Transactions]  [💳 Payment Status]
```

**Message 2 (3 buttons):**
```
More options:

[💸 Withdraw]  [🌐 Open VulaPay]  [❓ Help]
```

---

### 1. 💰 Check Balance — button ID: `BALANCE`

Shows available balance, today's earnings, and withdrawal-ready amount in one reply.

```
💰 Your VulaPay Balance

Available:          R850.00
Pending settlement: R120.00

Today's earnings:   R340.00
Ready to withdraw:  R850.00

Reply *0* for menu
```

**Supabase queries:**
- Available: `transactions` settled net_cents − in-flight withdrawals (same as `GET /merchants/me/balance`)
- Today's earnings: `transactions` where `status=success` and `paid_at >= today 00:00 SAST`
- Ready to withdraw: same as available (settled − in-flight)
- Pending settlement: `transactions` where `status=success` and `settlement_status=pending`

---

### 2. 📜 Transactions — button ID: `TRANSACTIONS`

Shows last 10 successful transactions.

```
📜 Last 10 Transactions

+ R85.00   · 19 Sep 14:32
+ R120.00  · 19 Sep 11:05
+ R50.00   · 19 Sep 09:44
+ R200.00  · 18 Sep 16:20
+ R75.00   · 18 Sep 13:11
+ R90.00   · 18 Sep 10:30
+ R110.00  · 17 Sep 15:55
+ R60.00   · 17 Sep 12:00
+ R45.00   · 16 Sep 17:22
+ R130.00  · 16 Sep 09:10

View all: scan2pay.site/transactions
Reply *0* for menu
```

**Supabase query:** `transactions` where `merchant_id=X`, `status=success`, order by `paid_at desc`, limit 10.

---

### 3. 💳 Payment Status — button ID: `PAYMENT_STATUS`

Shows the most recent transaction and its status.

```
💳 Latest Payment

Amount:  R85.00
Status:  ✅ Successful
Date:    19 Sep 2026, 14:32
Ref:     STP000068070EFA

Reply *0* for menu
```

If no transactions yet:
```
No payments found on your account yet.

Reply *0* for menu
```

**Supabase query:** `transactions` where `merchant_id=X`, order by `created_at desc`, limit 1.

---

### 4. 💸 Withdraw — button ID: `WITHDRAW`

Withdrawals are never processed via WhatsApp. Always redirect to the website.

```
💸 Withdrawals

Withdrawals are completed securely through your VulaPay account.

Your available balance: R850.00

Tap the link below to request a withdrawal:
https://scan2pay.site/withdrawals

Reply *0* for menu
```

The available balance is shown so the merchant knows what they can withdraw before they open the site.

---

### 5. 🌐 Open VulaPay — button ID: `WEBSITE`

```
🌐 VulaPay

https://scan2pay.site

Quick links:
• Dashboard: scan2pay.site/dashboard
• Transactions: scan2pay.site/transactions
• Withdrawals: scan2pay.site/withdrawals
• Settings: scan2pay.site/settings

Reply *0* for menu
```

---

### 6. ❓ Help — button ID: `HELP`

```
❓ VulaPay Help

For support, reply *agent* to speak to a VulaPay team member.

Common questions:
• Balance → reply *1*
• Transactions → reply *2*
• Payment status → reply *3*
• Withdraw → reply *4*
• Website → reply *5*

Or reply *0* for the main menu.
```

---

### 7. Speak to an agent — keyword: `agent`

When a merchant replies "agent" (case-insensitive):

```
👤 Connecting you to a VulaPay agent

A team member will respond shortly during business hours (Mon–Fri, 8am–5pm SAST).

Your account: {business_name}
Phone: {phone}

Reply *0* to return to the menu.
```

Backend action: log the handoff request to Supabase (`whatsapp_agent_requests` table: `merchant_id`, `phone`, `requested_at`) so the support team can see it in the admin console. No live chat infrastructure needed in Sprint 2 — the agent sees the request and calls/WhatsApps the merchant back manually.

---

### Shortcut keywords (always active)

| Keyword | Action |
|---|---|
| `0`, `menu`, `hi`, `hello` | Show main menu |
| `1` | Balance |
| `2` | Transactions |
| `3` | Payment status |
| `4` | Withdraw |
| `5` | Open VulaPay |
| `help`, `6` | Help |
| `agent` | Request agent handoff |

---

## Outbound Notifications (automatic, no user action needed)

These fire automatically when events happen. The merchant does not need to message first.

| Event | Template | Message |
|---|---|---|
| Payment received | `scan2pay_payment_received` | "💰 Payment received\n\nAmount: R{amount}\nRef: {reference}\nNew balance: R{available}" |
| Withdrawal approved | `scan2pay_withdrawal_approved` | "✅ Withdrawal approved\n\nR{amount} is being processed to your bank account." |
| Withdrawal rejected | `scan2pay_withdrawal_rejected` | "❌ Withdrawal declined\n\nR{amount} was not processed. Reason: {reason}" |
| KYC approved | `scan2pay_kyc_approved` | "✅ KYC approved\n\nYour identity has been verified. You can now withdraw." |
| KYC rejected | `scan2pay_kyc_rejected` | "❌ KYC not approved\n\nReason: {reason}\n\nPlease re-upload at scan2pay.site/settings" |

> All outbound notifications use approved Meta templates (no 24-hour window restriction). Template variables are filled server-side before sending.

---

## Architecture

```
Merchant's WhatsApp
        │
        ▼
Meta WhatsApp Cloud API
        │
        ├── POST /webhooks/whatsapp  ← inbound messages
        └── GET  /webhooks/whatsapp  ← webhook verification (hub.challenge)
        │
        ▼
app/api/routes/webhooks.py
        │
        ├── HMAC signature validation (X-Hub-Signature-256)
        ├── look up merchant by users.phone
        └── route to app/services/whatsapp_bot.py
                │
                ├── BALANCE        → Supabase: transactions + withdrawals
                ├── TRANSACTIONS   → Supabase: transactions limit 10
                ├── PAYMENT_STATUS → Supabase: transactions limit 1
                ├── WITHDRAW       → static reply + website link
                ├── WEBSITE        → static reply + links
                ├── HELP           → static reply
                └── AGENT          → log to whatsapp_agent_requests table
                │
                ▼
        app/services/whatsapp_service.py
                │
                │  POST https://graph.facebook.com/v25.0/{PHONE_ID}/messages
                ▼
        Meta WhatsApp Cloud API
                │
                ▼
        Merchant's WhatsApp
```

**Outbound notifications** fire from existing routes:
- `webhooks.py` → `_handle_charge_success()` → `whatsapp_service.send_whatsapp_template()`
- `admin.py` → `_notify_merchant()` → `whatsapp_service.send_whatsapp_template()`
- `kyc.py` → KYC decision handler → `whatsapp_service.send_whatsapp_template()`

---

## What is NEVER done via WhatsApp

- Withdrawals — always redirected to `https://scan2pay.site/withdrawals`
- KYC document upload
- Payout account changes
- Any write operation that touches money

---

## Sprint 1 — Outbound Notifications Only

> Goal: merchants receive WhatsApp messages when things happen to their account.
> No inbound. No webhook. No bot.

### New files

**`app/services/whatsapp_service.py`**
- `send_whatsapp_template(to, template_name, language="en_US", components=[]) -> bool`
- `send_whatsapp_text(to, body) -> bool` — for Sprint 2 (within 24h window only)

**`app/core/config.py`** additions:
```python
meta_whatsapp_phone_number_id: str = ""
meta_whatsapp_access_token: str = ""
meta_whatsapp_webhook_verify_token: str = ""
meta_whatsapp_app_secret: str = ""
```

**`template.yaml`** — add to `Scan2PayApiFunction` environment:
```yaml
META_WHATSAPP_PHONE_NUMBER_ID:         !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_PHONE_NUMBER_ID}}'
META_WHATSAPP_ACCESS_TOKEN:            !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_ACCESS_TOKEN}}'
META_WHATSAPP_WEBHOOK_VERIFY_TOKEN:    !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_WEBHOOK_VERIFY_TOKEN}}'
META_WHATSAPP_APP_SECRET:              !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_APP_SECRET}}'
```

### Notification trigger points

| Event | File | Alongside |
|---|---|---|
| Payment received | `webhooks.py` → `_handle_charge_success()` | WebSocket broadcast |
| Withdrawal approved/rejected | `admin.py` → `_notify_merchant()` | `send_sms()` |
| KYC approved/rejected | `kyc.py` → KYC decision handler | `send_sms()` |

### Notification preference

Read `merchants.notification_channel` before sending:
- `"sms"` (default) → WinSMS only
- `"whatsapp"` → WhatsApp only
- `"all"` → both

### Templates needed (submit to Meta for approval before Sprint 1 ships)

| Template name | Variables |
|---|---|
| `scan2pay_payment_received` | `{{1}}` amount, `{{2}}` reference, `{{3}}` new available balance |
| `scan2pay_withdrawal_approved` | `{{1}}` amount |
| `scan2pay_withdrawal_rejected` | `{{1}}` amount, `{{2}}` reason |
| `scan2pay_kyc_approved` | none |
| `scan2pay_kyc_rejected` | `{{1}}` reason |

### Sprint 1 checklist

**Backend:**
- [ ] `app/services/whatsapp_service.py`
- [ ] `app/core/config.py` — 4 WhatsApp settings
- [ ] `template.yaml` — 4 env vars on `Scan2PayApiFunction`
- [ ] `scripts/deploy.sh` — 4 SSM param pushes
- [ ] `webhooks.py` — wire `send_whatsapp_template` into `_handle_charge_success()`
- [ ] `admin.py` — wire into `_notify_merchant()`
- [ ] `kyc.py` — wire into KYC decision handler

**Meta:**
- [ ] Generate long-lived System User token in Meta Business Portfolio
- [ ] Store in SSM `/scan2pay/prod/META_WHATSAPP_ACCESS_TOKEN`
- [ ] Submit 5 templates for Meta approval

---

## Sprint 2 — Inbound Bot (Button UI)

> Goal: merchants can message VulaPay on WhatsApp and interact using buttons and number shortcuts.
> Full menu as designed above. Agent handoff. No free-text parsing (that's MVP 2).

### New files

**`app/api/routes/webhooks.py`** — two new routes:
```python
GET  /webhooks/whatsapp   # hub.challenge verification
POST /webhooks/whatsapp   # inbound message handler
```

**`app/services/whatsapp_bot.py`** — intent router + all response builders

**Supabase table: `whatsapp_agent_requests`**
```sql
id           text primary key
merchant_id  text references merchants(id)
phone        text
business_name text
requested_at timestamptz default now()
resolved     boolean default false
resolved_at  timestamptz
```

### Meta API payloads

**Interactive button message (menu):**
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": { "text": "👋 Welcome to VulaPay\n\nWhat would you like to do?" },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "BALANCE",        "title": "💰 Check Balance" } },
        { "type": "reply", "reply": { "id": "TRANSACTIONS",   "title": "📜 Transactions" } },
        { "type": "reply", "reply": { "id": "PAYMENT_STATUS", "title": "💳 Payment Status" } }
      ]
    }
  }
}
```

Second message (3 more options):
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": { "text": "More options:" },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "WITHDRAW", "title": "💸 Withdraw" } },
        { "type": "reply", "reply": { "id": "WEBSITE",  "title": "🌐 Open VulaPay" } },
        { "type": "reply", "reply": { "id": "HELP",     "title": "❓ Help" } }
      ]
    }
  }
}
```

**Plain text reply:**
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "text",
  "text": { "body": "💰 Your VulaPay Balance\n\nAvailable: R850.00\n..." }
}
```

> Plain text replies only work within the 24-hour customer service window (merchant messaged first). Outside that window, only approved templates can be sent.

### Webhook verification

```
GET /webhooks/whatsapp?hub.mode=subscribe&hub.verify_token={TOKEN}&hub.challenge={CHALLENGE}
```
Return `hub.challenge` as plain text with 200 if `hub.verify_token` matches SSM value.

### Webhook signature validation

Meta signs every POST with `X-Hub-Signature-256: sha256={hmac}` using the Meta App Secret.
Validate using same HMAC pattern as `verify_paystack_signature()` in `app/core/security.py`.

### Inbound message routing

```python
# Incoming payload structure (simplified)
message.type == "interactive"  →  message.interactive.button_reply.id  (e.g. "BALANCE")
message.type == "text"         →  message.text.body.strip().lower()     (e.g. "0", "menu", "agent")
```

Routing table:
```
"BALANCE" | "1"                          → handle_balance(merchant)
"TRANSACTIONS" | "2"                     → handle_transactions(merchant)
"PAYMENT_STATUS" | "3"                   → handle_payment_status(merchant)
"WITHDRAW" | "4"                         → handle_withdraw(merchant)
"WEBSITE" | "5"                          → handle_website()
"HELP" | "6"                             → handle_help()
"agent"                                  → handle_agent_request(merchant)
"0" | "menu" | "hi" | "hello" | unknown  → send_menu(merchant)
```

### Sprint 2 checklist

**Backend:**
- [ ] `GET /webhooks/whatsapp` — hub.challenge verification
- [ ] `POST /webhooks/whatsapp` — HMAC validation + message routing
- [ ] `app/services/whatsapp_bot.py` — all 7 handlers + menu sender
- [ ] `whatsapp_agent_requests` Supabase table migration
- [ ] Register webhook URL in Meta App dashboard: `https://{api}/webhooks/whatsapp`
- [ ] Subscribe to `messages` webhook field in Meta dashboard

**Blocked until:**
- [ ] Sprint 1 long-lived token in SSM
- [ ] Meta App Secret in SSM
- [ ] Webhook URL deployed and verified by Meta

---

## MVP 2 — Bedrock Natural Language

> Extends Sprint 2. Buttons remain the primary UI.
> Bedrock only handles free-text messages that don’t match a button reply or keyword.
> Bedrock never touches the ledger — it only resolves intent, then calls the same handlers Sprint 2 already uses.

### What changes

Sprint 2 router:
```
type: "text" + unknown keyword → send_menu()
```

MVP 2 router:
```
type: "text" + unknown keyword → resolve_intent() via Bedrock → route to existing handler
                                  fallback on error → send_menu()
```

Button replies are unchanged. Bedrock is never called for button taps.

### Controlled tools (Bedrock can only resolve these)

| Tool | Maps to |
|---|---|
| `get_balance` | `handle_balance()` |
| `get_transactions` | `handle_transactions()` |
| `get_payment_status` | `handle_payment_status()` |
| `get_withdraw` | `handle_withdraw()` (redirect only) |
| `open_website` | `handle_website()` |
| `get_help` | `handle_help()` |
| `unknown` | `send_menu()` |

Bedrock is never given a tool that writes data.

### Model

**Claude 3 Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`) via Amazon Bedrock.
- Available in `us-east-1` (not yet in `af-south-1`) — Bedrock client uses `us-east-1`, everything else stays `af-south-1`
- ~300 token input, ~20 token output. Cost negligible.

### New file

**`app/services/whatsapp_bedrock.py`**
- `resolve_intent(message: str) -> dict` — returns `{"tool": str}`
- Falls back to `{"tool": "unknown"}` on any error

### `template.yaml` addition
```yaml
- Statement:
    - Effect: Allow
      Action: bedrock:InvokeModel
      Resource: arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0
```

### MVP 2 checklist

**Backend:**
- [ ] `app/services/whatsapp_bedrock.py` — `resolve_intent()` with Claude 3 Haiku
- [ ] `app/services/whatsapp_bot.py` — add Bedrock branch for unmatched text messages
- [ ] `template.yaml` — `bedrock:InvokeModel` IAM permission

**AWS:**
- [ ] Enable Claude 3 Haiku model access in Bedrock console (`us-east-1`) — not on by default
- [ ] Confirm cross-region `bedrock:InvokeModel` permission on `Scan2PayApiFunction` role

**Blocked until:**
- [ ] Sprint 2 inbound bot live and stable
- [ ] Bedrock model access enabled in `us-east-1`

---

## Deferred

- **WhatsApp OTP** — OTP stays on WinSMS for now
- **`whatsapp_users` table** — not needed, `users.phone` is the link
- **Separate WhatsApp Lambda** — webhook lives in `Scan2PayApiFunction` (same as Paystack)
- **List/catalog messages** — buttons only for Sprint 2
- **Notification preferences UI** — settings page update is a separate frontend task
- **Multi-turn conversation state** — each message is stateless in Sprint 2; Bedrock MVP 2 is also stateless

---

## Credentials & Meta Assets

| Item | Value |
|---|---|
| Phone Number ID | `1379297795259081` |
| Business Account ID | `1095598982856337` |
| Phone number | `+1 (555) 147-8233` (Meta test number) |
| Template confirmed working | `jaspers_market_plain_text_v1` (en_US) — Meta demo template |
| Token in use | Temporary 24-hour token — **must be replaced with System User long-lived token before Sprint 1 build** |

### SSM Parameters (to be added)
```
/scan2pay/prod/META_WHATSAPP_PHONE_NUMBER_ID
/scan2pay/prod/META_WHATSAPP_ACCESS_TOKEN       ← long-lived System User token
/scan2pay/prod/META_WHATSAPP_WEBHOOK_VERIFY_TOKEN  ← random string you choose, used to verify Meta's GET on webhook registration
```

---

## Architecture

```
Merchant's WhatsApp
        │
        ▼
Meta WhatsApp Cloud API
        │
        │  POST (inbound messages)
        │  GET  (webhook verification)
        ▼
POST /webhooks/whatsapp   ← new route in webhooks.py
GET  /webhooks/whatsapp   ← webhook verification (hub.challenge)
        │
        ▼
Existing Scan2Pay services
  ├── GET /merchants/me/balance        (available_cents, pending_settlement_cents)
  ├── GET /merchants/me/transactions   (last 5, status=success)
  └── users.phone → merchant lookup   (no new table needed for outbound)
        │
        ▼
app/services/whatsapp_service.py
        │
        │  POST https://graph.facebook.com/v25.0/{PHONE_ID}/messages
        ▼
Meta WhatsApp Cloud API
        │
        ▼
Merchant's WhatsApp
```

**Key principle:** WhatsApp is a channel. All data comes from existing Scan2Pay endpoints and Supabase tables. No business logic is duplicated.

---

## What is NOT in scope (ever via WhatsApp)

- Withdrawals — always redirected to `https://scan2pay.site/withdrawals`
- KYC document upload
- Payout account changes
- Any write operation that touches money

---

## Sprint 1 — Outbound Notifications

> Goal: merchants receive WhatsApp messages when things happen to their account.
> No inbound handling. No webhook. No user linking table.

### How it works

We already have `users.phone` on every merchant. That IS their WhatsApp number (SA mobile numbers). We send outbound notifications to that number directly — no linking table needed for this phase.

### New files

**`app/services/whatsapp_service.py`**

Sends outbound messages via Meta Graph API.

Two functions:
- `send_whatsapp_text(to: str, body: str) -> bool` — free-form text (only valid within 24h of user initiating contact — for Sprint 2)
- `send_whatsapp_template(to: str, template_name: str, language: str = "en_US", components: list = []) -> bool` — template message (works any time, no 24h window restriction)

Config additions to `app/core/config.py`:
```
meta_whatsapp_phone_number_id: str = ""
meta_whatsapp_access_token: str = ""
meta_whatsapp_webhook_verify_token: str = ""
```

`template.yaml` additions to `Scan2PayApiFunction` environment:
```yaml
META_WHATSAPP_PHONE_NUMBER_ID: !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_PHONE_NUMBER_ID}}'
META_WHATSAPP_ACCESS_TOKEN: !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_ACCESS_TOKEN}}'
META_WHATSAPP_WEBHOOK_VERIFY_TOKEN: !Sub '{{resolve:ssm:/scan2pay/${Environment}/META_WHATSAPP_WEBHOOK_VERIFY_TOKEN}}'
```

### Notification trigger points (all existing files)

| Event | File | Where to add | Message |
|---|---|---|---|
| Payment received | `app/api/routes/webhooks.py` | `_handle_charge_success()` — after transaction update | "💰 Payment received: R{amount}. Ref: {reference}" |
| Withdrawal approved | `app/api/routes/admin.py` | `_notify_merchant("approved")` — alongside existing `send_sms` | "✅ Your withdrawal of R{amount} has been approved and is being processed." |
| Withdrawal rejected | `app/api/routes/admin.py` | `_notify_merchant("rejected")` — alongside existing `send_sms` | "❌ Your withdrawal of R{amount} was declined. Reason: {reason}" |
| KYC approved | `app/api/routes/kyc.py` | alongside existing `send_sms` call | "✅ Your Scan2Pay KYC has been approved. You can now withdraw." |
| KYC rejected | `app/api/routes/kyc.py` | alongside existing `send_sms` call | "❌ Your Scan2Pay KYC was not approved. Reason: {reason}" |

### Notification preference

Read `merchants.notification_channel` before sending. If `"whatsapp"` → send WhatsApp. If `"sms"` (default) → send WinSMS as today. Both can be sent if preference is `"all"` (future).

This means `notification_channel` column on merchants must exist (Sprint 2 backlog item — add migration if not already present).

### Meta API endpoint used

```
POST https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages
Authorization: Bearer {ACCESS_TOKEN}
Content-Type: application/json

{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "template",
  "template": {
    "name": "{approved_template_name}",
    "language": { "code": "en_US" }
  }
}
```

### Templates needed (must be approved in Meta Business Manager before Sprint 1 ships)

| Template name | Trigger | Variables |
|---|---|---|
| `scan2pay_payment_received` | Payment success | `{{1}}` = amount (e.g. "R85.00"), `{{2}}` = reference |
| `scan2pay_withdrawal_approved` | Withdrawal approved | `{{1}}` = amount |
| `scan2pay_withdrawal_rejected` | Withdrawal rejected | `{{1}}` = amount, `{{2}}` = reason |
| `scan2pay_kyc_approved` | KYC approved | none |
| `scan2pay_kyc_rejected` | KYC rejected | `{{1}}` = reason |

> Until these are approved by Meta, outbound notifications cannot be sent to non-test numbers. The `jaspers_market_plain_text_v1` demo template can be used for testing only.

### Sprint 1 checklist

**Backend:**
- [ ] `app/services/whatsapp_service.py` — `send_whatsapp_template()` + `send_whatsapp_text()`
- [ ] `app/core/config.py` — add 3 WhatsApp settings
- [ ] `template.yaml` — add 3 env vars to `Scan2PayApiFunction`
- [ ] `scripts/deploy.sh` — add 3 SSM param pushes
- [ ] `webhooks.py` — call `send_whatsapp_template` in `_handle_charge_success()` (alongside WebSocket broadcast)
- [ ] `admin.py` — call `send_whatsapp_template` in `_notify_merchant()` (alongside `send_sms`)
- [ ] `kyc.py` — call `send_whatsapp_template` on KYC decision (alongside `send_sms`)

**Meta:**
- [ ] Generate long-lived System User token in Meta Business Portfolio
- [ ] Store token in SSM `/scan2pay/prod/META_WHATSAPP_ACCESS_TOKEN`
- [ ] Submit `scan2pay_payment_received`, `scan2pay_withdrawal_approved`, `scan2pay_withdrawal_rejected`, `scan2pay_kyc_approved`, `scan2pay_kyc_rejected` templates for Meta approval

---

## Sprint 2 — Inbound Bot (Button UI)

> Goal: merchants can message the Scan2Pay WhatsApp number and get their balance, recent transactions, and payment status using interactive buttons. No free-text parsing.

### How inbound works

```
Merchant sends "Hi" or taps a button
        │
        ▼
Meta sends POST to /webhooks/whatsapp
        │
        ▼
Webhook handler reads:
  - from (phone number)
  - type: "text" | "interactive"
  - interactive.button_reply.id  (if button tapped)
  - text.body  (if free text — only used to show the menu)
        │
        ▼
Look up merchant by phone → users.phone → merchants
        │
        ▼
Route to handler:
  MENU        → send interactive button message (menu)
  BALANCE     → GET /merchants/me/balance → reply with balance
  TRANSACTIONS → GET /merchants/me/transactions?limit=5 → reply with list
  LAST_PAYMENT → GET /merchants/me/transactions?limit=1&status=success → reply with status
  WEBSITE     → reply with link to scan2pay.site
  HELP        → reply with support message
```

### New files

**`app/api/routes/webhooks.py`** — add two new routes:

```python
GET  /webhooks/whatsapp   # Meta webhook verification (hub.challenge)
POST /webhooks/whatsapp   # Inbound message handler
```

**`app/services/whatsapp_bot.py`** — intent router + response builders

### Meta API endpoints used

**Sending interactive button messages:**
```
POST https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages

{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": { "text": "👋 Welcome to Scan2Pay\n\nWhat would you like to do?" },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "BALANCE",      "title": "💰 Balance" } },
        { "type": "reply", "reply": { "id": "TRANSACTIONS", "title": "📜 Transactions" } },
        { "type": "reply", "reply": { "id": "LAST_PAYMENT", "title": "💳 Last payment" } }
      ]
    }
  }
}
```

> Note: Meta limits interactive button messages to 3 buttons max. A second message with more options (Website, Help) can follow if needed.

**Sending a plain text reply:**
```
POST https://graph.facebook.com/v25.0/{PHONE_NUMBER_ID}/messages

{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "text",
  "text": { "body": "💰 Your balance\n\nAvailable: R850.00\nPending settlement: R120.00" }
}
```

> Text replies are only valid within the 24-hour customer service window (i.e. the merchant messaged us first within the last 24h). Outside that window, only approved templates can be sent.

### User linking

For inbound, we look up the merchant by `users.phone` matching the WhatsApp `from` number. No separate `whatsapp_users` table needed in Sprint 2 — every Scan2Pay merchant registered with their phone number, which is the same number they use on WhatsApp.

If no match is found → reply: "We couldn't find a Scan2Pay account linked to this number. Please sign up at scan2pay.site"

### Menu flow

```
Any message → show main menu (3 buttons)

Button: BALANCE
  → query Supabase: settled net_cents - in_flight withdrawals
  → reply: "💰 Available: R{x}\nPending settlement: R{y}"

Button: TRANSACTIONS
  → query last 5 success transactions for merchant
  → reply: list of "+ R{amount} · {date}" lines
  → footer: "View all at scan2pay.site/transactions"

Button: LAST_PAYMENT
  → query last 1 success transaction
  → reply: "✅ R{amount} received on {date}\nRef: {reference}"
  → or: "No payments found yet."

Any message containing "website" or "help" (case-insensitive)
  → reply with link or support message
```

### Webhook verification (GET /webhooks/whatsapp)

Meta sends a GET request when you register the webhook URL in the Meta dashboard:
```
GET /webhooks/whatsapp?hub.mode=subscribe&hub.verify_token={VERIFY_TOKEN}&hub.challenge={CHALLENGE}
```
Handler must return `hub.challenge` as plain text with 200 if `hub.verify_token` matches `META_WHATSAPP_WEBHOOK_VERIFY_TOKEN` from SSM.

### Webhook signature validation (POST /webhooks/whatsapp)

Meta signs every inbound POST with `X-Hub-Signature-256: sha256={hmac}` using the Meta App Secret. Validate before processing — same pattern as Paystack webhook HMAC validation already in `app/core/security.py`.

New SSM param needed:
```
/scan2pay/prod/META_WHATSAPP_APP_SECRET   ← from Meta App dashboard, used for HMAC validation
```

### Sprint 2 checklist

**Backend:**
- [ ] `GET /webhooks/whatsapp` — hub.challenge verification
- [ ] `POST /webhooks/whatsapp` — inbound message handler, HMAC validation
- [ ] `app/services/whatsapp_bot.py` — intent router, menu builder, balance/transactions/last-payment handlers
- [ ] `app/core/config.py` — add `meta_whatsapp_app_secret`
- [ ] `template.yaml` + `deploy.sh` — add `META_WHATSAPP_APP_SECRET` SSM param
- [ ] Register webhook URL in Meta App dashboard → `https://{api}/webhooks/whatsapp`
- [ ] Subscribe to `messages` webhook field in Meta dashboard

**Blocked until:**
- [ ] Long-lived System User token (from Sprint 1)
- [ ] Meta App Secret retrieved from Meta App dashboard
- [ ] Webhook URL registered and verified in Meta dashboard (requires deployed endpoint)

---

## What is deferred (not in Sprint 1 or 2)

- **`whatsapp_users` table** — not needed while we match on `users.phone`
- **Separate WhatsApp Lambda** — the webhook handler lives in the existing `Scan2PayApiFunction` (same pattern as Paystack webhook)
- **WhatsApp OTP** — OTP stays on WinSMS for now
- **List messages / catalog messages** — buttons only for Sprint 2
- **Notification preferences UI** — settings page update is a separate Sprint 2 frontend task

---

## MVP 2 — Bedrock Natural Language (Post-Button)

> Replaces the deterministic button router in `whatsapp_bot.py` with Amazon Bedrock intent resolution.
> Buttons stay as the primary UI — Bedrock handles free-text messages that don't match a button reply.
> Bedrock never touches the ledger. It only resolves intent, then calls the same Scan2Pay services Sprint 2 already uses.

### Why Bedrock and not a simple keyword match

Sprint 2's deterministic router handles `BALANCE`, `TRANSACTIONS`, `LAST_PAYMENT` button IDs and a few hardcoded keywords. Bedrock extends this to handle natural language like:

- "How much did I make today?"
- "Did my last payment go through?"
- "What's my available balance?"
- "Show me payments from this week"

Without Bedrock, each of these would need its own keyword rule. With Bedrock, the intent resolution is handled by the model and the backend only executes the resolved, validated tool call.

### Architecture

```
Merchant sends free-text message
        │
        ▼
POST /webhooks/whatsapp
        │
        ├── type: "interactive" (button reply)
        │         │
        │         ▼
        │   existing Sprint 2 button router (unchanged)
        │
        └── type: "text" (free text)
                  │
                  ▼
          app/services/whatsapp_bedrock.py
                  │
                  │  invoke_model() → Claude via Bedrock
                  │  system prompt: Scan2Pay context + available tools
                  │  user message: merchant's text
                  ▼
          Bedrock returns resolved intent:
          { "tool": "get_balance" }
          { "tool": "get_transactions", "params": { "limit": 5 } }
          { "tool": "get_last_payment" }
          { "tool": "open_website", "page": "transactions" }
          { "tool": "unknown" }
                  │
                  ▼
          Tool executor → same Supabase queries as Sprint 2
                  │
                  ▼
          whatsapp_service.send_whatsapp_text()
```

### Controlled tools (what Bedrock is allowed to resolve)

| Tool | What it does | Scan2Pay query |
|---|---|---|
| `get_balance` | Returns available + pending balance | `merchants/me/balance` logic against Supabase |
| `get_transactions` | Returns last N success transactions | `transactions` table, `status=success`, `limit` param |
| `get_last_payment` | Returns most recent success transaction | `transactions` table, `limit=1` |
| `open_website` | Returns a deep link | Static URL map (no DB query) |
| `unknown` | Bedrock couldn't resolve intent | Reply with menu buttons |

**Bedrock is never given a tool that writes data.** No `withdraw`, no `update_profile`, no `cancel_payment`. The tool list is hardcoded in the system prompt — the model cannot invent new tools.

### System prompt structure

```
You are the Scan2Pay assistant. You help merchants check their payment account.

Available tools:
- get_balance: user wants to know their available or pending balance
- get_transactions: user wants to see recent payments received
- get_last_payment: user wants to know if a specific or recent payment went through
- open_website: user wants to visit the Scan2Pay website or a specific page
- unknown: you cannot determine the intent

Rules:
- Only return one of the above tool names as JSON: {"tool": "...", "params": {...}}
- Never make up financial figures
- Never suggest actions that modify account data
- If the request involves withdrawals, payout changes, or KYC, return open_website with page=withdrawals or page=settings
- If unsure, return unknown
```

### Bedrock model

Use **Amazon Bedrock — Claude 3 Haiku** (`anthropic.claude-3-haiku-20240307-v1:0`).
- Cheapest Claude model on Bedrock
- Fast enough for a WhatsApp reply (target < 2s)
- Available in `us-east-1` — Bedrock is not yet in `af-south-1`, so the Bedrock client uses `us-east-1` while everything else stays in `af-south-1`
- Input: ~300 tokens (system prompt + merchant message). Output: ~20 tokens (JSON intent). Cost is negligible.

### New files

**`app/services/whatsapp_bedrock.py`**
- `resolve_intent(message: str) -> dict` — calls Bedrock, returns `{"tool": str, "params": dict}`
- Falls back to `{"tool": "unknown"}` on any Bedrock error — never breaks the WhatsApp flow

### Changes to existing files

**`app/services/whatsapp_bot.py`** (Sprint 2 file)
- Add a branch: if `message.type == "text"` → call `resolve_intent()` → route to same tool handlers
- Button replies (`message.type == "interactive"`) are unchanged — still go through the deterministic router

**`template.yaml`**
- Add Bedrock `InvokeModel` IAM permission to `Scan2PayApiFunction`:
```yaml
- Statement:
    - Effect: Allow
      Action: bedrock:InvokeModel
      Resource: arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0
```

### New SSM parameter
```
/scan2pay/prod/BEDROCK_REGION   → us-east-1
```
(Or just hardcode `us-east-1` in `whatsapp_bedrock.py` since Bedrock availability is a known constraint, not a config concern.)

### What Bedrock does NOT do

- Does not query Supabase directly
- Does not generate financial figures
- Does not handle multi-turn conversation state (stateless — each message is independent)
- Does not replace button UI — buttons remain the primary interaction, Bedrock only handles free text
- Does not run for button replies — only for `type: "text"` messages

### MVP 2 checklist

**Backend:**
- [ ] `app/services/whatsapp_bedrock.py` — `resolve_intent()` with Claude 3 Haiku, fallback to `unknown`
- [ ] `app/services/whatsapp_bot.py` — add free-text branch calling `resolve_intent()`
- [ ] `template.yaml` — add `bedrock:InvokeModel` IAM permission on `Scan2PayApiFunction`
- [ ] Test: send "what's my balance" → Bedrock resolves `get_balance` → correct reply
- [ ] Test: send "show me this week's payments" → Bedrock resolves `get_transactions` → correct reply
- [ ] Test: send "I want to withdraw" → Bedrock resolves `open_website` with `page=withdrawals` → link reply
- [ ] Test: Bedrock timeout/error → falls back to menu buttons, no crash

**AWS:**
- [ ] Enable Claude 3 Haiku model access in Bedrock console (`us-east-1`) — model access is not on by default
- [ ] Confirm `Scan2PayApiFunction` execution role has cross-region `bedrock:InvokeModel` permission

**Blocked until:**
- [ ] Sprint 2 inbound bot is live and stable
- [ ] Bedrock model access enabled in `us-east-1`
