# Flux -> Universe Technical Specification

## Document Control

- Owner: Flux CLI Engineering
- Status: Draft for implementation
- Last updated: 2026-03-02
- Depends on: Universe Flux APIs
- Related:
  - `docs/universe-sync-prd.md`
  - `docs/universe-sync-requirements.md`

## 1) Scope

This document defines implementation details for:

- `flux login` (device flow only)
- `flux logout`
- `flux status`
- Background stats sync after `flux score`

Constraint: stdlib-only runtime dependencies.

## 2) Architecture Overview

### Local components

1. CLI command layer
2. Auth module (HTTP + token storage + session state)
3. Score integration hook
4. Browser launcher for device verification URL

### External components

1. Universe device auth API
2. Universe `/auth/device` browser flow
3. Universe stats ingest API

## 3) Command Surface

### 3.1 `flux login`

- CLI auth is device flow only.
- No email/password prompts in terminal.
- Replaces existing local token on success.
- Returns non-zero on denied/expired/unexpected failure.
- Never prints secrets (`deviceCode`, tokens, auth headers).

#### Output contract

```text
Opening browser...
Sign in at <verificationUri>
Your code: <userCode>
```

Success:

```text
✓ Logged in as @<username>
Flux will sync stats to your Universe profile.
```

### 3.2 `flux logout`

- Deletes local auth file only.
- No network call.
- Idempotent.

### 3.3 `flux status`

- Reads local auth state.
- Reports connected/disconnected.
- Supports text and JSON output.

### 3.4 `flux score`

- Existing score output completes before sync line.
- Sync is best-effort with short timeout.
- Print `↑ Synced to Universe` only after confirmed success.
- Print nothing on sync failure.

## 4) Local Storage

### 4.1 File location

- Directory: `~/.flux/`
- File: `~/.flux/universe-auth.json`

### 4.2 File schema (v1)

```json
{
  "schemaVersion": 1,
  "accessToken": "flux_...",
  "tokenType": "Bearer",
  "user": {
    "handle": "luka"
  },
  "issuedAt": "2026-03-01T12:00:00Z",
  "updatedAt": "2026-03-01T12:00:00Z"
}
```

Notes:

- Keep schema minimal.
- Do not store passwords or provider credentials.
- `email` is optional metadata when present in server response.

### 4.3 Permissions

- Create `~/.flux` if missing.
- Auth file mode target: `0600` on unix-like systems.
- Use atomic writes to avoid partial corruption.

## 5) API Contracts

Base URL:

- Production: `https://universe.naironai.com`

### 5.1 Start device login

```http
POST /api/flux/device/start
Content-Type: application/json

{
  "clientId": "flux-cli",
  "clientVersion": "0.1.0"
}
```

Success `200` includes: `deviceCode`, `userCode`, `verificationUri`, `verificationUriComplete`, `expiresIn`, `interval`.

### 5.2 Poll device login

```http
POST /api/flux/device/poll
Content-Type: application/json

{
  "deviceCode": "<secret>"
}
```

Responses:

- `202` pending: `{ "status": "pending" }`
- `200` approved: `{ "status": "approved", "accessToken": "flux_...", "username": "..." }`
- `400` denied/expired: `{ "status": "denied" | "expired" }`

### 5.3 Sync stats

```http
POST /api/flux/sync
Authorization: Bearer flux_...
Content-Type: application/json

{
  "sessionsCount": 47,
  "totalTokens": 1200000,
  "toolsUsed": ["Read", "Edit", "Bash"],
  "sentAt": 1739999999999,
  "sourceVersion": "0.1.0"
}
```

Success `200`: `{ "ok": true, "lastSyncedAt": 1739999999999 }`

## 6) CLI State Flows

### 6.1 `flux login`

1. Call `POST /api/flux/device/start`.
2. Print verification instructions and open browser to `verificationUriComplete`.
3. Poll `POST /api/flux/device/poll` using server-provided `interval`.
4. On approved: write token atomically and print success.
5. On denied/expired: print concise error and exit non-zero.

### 6.2 `flux logout`

1. Attempt local auth file delete.
2. If missing, continue.
3. Print disconnected message.

### 6.3 `flux status`

1. No auth file: report disconnected.
2. Valid auth file: report connected handle.
3. Corrupt or schema-mismatch file: treat as disconnected and suggest login.

### 6.4 `flux score` sync

1. Compute and print score output.
2. If no token: skip sync path silently.
3. If token exists: POST snapshot payload to `/api/flux/sync` with short timeout.
4. On success: print `↑ Synced to Universe`.
5. On any failure: remain silent.

## 7) Reliability and Security

- Sync timeout target: <= 3 seconds.
- No retries in score foreground path.
- `flux score` exit code is not affected by sync failures.
- Never print tokens or `deviceCode`.
- Use HTTPS endpoints in production.
- On auth JSON corruption, fail closed and require re-login.

## 8) Testing Plan

### Unit tests

- Auth file read/write/delete, schema mismatch, corruption handling.
- Permission behavior (`0600`) and atomic writes.
- Device flow states: pending, approved, denied, expired.

### Integration tests

- `flux login` success stores token + handle.
- `flux logout` idempotency.
- `flux status` connected/disconnected/corrupt behavior.
- `flux score` sync success line on 2xx; silence on any failure.

### Regression tests

- Existing `flux score` output unchanged for unauthenticated users.
