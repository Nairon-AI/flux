# Step 6.1: Assumption Stress Test

After the problem statement is confirmed (Step 6) and before entering the Solution Space (Step 7), Flux checks whether the scoping conversation contains assumptions that need stress-testing.

**This step auto-triggers. It is not optional.** The only question is whether the full dialectic runs or the lightweight version.

---

## Trigger Detection

Scan the entire conversation so far (Steps 1-6) for these signals:

### One-Way Door Decisions (always trigger full dialectic)
- Architecture choices that are expensive to reverse (database schema, auth strategy, API contracts, data model, state management approach)
- Technology selection (framework, language, infrastructure provider)
- User-facing commitments (URL structure, API shape, data format, pricing model)
- Third-party dependencies that create lock-in
- Security model decisions (auth flow, permission model, token strategy)

### UX Assumption Signals (trigger full dialectic)
- Developer making UX decisions without mentioning user research: "I think users would prefer...", "Users probably want...", "Most people would..."
- Auth/onboarding strategy chosen without user input: "We'll use email/password", "OAuth should work", "We'll add SSO"
- Workflow assumptions: "Users will click X then Y", "The flow should be...", "We'll put this in settings"
- Accessibility or platform assumptions made implicitly

### Deferred Authority Signals (trigger full dialectic)
- "My senior told me to...", "My lead said...", "The architect decided..."
- "We've always done it this way", "That's how the existing system works"
- "The competitor does it like this", "I read that the best practice is..."
- External authority cited without independent validation

### Competing Approaches (trigger full dialectic)
- User explicitly mentioned alternatives: "We could do A or B", "I'm torn between..."
- User dismissed an approach too quickly: "We definitely shouldn't...", "That won't work"
- Contradictions in the conversation: user said X in Step 1 but implied not-X in Step 3

### Lightweight Check (no signals above, but always runs)
- If NONE of the above signals are detected, run the Quick Assumptions Audit (below) and move on.

---

## Quick Assumptions Audit (always runs, ~2 min)

Even when no strong signals are detected, surface the top assumptions before proceeding:

```
Before we move to the solution, let me surface the key assumptions we're making:

1. [Assumption from Core Desire — e.g., "This is the right problem to solve"]
2. [Assumption from Reasoning — e.g., "X approach will address the core need"]
3. [Assumption from User Perspective — e.g., "Users will adopt this because..."]
4. [Technical assumption — e.g., "The existing auth system can support this"]

For each: Are you confident, or is this worth questioning?
```

If the user confirms all assumptions → proceed to Step 7.
If ANY assumption is flagged as uncertain → escalate to the full dialectic for that assumption.

---

## Full Dialectic (auto-triggered when signals detected, ~8-12 min)

Adapted from the Electric Monks pattern. Runs inside the scope session — no separate directory or files needed. The output feeds directly into the epic spec.

### Phase 1: Frame the Tension

Identify the core tension from the signals detected. Frame it as a genuine contradiction, not a false choice.

**Examples of well-framed tensions:**
- "OAuth-first vs. email/password-first for onboarding" (UX assumption)
- "Microservices vs. modular monolith for this feature's architecture" (one-way door)
- "Build custom vs. integrate third-party for [capability]" (technology lock-in)
- "Optimize for power users vs. optimize for new users" (competing user needs)
- "Follow the existing pattern vs. introduce a better pattern" (deferred authority)

Present the tension to the user:

```
I've detected a key assumption that's worth stress-testing before we commit:

**Tension:** [framed contradiction]
**Why this matters:** [one-way door / UX risk / unvalidated authority / competing approaches]
**What's at stake:** [what happens if we get this wrong]

I'm going to quickly stress-test both sides. This takes ~5 minutes and will sharpen the plan.
```

### Phase 2: Spawn Opposing Positions (subagents)

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

[Same structure as above, for the opposing position]
```

### Phase 3: Structural Analysis (orchestrator)

After both subagents return, the orchestrator (main agent) performs:

1. **Decomposition** — Break both arguments into atomic claims
2. **Find self-undermining** — Where does each position's own logic weaken itself?
3. **Find shared assumptions** — What do both sides take for granted without realizing it?
4. **Find the specific failure mode** — Not "it's wrong" but "it fails WHEN [condition], which points toward [what's missing]"
5. **Cross-domain connections** — What do the atomic parts from both sides have in common that wasn't visible from within either frame?

### Phase 4: Synthesis

Generate a synthesis that:
- **Cancels** both positions as complete answers
- **Preserves** the genuine insight in each
- **Elevates** to a reframing that makes the original tension predictable

This is NOT compromise ("use A for some cases, B for others"). It's reconceptualization — a new framing that transforms the question.

**Present to user:**

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

### Phase 5: User Decision

Ask the user:

```
Based on this analysis:
1. Go with the recommendation above
2. Go with Position A (despite the identified risks)
3. Go with Position B (despite the identified risks)
4. I see something neither side considered — let me explain
5. Run another round on a different tension
```

If option 4 → incorporate the user's insight and re-synthesize (one more pass, not a full re-run).
If option 5 → return to Phase 1 with the next tension.

Record the decision and reasoning in the epic spec (Step 7).

---

## Multiple Tensions

If multiple signals are detected, prioritize:
1. **One-way door decisions** — hardest to reverse, test first
2. **UX assumptions without user validation** — highest user impact risk
3. **Deferred authority** — "someone told me" without independent validation
4. **Competing approaches** — user is already uncertain

Run the full dialectic for the top 1-2 tensions. For remaining tensions, add them to the epic spec as "Assumptions to validate during implementation" — the worker will see these during re-anchor.

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

---

## User Research Prompt

During the User Perspective step (Step 3), if the feature involves user-facing decisions and the user hasn't mentioned talking to users, ask:

```
This feature involves [UX decision]. Have you spoken to users about what they'd prefer?

If not — that's fine, we can still scope this. But I'll flag the UX assumptions
in the stress test so we can validate them during implementation
(e.g., A/B test, user interviews, analytics check).
```

This is a genuine question, not a gate. Many features ship without user research and that's OK. But the assumption should be explicit, not invisible.
