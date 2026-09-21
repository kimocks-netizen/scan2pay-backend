# VulaPay — WhatsApp Integration Plan

> Based on the actual VulaPay backend (FastAPI · Supabase · AWS SAM · af-south-1).
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
| This month's summary | ✅ | ✅ |
| View last 10 transactions | ✅ | ✅ |
| Withdrawal status (last 3) | ✅ | ✅ |
| View active products + prices | ✅ (contextual button) | ✅ |
| View QR code | ✅ (link to QR image) | ✅ |
| Withdraw | ❌ redirect to website | ✅ |
| Create a charge | ❌ redirect to website | ✅ |
| KYC verification | ❌ redirect to website | ✅ |
| Payout account changes | ❌ redirect to website | ✅ |
| Speak to an agent | ✅ (HELP → agent handoff) | ✅ |
| Receive payment notification | ✅ (automatic) | — |
| Receive KYC decision | ✅ (automatic) | — |
| Receive withdrawal decision | ✅ (automatic) | — |

---

## Conversation UI — Full Flow

> **UI pattern:** Hybrid — interactive list message (7 rows main menu + Account & Tools sub-list) + 3 quick-tap reply buttons beneath every response + number shortcuts always active. Merchants who use it daily just type `1` and get their balance in 2 seconds. Merchants who are new tap buttons. Both work.
> My Products is not in the main menu — it surfaces as a contextual button on Balance and Transactions responses, and via keyword `products` anytime.

---

### Step 1 — Merchant sends any greeting

Triggered by: any first message, `hi`, `hello`, `hey`, `good day`, `hola`, or any unrecognised text.

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│               Good day 👋     14:32 │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Good day, Bryne! 👋          │   │
│  │                             │   │
│  │ Welcome to VulaPay.         │   │
│  │ Tap Menu to see what you    │   │
│  │ can do, or reply with a     │   │
│  │ number anytime:             │   │
│  │                             │   │
│  │ 1️⃣  Balance                  │   │
│  │ 2️⃣  Today's Earnings         │   │
│  │ 3️⃣  This Month's Summary     │   │
│  │ 4️⃣  Recent Transactions      │   │
│  │ 5️⃣  Withdrawals              │   │
│  │ 6️⃣  Account & Tools          │   │
│  │ 0️⃣  Help / Agent             │   │
│  │                             │   │
│  │ ⏰ 14:32                    │   │
│  └─────────────────────────────┘   │
│                                     │
│       ┌─────────────────────┐       │
│       │      📋 Menu        │       │
│       └─────────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 2 — Merchant taps Menu button

Opens a WhatsApp **list message** — single tap reveals all 6 options as selectable rows. No 3-button cap applies to list messages.

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📋 VulaPay Menu             │   │
│  │─────────────────────────────│   │
│  │ What would you like to do?  │   │
│  │ Tap an option or reply with │   │
│  │ its number.                 │   │
│  │                             │   │
│  │ 1️⃣  💰 Balance               │   │
│  │ 2️⃣  📅 Today's Earnings      │   │
│  │ 3️⃣  📊 This Month           │   │
│  │ 4️⃣  📜 Recent Transactions   │   │
│  │ 5️⃣  💸 Withdrawals           │   │
│  │ 6️⃣  🔧 Account & Tools       │   │
│  │ 0️⃣  ❓ Help / Agent          │   │
│  │                             │   │
│  │ ⏰ 14:33                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │💰 Balance │  │📅 Today's     │  │
│  └───────────┘  └───────────────┘  │
│         ┌───────────────────┐       │
│         │  📋 Full Menu     │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

> **Meta message types used here:**
> - The numbered list in the body = plain text (always visible)
> - The 2 quick-tap buttons = `interactive/button` (3 max — we use 2 + "Full Menu" as the third)
> - Tapping "Full Menu" sends a `interactive/list` message with all 6 rows as selectable sections

---

