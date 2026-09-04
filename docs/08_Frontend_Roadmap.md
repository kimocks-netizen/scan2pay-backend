# scan2pay-web — Migration Roadmap

## Stack
Next.js 15 App Router · TypeScript · Tailwind v4 · shadcn/ui · TanStack Query v5 · Zustand · React Hook Form · Zod · next-themes

## Architecture Pattern
Hybrid: `features/<domain>/schemas.ts` co-location (orderflow-ui style) + separate `providers/` folder (predictiq style)

---

## ✅ Done

### Project Setup
- [x] Next.js 15 scaffolded with TypeScript, Tailwind, ESLint, App Router, `src/` dir, `@/*` alias
- [x] All runtime deps installed (TanStack Query, Zustand, next-themes, React Hook Form, Zod, Recharts, qrcode, Radix primitives, etc.)
- [x] Dev deps installed (`@types/qrcode`, `@tanstack/react-query-devtools`, `prettier`, `prettier-plugin-tailwindcss`)
- [x] shadcn/ui initialised with `--defaults`
- [x] `.prettierrc` + `.prettierignore` copied

### Copied from Scan2Pay-frontend (no changes needed)
- [x] `src/components/ui/` — all 45 shadcn/ui primitives
- [x] `src/components/shared/` — Logo, QrCode, QrPoster, ThemeToggle, AdminCharts
- [x] `src/hooks/use-mobile.tsx`
- [x] `src/lib/utils.ts`
- [x] `src/lib/format.ts`
- [x] `src/lib/api/types.ts`
- [x] `src/assets/` — hero-vendor, kit-lanyard-bib, use-petrol, use-taxi, use-tips
- [x] `mock/` — all JSON fixtures (audit-log, merchants, payment-codes, plans, pricing, products, transactions, users, withdrawals)
- [x] `docs/` — admin.md, api.md, architecture.md, database.md, payments.md, README.md

---

## 🔲 To Build

### Foundation Layer
- [x] `src/lib/constants.ts` — API base URL, app name, route constants
- [x] `src/lib/api-client.ts` — fetch wrapper with auth headers + error handling
- [x] `src/lib/query-client.ts` — TanStack QueryClient singleton config

### Zustand Stores (`src/stores/`)
- [x] `useAuthStore.ts` — token, user, login/logout actions
- [x] `useUIStore.ts` — sidebar open/close, active modal
- [x] `useThemeStore.ts` — dark/light preference

### Providers (`src/providers/`)
- [x] `QueryProvider.tsx` — TanStack QueryClient + Devtools
- [x] `ThemeProvider.tsx` — next-themes wrapper
- [x] `AuthProvider.tsx` — session hydration on mount
- [x] `Providers.tsx` — combined root wrapper

### App Shell (`src/app/layout.tsx`)
- [x] Wire `<Providers>` into root layout
- [x] Set metadata (title, description, icons)
- [x] Apply font + base HTML attributes

### Types (`src/types/`)
- [x] `auth.ts` — AuthTokens, AuthResponse, LoginPayload, RegisterPayload
- [x] `api.ts` — ApiError, ApiErrorResponse, PaginatedResponse
- [x] `domain.ts` — re-exports all domain types + MerchantStats, Payout, PaymentInitResponse

### Middleware (`src/middleware.ts`)
- [x] Protect authenticated routes
- [x] Redirect unauthenticated users to `/login`
- [x] Redirect authenticated users away from `/login`

### Layout Components (`src/components/layout/`)
- [x] `AppShell.tsx` — merchant-facing shell (Navbar + Sidebar + mobile nav)
- [ ] `AdminShell.tsx` — admin-facing shell

### Features (`src/features/`)

#### `auth/`
- [x] `schemas.ts` — login/register Zod schemas
- [x] `api.ts` — login, logout, refresh endpoints
- [x] `mutations.ts` — useLoginMutation, useLogoutMutation, useRegisterMutation

#### `dashboard/`
- [x] `api.ts` — transactions + payment codes endpoints
- [x] `queries.ts` — useDashboardTransactions, useDashboardCodes

#### `transactions/`
- [x] inline in page (queries via api-client)

#### `payment-codes/`
- [x] inline in page

#### `withdrawals/`
- [x] inline in page

#### `merchants/`
- [ ] `schemas.ts`
- [ ] `api.ts`
- [ ] `queries.ts` + `mutations.ts`
- [ ] `components/` — MerchantTable, MerchantForm

#### `plans/` (admin)
- [ ] `schemas.ts`
- [ ] `api.ts`
- [ ] `queries.ts` + `mutations.ts`
- [ ] `components/` — PlanTable, PlanForm

#### `users/` (admin)
- [ ] `api.ts`
- [ ] `queries.ts`
- [ ] `components/` — UserTable

### App Routes (`src/app/`)
- [x] `/` — home / landing page
- [x] `(auth)/login/page.tsx`
- [x] `(merchant)/dashboard/page.tsx`
- [x] `(merchant)/charge/page.tsx`
- [x] `(merchant)/my-code/page.tsx`
- [x] `(merchant)/transactions/page.tsx`
- [x] `(merchant)/payment-codes/page.tsx`
- [x] `(merchant)/withdrawals/page.tsx`
- [x] `(merchant)/settings/page.tsx`
- [ ] `(admin)/admin/dashboard/page.tsx`
- [ ] `(admin)/admin/merchants/page.tsx`
- [ ] `(admin)/admin/users/page.tsx`
- [ ] `(admin)/admin/plans/page.tsx`
- [ ] `(admin)/admin/transactions/page.tsx`
- [ ] `(admin)/admin/withdrawals/page.tsx`
- [ ] `(admin)/admin/pricing/page.tsx`
- [ ] `(admin)/admin/audit/page.tsx`

---

## Build Order

1. `types/` → `lib/constants.ts` → `lib/api-client.ts` → `lib/query-client.ts`
2. `stores/` (auth, ui, theme)
3. `providers/` → wire into `app/layout.tsx`
4. `middleware.ts`
5. `components/layout/` (shells + nav)
6. `features/auth/` → `(auth)/login/page.tsx`
7. Remaining features + routes (dashboard → transactions → payment-codes → withdrawals → merchants → admin)
