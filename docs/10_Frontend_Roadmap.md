# scan2pay-web — Frontend Roadmap

> Living document. Updated as each feature is wired to the real backend.
> Backend API base: `https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod`
> Set in `scan2pay-web/.env` → `NEXT_PUBLIC_API_URL`

---

## Stack
Next.js 15 App Router · TypeScript · Tailwind v4 · shadcn/ui · TanStack Query v5 · Zustand · React Hook Form · Zod · next-themes · `@paystack/inline-js`

---

## Current State Summary

### ✅ Real backend wired
| Feature | File | Notes |
|---|---|---|
| Login | `(auth)/login/page.tsx` | Calls `POST /auth/login` via `features/auth/api.ts` |
| Register | `(auth)/login/page.tsx` | Calls `POST /auth/register` |
| Logout | `features/auth/mutations.ts` | Calls `POST /auth/logout` with refresh token |
| OTP verify | `(auth)/verify-otp/page.tsx` | Calls `POST /auth/otp/verify` |
| Auth store | `stores/useAuthStore.ts` | Zustand persist — stores `accessToken`, `refreshToken`, `user` |
| API client | `lib/api-client.ts` | Attaches `Authorization: Bearer` from localStorage |

### 🔴 Still on mockApi — needs wiring
| Feature | File | Mock function used |
|---|---|---|
| Dashboard transactions | `features/dashboard/api.ts` | ✅ wired — `GET /merchants/me/transactions?limit=50` |
| Dashboard payment codes | `features/dashboard/api.ts` | ✅ wired — `GET /merchants/me/payment-codes` |
| Transactions list | `(merchant)/transactions/page.tsx` | ✅ wired — `GET /merchants/me/transactions?limit=200` |
| Payment codes list | `(merchant)/payment-codes/page.tsx` | `mockApi.listPaymentCodes` |
| Create payment code | `(merchant)/payment-codes/page.tsx` | `mockApi.createPaymentCode` |
| Charge (create) | `(merchant)/charge/page.tsx` | ✅ wired — `POST /charges` + `POST /payments/initialise` |
| Charge (poll) | `(merchant)/charge/page.tsx` | ✅ wired — `GET /payments/:id` |
| Charge (recent list) | `(merchant)/charge/page.tsx` | ✅ wired — `GET /merchants/me/transactions?single_use=true` |
| Charge (cancel) | `(merchant)/charge/page.tsx` | 🔴 removed — no cancel on real charges |
| **Paystack popup** | `(merchant)/charge/page.tsx` | ✅ wired — `@paystack/inline-js` dynamic import, `popup.resumeTransaction(access_code)` |
| Withdrawals balance | `(merchant)/withdrawals/page.tsx` | `mockApi.getBalance` |
| Withdrawals list | `(merchant)/withdrawals/page.tsx` | `mockApi.listWithdrawals` |
| Request withdrawal | `(merchant)/withdrawals/page.tsx` | `mockApi.requestWithdrawal` |
| Cancel withdrawal | `(merchant)/withdrawals/page.tsx` | `mockApi.cancelWithdrawal` |
| Merchant profile | `(merchant)/settings/page.tsx` | `mockApi.getMerchant` / `mockApi.updateMerchant` |
| Products | `(merchant)/products/page.tsx` | `mockApi.listProducts` / `mockApi.updateProductPrice` |
| My code (primary QR) | `(merchant)/my-code/page.tsx` | `mockApi.getPrimaryCode` |
| Admin — all pages | `(admin)/admin/*/page.tsx` | All on mockApi |

### 🟡 Pages that exist but are empty stubs
| Page | Path |
|---|---|
| Reports | `(merchant)/reports/page.tsx` |
| Admin providers | `(admin)/admin/providers/page.tsx` |
| Admin settlements | `(admin)/admin/settlements/page.tsx` |

---

## Hardcoded values to fix before go-live
| Location | Hardcoded value | Fix |
|---|---|---|
| `charge/page.tsx` | `payUrl = https://scan2pay.co.za/pay/${charge.reference}` | Use env var or constants |
| `payment-codes/page.tsx` | QR value `https://scan2pay.co.za/pay/${c.reference}` | Use `NEXT_PUBLIC_PAY_BASE_URL` constant |
| `my-code/page.tsx` | Same QR URL pattern | Same fix |
| `charge/page.tsx` | Entire charge flow uses `mockApi` — no Paystack popup | Wire to real backend + Paystack Inline JS |

---

## API Endpoints Available (backend live ✅)

### Auth (all wired ✅)
| Method | Path | Frontend status |
|---|---|---|
| POST | `/auth/register` | ✅ wired |
| POST | `/auth/login` | ✅ wired |
| POST | `/auth/refresh` | ✅ wired |
| POST | `/auth/logout` | ✅ wired |
| GET | `/auth/me` | ✅ wired |
| POST | `/auth/otp/request` | ✅ wired |
| POST | `/auth/otp/verify` | ✅ wired |