### Step 2b — Full Menu list (opened by tapping 📋 Full Menu)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📋 VulaPay Menu             │   │
│  │─────────────────────────────│   │
│  │ 💰 Balance                  │   │
│  │ Check available balance     │   │
│  │─────────────────────────────│   │
│  │ 📅 Today's Earnings         │   │
│  │ What you made today         │   │
│  │─────────────────────────────│   │
│  │ 📊 This Month's Summary      │   │
│  │ Month-to-date totals        │   │
│  │─────────────────────────────│   │
│  │ 📜 Recent Transactions      │   │
│  │ Last 10 payments            │   │
│  │─────────────────────────────│   │
│  │ 💸 Withdrawals               │   │
│  │ Status + request payout     │   │
│  │─────────────────────────────│   │
│  │ 🔧 Account & Tools           │   │
│  │ QR code, charges, KYC       │   │
│  │─────────────────────────────│   │
│  │ ❓ Help / Agent              │   │
│  │ Speak to the team           │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 2c — Account & Tools sub-list (opened by tapping 🔧 Account & Tools)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 🔧 Account & Tools          │   │
│  │─────────────────────────────│   │
│  │ 📷 View QR Code              │   │
│  │ Your payment QR link        │   │
│  │─────────────────────────────│   │
│  │ ⚡ Create Charge              │   │
│  │ Set amount → vula-pay.co.za │   │
│  │─────────────────────────────│   │
│  │ 📄 KYC Verification          │   │
│  │ Upload docs → vula-pay.co.za│   │
│  │─────────────────────────────│   │
│  │ 📊 Withdrawal Status         │   │
│  │ Track your last payouts     │   │
│  │─────────────────────────────│   │
│  │ 🔔 Notifications             │   │
│  │ Manage alert preferences    │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3a — Balance (tap row or type `1`)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│                       1       14:34 │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 💰 Your Balance             │   │
│  │                             │   │
│  │ Available:        R 850.00  │   │
│  │ Pending:          R 120.00  │   │
│  │ Ready to withdraw: R 850.00 │   │
│  │                             │   │
│  │ Reply *0* for menu          │   │
│  │ ⏰ 14:34                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │📅 Earnings│  │📜 Transactions│  │
│  └───────────┘  └───────────────┘  │
│         ┌───────────────────┐       │
│         │    📋 Full Menu   │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3b — Today's Earnings (tap row or type `2`)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│                       2       14:35 │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📅 Today's Earnings         │   │
│  │ Thursday, 19 Sep 2026       │   │
│  │                             │   │
│  │ Transactions:    6          │   │
│  │ Total received:  R 610.00   │   │
│  │ Fees:          - R  36.60   │   │
│  │ Net earned:      R 573.40   │   │
│  │                             │   │
│  │ Reply *0* for menu          │   │
│  │ ⏰ 14:35                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │💰 Balance │  │📜 Transactions│  │
│  └───────────┘  └───────────────┘  │
│         ┌───────────────────┐       │
│         │    📋 Full Menu   │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3c — Recent Transactions (tap row or type `3`)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│                       3       14:36 │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 📜 Recent Transactions      │   │
│  │                             │   │
│  │ + R  85.00  · Today 14:32   │   │
│  │ + R 120.00  · Today 11:05   │   │
│  │ + R  50.00  · Today 09:44   │   │
│  │ + R 200.00  · 18 Sep 16:20  │   │
│  │ + R  75.00  · 18 Sep 13:11  │   │
│  │ + R  90.00  · 18 Sep 10:30  │   │
│  │ + R 110.00  · 17 Sep 15:55  │   │
│  │ + R  60.00  · 17 Sep 12:00  │   │
│  │ + R  45.00  · 16 Sep 17:22  │   │
│  │ + R 130.00  · 16 Sep 09:10  │   │
│  │                             │   │
│  │ View all:                   │   │
│  │ vula-pay.co.za/transactions  │   │
│  │                             │   │
│  │ Reply *0* for menu          │   │
│  │ ⏰ 14:36                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │💰 Balance │  │💳 Last Payment│  │
│  └───────────┘  └───────────────┘  │
│         ┌───────────────────┐       │
│         │    📋 Full Menu   │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3d — Last Payment (tap row or type `4`)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│                       4       14:37 │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 💳 Last Payment             │   │
│  │                             │   │
│  │ Amount:   R 85.00           │   │
│  │ Status:   ✅ Successful      │   │
│  │ Date:     19 Sep, 14:32     │   │
│  │ Ref:      STP000068070EFA   │   │
│  │                             │   │
│  │ Reply *0* for menu          │   │
│  │ ⏰ 14:37                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │💰 Balance │  │📜 Transactions│  │
│  └───────────┘  └───────────────┘  │
│         ┌───────────────────┐       │
│         │    📋 Full Menu   │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3e — Withdraw (tap row or type `5`)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│                       5       14:38 │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 💸 Withdrawals              │   │
│  │                             │   │
│  │ Available to withdraw:      │   │
│  │ R 850.00                    │   │
│  │                             │   │
│  │ Withdrawals are processed   │   │
│  │ securely on your account.   │   │
│  │                             │   │
│  │ 👉 vula-pay.co.za/withdrawals│   │
│  │                             │   │
│  │ Reply *0* for menu          │   │
│  │ ⏰ 14:38                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌───────────┐  ┌───────────────┐  │
│  │💰 Balance │  │❓ Help        │  │
│  └───────────┘  └───────────────┘  │
│         ┌───────────────────┐       │
│         │    📋 Full Menu   │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3f — Help / Agent (tap row or type `6`)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│                       6       14:39 │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ ❓ Help                     │   │
│  │                             │   │
│  │ Reply *agent* to speak to   │   │
│  │ a VulaPay team member.      │   │
│  │ Mon–Fri · 8am–5pm SAST      │   │
│  │                             │   │
│  │ Or jump straight to:        │   │
│  │ 1️⃣  Balance                  │   │
│  │ 2️⃣  Today's Earnings         │   │
│  │ 3️⃣  Recent Transactions      │   │
│  │ 4️⃣  Last Payment             │   │
│  │ 5️⃣  Withdraw                 │   │
│  │                             │   │
│  │ Reply *0* for menu          │   │
│  │ ⏰ 14:39                    │   │
│  └─────────────────────────────┘   │
│                                     │
│  ┌───────────────────────────────┐ │
│  │       💬 Speak to Agent       │ │
│  └───────────────────────────────┘ │
│         ┌───────────────────┐       │
│         │    📋 Full Menu   │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Step 3g — Agent handoff (type `agent` or tap 💬 Speak to Agent)

