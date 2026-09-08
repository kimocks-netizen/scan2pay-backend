# scan2pay-web — Frontend Roadmap

> Living document. Updated as each feature is wired to the real backend.
> Backend API base: `https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod`
> Set in `scan2pay-web/.env` → `NEXT_PUBLIC_API_URL`

---

## Stack
Next.js 15 App Router · TypeScript · Tailwind v4 · shadcn/ui · TanStack Query v5 · Zustand · React Hook Form · Zod · next-themes · `@paystack/inline-js`

---

## Current State Summary

### ✅ Wired to real backend

| Feature | File | Notes |
|---|---|---|
| Login / Register | `(auth)/login/page.tsx` | `POST /auth/login`, `POST /auth/register` |
| OTP verify | `(auth)/verify-otp/page.tsx` | `POST /auth/otp/verify` |
| Logout | `features/auth/mutations.ts` | `POST /auth/logout` |
| Auth store | `stores/useAuthStore.ts` | Zustand persist — `accessToken`, `refreshToken`, `user` |
| API client | `lib/api-client.ts` | Bearer token, parses `body.detail.code/message` (FastAPI shape) |
| Dashboard | `features/dashboard/api.ts` | `GET /merchants/me/transactions?limit=50`, `GET /merchants/me/payment-codes` |
| Transactions page | `(merchant)/transactions/page.tsx` | Server-side pagination + filters — `limit`, `offset`, `status`, `method`, `q` params |
| Charge page | `(merchant)/charge/page.tsx` | `POST /charges` → `POST /payments/initialise` → `popup.newTransaction(access_code)` → poll `GET /payments/:id` |
| Charge recent list | `(merchant)/charge/page.tsx` | `GET /merchants/me/payment-codes?single_use=true&limit=5` |
| My QR code | `(merchant)/my-code/page.tsx` | `GET /merchants/me` + `GET /merchants/me/payment-codes` (is_primary), `PATCH` for saves |
| Customer pay page | `app/pay/[reference]/page.tsx` | Public — `GET /pay/:reference` → `POST /pay/:reference/initialise` → Paystack popup |
| ThemeToggle hydration | `components/shared/ThemeToggle.tsx` | `mounted` guard — no SSR mismatch |

### 🔴 Still on mockApi — needs wiring

| Feature | File | Notes |
|---|---|---|
| Payment codes list | `(merchant)/payment-codes/page.tsx` | `mockApi.listPaymentCodes` |
| Create payment code | `(merchant)/payment-codes/page.tsx` | `mockApi.createPaymentCode` |
| Merchant settings | `(merchant)/settings/page.tsx` | `mockApi.getMerchant` / `mockApi.updateMerchant` |
| Products | `(merchant)/products/page.tsx` | `mockApi.listProducts` / `mockApi.updateProductPrice` |
| Withdrawals balance | `(merchant)/withdrawals/page.tsx` | `mockApi.getBalance` |
| Withdrawals list | `(merchant)/withdrawals/page.tsx` | `mockApi.listWithdrawals` |
| Request withdrawal | `(merchant)/withdrawals/page.tsx` | `mockApi.requestWithdrawal` |
| Admin — all pages | `(admin)/admin/*/page.tsx` | All on mockApi |

### 🟡 Empty stubs (not yet built)

| Page | Path | Depends on |
|---|---|---|
| Reports | `(merchant)/reports/page.tsx` | `GET /merchants/me/transactions` (already live) |
| Admin providers | `(admin)/admin/providers/page.tsx` | Admin backend |
| Admin settlements | `(admin)/admin/settlements/page.tsx` | Admin backend |

---

## API Endpoints — Wired Status

### Auth ✅ all wired
| Method | Path | Status |
|---|---|---|
| POST | `/auth/register` | ✅ |
| POST | `/auth/login` | ✅ |
| POST | `/auth/refresh` | ✅ |
| POST | `/auth/logout` | ✅ |
| GET | `/auth/me` | ✅ |
| POST | `/auth/otp/request` | ✅ |
| POST | `/auth/otp/verify` | ✅ |

### Merchant
| Method | Path | Status |
|---|---|---|
| GET | `/merchants/me` | ✅ my-code page |
| PATCH | `/merchants/me` | ✅ my-code page |
| GET | `/merchants/:id` | — (public, not needed in merchant UI) |

