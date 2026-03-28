# Future Pressure

Future pressure is Flux's anti-slop forecasting pass. It exists to catch the "correct in isolation, wrong for the system" failure mode before implementation starts.

This is not a giant ceremony for every change.

## When To Run It

Use three levels:

- **Quick pass (default)**: Run on every scoped feature or plan. Takes 2-3 minutes.
- **Deep pass**: Required for one-way doors, shared abstractions, public APIs, schemas, state machines, auth/permissions, analytics/event models, and workflow engines.
- **Periodic audit**: Run during `/flux:meditate` to find patterns the feature-level passes still missed.

## Decision Rule

Use the deep pass when both are true:

- Reversing the decision later would be painful.
- The decision affects more than one task, team, feature, or user flow.

Otherwise use the quick pass and keep moving.

## Quick Pass

Ask:

1. What are the next 2-3 likely features that will want to reuse or extend this?
2. If usage, data volume, or concurrency grows 10x, what breaks first?
3. What failure modes will users actually feel?
4. If this abstraction is wrong, what is the cheapest reversal path?
5. Are we about to encode a temporary workaround into a durable schema or API?

## Deep Pass

Write explicit answers for:

- **Product pressure**: adjacent features likely within 6-12 months
- **Reuse pressure**: who else will consume this module, endpoint, schema, or flow
- **Scale pressure**: growth in traffic, rows, tenants, concurrency, background jobs
- **Failure pressure**: retries, partial failure, invalid states, degraded mode, support burden
- **Observability pressure**: metrics, logs, traces, analytics, alertability
- **Migration pressure**: rollback path, compatibility window, data migration cost, reversibility
- **Model pressure**: enum vs boolean, lifecycle states, history/audit needs, query shape

## Output Contract

Epic specs should include:

- `## Future Pressure`
- likely follow-on features
- main failure/reuse/migration risks
- reversal signals and validation triggers

Task specs should include:

- `## Pitfalls to Avoid`
- `## Future Pressure Checks`

These sections should be short and specific. If there is no notable pressure, say so explicitly.

## Monthly Role

Monthly or between major epics, use `/flux:meditate` to audit:

- repeated workaround fields
- duplicated abstractions
- recurring pitfall categories
- missing observability on new surfaces
- places where the forecast was wrong and should become a principle

Monthly audit is the correction loop. Feature-by-feature future pressure is the prevention loop.