```
┌─────────────────────────────────────┐
│  ← VulaPay                     🔍  │
├─────────────────────────────────────┤
│                                     │
│                   agent      14:40  │
│                              ✓✓    │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ 👤 Agent Request Received   │   │
│  │                             │   │
│  │ Hi Bryne, a VulaPay team    │   │
│  │ member will reach out to    │   │
│  │ you shortly.                │   │
│  │                             │   │
│  │ Business: Bryne's Store     │   │
│  │ Phone:    +27 61 658 3827   │   │
│  │                             │   │
│  │ Hours: Mon–Fri 8am–5pm SAST │   │
│  │                             │   │
│  │ Reply *0* for menu          │   │
│  │ ⏰ 14:40                    │   │
│  └─────────────────────────────┘   │
│                                     │
│         ┌───────────────────┐       │
│         │    📋 Full Menu   │       │
│         └───────────────────┘       │
│                                     │
└─────────────────────────────────────┘
```

---

### Main menu — summary of UI types used

| Element | Meta message type | Notes |
|---|---|---|
| Greeting body text + number list | `text` | Always visible, no interaction needed |
| 📋 Menu button on greeting | `interactive/button` | Single CTA button |
| Main menu rows (7 options) | `interactive/list` | Single button opens it |
| Account & Tools sub-list (4 options) | `interactive/list` | Second list triggered by row selection |
| Quick-tap buttons on responses | `interactive/button` | Max 3 — 2 contextual + Full Menu |
| Number shortcuts `0`–`6`, `agent` | `text` routing | Always active, no button tap needed |

