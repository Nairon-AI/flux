# Recommendation Engine Monetization Plan

> **Goal**: Turn the Flux recommendation engine into a paid add-on with a data moat, using Polar.sh for billing and license key validation. Free users get friction detection; Pro users get matched recommendations powered by community success data.
>
> **Status**: Phase 1 complete. Phase 2 nearly complete — Polar setup done, Flux client gating done, Universe API deployed + seeded. Remaining: wire Polar webhooks for auto-revoke on churn.

---

## Decisions Made

| Question | Decision |
|----------|----------|
| Access mechanism | **API-only** — no GitHub repo access benefit. Eliminates clone-and-cancel risk. |
| Pro pricing | **$10/mo** individual, $96/yr annual (20% discount) |
| Teams | **Coming soon** — observability layer with org-wide dashboards. Focus on Pro for individuals first. |
| Public recommendations repo | **Already privated** — `Nairon-AI/flux-recommendations` is now private. Free users get a small hardcoded set baked into the plugin. |
| Free tier recommendations | **Hardcoded in Flux** — top 5-10 universal tools (jq, gh, ripgrep, etc.) shipped with the plugin. No network fetch needed. |
| Upgrade prompt frequency | 1x per session max. Only when friction is detected. |
| Offline/network failure | Cache last successful API response (24h). If cache expired + network down, degrade to free (hardcoded set). |

---

## Pricing Tiers

| | Free | Pro ($10/mo) | Teams (coming soon) |
|---|---|---|---|
| **Friction detection** | Inline signals after each task | Inline signals after each task | Org-wide friction heatmap |
| **Signal cooldown** | 7-day snooze + resurface (no recs) | 7-day snooze + resurface with fresh recs | Auto-surface to team leads |
| **Recommendations** | Hardcoded set (top 5-10 universal tools) | Stack-aware, community-ranked, weekly updated | Team-level + standardization |
| **Feedback loop** | — | Contributes to + benefits from community data | Private org data silo |
| **Flux Score** | Local only | Syncs to Universe profile | Aggregated across org |
| **Analytics** | — | Personal friction trends | Department dashboards |
| **Support** | Community (Discord) | Priority | Dedicated + onboarding |

### Free tier value proposition
"Flux tells you **what's wrong** — friction signals surface the exact pain points in your workflow. You get basic recommendations for universal tools, but not the full stack-aware, community-ranked engine."

### Pro tier value proposition
"Flux tells you what's wrong AND what to install. Recommendations are ranked by what actually works for your specific stack, powered by anonymous community data from thousands of developers."

---

## Existing Infrastructure

### Universe backend (`Nairon-AI/nairon-universe`)

**Already built:**
- Convex backend (serverless, real-time)
- Full Flux device auth flow (`convex/flux.ts`) — device codes, access tokens, connection management
- `@polar-sh/sdk` v0.32.16 already installed
- `@convex-dev/polar` v0.4.5 installed (NOT yet wired into `convex.config.ts`)
- Better Auth for user management
- Flux Score stats syncing (sessions, tokens, tools used)
- Convex HTTP router with existing endpoints (`/health`, `/waitlist`)
- Deployed on Vercel
- Engineer profiles with user → profile mapping

**Needs to be added:**
- Wire `@convex-dev/polar` into `convex.config.ts`
- Recommendations table in Convex schema
- Feedback/analytics tables in Convex schema
- HTTP endpoints for `/api/recommendations` and `/api/recommendations/feedback`
- License key validation logic (via Polar SDK)
- Recommendation matching engine (server-side)

### Nairon website (`Nairon-AI/nairon-website`)

Separate repo — landing page + waitlist. Has its own Convex backend. **Not involved in recommendation engine.** May add a "Flux Pro" marketing page later.

### Flux recommendations (`Nairon-AI/flux-recommendations`)

**Now private.** Contains the curated tool index and matching logic. Will become the source of truth for the Pro recommendations database. The matching engine will move server-side to Universe.

---

## Payment & Access Architecture

### Why Polar.sh