### Merchant (backend live, frontend mocked)
| Method | Path | Frontend status |
|---|---|---|
| GET | `/merchants/me` | 🔴 mockApi |
| PATCH | `/merchants/me` | 🔴 mockApi |

### Products (backend live, frontend mocked)
| Method | Path | Frontend status |
|---|---|---|
| GET | `/merchants/me/products` | 🔴 mockApi |
| POST | `/merchants/me/products` | 🔴 mockApi |
| PATCH | `/merchants/me/products/:id` | 🔴 mockApi |
| DELETE | `/merchants/me/products/:id` | 🔴 mockApi |

### Payment Codes (backend live, frontend mocked)
| Method | Path | Frontend status |
|---|---|---|
| GET | `/merchants/me/payment-codes` | 🔴 mockApi |
| POST | `/merchants/me/payment-codes` | 🔴 mockApi |
| PATCH | `/merchants/me/payment-codes/:id` | 🔴 mockApi |
| DELETE | `/merchants/me/payment-codes/:id` | 🔴 mockApi |
| GET | `/pay/:reference` | 🔴 not wired (public resolve endpoint) |

### Charges (backend live, frontend mocked)
| Method | Path | Frontend status |
|---|---|---|
| POST | `/charges` | 🔴 mockApi |
| GET | `/charges/:reference` | 🔴 mockApi (used for polling) |

### Payments — Paystack (backend live, frontend NOT implemented)
| Method | Path | Frontend status |
|---|---|---|
| POST | `/payments/initialise` | 🔴 **not implemented** |
| GET | `/payments/:id` | 🔴 **not implemented** |

### Transactions (backend live, frontend mocked)
| Method | Path | Frontend status |
|---|---|---|
| GET | `/merchants/me/transactions` | 🔴 mockApi |
| GET | `/merchants/me/transactions/:id` | 🔴 mockApi |

### Withdrawals (backend live, frontend mocked)
| Method | Path | Frontend status |
|---|---|---|
| GET | `/merchants/me/withdrawals` | 🔴 mockApi (endpoint exists in backend stub) |
| POST | `/merchants/me/withdrawals` | 🔴 mockApi |

---

## Build Order — What to Wire Next

### 1. ✅ Charge page — Paystack Inline JS (done)
- `POST /charges` → `POST /payments/initialise` → `popup.resumeTransaction(access_code)` → poll `GET /payments/:id`
- `@paystack/inline-js` dynamically imported (avoids SSR `window` error)
- `?paid=true` callback from Paystack handled via `useSearchParams`
- Recent charges list wired to `GET /merchants/me/transactions?single_use=true`

**Payment method TODOs (before go-live):**
- Apple Pay: register `scan2pay.site` via `POST /apple-pay/domain` — surfaces automatically in Paystack Inline
- Google Pay: enabled automatically once Paystack account is verified
- Capitec Pay: confirm exact channel name with Paystack support before adding

### 2. ✅ Transactions page (done)
Wired to `GET /merchants/me/transactions?limit=200` with snake_case → camelCase mapper.

### 3. ✅ Dashboard (done)
Wired to `GET /merchants/me/transactions?limit=50` and `GET /merchants/me/payment-codes`.

### 4. 🔴 Payment codes page — next
Replace `mockApi.listPaymentCodes` / `mockApi.createPaymentCode` with real endpoints.
Fix hardcoded QR URL → use `PAY_BASE_URL` constant.

### 5. 🔴 Merchant settings page
Replace `mockApi.getMerchant` / `mockApi.updateMerchant` with `GET/PATCH /merchants/me`.

### 6. 🔴 Products page
Replace mock with `GET/POST/PATCH/DELETE /merchants/me/products`.

### 7. 🔴 Withdrawals page
Backend withdrawal routes are stubs — implement backend first, then wire frontend.
Balance calculation needs a `GET /merchants/me/balance` endpoint (not yet built).

### 8. 🔴 Admin pages
All admin pages are on mockApi. Wire after merchant-facing pages are done.

---

## Features Not Yet Built (backend + frontend)

| Feature | Backend | Frontend |
|---|---|---|
| Bank account management | ❌ not built | ❌ not built |
| Withdrawal request flow | ❌ stub only | 🔴 mockApi |
| Merchant balance endpoint | ❌ not built | 🔴 mockApi |
| Public pay page (`/pay/:ref`) | ✅ `GET /pay/:reference` exists | ❌ not built |
| Admin dashboard | ❌ stub | 🔴 mockApi |
| Plans / billing page | ❌ stub | 🔴 mockApi |
| Push / SMS notifications | ❌ not built | ❌ not built |

---

## Environment Variables

```env
# scan2pay-web/.env
NEXT_PUBLIC_API_URL=https://8fhbnwufgi.execute-api.af-south-1.amazonaws.com/Prod
NEXT_PUBLIC_PAY_BASE_URL=https://scan2pay.site/pay   # TODO: add this constant
NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY=pk_test_23c73dd403061843824f61e3cb4cd96bd5220110
```

> `NEXT_PUBLIC_PAYSTACK_PUBLIC_KEY` is needed for `@paystack/inline-js` — not yet in `.env`.