---

### Handler responses — text content

All response text is documented in the UI mockups above. Supabase queries per handler:

**1 — Balance** (`BALANCE` list row or keyword `1`)
- Available: `transactions` settled `net_cents` − in-flight withdrawals (same logic as `GET /merchants/me/balance`)
- Pending: `transactions` where `status=success` and `settlement_status=pending`
- Ready to withdraw: same as available
- Contextual buttons: `📦 Products` + `📅 Earnings` + `📋 Full Menu`

**2 — Today's Earnings** (`TODAYS_EARNINGS` list row or keyword `2`)
- `transactions` where `merchant_id=X`, `status=success`, `paid_at >= today 00:00 SAST`
- Return: count, sum of `amount_cents`, sum of `platform_fee_cents`, net
- Contextual buttons: `💰 Balance` + `📜 Transactions` + `📋 Full Menu`

**3 — This Month's Summary** (`MONTHLY_SUMMARY` list row or keyword `3`)
- `transactions` where `merchant_id=X`, `status=success`, `paid_at >= first day of current month SAST`
- Return: count, sum of `amount_cents`, sum of `platform_fee_cents`, net, total withdrawn this month
- Contextual buttons: `💰 Balance` + `📅 Today` + `📋 Full Menu`

**4 — Recent Transactions** (`TRANSACTIONS` list row or keyword `4`)
- `transactions` where `merchant_id=X`, `status=success`, order by `paid_at desc`, limit 10
- Contextual buttons: `💰 Balance` + `📦 Products` + `📋 Full Menu`

**5 — Withdrawals** (`WITHDRAWALS` list row or keyword `5`)
- Fetch available balance (same as handler 1) + last 3 withdrawals from `withdrawals` table ordered by `requested_at desc`
- Show status of each: pending / approved / paid
- Link to `vula-pay.co.za/withdrawals` to request a new one
- Never processes a withdrawal — read-only + redirect
- Contextual buttons: `💰 Balance` + `📜 Transactions` + `📋 Full Menu`

**6 — Account & Tools** (`ACCOUNT_TOOLS` list row or keyword `6`)
- Sends the Account & Tools sub-list (4 rows: View QR Code, Create Charge, KYC, Withdrawal Status)

**6.1 — View QR Code** (`VIEW_QR` sub-list row or keyword `qr`)
- Fetch primary payment code reference from `payment_codes` where `merchant_id=X` and `is_primary=true`
- Reply with link: `vula-pay.co.za/pay/{reference}`
- Contextual buttons: `💰 Balance` + `⚡ Create Charge` + `📋 Full Menu`

**6.2 — Create Charge** (`CREATE_CHARGE` sub-list row or keyword `charge`)
- Static reply with link to `vula-pay.co.za/charges`
- Contextual buttons: `📷 View QR` + `💰 Balance` + `📋 Full Menu`

**6.3 — KYC** (`KYC` sub-list row or keyword `kyc`)
- Fetch `merchants.kyc_status` — show current status + link to `vula-pay.co.za/settings`
- Contextual buttons: `💰 Balance` + `❓ Help` + `📋 Full Menu`

**6.4 — Withdrawal Status** (`WITHDRAWAL_STATUS` sub-list row or keyword `wd`)
- Last 3 withdrawals from `withdrawals` table, show amount + status + date
- Contextual buttons: `💰 Balance` + `💸 Withdrawals` + `📋 Full Menu`

