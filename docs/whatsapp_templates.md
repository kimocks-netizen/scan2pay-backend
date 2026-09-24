# VulaPay — WhatsApp Message Templates

> Submit all 6 to Meta Business Manager under category: **UTILITY**
> Language: **English (en_US)**
> Header: plain text only — no emojis, no variables (Meta requirement)
> Body: emojis + variables only — no URLs in body
> Footer: static plain text opt-out
> CTA button: only on **Template 6** (daily digest) — no button on per-event templates 1–5

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

Please reply to this message for help.
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

Please re-upload your documents. If you need help, reply to this message.
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | `users.full_name.split()[0]` — first name only | `Bryne` |
| `{{2}}` | rejection reason from admin | `ID document is expired` |

---

## Template 6 — Daily Summary (Digest)

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
```

**Footer:** `Reply STOP to opt out of WhatsApp notifications`

**Button:** CTA — Visit Website
| Field | Value |
|---|---|
| Button text | `View transactions` |
| URL | `https://app.vula-pay.co.za/transactions` |

**Variables:**
| Variable | Source | Example |
|---|---|---|
| `{{1}}` | `users.full_name.split()[0]` — first name only | `Bryne` |
| `{{2}}` | date formatted `DD Mon YYYY` | `19 Sep 2026` |
| `{{3}}` | count of successful transactions today | `6` |
| `{{4}}` | `sum(amount_cents) / 100:.2f` for today | `610.00` |
| `{{5}}` | `sum(platform_fee_cents) / 100:.2f` for today | `36.60` |
| `{{6}}` | net earned `(total − fees) / 100:.2f` for today | `573.40` |

**When it fires:**
Sent by the `SendDailyDigestFunction` cron at 19:00 SAST (17:00 UTC) to merchants
whose `notification_prefs.payments_whatsapp_mode = 'digest'`.
Not sent if the merchant had zero transactions that day.

---

## Variable summary across all templates

| Template | `{{1}}` | `{{2}}` | `{{3}}` | `{{4}}` | `{{5}}` | `{{6}}` |
|---|---|---|---|---|---|---|
| `vulapay_payment_received` | first name | amount | reference | balance | — | — |
| `vulapay_withdrawal_approved` | first name | amount | — | — | — | — |
| `vulapay_withdrawal_rejected` | first name | amount | reason | — | — | — |
| `vulapay_kyc_approved` | first name | — | — | — | — | — |
| `vulapay_kyc_rejected` | first name | reason | — | — | — | — |
| `vulapay_daily_summary` | first name | date | tx count | total received | fees | net earned |

---

## Submission checklist

- [ ] Log in to [Meta Business Manager](https://business.facebook.com)
- [ ] Go to **WhatsApp Manager → Message Templates → Create Template**
- [ ] For each template: set category = **UTILITY**, language = **English (en_US)**
- [ ] Paste header exactly as shown — plain text, no emojis
- [ ] Paste body exactly as shown — emojis and variables only, **no URLs in body**
- [ ] Paste footer exactly as shown — `Reply STOP to opt out of WhatsApp notifications`
- [ ] For **Template 6 only**: add CTA button — type = **Visit Website**, text = `View transactions`, URL = `https://app.vula-pay.co.za/transactions`
- [ ] Templates 1–5: no button
- [ ] Submit all 6 for review
- [ ] Approval usually takes 24–48h — do not start Sprint 1 build until at least `vulapay_payment_received` is approved
- [ ] Once approved, update template names in `app/services/whatsapp_service.py`

## Tips for fast approval

- UTILITY category is approved faster than MARKETING — these all qualify as UTILITY (transactional notifications)
- Header must be plain text — no emojis, no variables (Meta will reject otherwise)
- Body emojis are fine and encouraged for readability
- Footer opt-out language signals compliance to Meta reviewers — helps approval speed
- Variable placeholders must match exactly: `{{1}}`, `{{2}}` — double curly braces
- Only include URLs from your registered business domain (`vula-pay.co.za`)
