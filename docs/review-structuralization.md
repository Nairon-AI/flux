# Review Structuralization Checkpoint

Use this checkpoint when a manual review, impl-review, epic-review, or engineering-taste review surfaces a code pattern that may be worth preventing structurally in the future.

The goal is not to convert every review comment into a rule. The goal is to identify patterns the developer genuinely does not want repeated in this repo, confirm that judgment, and then encode it at the right layer.

## Decision Flow

For each review finding that looks repeatable:

1. **Classify the finding**
   - `Objective anti-pattern`: almost always bad regardless of local style.
   - `Project convention`: not universally wrong, but this repo should avoid it.
   - `Contextual / one-off`: fix it, but do not encode it.
   - `Not machine-detectable`: important taste judgment, but too nuanced for linting.

2. **Confirm with the developer when the judgment is subjective**
   Ask directly:
   - "I spotted this pattern: [pattern]. Was it actually a bad tradeoff here, or acceptable in this case?"
   - "If it is undesirable, do you want this enforced repo-wide going forward?"

3. **Choose the mechanism**
   - `lintcn rule`: use when the pattern is repeatable, machine-detectable, and the developer wants enforcement.
   - `Brain principle / pitfall`: use when the pattern matters but requires judgment and would create too many false positives as a lint rule.
   - `Fix only`: use when the issue is local and not worth encoding.
   - `Backlog task`: use when the structural fix is right but too large to implement during the current review flow.

## `lintcn` Guidance

If the decision is to encode the pattern as a `lintcn` rule:

1. Check whether the repo already uses `lintcn`.
2. Prefer `warn` first for new or taste-oriented rules.
3. Use `error` when the pattern is a clear anti-pattern with low false-positive risk.
4. If the rule cannot be added immediately, create a concrete follow-up item instead of leaving it as an informal suggestion.

## When NOT to Create a Rule

Do not recommend a `lintcn` rule when:
- the pattern depends too heavily on business semantics
- the reviewer cannot describe a reliable detection heuristic
- the developer does not want repo-wide enforcement
- the issue is really about architecture judgment, not syntax or static structure
- the maintenance cost of the rule exceeds the recurrence risk

## Output Template

```markdown
## Structuralization Checkpoint

**Pattern**
- [short description]

**Classification**
- [objective anti-pattern / project convention / contextual / not machine-detectable]

**Developer confirmation**
- [confirmed undesirable repo-wide / acceptable here / undecided]

**Recommended mechanism**
- [`lintcn` rule / brain principle / fix only / backlog task]

**Enforcement level**
- [`warn` / `error` / n/a]

**Reasoning**
- [why this should or should not be encoded]
```