**6.5 — Notifications** (`NOTIFICATIONS` sub-list row or keyword `notifications`)
- Static reply showing current `merchants.notification_channel` value
- Link to `vula-pay.co.za/settings/notifications` for granular preferences
- Also handles `STOP` (opt out) and `START` (opt back in) as global toggle
- Contextual buttons: `💰 Balance` + `❓ Help` + `📋 Full Menu`

**0 — Help** (`HELP` list row or keyword `0`, `help`)
- Static reply. Adds `💬 Speak to Agent` as a single reply button.

**agent** — keyword `agent` or button tap from Help screen
- Static reply with merchant name + phone
- Log to `whatsapp_agent_requests` table: `merchant_id`, `phone`, `business_name`, `requested_at`

**products** — keyword `products` (contextual button from Balance / Transactions)
- `products` where `merchant_id=X`, `active=true`, order by `name`, limit 10
- Return: name + price for each

---

### Shortcut keywords (always active)

| Keyword | Action |
|---|---|
| `menu`, `hi`, `hello`, `hey`, `good day` | Show greeting + Menu button |
| `1` | Balance |
| `2` | Today's Earnings |
| `3` | This Month's Summary |
| `4` | Recent Transactions |
| `5` | Withdrawals |
| `6` | Account & Tools sub-list |
| `qr` | View QR Code |
| `charge` | Create Charge link |
| `kyc` | KYC status + link |
| `wd` | Withdrawal Status |
| `notifications` | Notifications status + link |
| `0`, `help` | Help |
| `agent` | Agent handoff |
| `products` | My Products list |
| `stop` | Opt out — sets `notification_channel = 'sms'` |
| `start` | Opt back in — sets `notification_channel = 'whatsapp'` |

---

## Outbound Notifications (automatic, no user action needed)

These fire automatically when events happen. The merchant does not need to message first.

| Event | Template | Message |
|---|---|---|
| Payment received | `vulapay_payment_received` | "💰 Hi {name}, payment received on VulaPay!\n\nAmount: R{amount}\nRef: {reference}\nAvailable balance: R{balance}" |
| Withdrawal approved | `vulapay_withdrawal_approved` | "✅ Hi {name}, your withdrawal has been approved on VulaPay!\n\nR{amount} is being processed to your bank account." |
| Withdrawal rejected | `vulapay_withdrawal_rejected` | "❌ Hi {name}, your withdrawal was unsuccessful on VulaPay.\n\nAmount: R{amount}\nReason: {reason}" |
| KYC approved | `vulapay_kyc_approved` | "✅ Hi {name}, your KYC has been approved on VulaPay!\n\nYour identity has been verified. You can now request withdrawals." |
| KYC rejected | `vulapay_kyc_rejected` | "❌ Hi {name}, your KYC was not approved on VulaPay.\n\nReason: {reason}\n\nPlease re-upload at vula-pay.co.za/settings" |

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

- Withdrawals — always redirected to `https://vula-pay.co.za/withdrawals`
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

> Full template bodies are in `docs/whatsapp_templates.md`.

| Template name | Variables |
|---|---|
| `vulapay_payment_received` | `{{1}}` first name, `{{2}}` amount, `{{3}}` reference, `{{4}}` new available balance |
| `vulapay_withdrawal_approved` | `{{1}}` first name, `{{2}}` amount |
| `vulapay_withdrawal_rejected` | `{{1}}` first name, `{{2}}` amount, `{{3}}` reason |
| `vulapay_kyc_approved` | `{{1}}` first name |
| `vulapay_kyc_rejected` | `{{1}}` first name, `{{2}}` reason |

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