### Payment Codes
| Method | Path | Status |
|---|---|---|
| GET | `/merchants/me/payment-codes` | ✅ dashboard, my-code, charge recent |
| POST | `/merchants/me/payment-codes` | 🔴 payment-codes page |
| PATCH | `/merchants/me/payment-codes/:id` | ✅ my-code page |
| DELETE | `/merchants/me/payment-codes/:id` | 🔴 payment-codes page |
| GET | `/pay/:reference` | ✅ customer pay page |

### Charges
| Method | Path | Status |
|---|---|---|
| POST | `/charges` | ✅ charge page |
| GET | `/charges/:reference` | — (not needed, poll via /payments/:id) |
| POST | `/pay/:reference/initialise` | ✅ customer pay page (public, no auth) |

### Payments
| Method | Path | Status |
|---|---|---|
| POST | `/payments/initialise` | ✅ charge page |
| GET | `/payments/:id` | ✅ charge page poll |

### Transactions
| Method | Path | Status |
|---|---|---|
| GET | `/merchants/me/transactions` | ✅ dashboard, transactions page |
| GET | `/merchants/me/transactions/:id` | — (not needed yet) |

### Products
| Method | Path | Status |
|---|---|---|
| GET | `/merchants/me/products` | 🔴 products page |
| POST | `/merchants/me/products` | 🔴 products page |
| PATCH | `/merchants/me/products/:id` | 🔴 products page |
| DELETE | `/merchants/me/products/:id` | 🔴 products page |

### Withdrawals (backend stubs exist, not fully implemented)
| Method | Path | Status |
|---|---|---|
| GET | `/merchants/me/withdrawals` | 🔴 needs backend + frontend |
| POST | `/merchants/me/withdrawals` | 🔴 needs bank accounts first |
| GET | `/merchants/me/balance` | ❌ not built yet |

### Bank Accounts (not built)
| Method | Path | Status |
|---|---|---|
| GET | `/merchants/me/bank-accounts` | ❌ not built |
| POST | `/merchants/me/bank-accounts` | ❌ not built |
| PATCH | `/merchants/me/bank-accounts/:id/set-default` | ❌ not built |
| DELETE | `/merchants/me/bank-accounts/:id` | ❌ not built |

---

## Build Order — What's Next

### 1. ✅ Charge page (done)
### 2. ✅ Transactions page (done)
### 3. ✅ Dashboard (done)
### 4. ✅ My QR code page (done)
### 5. ✅ Customer pay page `/pay/[reference]` (done)

### 6. 🔴 Payment codes page — next
- Replace `mockApi.listPaymentCodes` / `mockApi.createPaymentCode`
- Wire `GET/POST/PATCH/DELETE /merchants/me/payment-codes`
- Fix hardcoded QR URL → use `PAY_BASE_URL` constant
- Show QR preview per code

### 7. 🔴 Merchant settings page
- Replace `mockApi.getMerchant` / `mockApi.updateMerchant`
- Wire `GET/PATCH /merchants/me`
- Fields: `business_name`, `display_name`, `trading_category`, `city`, `province`, `settlement_cycle`

### 8. 🔴 Products page
- Wire `GET/POST/PATCH/DELETE /merchants/me/products`
- Straightforward CRUD — no Paystack involvement

### 9. 🔴 Bank accounts + Withdrawals
- Backend needs `bank_accounts` route first (migration 009 + route)
- Flow: add bank account → Paystack `POST /bank/resolve` validates → `POST /transferrecipient` → store `recipient_code`
- Then withdrawal request → `POST /transfer` (prod only — blocked on test accounts)
- Frontend: settings sub-section for bank accounts + withdrawals page

### 10. 🔴 Admin pages
- Wire after all merchant-facing pages done
- Stats, merchant list, transaction list, settlement management

---

## Known Issues / TODOs

| Item | Status |
|---|---|
| `POST /transfer` blocked on test accounts | Expected — only works on prod Paystack account |
| Apple Pay domain registration (`POST /apple-pay/domain`) | Before go-live |
| Google Pay | Auto-enabled once Paystack account verified |
| Capitec Pay channel name | Confirm with Paystack support before adding |
| `middleware` deprecation warning in Next.js 16 | Low priority — rename to `proxy` |
| `GET /merchants/me/transactions` — `q` search only matches `reference` | Needs Supabase RPC for multi-column OR search |

---

## Environment Variables

```env
# scan2pay-web/.env
NEXT_PUBLIC_API_URL=https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod
NEXT_PUBLIC_PAY_BASE_URL=https://scan2pay.site/pay
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_test_23c73dd403061843824f61e3cb4cd96bd5220110
```
