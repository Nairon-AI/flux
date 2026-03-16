# Assumption Stress Test — Full Dialectic Execution

> Only read this file when SKILL.md Step 6.1 detects signals requiring the full dialectic.
> Detection logic and the Quick Assumptions Audit live in SKILL.md — not here.

---

## Phase 1: Frame the Tension

Identify the core tension from the detected signals. Frame it as a genuine contradiction, not a false choice.

**Well-framed tensions:**
- "OAuth-first vs. email/password-first for onboarding" (UX assumption)
- "Microservices vs. modular monolith for this feature" (one-way door)
- "Build custom vs. integrate third-party for [capability]" (lock-in)
- "Optimize for power users vs. new users" (competing needs)
- "Follow existing pattern vs. introduce better pattern" (deferred authority)

Present to user:

```
I've detected a key assumption worth stress-testing before we commit:

**Tension:** [framed contradiction]
**Why this matters:** [one-way door / UX risk / unvalidated authority / competing approaches]
**What's at stake:** [what happens if we get this wrong]

I'm going to stress-test both sides. This takes ~5 minutes and will sharpen the plan.
```

---

## Phase 2: Spawn Opposing Positions (subagents)

Spawn TWO subagents in parallel. Each builds the strongest possible case for one side.

**Subagent A prompt:**
```
You are arguing FOR [Position A]. Build the absolute strongest case.
Context: [problem statement + relevant conversation excerpts]

Your job:
1. Research this position using web search — find real evidence, case studies, data
2. Identify the strongest 3-5 arguments FOR this approach
3. Identify the specific conditions under which this approach WINS
4. Name the failure mode of the opposing approach that makes yours necessary
5. Be specific — cite real tools, patterns, numbers. No generics.

Do NOT hedge. Do NOT acknowledge the other side. Fully commit.
Write 300-500 words.
```

**Subagent B prompt:**
```
You are arguing FOR [Position B]. Build the absolute strongest case.
Context: [problem statement + relevant conversation excerpts]

[Same structure, for the opposing position]
```

---

## Phase 3: Structural Analysis (orchestrator)

After both subagents return, perform:

1. **Decomposition** — Break both arguments into atomic claims
2. **Self-undermining** — Where does each position's own logic weaken itself?
3. **Shared assumptions** — What do both sides take for granted without realizing it?
4. **Specific failure mode** — Not "it's wrong" but "it fails WHEN [condition], pointing toward [what's missing]"
5. **Cross-domain connections** — What do atomic parts from both sides share that wasn't visible from within either frame?

---

## Phase 4: Synthesis

Generate a synthesis that:
- **Cancels** both positions as complete answers
- **Preserves** the genuine insight in each
- **Elevates** to a reframing that makes the original tension predictable

NOT compromise ("use A for some cases, B for others"). Reconceptualization — a new framing that transforms the question.

Present to user:

```
## Stress Test Results

**Tension:** [the framed contradiction]

**Position A — [name]:**
[2-3 sentence summary of strongest case]

**Position B — [name]:**
[2-3 sentence summary of strongest case]

**Where each breaks down:**
- A fails when: [specific condition]
- B fails when: [specific condition]

**What both sides missed:**
[The shared blind spot or assumption neither questioned]

**Synthesis:**
[The reframing — 2-4 sentences. Not a compromise. A new way to think about it.]

**Recommendation for this scope:**
[Concrete: which approach, with what modifications, and why]

**Reversibility check:**
- Can we change course later? [yes/no + cost]
- What would we need to see to know we chose wrong? [specific signal]
```

---

## Phase 5: User Decision

Ask the user:

```
Based on this analysis:
1. Go with the recommendation above
2. Go with Position A (despite the identified risks)
3. Go with Position B (despite the identified risks)
4. I see something neither side considered — let me explain
5. Run another round on a different tension
```

If option 4 → incorporate user's insight and re-synthesize (one more pass, not a full re-run).
If option 5 → return to Phase 1 with the next tension.

Record the decision and reasoning in the epic spec (Step 7).

---

## Multiple Tensions

If multiple signals detected, prioritize:
1. **One-way door decisions** — hardest to reverse
2. **UX assumptions without user validation** — highest user impact risk
3. **Deferred authority** — "someone told me" without independent validation
4. **Competing approaches** — user is already uncertain

Run the full dialectic for the top 1-2. Remaining tensions → add to epic spec as "Assumptions to validate during implementation" — the worker sees these during re-anchor.

---

## Output Integration

The stress test output feeds into the epic spec at Step 7:

```markdown
## Stress-Tested Assumptions

### [Tension 1 name]
- **Decision:** [chosen approach]
- **Rationale:** [synthesis summary]
- **Reversal signal:** [what would tell us we chose wrong]
- **Reversal cost:** [low/medium/high + what it would take]

### Assumptions Deferred to Implementation
- [Assumption]: validate during [task] by [method]
```

This section persists through the entire workflow. The worker reads it during re-anchor. The epic review checks whether reversal signals have appeared.
