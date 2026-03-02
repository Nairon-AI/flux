# Flux -> Universe Requirements

## Document Control

- Owner: Flux Product + Engineering
- Status: Draft baseline requirements
- Last updated: 2026-03-01
- Related:
  - `docs/universe-sync-prd.md`
  - `docs/universe-sync-spec.md`

## 1) Requirement Conventions

- `FR-*`: functional requirements
- `UX-*`: user experience requirements
- `NFR-*`: non-functional requirements
- `SEC-*`: security and privacy requirements
- `OPS-*`: operational requirements

Priority legend:

- P0: required for launch
- P1: should have
- P2: future

## 2) Functional Requirements

## Authentication Commands

- FR-001 (P0): System shall provide `flux login` to connect local Flux usage to a Universe account.
- FR-002 (P0): `flux login` shall use Universe device flow (`/api/flux/device/start` + `/api/flux/device/poll`).
- FR-003 (P0): `flux login` shall print verification URL and user code, then open browser to verification URI.
- FR-004 (P0): Account sign-in/sign-up shall occur in browser UI, not via CLI prompts.
- FR-005 (P0): `flux login` shall replace existing local token upon successful re-authentication.
- FR-006 (P0): System shall provide `flux logout` to remove local auth state.
- FR-007 (P0): `flux logout` shall be idempotent and succeed even when no token exists.
- FR-008 (P0): System shall provide `flux status` to report connected or disconnected state.
- FR-009 (P1): `flux status` should show connected handle when available.

## Device Flow Path

- FR-010 (P0): Device flow shall poll at server-provided interval until approved, denied, or expired.
- FR-011 (P0): Device flow shall return control to terminal with success, denied, or expired outcome.

## Score Sync

- FR-012 (P0): System shall attempt stats sync automatically after every successful `flux score` execution when authenticated.
- FR-013 (P0): System shall skip sync with zero output when unauthenticated.
- FR-014 (P0): System shall sync only these fields: `sessionsCount`, `totalTokens`, `toolsUsed`.
- FR-015 (P0): System shall print `↑ Synced to Universe` only on confirmed successful sync.
- FR-016 (P0): System shall not print sync failure messages during `flux score`.

## Compatibility

- FR-017 (P0): Existing Flux commands unrelated to auth or score sync shall remain behaviorally unchanged.
- FR-018 (P0): Unauthenticated users shall retain full current Flux functionality.

## 3) UX Requirements

- UX-001 (P0): `flux login` should be completable in under 30 seconds for returning users with healthy network.
- UX-002 (P0): `flux login` shall keep output minimal and avoid promotional messaging.
- UX-003 (P0): `flux score` output shall remain focused on score content.
- UX-004 (P0): Auth failures shall be surfaced in explicit auth commands, not in `flux score`.
- UX-005 (P1): Error messages in auth commands should be actionable and concise.
- UX-006 (P1): Password input shall be masked in terminal.

## 4) Non-Functional Requirements

## Performance

- NFR-001 (P0): Score computation path shall not be blocked by sync retries.
- NFR-002 (P0): Sync path shall use bounded timeout and fail fast.
- NFR-003 (P1): End-to-end overhead added to `flux score` should remain negligible for unauthenticated users.

## Reliability

- NFR-004 (P0): Sync failures shall not change score command exit success when score calculation succeeds.
- NFR-005 (P0): Local auth file corruption shall not crash CLI; system shall require re-login.
- NFR-006 (P1): Auth state writes should be atomic to reduce corruption risk.

## Maintainability

- NFR-007 (P0): Implementation shall use stdlib-only runtime dependencies.
- NFR-008 (P1): Auth and sync logic should be isolated from scoring math for maintainability.

## 5) Security and Privacy Requirements

- SEC-001 (P0): System shall never persist plaintext passwords.
- SEC-002 (P0): System shall store auth token only in local user directory.
- SEC-003 (P0): Auth token file shall use restrictive filesystem permissions where supported.
- SEC-004 (P0): CLI shall avoid printing tokens or authorization headers.
- SEC-005 (P0): Network calls carrying credentials or tokens shall use HTTPS endpoints.
- SEC-006 (P0): Only `sessionsCount`, `totalTokens`, and `toolsUsed` may be transmitted in score sync.
- SEC-007 (P1): Debug logging mode must redact secrets by default.

## 6) Operational Requirements

- OPS-001 (P0): Feature shall launch without migration steps for existing users.
- OPS-002 (P0): Troubleshooting documentation shall include auth status and reconnect guidance.
- OPS-003 (P1): Team shall monitor login completion and sync success post-release.

## 7) Acceptance Criteria

## Login

- AC-001: Given a valid approval through `/auth/device`, when user runs `flux login`, then system stores token and prints connected identity.
- AC-002: Given a user without an account, when they create one in browser during device flow, then CLI login completes successfully.
- AC-003: Given existing token, when user logs in again, then old token is replaced.
- AC-004: Given device login selection, when browser approval completes, then CLI stores token and prints success.

## Logout and Status

- AC-005: Given logged-in state, when user runs `flux logout`, then token file is removed and command succeeds.
- AC-006: Given logged-out state, when user runs `flux logout`, then command still succeeds with disconnect message.
- AC-007: Given connected state, `flux status` reports connected handle.
- AC-008: Given no token, `flux status` reports not connected.

## Score Sync

- AC-009: Given unauthenticated state, `flux score` prints normal score output and no Universe output.
- AC-010: Given authenticated state and reachable API, `flux score` prints normal score output and then sync success line.
- AC-011: Given authenticated state and sync API failure, `flux score` still succeeds and prints no sync error.
- AC-012: Sync payload contains only required fields with correct types.

## 8) Traceability Matrix

| Requirement | PRD Section | Spec Section | Test Target |
|---|---|---|---|
| FR-001..009 | UX + Scope | Command Surface | Auth command tests |
| FR-010..011 | UX device-flow branch | API + flow state | Device flow tests |
| FR-012..016 | Score integration | Sync flow + payload | Score sync tests |
| SEC-001..006 | Principles + Risks | Security controls | Security and redaction tests |
| NFR-001..006 | Guardrails | Reliability + performance | Regression and failure tests |

## 9) Deferred Items (Not Required for Launch)

- D-001: Refresh token lifecycle and silent renewal.
- D-002: Offline sync queue with replay.
- D-003: OS keychain-backed token storage.
- D-004: Extended auth diagnostics (`flux auth doctor`).
