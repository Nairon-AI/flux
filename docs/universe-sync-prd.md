# Flux -> Universe PRD

## Document Control

- Owner: Flux Product + CLI Engineering
- Status: Draft for implementation
- Last updated: 2026-03-01
- Related docs:
  - `docs/universe-sync-requirements.md`
  - `docs/universe-sync-spec.md`
  - `docs/commands-reference.md`

## 1) Product Summary

Flux is a local-first workflow tool. Universe is the cloud profile layer for engineers who want their activity reflected publicly or analyzed over time.

This initiative adds first-party account connection and automatic stats sync while preserving Flux's core principle: full local utility without an account.

## 2) Problem Statement

Today, users can compute Flux scores locally, but there is no seamless way to connect those usage signals to a persistent Universe identity.

Consequences:

- Users who want cloud presence have no one-command onboarding path.
- Existing score output is isolated from long-term profile progression.
- New users discovering Universe through Flux do not get a terminal-first account creation flow.

## 3) Vision and Product Principles

### Vision

Connect Flux to Universe in under 30 seconds using a device flow, then make sync invisible and reliable.

### Principles

1. Flux remains local-first and fully useful without auth.
2. Connection must be easy enough that users do it once and forget it.
3. No growth nags in core commands.
4. Sync failures must never degrade the main scoring experience.
5. CLI auth is device-flow only; the browser handles account sign-in/creation UI.

## 4) Goals and Non-Goals

### Goals

- Add `flux login` with device-flow auth.
- Add `flux logout` with idempotent local disconnect.
- Add `flux status` for explicit visibility when requested.
- Auto-sync minimal metrics after each score when authenticated.
- Preserve current unauthenticated behavior with no prompts.

### Non-Goals

- No gating of existing Flux features behind login.
- No social graphs, follows, feeds, or notifications in CLI.
- No multi-device token management UI in CLI v1.
- No additional non-stdlib runtime dependencies.

## 5) Users and Personas

### Primary persona: AI-native engineer using Flux daily

- Already runs `flux score` and other commands locally.
- Wants public proof of AI tooling usage with minimal effort.
- Values speed and low terminal noise.

### Secondary persona: New user discovering Universe through Flux

- Does not yet have a Universe account.
- Expects a minimal CLI flow that opens browser sign-in only when needed.
- Can create a Universe account from the `/auth/device` browser page.

## 6) Jobs To Be Done

- When I run Flux, I want to connect my account quickly so my usage stats sync automatically.
- When I do not want cloud sync, I want Flux to behave exactly as before.
- When connection breaks, I want score commands to keep working and only check auth when I ask.

## 7) User Experience

## 7.1 `flux login`

### Device-flow login

1. User runs `flux login`.
2. CLI requests a device code from Universe.
3. CLI shows verification URL + user code, then opens browser to the complete verification URL.
4. User signs in (or signs up) in browser.
5. CLI polls approval and stores token locally.

Expected output style:

```text
$ flux login

  Opening browser...
  Sign in at https://universe.naironai.com/auth/device
  Your code: ABCD-EFGH

  ✓ Logged in as @luka
  Flux will sync stats to your Universe profile.
```

### New user behavior

1. User runs `flux login`.
2. Browser `/auth/device` page shows normal Universe sign-in UI.
3. If user does not have an account, they create one in browser.
4. On approval, CLI stores token and completes login.

### Re-auth behavior

- Running `flux login` while already authenticated replaces old token with new token.
- No extra warning required unless auth service returns conflict/error.

## 7.2 `flux logout`

- Deletes local token data only.
- No network dependency.
- Idempotent success whether currently logged in or not.

Expected output:

```text
$ flux logout

  ✓ Disconnected from Universe.
```

## 7.3 `flux status`

- Read-only command for explicit visibility.
- Default output should be minimal and deterministic.

Examples:

```text
$ flux status

  Connected as @luka
  Sync: enabled
```

```text
$ flux status

  Not connected
  Run: flux login
```

## 7.4 `flux score` integration

- Score behavior remains unchanged for unauthenticated users.
- If authenticated, sync happens in background after normal score output.
- On successful sync, print one-line confirmation.
- On failure, print nothing and do not alter exit path.

## 8) Functional Scope

### In scope

- Terminal auth API integration.
- Local credential persistence and deletion.
- Post-score background sync of three fields only.
- Minimal auth status command.

### Out of scope

- Rich profile editing in terminal.
- Retry queues and offline replay (future).
- Interactive account settings management.

## 9) Success Metrics

### Product KPIs

- Login completion rate (overall and first-run).
- New account creation completion rate from `flux login`.
- Time to connected state (P50/P90).
- Sync success rate for authenticated score executions.
- Unauthenticated churn impact (must remain neutral).

### Guardrail metrics

- `flux score` runtime regression (must stay within tolerance).
- Crash/error rate in score command (must not increase).
- Support tickets mentioning unexpected prompts/nagging (target: near zero).

## 10) Risks and Mitigations

### Risk: device-flow auth/approval edge cases

Mitigation:

- Keep API contract narrow.
- Restrict v1 to `POST /api/flux/device/start` + `POST /api/flux/device/poll` contract.
- Validate with integration tests and mocked auth responses.

### Risk: sync delays score UX

Mitigation:

- Run sync async with short timeout.
- Fail closed and silent.

### Risk: token compromise on disk

Mitigation:

- Store only access token and identity metadata needed for UX.
- Enforce file permissions and avoid sensitive logging.

## 11) Rollout Strategy

1. Implement behind no user-facing migration requirement.
2. Release with docs updates and troubleshooting guidance.
3. Observe auth/sync KPIs for one release cycle.
4. Add optional enhancements (refresh tokens, queueing, keychain support) in follow-up.

## 12) Open Decisions for Product + Backend Alignment

1. Final device start/poll contract stability.
2. Browser `/auth/device` UX copy for sign-in vs sign-up.
3. Token lifetime and refresh strategy for v1 vs v1.1.
4. Canonical definition of `totalTokens` accepted by Universe ingestion.

## 13) Launch Checklist (Product)

- Requirements signed off.
- API contract frozen.
- CLI UX copy approved.
- Security review complete.
- Docs published.
- Telemetry instrumentation verified.