**1. Greeting message — text body + single Menu button:**
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": {
      "text": "Good day, Bryne! 👋\n\nWelcome to VulaPay.\nTap Menu to get started, or reply with a number:\n\n1️⃣  💰 Balance\n2️⃣  📅 Today's Earnings\n3️⃣  📜 Recent Transactions\n4️⃣  💳 Last Payment\n5️⃣  💸 Withdraw\n6️⃣  ❓ Help / Agent"
    },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "OPEN_MENU", "title": "📋 Menu" } }
      ]
    }
  }
}
```

**2. Main menu — interactive list message (7 rows):**
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "interactive",
  "interactive": {
    "type": "list",
    "body": { "text": "What would you like to do?\nTap an option or reply with its number." },
    "action": {
      "button": "📋 VulaPay",
      "sections": [
        {
          "title": "VulaPay",
          "rows": [
            { "id": "BALANCE",         "title": "💰 Balance",              "description": "Check available balance" },
            { "id": "TODAYS_EARNINGS", "title": "📅 Today's Earnings",     "description": "What you made today" },
            { "id": "MONTHLY_SUMMARY", "title": "📊 This Month's Summary",  "description": "Month-to-date totals" },
            { "id": "TRANSACTIONS",    "title": "📜 Recent Transactions",  "description": "Last 10 payments" },
            { "id": "WITHDRAWALS",     "title": "💸 Withdrawals",           "description": "Status + request payout" },
            { "id": "ACCOUNT_TOOLS",   "title": "🔧 Account & Tools",      "description": "QR code, charges, KYC" },
            { "id": "HELP",            "title": "❓ Help / Agent",         "description": "Speak to the team" }
          ]
        }
      ]
    }
  }
}
```

**3. Account & Tools sub-list (4 rows):**
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "interactive",
  "interactive": {
    "type": "list",
    "body": { "text": "🔧 Account & Tools\n\nTap an option or type a shortcut." },
    "action": {
      "button": "🔧 Tools",
      "sections": [
        {
          "title": "Account & Tools",
          "rows": [
            { "id": "VIEW_QR",           "title": "📷 View QR Code",       "description": "Your payment QR link" },
            { "id": "CREATE_CHARGE",     "title": "⚡ Create Charge",      "description": "Set amount → vula-pay.co.za" },
            { "id": "KYC",              "title": "📄 KYC Verification",   "description": "Upload docs → vula-pay.co.za" },
            { "id": "WITHDRAWAL_STATUS", "title": "📊 Withdrawal Status",  "description": "Track your last payouts" },
            { "id": "NOTIFICATIONS",    "title": "🔔 Notifications",      "description": "Manage alert preferences" }
          ]
        }
      ]
    }
  }
}
```

**3. Response with contextual quick-tap buttons (example: Balance response):**
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "interactive",
  "interactive": {
    "type": "button",
    "body": {
      "text": "💰 Your Balance\n\nAvailable:         R 850.00\nPending:           R 120.00\nReady to withdraw: R 850.00\n\nReply *0* for menu"
    },
    "action": {
      "buttons": [
        { "type": "reply", "reply": { "id": "TODAYS_EARNINGS", "title": "📅 Earnings" } },
        { "type": "reply", "reply": { "id": "TRANSACTIONS",    "title": "📜 Transactions" } },
        { "type": "reply", "reply": { "id": "OPEN_MENU",       "title": "📋 Full Menu" } }
      ]
    }
  }
}
```

> Each response uses 2 contextual buttons relevant to what the merchant likely wants next, plus "📋 Full Menu" as the third. This keeps navigation fast without ever hitting the 3-button cap.

**4. Plain text reply (fallback / agent handoff — no buttons needed):**
```json
{
  "messaging_product": "whatsapp",
  "to": "27XXXXXXXXX",
  "type": "text",
  "text": { "body": "👤 Agent Request Received\n\nHi Bryne, a VulaPay team member will reach out shortly.\n\nBusiness: Bryne's Store\nPhone: +27 61 658 3827\n\nHours: Mon–Fri 8am–5pm SAST\n\nReply *0* for menu" }
}
```

