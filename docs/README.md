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
| Frontend (Next.js 15) | `../scan2pay-web/` | ✅ All merchant + admin pages built, mock data |
| Backend (FastAPI + SAM) | `../scan2pay-backend/` | 🔲 Scaffolded, ready to implement |
| Original frontend (TanStack/Vite) | `../Scan2Pay-frontend/` | Reference only |

## Quick Reference

### Demo Accounts (mock)
| Role | Phone | Password |
|------|-------|----------|
| Vendor | 082 123 4567 | password123 |
| Tip earner | 083 765 4321 | password123 |
| Taxi | 084 555 0192 | password123 |
| Admin | 087 000 1234 | admin123 |

### API Base URL
| Env | URL |
|-----|-----|
| Local | `http://localhost:8000/v1` |
| Staging | `https://api-staging.scan2pay.co.za/v1` |
| Production | `https://api.scan2pay.co.za/v1` |

### Lambda Summary
| Lambda | Trigger | Job |
|--------|---------|-----|
| `Scan2PayApiFunction` | API Gateway | Entire FastAPI app |
| `ExpireChargesFunction` | Every 1 min | Expire single-use charges |
| `ReconcilePaystackFunction` | Every 15 min | Verify pending payments |
| `BuildSettlementsFunction` | Daily 02:00 SAST | Build merchant payout rows |