[Polar](https://polar.sh) is purpose-built for developer monetization:

- **4% + 40¢ per transaction** — lower than typical MoR (5-8%)
- **License key generation** — auto-generated on purchase, no auth server needed
- **Client-side validation** — `POST /v1/customer-portal/license-keys/validate` requires no API key, safe for CLI tools
- **Webhook support** — Standard Webhooks spec with SDK helpers for signature validation
- **Subscription lifecycle** — auto-grants and auto-revokes benefits on subscribe/churn
- **Already in Universe** — `@polar-sh/sdk` and `@convex-dev/polar` are installed in nairon-universe

### Access mechanism: API-only via license key

No GitHub repo access. No cloneable artifacts. All recommendations served via Universe API.

```
User purchases Pro on Polar → receives license key (FLUX-XXXX-XXXX-XXXX)
  → runs /flux:login → pastes license key
  → key validated via Polar API (client-side, no auth needed)
  → key stored in .flux/config.json (gitignored)
  → every recommendation request includes key in header
  → Universe API validates key (cached server-side, not per-request)
  → on churn, key becomes invalid → Flux degrades to free
```

Polar client-side validation:
```bash
# No API key needed — safe for CLI tools
curl -X POST https://api.polar.sh/v1/customer-portal/license-keys/validate \
  -H "Content-Type: application/json" \
  -d '{"key": "FLUX-XXXX-XXXX-XXXX", "organization_id": "nairon-ai"}'

# Response: { "valid": true, "expires_at": "...", "customer": {...} }
```

Rate limit: 3 req/sec for unauthenticated validation. Flux caches validation locally for 24 hours.

---

## Technical Architecture

### Current state (broken — repo is now private)

```
Flux (local)
  → fetches https://github.com/Nairon-AI/flux-recommendations (NOW PRIVATE — 404)
  → matches friction signals locally via match-recommendations.py
  → presents recommendations
```

**This is currently broken for all users.** Need to ship the free hardcoded set ASAP or re-public the repo temporarily.

### Target state

```
┌─────────────────────────────────────────────────────┐
│  Flux (open source, local)                           │
│                                                       │
│  Friction detection → signals            [FREE]       │
│  Signal cooldown + resurface             [FREE]       │
│  Hardcoded basic recommendations         [FREE]       │
│       │                                               │
│       ▼                                               │
│  Has valid license key?                               │
│    NO  → show hardcoded recs (if match)               │
│         + "Upgrade to Pro for stack-aware recs"        │
│         (1x per session max)                          │
│                                                       │
│    YES → POST universe-api/api/recommendations        │
│          { signals, stack, installed, license_key }   │
│       │                                               │
│       ▼                                               │
│  Show matched recommendations            [PRO]        │
│  Report feedback (install/dismiss/snooze) [PRO]       │
└───────┼───────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────┐
│  Universe API — Convex HTTP routes                    │
│  (nairon-universe, deployed on Vercel)                │
│                                                       │
│  POST /api/recommendations                            │
│  1. Validate license key (Polar SDK, cached 24h)      │
│  2. Load recommendations index from Convex DB         │
│  3. Match signals → recommendations                   │
│     - Filter by stack (framework + deploy platform)   │
│     - Filter out already-installed tools              │
│     - Rank by community success rate                  │
│  4. Return top 3 recommendations                      │
│                                                       │
│  POST /api/recommendations/feedback                   │
│  1. Validate license key                              │
│  2. Store: { tool, action, stack, friction_delta }    │
│  3. Async: update aggregated success rates            │
│                                                       │
│  Data stored in Convex tables:                        │
│  - recommendations (curated index)                    │
│  - recommendationFeedback (per-user actions)          │
│  - recommendationStats (aggregated per tool+stack)    │
└─────────────────────────────────────────────────────┘
```

### Convex schema additions (nairon-universe)

```typescript
// New tables for recommendation engine
recommendations: defineTable({
  name: v.string(),           // e.g., "tailwind-intellisense"
  description: v.string(),
  installCommand: v.string(), // e.g., "npm i -g tailwind-intellisense"
  signals: v.array(v.string()),      // friction signals this addresses
  stacks: v.array(v.string()),       // compatible stacks, empty = universal
  category: v.string(),       // "mcp", "cli", "plugin", "extension"
  url: v.optional(v.string()),
  addedAt: v.number(),
  updatedAt: v.number(),
  deprecated: v.optional(v.boolean()),
})
  .index("by_signal", ["signals"])
  .searchIndex("search_name", { searchField: "name" }),

recommendationFeedback: defineTable({
  userId: v.id("users"),
  recommendationId: v.id("recommendations"),
  action: v.string(),         // "installed" | "dismissed" | "snoozed"
  stackFingerprint: v.string(), // e.g., "next,vercel,typescript"
  frictionSignal: v.string(),
  frictionBefore: v.optional(v.number()),
  frictionAfter: v.optional(v.number()),  // measured 7 days later
  createdAt: v.number(),
})
  .index("by_userId", ["userId"])
  .index("by_recommendation", ["recommendationId"])
  .index("by_stack_signal", ["stackFingerprint", "frictionSignal"]),

recommendationStats: defineTable({
  recommendationId: v.id("recommendations"),
  stackFingerprint: v.string(),
  frictionSignal: v.string(),
  installCount: v.number(),
  dismissCount: v.number(),
  avgFrictionReduction: v.optional(v.number()), // 0-100 percentage
  sampleSize: v.number(),
  updatedAt: v.number(),
})
  .index("by_recommendation_stack", ["recommendationId", "stackFingerprint"])
  .index("by_signal_stack", ["frictionSignal", "stackFingerprint"]),
```

### Universe API endpoints (Convex HTTP routes)

| Endpoint | Method | Auth | Purpose |
|----------|--------|------|---------|
| `/api/recommendations` | POST | License key | Get matched recommendations for friction signals |
| `/api/recommendations/feedback` | POST | License key | Report install/dismiss/snooze + friction delta |

### What gets reported (anonymized)

| Data | Example | Purpose |
|------|---------|---------|
| Friction signal | `css_issues` | What problem they had |
| Recommendation shown | `tailwind-intellisense` | What was suggested |
| Action taken | `installed` / `dismissed` / `snoozed` | Did they want it |
| Stack fingerprint | `next, vercel, typescript` | For stack-specific ranking |
| Friction delta (7 days later) | `7 → 1` | Did it actually help |

**NOT reported**: code, file contents, repo names, file paths, error messages, or any PII beyond Universe user ID (for deduplication).

### Data flow for feedback loop

```
1. User hits css_issues friction → engine recommends tailwind-intellisense
2. User installs it → Flux reports: { tool: "tailwind-intellisense", action: "installed", stack: "next+vercel" }
3. 7 days later, Flux measures friction delta → reports: { friction_before: 7, friction_after: 1 }
4. Engine updates: "tailwind-intellisense reduces css_issues by 85% for next+vercel users"
5. Next user with same stack + signal gets this recommendation ranked #1
```

---

## Implementation in Flux (client-side changes)

### Hardcoded free recommendations

Ship a small set baked into the plugin (no network fetch):

```json
// scripts/free-recommendations.json
[
  { "name": "jq", "signal": "search_needed", "install": "brew install jq", "desc": "JSON processor for CLI" },
  { "name": "ripgrep", "signal": "search_needed", "install": "brew install ripgrep", "desc": "Fast code search" },
  { "name": "gh", "signal": "ci_failures", "install": "brew install gh", "desc": "GitHub CLI" },
  { "name": "fd", "signal": "search_needed", "install": "brew install fd", "desc": "Fast file finder" },
  { "name": "lefthook", "signal": "lint_errors", "install": "npm i -g lefthook", "desc": "Git hooks manager" }
]
```

### License key storage

```json
// .flux/config.json (gitignored)
{
  "license": {
    "key": "FLUX-XXXX-XXXX-XXXX",
    "tier": "pro",
    "validated_at": "2026-03-15T10:30:00Z",
    "expires_at": "2026-04-15T10:30:00Z"
  }
}
```

### Validation caching

- Cache Polar validation result for 24 hours locally
- On cache miss, validate via Polar API (client-side endpoint, no auth needed)
- On validation failure (expired, revoked), clear cached result and show upgrade prompt
- Never block the workflow — if validation fails due to network, use cached result or degrade to free

### Upgrade prompt (free tier)

When friction is detected but no license key:

```
Friction detected: css_issues (3x this session)

Flux Pro can recommend tools to fix this — matched to your stack,
ranked by what actually works for other developers.

→ Get Flux Pro: https://polar.sh/nairon-ai/flux-pro

(Press Enter to continue)
```

**Rules:**
- Maximum ONE upgrade prompt per session (not per task)
- Only show when friction is actually detected (never unprompted)
- Never block the workflow — Enter always continues
- Track `last_upgrade_prompt` timestamp in config to enforce rate limit

### Pro recommendation prompt

When friction is detected and license key is valid:

```
Friction detected: css_issues (3x this session)
Recommended: tailwind-intellisense — autocomplete + error detection for Tailwind
  Success rate: 85% friction reduction for Next.js + Vercel users

  [i] Install now
  [s] Skip for now
  [d] Snooze this signal (resurfaces in 7 days)
```

### Pro cooldown resurface

When a snoozed signal expires after 7 days:

```
It's been a week since we last looked for optimizations for css_issues.
Checking for new recommendations...

New since last check:
  → tailwind-v4-migrator (added 3 days ago) — auto-migrate Tailwind v3 → v4
  Success rate: 92% for css_issues on Next.js projects

  [i] Install now
  [s] Skip for now
  [d] Snooze for another 7 days
```

### Update /flux:login

```
/flux:login flow:
  1. "Do you have a Flux Pro license key?" → [y/n]
  2. If yes → paste key → validate via Polar API → store in .flux/config.json
  3. If no → "Get Flux Pro: https://polar.sh/nairon-ai/flux-pro"
  4. Continue with Universe device flow (for Flux Score sync, separate from Pro)
```

---

## Polar.sh Setup Steps

### 1. Create Polar account for Nairon-AI ✅

Set up at https://polar.sh — connected to Nairon-AI GitHub org.

**Organization ID**: `3a10c412-6423-45ee-97f5-439501dbc2c2`

### 2. Create products ✅

| Product | Type | Price | Product ID |
|---------|------|-------|------------|
| Harness Recommendations Engine (Monthly) | Subscription | $10/mo | `f8a4ce6e-9034-4881-8fbe-f45186368864` |
| Harness Recommendations Engine (Yearly) | Subscription | $96/yr ($8/mo) | `768ef726-83d0-42fc-9dd8-4a2a17490193` |

### 3. Configure benefits ✅

- **Flux Pro** (License Keys) — auto-generated on purchase
- **Harness Recommendations Engine Access** (Feature Flag) — for API gating
- Webhook configured at `https://universe.nairon.ai/` with all events

### 4. Wire Polar into Universe — PENDING

- Add `app.use(polar)` to `convex.config.ts`
- Configure webhook endpoint in Convex HTTP router
- Handle `subscription.created`, `subscription.revoked` events
- Store subscription status linked to Universe user ID

---

## Teams Plan (Coming Soon)

> **Not implementing now.** Documented here for future reference. Will revisit after 100+ Pro users generate meaningful aggregate data.

Target audience: Engineering managers and team leads wanting AI effectiveness analytics.

Features: org-wide friction heatmaps, team-level metrics, tool standardization recommendations, department comparison dashboards, private data silos, SSO integration.

---

## Ship Order

### Phase 1: Free hardcoded set ✅ COMPLETE
1. ✅ Baked 20 curated recommendations into the Flux plugin (`recommendations/`)
2. ✅ Updated `match-recommendations.py` to use three-tier fallback
3. ✅ Unblocks existing free users immediately

### Phase 2: Pro paywall (revenue unlock) — IN PROGRESS
1. ✅ Set up Polar account + create products (Monthly + Annual)
2. ✅ Webhook configured at `https://universe.nairon.ai/`
3. ✅ License key benefit ("Flux Pro") + feature flag benefit added
4. ✅ `scripts/flux-license.py` — validate, activate, cache, check (client-side via Polar API)
5. ✅ Updated `/flux:login` to accept Polar license keys
6. ✅ License gating in `/flux:improve` workflow (Step 6 rewritten)
7. ✅ Upgrade prompt for free users (rate-limited, 1x per session, only on friction)
8. ✅ Inline friction check in task loop differentiates Pro vs Free
9. ⬜ Wire `@convex-dev/polar` into Universe's `convex.config.ts` (auto-revoke on churn)
10. ✅ Added Convex tables: `fluxRecommendations`, `fluxRecommendationFeedback`, `fluxRecommendationStats`
11. ✅ Built Universe HTTP endpoints: `POST /api/recommendations`, `POST /api/recommendations/feedback`
12. ✅ Seeded 20 recommendations into Convex DB (prod: robust-peccary-479)
13. ✅ Built matching engine server-side with signal + stack scoring
14. ✅ Deployed to production + verified API returns `license_required` correctly
15. ✅ Added Flux Pro pricing section to nairon-website (PR #26 merged)

### Phase 3: Feedback loop (data moat)
1. Update Flux to report install/dismiss/snooze actions to Universe API
2. Add 7-day friction delta measurement + reporting
3. Build aggregation pipeline (success rates per tool per stack)
4. Use aggregated data to rank recommendations in matching engine

### Phase 4: Universe dashboard for Pro users
1. Personal friction trend graphs
2. Recommendation history + effectiveness
3. Stack profile + personalization settings

### Phase 5: Teams tier (coming soon)

---

## References

- [Polar — Product benefits & fulfillment](https://polar.sh/features/benefits)
- [Polar — License Key Validation API (client-side)](https://docs.polar.sh/api-reference/customer-portal/license-keys/validate)
- [Polar — Webhook delivery](https://polar.sh/docs/integrate/webhooks/delivery)
- [Polar — API Overview](https://polar.sh/docs/api-reference/introduction)
- [Universe repo](https://github.com/Nairon-AI/nairon-universe) — Convex backend with existing Flux auth + Polar SDK
- [Nairon website](https://github.com/Nairon-AI/nairon-website) — Landing page (separate, not involved)
