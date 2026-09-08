# Scan2Pay — Documentation Index

Central reference for the entire Scan2Pay platform.

---

## ⚠️ AI Assistant Rules (read before every session)

1. **Third-party APIs** — if unsure about the exact payload structure, authentication format, or endpoint behaviour of any external API (WinSMS, Paystack, WhatsApp, etc.), **ask the user first**. Do not guess or invent a format. The WinSMS incident (wrong payload — `messages[].messageText` instead of `message` + `recipients[]`) is a direct example of what happens when this rule is broken.

2. **What to build** — if the requirement is ambiguous or the scope of a feature is unclear, **ask before writing any code**. Do not assume what endpoints, fields, or behaviours are needed. A one-line question saves more time than rewriting the wrong implementation.

3. **Scope creep** — only build what was explicitly asked for in the current session. Do not add extra endpoints, fields, or logic that were not requested.

4. **Existing patterns** — before implementing anything new, check how it is already done in the codebase (e.g. check PredictIQ for WinSMS, check existing routes for DB query patterns). Prefer consistency over novelty.

---
## Documents

| # | File | Contents |
|---|------|----------|
| 01 | `01_Business_Overview.md` | Product vision, target market, user types, revenue model, competitive advantage |
| 02 | `02_Technical_Specification.md` | Full technical spec — all user flows, DB tables, API areas, security requirements |
| 03 | `03_Architecture.md` | Stack decisions, request flow, code modes, till charges, background jobs, rate limits |
| 04 | `04_Database.md` | Full PostgreSQL schema — every table, column, index, constraint and migration order |
| 05 | `05_API_Reference.md` | Every endpoint — request/response shapes, error codes, auth rules |
| 06 | `06_Payments_Paystack.md` | Paystack integration — charge lifecycle, webhook verification, fee formulas, settlement |
| 07 | `07_Admin_System.md` | Admin console — pricing versioning, audit log, withdrawal state machine |
| 08 | `08_Frontend_Roadmap.md` | Next.js migration progress and remaining frontend work |
| 09 | `09_Backend_Roadmap.md` | FastAPI backend — phase-by-phase build plan, Lambda architecture, SSM parameters |

## Projects

| Project | Path | Status |
|---------|------|--------|
| Frontend (Next.js 15) | `../scan2pay-web/` | ✅ All merchant pages live, wired to real API |
| Backend (FastAPI + SAM) | `../scan2pay-backend/` | ✅ Live on AWS Lambda (`af-south-1`) |
| Original frontend (TanStack/Vite) | `../Scan2Pay-frontend/` | Reference only — do not modify |

## Quick Reference

### Live Accounts (dev)
| Role | Phone | Password | Notes |
|------|-------|----------|-------|
| Vendor | 082 100 0001 | Vendor1234! | user_id: usr_001, mch_001, QR: QR-DEMO0001 |
| Tip earner | 066 040 4333 | 123456 | user_id: usr_004, mch_003, QR: QR-BA5ECDB1 |
| Admin | 061 658 3827 | Admin1234 | role: admin |

OTP bypass: code `0000`

### API
| Env | URL |
|-----|-----|
| Dev (live) | `https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod` |
| Prod | TBD |

### Deploy
```bash
bash scripts/deploy.sh        # dev
bash scripts/deploy.sh prod   # prod
```
Verifies AWS account `542727784619` (profile: `predictiq`) before deploying.

### Lambda Summary
| Lambda | Trigger | Job |
|--------|---------|-----|
| `Scan2PayApiFunction` | API Gateway | Entire FastAPI app |
| `ExpireChargesFunction` | Every 1 min | Expire single-use charges |
| `ReconcilePaystackFunction` | Every 15 min | Verify pending payments |
| `BuildSettlementsFunction` | Daily 02:00 SAST | Build merchant payout rows |
