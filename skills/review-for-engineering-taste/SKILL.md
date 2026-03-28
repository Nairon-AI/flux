---
name: review-for-engineering-taste
description: Review code at a high level for subtle design papercuts that create long-term slop creep. Use when the user asks for an engineering taste review, wants a high-level code quality pass, asks "does this feel clean?", "what feels off?", "what are the papercut decisions here?", or wants to catch problematic small decisions before they calcify into local conventions.
---

# Review For Engineering Taste

Use this skill for a taste review, not a correctness review.

The job is to spot small design decisions that individually look acceptable but collectively make a codebase slower to change, harder to trust, or easier to bloat. Focus on choices that create future drag: awkward boundaries, vague ownership, leaky abstractions, incidental complexity, and defensive structure added before it pays for itself.

If a concern looks repeatable, do not stop at the review comment. Run the structuralization checkpoint in [../../docs/review-structuralization.md](../../docs/review-structuralization.md) so the developer can decide whether the pattern should become a project constraint, a `lintcn` rule, a brain note, or just a one-off fix.

## Default Stance

- Review the shape of the solution before the syntax.
- Prefer questions that expose design tension over style comments.
- Look for decisions that will get copied.
- Favor the smallest cleanup that restores clarity.
- Be specific about why something is a slop risk.

## Workflow

1. Build a quick mental model of the change or area under review.
2. Run the question set below.
3. Report only the questions that surfaced real risk.
4. For any repeatable concern, run the structuralization checkpoint with the developer.
5. End with the top 1 to 3 slop-creep concerns and the smallest worthwhile correction for each.

If nothing rises above taste preference, say that explicitly.

## Structuralization Checkpoint

When a concern looks like something the codebase could accidentally normalize, ask before encoding:

- "Is this actually undesirable in this repo, or was it a reasonable tradeoff here?"
- "If it's undesirable, do you want to enforce that going forward?"

Then use [../../docs/review-structuralization.md](../../docs/review-structuralization.md) to decide whether the finding should become:
- a `lintcn` rule
- a brain principle or pitfall
- a one-off correction with no structural follow-up

Default to `warn` for new taste-oriented `lintcn` rules unless the pattern is an objective anti-pattern with low false-positive risk.

## Question Set

Ask these questions in order. Skip ones that are clearly irrelevant.

### 1. Boundary Fit

- Does this code live in the right module, layer, or component, or is it quietly teaching the wrong ownership boundary?
- Did the change introduce a new concept that is really just a one-off detail in disguise?
- Is an abstraction being added because multiple callers need it now, or because it might be useful later?

### 2. Local Reasoning

- Can a future reader understand the control flow without jumping through too many files, helpers, or indirections?
- Did the code trade a simple direct path for a "cleaner" structure that is harder to mentally execute?
- Are there too many moving pieces for the amount of behavior implemented?

### 3. Naming And Intent

- Do the names describe the real job of the code, or do they hide uncertainty behind generic terms like `utils`, `manager`, `data`, `handle`, or `process`?
- Is the public API sharper than the implementation, or is vagueness leaking outward?
- Would a new engineer form the right mental model from the names alone?

### 4. Data Shape And Invariants

- Are important invariants obvious in the types, function boundaries, or data model, or are they only implied by call-site discipline?
- Did the change add optionality, fallback behavior, or config surface where the domain really wants one clear path?
- Is the code preserving the natural shape of the data, or forcing it through unnecessary mapping, normalization, or wrapper layers?

### 5. Coupling And Escape Hatches

- Did this introduce hidden coupling between modules, UI state, storage, network logic, or framework details?
- Is there a new flag, callback, prop, or option that acts as an escape hatch for unclear ownership?
- Are we solving one awkward call site by making the whole API less coherent?

### 6. Complexity Versus Change Rate

- Is the amount of structure proportional to how often this code is likely to change?
- Did the author pay an abstraction tax before the repetition or volatility justified it?
- Would deleting or inlining part of this make the system easier to evolve?

### 7. Failure And Debuggability

- When this breaks, will the failure show up near the cause, or will it become a scavenger hunt?
- Did the change hide important branching or fallback behavior behind helpers that make debugging harder?
- Are errors, defaults, retries, or null handling making the happy path look cleaner while obscuring real behavior?

### 8. Test Shape

- Do the tests reinforce the intended contract, or do they lock in incidental structure?
- Is the code hard to test because the design is muddy, not because the test is weak?
- Are mocks, setup, or fixture layers compensating for avoidable design friction?

### 9. Copyability

- If another engineer copied this pattern five times, would the codebase get cleaner or sloppier?
- Is this setting a precedent for new wrappers, new configuration knobs, or new special cases?
- Does this teach restraint, or does it normalize ceremony?

## Output Format

When you find issues, report them as:

- `Question:` the specific question that tripped
- `Why it matters:` the slop-creep risk, in concrete terms
- `Smallest fix:` the least invasive correction that would materially improve the design
- `Structural follow-up:` only when applicable. State whether this should become a `lintcn` rule candidate, a brain principle, or nothing structural.

Keep the final summary high signal:

- `Top risks:` 1 to 3 bullets
- `What to leave alone:` call out anything that looks unusual but is actually a reasonable tradeoff

## Gotchas

- Do not turn this into a bug hunt, security review, or lint pass unless those issues reveal a deeper taste problem.
- Do not flag code just because you would personally write it differently.
- Do not reward abstraction density. Fewer concepts is usually better when the behavior is still small.
- Do not recommend framework-shaped patterns unless they clearly improve local reasoning in this codebase.
- Do not confuse "a little duplication" with a design failure. Premature deduplication is a common source of slop.
- Do not produce a long list of weak nits. If the issue would not matter six months from now, drop it.
- Do not create a `lintcn` rule candidate without confirming that the developer actually wants repo-wide enforcement for subjective taste issues.
