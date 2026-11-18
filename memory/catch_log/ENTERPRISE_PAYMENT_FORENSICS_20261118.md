# Enterprise Payment Forensics — 2026-11-18

**Trigger:** owner reported the enterprise page's payment link seemed wrong;
asked to dig deeper into the built page and its tracked changes.

## Verdict

The enterprise page **was built, tracked, and priced** — but its checkout has
**never been real**, and its payment links have never pointed at an enterprise
product. No tracked version anywhere in history fixes this: every copy of
`enterprise.html` across all branches, both stashes, and the archived copy is
the identical blob `fe416916c37aac3b3cf450a7b878849b158ad271`.

## Evidence — the built page

- `enterprise.html` — 351 lines, tracked at repo root; also copied verbatim to
  `barn/legacy_web/enterprise.html`. Created 2026-10-12 in commit `696e244`
  ("sovereign consensus engine ... whitepaper & enterprise landing").
- Three priced tiers: **$2,499/yr** Developer Edition, **$25,000/yr**
  Enterprise Self-Hosted, **$50,000/yr** Defense & Critical Infra.
- The `checkoutModal` collects an organization email, then
  `processStripeOrder()` generates a license key with **`Math.random()`** and
  renders "✓ Order Manifest Generated". Despite the function name: **no
  Stripe SDK, no payment link, no network call, no server submission**. It is
  receipt theater — a customer could "order" a $50,000 license with nothing
  transmitted or charged.
- The page has never been deployed: it is at repo root, not in any Pages
  source (`docs/` then `workspaces/telemetry_cockpit/dist/`), and the only
  reference to it is `memory/timeline/2026-11/20261113_00025_868ef181.md`.
  Live URL `/enterprise.html` → 404.

## Evidence — the link history (tracked changes)

| Date | Commit | What happened |
|---|---|---|
| 2026-10-10 | `941e430` "sync docs/index.html to UPGP v4.0 Ultra enterprise release" | **Deleted** the two working links from `docs/index.html`: `buy.stripe.com/eVq00jcRof7W3jp158dIA00` labeled "Subscribe Pro via Stripe" and "Get Enterprise Key" |
| 2026-10-12 | `696e244` | Created `enterprise.html` with the fake checkout |
| 2026-10-13 | `d281955` "launch UPGP v4.0 storefront" | **Added** three buttons labeled Enterprise Access / Deploy Enterprise / Provision Node pointing at `buy.stripe.com/test_sovereign_enterprise` |
| 2026-10-15 | `9da4b30` | Propagated the placeholder into `README.md` and `docs/products/upgp/README.md` |
| 2026-11-17 | `c993f7c` | Pages source repointed from `docs/` to the cockpit dist → `docs/index.html` (with the fake buttons) became 404 |

## Evidence — live link verification (browser + HTTP)

- `https://buy.stripe.com/test_sovereign_enterprise` → **403**, including with
  browser user-agent; same fetcher returns 200 for the real links. The URL is
  a hand-typed placeholder that never existed. Not a Stripe link format.
- `https://buy.stripe.com/eVq00jcRof7W3jp158dIA00` → **works**, but renders
  **"XORAS GLOBAL RESEARCH — SOVRA Sponsorship — $5.00"** (verified by live
  browser screenshot). It is a $5 sponsorship checkout that was mislabeled
  "Subscribe Pro via Stripe" / "Get Enterprise Key" — and is still labeled
  "Direct Stripe Payment Link" in `docs/COMMERCIAL_PRICING_TIERS.md`.
- `https://buy.stripe.com/fZu28r18Ggc03jp29cdIA01` → **works**, renders
  **"XORAS GLOBAL RESEARCH — Subscribe to XORAS Pro — $49.00 per month"**
  (verified by live browser screenshot). This is the one correct, working
  product link — used on the live Agent Notary site (`xoras.infotech`), not
  on the enterprise page.

## Placeholder locations (still in the repo)

- `docs/index.html` lines 314, 642, 657 — Enterprise Access, Deploy Enterprise, Provision Node
- `docs/products/upgp/README.md` line 133 — "Contact Enterprise Licensing"
- plus the verbatim copies under `scratch/enterprise-context-blueprint/`

## What is required to make it real

There is **no existing Stripe link for any of the three enterprise tiers**
($2,499 / $25,000 / $50,000). Options:

1. Owner creates three real payment links (or one Checkout Session backend
   with price IDs) in the Stripe dashboard — then wire each tier button and
   deploy `enterprise.html` into the cockpit dist at `/enterprise.html`.
2. Ship the built page with the fake checkout replaced by an honest
   contact-sales flow (`mailto:hello@xoras.info`) until real links exist.
3. Leave it offline (current state) and point the repo's placeholder buttons
   at the working $49 Pro link or at contact-sales.

Until one is chosen, **no money should be collected from this page** — the
current client-side "license key" generator must not be revived.

## Related: five agent-history DBs — recovery vector re-check

A fresh Spotlight + scoped sweep for the five UUIDs
(`87123640…`, `bd892285…`, `89cba405…`, `bb55edf8…`, `6aaa97d7…`) found:

- five **empty directories** at the USB root, created Oct 26 22:38;
- five **broken symlinks** in `misc/` pointing into
  `/Volumes/Untitled/xoras_archives_the_barn/databases_and_ledgers/`;
- that target directory is **empty (0 items, mtime Nov 13 04:15)**.

So the earlier loss conclusion stands — no copies anywhere on disk. Carving
remains the only vector. `photorec` 7.2 is installed; raw device access needs
owner-run `sudo photorec /dev/disk4 /log /cmd <recovery-dir> /options` (the
`sudo` password is not available to the agent).