> Plain text and interactive replies only work within the 24-hour customer service window (merchant messaged first). Outside that window, only approved templates can be sent.

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
"BALANCE"          | "1"                                     → handle_balance(merchant)
"TODAYS_EARNINGS"  | "2"                                     → handle_todays_earnings(merchant)
"MONTHLY_SUMMARY"  | "3"                                     → handle_monthly_summary(merchant)
"TRANSACTIONS"     | "4"                                     → handle_transactions(merchant)
"WITHDRAWALS"      | "5"                                     → handle_withdrawals(merchant)
"ACCOUNT_TOOLS"    | "6"                                     → send_account_tools_submenu(merchant)
"VIEW_QR"          | "qr"                                    → handle_view_qr(merchant)
"CREATE_CHARGE"    | "charge"                                → handle_create_charge(merchant)
"KYC"              | "kyc"                                   → handle_kyc(merchant)
"WITHDRAWAL_STATUS"| "wd"                                    → handle_withdrawal_status(merchant)
"NOTIFICATIONS"    | "notifications"                         → handle_notifications(merchant)
"HELP"             | "0" | "help"                            → handle_help(merchant)
"agent"            | "AGENT"                                 → handle_agent_request(merchant)
"products"                                                   → handle_products(merchant)
"OPEN_MENU"        | "menu" | "hi" | "hello" | unknown        → send_greeting(merchant)
"stop"             | "STOP"                                  → handle_stop(merchant)
"start"            | "START"                                 → handle_start(merchant)
```

### Sprint 2 checklist

**Backend:**
- [ ] `GET /webhooks/whatsapp` — hub.challenge verification
- [ ] `POST /webhooks/whatsapp` — HMAC validation + message routing
- [ ] `app/services/whatsapp_bot.py` — all 13 handlers + menu sender + sub-list sender
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
- **Notification preferences UI** — settings page update is a separate frontend task
- **Multi-turn conversation state** — each message is stateless in Sprint 2; Bedrock MVP 2 is also stateless
- **Catalog messages** — not needed, list messages cover the menu use case fully

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

- Withdrawals — always redirected to `https://vula-pay.co.za/withdrawals`
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
| KYC approved | `app/api/routes/kyc.py` | alongside existing `send_sms` call | "✅ Your VulaPay KYC has been approved. You can now withdraw." |
| KYC rejected | `app/api/routes/kyc.py` | alongside existing `send_sms` call | "❌ Your VulaPay KYC was not approved. Reason: {reason}" |

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
| `vulapay_payment_received` | Payment success | `{{1}}` = amount (e.g. "R85.00"), `{{2}}` = reference |
| `vulapay_withdrawal_approved` | Withdrawal approved | `{{1}}` = amount |
| `vulapay_withdrawal_rejected` | Withdrawal rejected | `{{1}}` = amount, `{{2}}` = reason |
| `vulapay_kyc_approved` | KYC approved | none |
| `vulapay_kyc_rejected` | KYC rejected | `{{1}}` = reason |

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
- [ ] Submit `vulapay_payment_received`, `vulapay_withdrawal_approved`, `vulapay_withdrawal_rejected`, `vulapay_kyc_approved`, `vulapay_kyc_rejected` templates for Meta approval

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
  WEBSITE     → reply with link to vula-pay.co.za
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

If no match is found → reply: "We couldn't find a Scan2Pay account linked to this number. Please sign up at vula-pay.co.za"

### Menu flow

```
Any message → show main menu (3 buttons)

Button: BALANCE
  → query Supabase: settled net_cents - in_flight withdrawals
  → reply: "💰 Available: R{x}\nPending settlement: R{y}"

Button: TRANSACTIONS
  → query last 5 success transactions for merchant
  → reply: list of "+ R{amount} · {date}" lines
  → footer: "View all at vula-pay.co.za/transactions"

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
- **Catalog messages** — list messages cover the menu use case fully
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
