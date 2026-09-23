# Scan2Pay → Vula Pay — Rebrand Migration Plan

> Planning doc, not a build log. Nothing here has been executed.
> Written: 22 September 2026

## Where things actually stand

The product itself is already "Vula Pay" everywhere a user can see it — every
UI string, every SMS, both marketing sites. What's left is internal: repo
names, infra identifiers, and a couple of mobile-app identifiers that are
expensive to change *later* but free to change *now*, before anything ships.

This plan is ordered by risk, not by repo, because the risk is almost
entirely about **what's already live** vs **what's still safe to rename**.

---

## Tier 1 — Free (do anytime, zero risk)

Pure find-and-replace, nothing external depends on the name.

- **GitHub repo renames** — `scan2pay-backend`, `scan2pay-web`, `scan2pay-app`
  → GitHub keeps a redirect on the old URL forever, so existing clones/remotes
  keep working with no action from anyone.
- **Doc references** — ~25 files under `scan2pay-backend/docs/*.md` mention
  "Scan2Pay" in prose/comments (this file's own siblings included). Cosmetic.
- **`package.json` `name` fields** — `scan2pay-web`, `scan2pay-app`. Only used
  by local tooling (`npm run`, lockfile), nothing external reads it.
- **Downloaded-file naming** — `scan2pay-${reference}.png` in
  `(merchant)/my-code/page.tsx` and `(merchant)/catalog/page.tsx` (QR poster
  downloads). Purely cosmetic filename prefix.

---

## Tier 2 — Contained (careful, but self-contained)

Still no external party depends on these, but they touch config/deploy
tooling so a typo breaks a deploy, not just a display string.

- **Deploy script variables** — `scripts/deploy.sh`: `STACK="scan2pay-backend"`,
  `s3_prefix = "scan2pay-backend"` (`samconfig.toml`), and every
  `/scan2pay/$ENV/...` SSM parameter path (`SUPABASE_URL`, `JWT_SECRET`,
  `GOOGLE_CLIENT_ID`, `PAYSTACK_SECRET_KEY`, etc. — see `template.yaml`
  `!Sub` lines and `IAM` policy `ParameterName: 'scan2pay/${Environment}/*'`).
  Renaming the SSM path means re-running `deploy.sh`'s `ssm_put` step under
  the new path *before* cutting the stack over (Tier 3), or the new stack
  boots with no secrets.
- **Mobile deep-link scheme** — `"scheme": "scan2payapp"` in `app.json`.
  Free to change now; would break any existing deep links into a *published*
  build, but the app isn't published yet (see Tier 3 note on bundle ID).

---

## Tier 3 — Real infra migration (deploy events, plan a window)

These can't be renamed in place — AWS doesn't support renaming a
CloudFormation stack, an S3 bucket, or a DynamoDB table. Each of these is a
**create-new, cut over, decommission-old** sequence, not a find-and-replace.

- **CloudFormation stack** — `scan2pay-backend` (`samconfig.toml`). A rename
  means deploying a parallel stack under the new name, which mints:
  - a new API Gateway endpoint (new URL)
  - new Lambda function ARNs (all 8: API, WebSocket connect/disconnect,
    ExpireCharges, ReconcilePaystack, BuildSettlements, PurgeArchivedAccounts)
  - a new DynamoDB table (`scan2pay-ws-connections-${env}` →
    `TableName: !Sub` in `template.yaml`)
  - a new S3 bucket (`scan2pay-assets-${env}-${accountId}` — buckets can't be
    renamed; needs a bucket + `aws s3 sync` copy of existing assets)

  Then: update `NEXT_PUBLIC_API_URL` in `scan2pay-web`, `extra.apiUrl` /
  `extra.wsUrl` in `scan2pay-app`'s build config, redeploy both frontends,
  smoke-test end-to-end, *then* decommission the old stack. This is the one
  item on this whole list that's a genuine deploy-and-verify event.

- **`scan2pay.site` domain** — currently only referenced for CORS
  (`template.yaml` S3 CORS origin) and as the target of two **not-yet-built**
  `SPRINT.md` backlog items: Apple Pay domain verification and the API
  Gateway custom domain. Do the rebrand *before* building those two — build
  them once against a `vula-pay.co.za` subdomain instead of building against
  `scan2pay.site` and re-verifying later.

- **Mobile bundle identifiers** — `com.scan2pay.app` (both iOS
  `bundleIdentifier` and Android `package` in `app.json`). **This is free
  right now and won't be later.** Once an app is submitted to the App
  Store/Play Store under a bundle ID, that ID is permanent — changing it
  means a brand-new store listing (zero installs, zero reviews, starting
  over), not a rename. Confirmed via the "Coming soon" store badges on
  `vula-pay-home` that neither store submission has happened yet, so this is
  the highest-value item to fix *before* it becomes expensive.

---

## Recommended order

1. **Now, no coordination needed:** Tier 1 (repo renames, docs, package.json,
   filenames) + the mobile bundle ID / package name in `app.json`, since it's
   free today and never will be again.
2. **Next deploy window:** Tier 2 (SSM path + deploy script vars) — do this
   as prep, immediately before Tier 3, so the new stack has secrets waiting
   under the new path the moment it boots.
3. **Planned cutover:** Tier 3's CloudFormation/S3/DynamoDB migration —
   ideally bundled with the custom-domain work already on the backlog
   (`SPRINT.md` → Infrastructure), so it's one deploy event instead of two.

## Already done

- **Supabase project** — renamed. Note this only matters if the project
  *ref* (the random string in `SUPABASE_URL`, e.g.
  `jefuasxrwqpbhydiulni.supabase.co`) changed too — the display name alone
  doesn't touch connection strings or RLS policies. If the ref is unchanged,
  no `.env`/SSM update is needed; if it did change, `SUPABASE_URL` and
  `SUPABASE_SERVICE_ROLE_KEY` need updating in SSM (`/scan2pay/{env}/...`,
  see Tier 2) and redeploying.
- **GitHub repo renames** — self-serve via each repo's Settings page, no
  coordination needed (see Tier 1). GitHub keeps the old URL as a permanent
  redirect.

## Explicitly out of scope here

- Anything already "Vula Pay" in user-facing copy — there's nothing left to
  do there, it's already consistent across both marketing sites and both
  apps.
