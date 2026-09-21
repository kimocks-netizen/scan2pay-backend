# VulaPay — WhatsApp Message Templates

> Submit all 5 to Meta Business Manager under category: **UTILITY**
> Language: **English (en_US)**
> Header: plain text only — no emojis, no variables (Meta requirement)
> Body: emojis + variables + website URL
> Footer: static plain text opt-out
> No CTA button — notification preferences managed via Account & Tools in the WhatsApp bot

---

## Template 1 — Payment Received

**Template name:** `vulapay_payment_received`
**Category:** UTILITY
**Language:** en_US

**Header:** `Payment received on VulaPay`

**Body:**
```
💰 Hi {{1}}, you just received a payment!

Amount: R{{2}}
Reference: {{3}}
Available balance: R{{4}}

View transactions: vula-pay.co.za/transactions
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | `users.full_name.split()[0]` — first name only | `Bryne` |
| `{{2}}` | `transaction.amount_cents / 100:.2f` | `85.00` |
| `{{3}}` | `transaction.reference` | `STP000068070EFA` |
| `{{4}}` | available balance (`settled net_cents` − in-flight withdrawals) | `935.00` |

---

## Template 2 — Withdrawal Approved

**Template name:** `vulapay_withdrawal_approved`
**Category:** UTILITY
**Language:** en_US

**Header:** `Withdrawal approved on VulaPay`

**Body:**
```
✅ Hi {{1}}, your withdrawal has been approved!

R{{2}} is being processed to your bank account. This usually takes 1–2 business days.

View withdrawals: vula-pay.co.za/withdrawals
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | `users.full_name.split()[0]` — first name only | `Bryne` |
| `{{2}}` | `withdrawal.amount_cents / 100:.2f` | `500.00` |

---

## Template 3 — Withdrawal Rejected

**Template name:** `vulapay_withdrawal_rejected`
**Category:** UTILITY
**Language:** en_US

**Header:** `Withdrawal unsuccessful on VulaPay`

**Body:**
```
❌ Hi {{1}}, your withdrawal was unsuccessful.

Amount: R{{2}}
Reason: {{3}}

Please visit vula-pay.co.za/withdrawals or reply to this message for help.
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | `users.full_name.split()[0]` — first name only | `Bryne` |
| `{{2}}` | `withdrawal.amount_cents / 100:.2f` | `500.00` |
| `{{3}}` | rejection reason from admin | `Incorrect bank account details` |

---

## Template 4 — KYC Approved

**Template name:** `vulapay_kyc_approved`
**Category:** UTILITY
**Language:** en_US

**Header:** `KYC approved on VulaPay`

**Body:**
```
✅ Hi {{1}}, your KYC has been approved!

Your identity has been verified. You can now request withdrawals.

Visit vula-pay.co.za to get started.
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | `users.full_name.split()[0]` — first name only | `Bryne` |

---

## Template 5 — KYC Rejected

**Template name:** `vulapay_kyc_rejected`
**Category:** UTILITY
**Language:** en_US

**Header:** `KYC not approved on VulaPay`

**Body:**
```
❌ Hi {{1}}, your KYC was not approved.

Reason: {{2}}

Please re-upload your documents at vula-pay.co.za/settings. If you need help, reply to this message.
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | `users.full_name.split()[0]` — first name only | `Bryne` |
| `{{2}}` | rejection reason from admin | `ID document is expired` |

---

## How first name is extracted (backend)

All 5 templates use `{{1}}` as first name. Extract it consistently at send time:

```python
first_name = (user["full_name"] or "").split()[0] if user.get("full_name") else "there"
```

Fallback to `"there"` if `full_name` is null — message reads `Hi there,` instead of breaking.

---

## STOP opt-out handler (Sprint 2)

When a merchant replies `STOP`:
1. Update `merchants.notification_channel = 'sms'`
2. Reply with confirmation:
```
You have been unsubscribed from VulaPay WhatsApp notifications.
You will continue to receive SMS notifications.

To resubscribe, reply START anytime.
```

When a merchant replies `START`:
1. Update `merchants.notification_channel = 'whatsapp'`
2. Reply with confirmation:
```
✅ You are now subscribed to VulaPay WhatsApp notifications.

Reply with a number to get started:
1 - Balance
2 - Today's Earnings
3 - This Month's Summary
4 - Recent Transactions
```

> Full notification preferences (per event type, per channel) will be managed via
> Account & Tools → 🔔 Notifications → vula-pay.co.za/settings/notifications
> STOP/START is a blunt global toggle for now — granular control comes with the preferences page.

---

## Variable summary across all templates

| Template | `{{1}}` | `{{2}}` | `{{3}}` | `{{4}}` |
|---|---|---|---|---|
| `vulapay_payment_received` | first name | amount | reference | balance |
| `vulapay_withdrawal_approved` | first name | amount | — | — |
| `vulapay_withdrawal_rejected` | first name | amount | reason | — |
| `vulapay_kyc_approved` | first name | — | — | — |
| `vulapay_kyc_rejected` | first name | reason | — | — |

---

## Submission checklist

- [ ] Log in to [Meta Business Manager](https://business.facebook.com)
- [ ] Go to **WhatsApp Manager → Message Templates → Create Template**
- [ ] For each template: set category = **UTILITY**, language = **English (en_US)**
- [ ] Paste header exactly as shown — plain text, no emojis
- [ ] Paste body exactly as shown — emojis, variables and URL included
- [ ] Paste footer exactly as shown — `Reply STOP to opt out of WhatsApp notifications`
- [ ] Submit all 5 for review
- [ ] Approval usually takes 24–48h — do not start Sprint 1 build until at least `vulapay_payment_received` is approved
- [ ] Once approved, update template names in `app/services/whatsapp_service.py`

## Tips for fast approval

- UTILITY category is approved faster than MARKETING — these all qualify as UTILITY (transactional notifications)
- Header must be plain text — no emojis, no variables (Meta will reject otherwise)
- Body emojis are fine and encouraged for readability
- Footer opt-out language signals compliance to Meta reviewers — helps approval speed
- Variable placeholders must match exactly: `{{1}}`, `{{2}}` — double curly braces
- Only include URLs from your registered business domain (`vula-pay.co.za`)
