# Scan2Pay — Business Overview

> Reflects the actual implemented product.

---

## The One-Line Pitch

> Scan a QR code. Pay. Done. No card machine. No app. No reprinting.

---

## The Problem

Small vendors, taxi operators, petrol attendants, waiters and informal workers across South Africa cannot easily accept digital payments. Card machines are expensive and require a formal banking relationship. Cash is declining. These people are being left out.

---

## The Solution

Scan2Pay gives every merchant a permanent QR code tied to their account. The customer scans it with their normal phone camera, pays by card, and the merchant sees the money instantly.

There are **three distinct ways** merchants use Scan2Pay, depending on their business type. All three share one rule: **the QR code is permanent and never needs to be reprinted.**

---

## The Three Merchant Types

---

### Type 1 — Tip & Open Payments (permanent QR, customer enters amount)

**Who:** Waiters, petrol attendants, car guards, baristas, buskers, freelancers.

**How it works:**

The merchant gets one permanent QR code when they register. They print it, laminate it, put it on a card or lanyard, and display it. It never changes.

When a customer wants to pay or tip:
1. Customer scans the QR with their phone camera
2. Sees the merchant's name
3. Types in any amount they choose
4. Pays by card

The merchant does nothing per transaction. The QR is always live, always ready, always the same.

```
Permanent QR (variable mode)
        |
        v
Customer scans
        |
        v
"Enter amount: R ____"
        |
        v
Customer types R50 → pays by card
        |
        v
Merchant notified — QR stays active for next customer
```

---

### Type 2 — Vendor Charge (merchant sets amount, permanent QR shows it for 5 minutes)

**Who:** Street vendors, market traders, spaza shops — any merchant present with the customer who wants to charge a specific amount right now.

**How it works:**

The merchant opens the **Charge page**, types the amount (e.g. R85), and taps "Create payment request". Their **permanent QR code** appears on screen — the same QR they always have — but for the next 5 minutes it shows R85 to anyone who scans it. The customer scans and pays R85. After payment (or after 5 minutes), the QR goes back to normal.

```
Merchant opens Charge page
        |
        v
Types R85 → taps "Create payment request"
        |
        v
Permanent QR appears on screen
(same QR as always — now locked to R85 for 5 minutes)
        |
        v
Customer scans the QR
        |
        v
Sees "R85" — taps Pay — pays by card
        |
        v
Merchant screen shows "Paid"
QR returns to normal — ready for next customer
```

**Key points:**
- The QR code itself **never changes** — it is the merchant's permanent primary QR
- Only the **amount** is temporary — it is locked to R85 for 5 minutes, then clears
- If nobody pays within 5 minutes, the charge session expires and the QR goes back to variable mode
- The merchant can start a new charge at any time — the previous session is cancelled
- The recent charges panel shows the last 5 charge sessions

**Why this is better than a temporary QR:**
The merchant prints their QR once and sticks it somewhere permanent (counter, table, wall). They never need to show a new QR — they just type the amount and the existing sticker/screen QR temporarily shows that amount.

---

### Type 3 — Product QR Codes (permanent QR per product, fixed price)

**Who:** Barbers, car washes, small shops — any merchant with defined products or services at set prices.

**How it works:**

The merchant creates products in their dashboard (e.g. "Haircut — R80", "Full Car Wash — R150"). Each product automatically gets its own permanent QR code. The merchant prints a QR sticker per product and sticks it next to that product or service.

When a customer wants to pay for a specific product:
1. Customer scans the product's QR code
2. Sees the product name and current price
3. One tap to pay — no amount entry needed

```
Product: "Haircut"
Permanent QR: PRD-A3F2C1B4
        |
        v
Customer scans
        |
        v
"Haircut — R80" → [ Pay R80 ]
        |
        v
Pays by card — QR stays active for next customer
```

**Price changes without reprinting:**

If the barber increases the price from R80 to R100, they update it once in the dashboard. The same QR sticker now shows R100 to the next customer. No new sticker. No reprinting.

---

## Summary — The Three Types Side by Side

| | Type 1: Tip / Open | Type 2: Vendor Charge | Type 3: Product QR |
|---|---|---|---|
| **Who** | Waiters, tip earners | Vendors, market traders | Barbers, shops, car washes |
| **QR** | Permanent — never changes | Permanent — never changes | Permanent — never changes |
| **Amount** | Customer enters | Merchant sets per charge (5 min window) | Fixed to product price |
| **QR count** | One (primary) | One (primary, reused every charge) | One per product |
| **Reprinting needed?** | Never | Never | Never |
| **Where QR lives** | Printed card / lanyard / wall | Printed sticker or screen | Printed sticker per product |
| **After payment** | QR stays active | QR clears charge, back to normal | QR stays active |

---

## What the Customer Always Does

Regardless of which type:

1. Opens phone camera → points at QR
2. Taps the link (`scan2pay.site/pay/...`)
3. Sees merchant name + amount (or keypad for Type 1 when no charge active)
4. Optionally enters email for receipt
5. Taps Pay → enters card details in Paystack popup
6. Done

No app. No account. No friction.

---

## Revenue Model

Scan2Pay charges a platform fee on every transaction, on top of Paystack's processing fee.

```
Customer pays:        R100.00
Paystack fee:          -R3.90   (2.9% + R1.00)
Platform fee:          -R2.50   (2.5% on Free plan)
Merchant receives:     R93.60
```

| Plan | Monthly | Platform fee |
|---|---|---|
| Free | R0 | 2.5% per transaction |
| Starter | R99 | 2.0% per transaction |
| Pro | R299 | 1.5% per transaction |

---

## Payment Processing

Scan2Pay uses **Paystack** for all card processing. Currently card-only. Apple Pay, Google Pay and Capitec Pay will be added before go-live.

---

## What Scan2Pay Is Not

- Not a wallet — no customer funds held
- Not a bank — no banking licence required
- Not a card machine — Paystack processes the cards
- Not an app — customers need nothing installed

---

## Core Principle

> Every QR code is permanent. The QR never changes — only what it resolves to changes. For Type 2 charges, the amount is temporarily locked for 5 minutes then clears. For Type 3 products, the price updates in the database. The physical sticker never needs to be replaced.
