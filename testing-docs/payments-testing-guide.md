# Flux Pro Payments Testing Guide

## Overview

This guide covers end-to-end testing of the Flux Pro payment flow, from free-tier experience through Polar checkout to Pro license activation.

## Architecture

| Component | Location | Role |
|-----------|----------|------|
| `scripts/flux-license.py` | Flux plugin | License key management CLI (activate/deactivate/status/check) |
| `POST /api/recommendations` | Universe API (`robust-peccary-479.convex.site`) | Validates Polar key, returns matched recommendations |
| `POST /api/recommendations/feedback` | Universe API | Records install/dismiss/snooze actions |
| Polar checkout | `https://buy.polar.sh/polar_cl_mvTstXLrEX4XyDe0dzS7WMdpnaSCmxPkIVjq01dbj0D` | Individual plan ($10/month, 1-week free trial) |

## Plans

| Plan | Price | Status |
|------|-------|--------|
| Free | $0 | Live — bundled 20 recommendations from YAML |
| Pro (Individual) | $10/month or yearly | Live — Universe API recommendations |
| Teams | TBD | Coming soon |

## Polar Product IDs

- **Monthly**: `f8a4ce6e-9034-4881-8fbe-f45186368864`
- **Yearly**: `768ef726-83d0-42fc-9dd8-4a2a17490193`
- **Org ID**: `3a10c412-6423-45ee-97f5-439501dbc2c2`

## Test Scenarios

### 1. Free User Experience

**Setup**: No `~/.flux/config.json` or no license key stored.

**Steps**:
1. Run `/flux:improve`
2. Verify bundled recommendations (from `recommendations/` YAML files) are shown
3. Trigger a friction signal — confirm upgrade prompt appears
4. Verify the upgrade prompt includes:
   - Friction count ("We detected X friction signals")
   - 1-week free trial mention
   - Direct checkout link
   - Instructions to check email for license key after purchase
5. Verify upgrade prompt is rate-limited to **1x per 8 hours**
6. Dismiss the prompt — confirm it doesn't reappear within the same session

**Expected**:
- `flux-license.py check` exits with code `1`
- No API calls to Universe
- Bundled YAML recommendations are used for matching

### 2. Inline Friction Prompt (During `/flux:work`)

**Setup**: Free user running task loop.

**Steps**:
1. Run `/flux:work` and complete a task that triggers friction
2. Confirm inline upgrade prompt appears (max 1x per session)
3. Verify `[s] Skip` and `[d] Snooze for 7 days` options work
4. Snooze — confirm prompt doesn't appear for 7 days

### 3. Polar Checkout Flow

**Steps**:
1. Click checkout link: `https://buy.polar.sh/polar_cl_mvTstXLrEX4XyDe0dzS7WMdpnaSCmxPkIVjq01dbj0D`
2. Complete payment with a test email
3. Verify Polar sends a license key to the email
4. Note the key format (Polar-generated, NOT `FLUX-` prefixed)

**Important**: Verify Polar Success/Return URLs are set to something real (not `https://example.com/...` placeholders). Update in Polar dashboard if needed.

### 4. License Key Activation

**Steps**:
1. Run `/flux:login`
2. When prompted "Do you have a Flux Pro license key?" select `[y]`
3. Paste the license key from the Polar email
4. Verify validation against Polar API succeeds
5. Confirm key is stored in `~/.flux/config.json`
6. Run `python3 scripts/flux-license.py status` — should show Pro tier
7. Run `python3 scripts/flux-license.py check` — should exit with code `0`

### 5. Pro User Experience

**Setup**: Valid license key in `~/.flux/config.json`.

**Steps**:
1. Run `/flux:improve`
2. Verify it calls `POST https://robust-peccary-479.convex.site/api/recommendations` with:
   - License key from config
   - Friction signals from session analysis
   - Stack fingerprint from repo context
   - Installed tools list
3. Verify API returns stack-matched, community-ranked recommendations
4. Confirm no upgrade prompts are shown
5. Install a recommendation — verify feedback is posted to `/api/recommendations/feedback`

### 6. License Validation Caching

**Steps**:
1. Activate a valid key
2. Run `/flux:improve` — should validate via Polar API
3. Disconnect from internet
4. Run `/flux:improve` again within 24 hours — should use cached validation (graceful offline degradation)
5. Wait >24 hours (or manually expire cache) — should fail validation when offline

### 7. License Deactivation

**Steps**:
1. Run `python3 scripts/flux-license.py deactivate`
2. Confirm `~/.flux/config.json` no longer has a license key
3. Run `/flux:improve` — should fall back to free-tier bundled recommendations

### 8. Invalid/Revoked Key

**Steps**:
1. Activate a fake key (e.g., `AAAA-BBBB-CCCC-DDDD`)
2. Verify Polar API rejects it
3. Confirm Flux falls back to free-tier behavior
4. If testing revocation: cancel subscription in Polar, wait for key to be revoked, verify `/flux:improve` returns to free tier

### 9. API Fallback

**Steps**:
1. Activate a valid Pro key
2. Simulate Universe API being down (e.g., block `robust-peccary-479.convex.site`)
3. Run `/flux:improve`
4. Verify it falls back to bundled recommendations gracefully (no crash)

## Testing Tips

- **Simulate free user**: Rename `~/.flux/config.json` temporarily, restore after testing
- **Different GitHub account not required**: License keys are Polar-based, independent from GitHub auth
- **Use a real purchase for full E2E**: The 1-week free trial means you can test without paying
- **Check Convex dashboard**: Go to `dashboard.convex.dev` → `robust-peccary-479` → Data → `fluxRecommendations` to verify 20 recommendations are seeded

## Known Gotchas

1. **Polar Success/Return URLs** may still be `https://example.com/...` placeholders — update in Polar dashboard
2. **24h validation cache** means key revocation isn't instant on the client
3. **Rate limiting on upgrade prompts** (1x/8hrs for improve, 1x/session for work) — wait or clear state to re-test
4. **Convex deployment** is `robust-peccary-479` (prod) — do not confuse with dev deployments
