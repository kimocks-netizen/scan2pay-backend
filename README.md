# scan2pay-backend

FastAPI · Mangum · Supabase · Paystack · WinSMS · AWS SAM

See [`../Scan2PayDocumentation/09_Backend_Roadmap.md`](../Scan2PayDocumentation/09_Backend_Roadmap.md) for the full build roadmap.

---

## Project Structure

```
scan2pay-backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── admin.py          # Admin stats, users, pricing, settlements
│   │   │   ├── auth.py           # Register, login, refresh, logout, OTP
│   │   │   ├── billing.py        # Plans, pricing versions
│   │   │   ├── charges.py        # Create/list/cancel charges, SSE
│   │   │   ├── health.py         # GET /health
│   │   │   ├── merchants.py      # Merchant profile, payout account
│   │   │   ├── payment_codes.py  # CRUD payment codes
│   │   │   ├── payments.py       # Initialise payment, get status
│   │   │   ├── products.py       # CRUD products
│   │   │   ├── transactions.py   # List, stats, CSV export, payouts
│   │   │   ├── webhooks.py       # Paystack webhook (HMAC verified)
│   │   │   └── withdrawals.py    # Balance, list, create, cancel
│   │   └── __init__.py
│   ├── core/
│   │   ├── config.py             # All settings via SSM / env vars
│   │   ├── deps.py               # get_current_user_id, require_admin
│   │   └── security.py           # JWT, bcrypt, Paystack HMAC-SHA512
│   ├── cron/
│   │   ├── build_settlements.py  # Daily: group settled txns into payouts
│   │   ├── expire_charges.py     # Every 1 min: deactivate expired codes
│   │   └── reconcile_paystack.py # Every 15 min: verify pending payments
│   ├── db/
│   │   ├── repositories/         # One file per domain (Phase 4)
│   │   └── connection.py         # Supabase client singleton
│   ├── schemas/                  # Pydantic request/response models (Phase 3)
│   ├── services/
│   │   ├── paystack_service.py   # Init, verify, transfer, webhook
│   │   ├── settlement_service.py # Balance calc, payout grouping
│   │   └── sms_service.py        # WinSMS OTP
│   └── main.py                   # FastAPI app + all routers + Mangum handler
├── database/
│   └── migrations/               # Numbered .sql files (Phase 2)
├── scripts/                      # One-off utility scripts
├── tests/
│   ├── integration/              # Auth, payments, webhooks
│   └── unit/                     # Security, fee calc
├── .env.example
├── requirements.txt
└── template.yaml                 # SAM: 1 API Lambda + 3 cron Lambdas + S3
```

## Lambda Architecture

| Lambda | Trigger | Purpose |
|--------|---------|---------|
| `Scan2PayApiFunction` | API Gateway `/{proxy+}` | Entire FastAPI app via Mangum |
| `ExpireChargesFunction` | EventBridge every 1 min | Deactivate codes past `expires_at` |
| `ReconcilePaystackFunction` | EventBridge every 15 min | Verify `pending` payments > 10 min old |
| `BuildSettlementsFunction` | EventBridge daily 02:00 SAST | Group settled transactions into payout rows |

## Quick Start (local)

```bash
cp .env.example .env          # fill in Supabase + Paystack keys
pip install -r requirements.txt
uvicorn app.main:app --reload
```
