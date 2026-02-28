# Problem Space Questions

Questions for the Discover phase of `/flux:scope`. Use the question tool for your agent — never output questions as text.

**Question Tool by Agent:**
- Claude Code: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`

## Core Desire

Understand WHY this is being requested.

### Quick Mode (pick 2-3)
- "Why do we need this? What's the business driver?"
- "What happens if we don't build this?"
- "Who asked for this and what triggered it?"

### Deep Mode (ask all relevant)
- "Why does the stakeholder want this?"
- "What's the underlying business need — not the surface ask?"
- "What happens if we don't build this? What's the cost of inaction?"
- "Is this solving a symptom or root cause?"
- "What's the opportunity cost of building this vs. something else?"
- "How urgent is this? What's driving the timeline?"
- "Has this been attempted before? What happened?"

---

## Reasoning Chain

Validate the logic from problem to proposed solution.

### Quick Mode (1-2)
- "The ask is X. Is X actually the right solution?"
- "What's the key assumption we're making?"

### Deep Mode (ask all relevant)
- "Walk me through the reasoning: problem → solution"
- "What assumptions are we making? Which are risky?"
- "What would have to be true for this to be the right approach?"
- "Are there simpler alternatives we haven't considered?"
- "If this fails, why would it fail?"
- "What evidence do we have that this will work?"

---

## User Perspective

Understand how users will experience this.

### Quick Mode (1-2)
- "How would users react to this?"
- "What's their current workaround?"

### Deep Mode (ask all relevant)
- "Who are the specific users affected by this?"
- "What's their current workflow? What's broken about it?"
- "What would delight them vs. just satisfy them?"
- "How will they discover this feature?"
- "How will they learn to use it?"
- "What would make them NOT use this feature?"
- "Are there different user segments with different needs?"

---

## Blind Spots

Surface what might be missing.

### Quick Mode (1)
- "What are we not thinking about? Who else is affected?"

### Deep Mode (2-3)
- "What are we not thinking about?"
- "Who else is affected by this change? (other teams, systems, users)"
- "What related problems exist that we might be ignoring?"
- "What would a skeptic say about this approach?"
- "What's the second-order effect of this change?"

---

## Risks

Identify what could go wrong.

### Quick Mode (1)
- "What's the biggest risk or what could go wrong?"

### Deep Mode (3-4)
- "What could go wrong with this direction?"
- "What are the risks of building this? (technical, UX, business)"
- "What are the risks of NOT building this?"
- "What's the rollback plan if this fails?"
- "What's the worst-case scenario?"
- "What dependencies could block us?"
- "What's the blast radius if something breaks?"

---

## Problem Statement Synthesis

After discovery, synthesize into one clear statement.

**Template**:
```
Based on our discussion:

Core need: [1 sentence]
Key assumptions: [bullet list]
User impact: [1 sentence]
Main risk: [1 sentence]

Proposed problem statement:
"[User/stakeholder] needs [capability] because [reason], but currently [obstacle]."

Does this capture it? What would you change?
```

**Good problem statements**:
- "Enterprise customers need to invite team members without IT involvement because onboarding is slow, but currently there's no self-service invite flow."
- "Mobile users need offline access to their data because connectivity is unreliable, but currently the app requires constant connection."

**Bad problem statements**:
- "We need to add OAuth" (solution, not problem)
- "Users are unhappy" (too vague)
- "The competitor has this feature" (not a problem statement)

---

## Question Guidelines

1. **Use the question tool** — never output questions as plain text
2. **Group 2-4 related questions** per tool call
3. **Ask follow-ups** based on answers
4. **Don't ask obvious questions** — assume technical competence
5. **Probe contradictions** — if answers don't align, dig deeper
6. **Stop at diminishing returns** — don't exhaust the user

### Question Tool Pattern

**Anti-pattern (WRONG)**:
```
Here are some questions:
1. Why do we need this?
2. What's the business driver?
```

**Correct pattern**: Call the question tool with questions and options.

### Batching Questions

Group related questions:
- Core Desire: 2-3 questions together
- User Perspective: 2-3 questions together

Don't ask 10 questions in one batch — too overwhelming.

### When to Stop Discovery

**Quick mode**: After 5-8 questions total, move to synthesis
**Deep mode**: When you hear the same themes repeated (diminishing returns)

Signs you're done:
- User starts repeating themselves
- No new angles emerging
- Clear themes have crystallized
- User says "I think that covers it"
