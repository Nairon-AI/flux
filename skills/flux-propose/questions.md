# Stakeholder Questions

Questions for the feature proposal conversation in `/flux:propose`. Use the question tool for your agent — never output questions as text.

**Question Tool by Agent:**
- Claude Code: `AskUserQuestion`
- OpenCode: `mcp_question`
- Codex: `AskUserTool`

---

## The Problem (Step 1)

Understand the pain that exists today.

- "What's the problem you're trying to solve? What's not working today?"
- "Who's experiencing this problem? How often does it come up?"
- "How are people working around it right now?"
- "What happens if we don't address this? What's the cost of doing nothing?"

**Follow-up probes:**
- If vague: "Can you give me a specific example? Walk me through a time this was a problem."
- If solution-shaped: "That sounds like a solution — what's the underlying problem it's solving?"
- If too broad: "That's a big area. What's the single most painful part?"

---

## The Vision (Step 2)

Understand the desired outcome — in their words, not technical terms.

- "If this was built exactly how you imagine it, what would the experience look like?"
- "What would change for the people who use this?"
- "How would you know this was successful? What would you measure?"

**Follow-up probes:**
- If feature-list shaped: "Those are features — what's the outcome you're going for?"
- If unclear scope: "Is this a small improvement or a major new capability?"

---

## Users (Step 3)

Understand who benefits and how.

- "Who specifically would use this? (customers, internal team, partners?)"
- "How many people are affected? Is this 10 users or 10,000?"
- "How often would they use it? Daily, weekly, occasionally?"
- "Are there different types of users who'd use this differently?"

---

## Priority (Step 4)

Understand urgency and business context.

- "Why is this important now? What's changed?"
- "Is there a deadline or event driving this? (launch, contract, season)"
- "How does this rank against other things the team could be working on?"
- "Is anyone else asking for this? Customers, sales, leadership?"

---

## Simplification (Step 7)

After pushback, probe for a simpler version.

- "What's the absolute minimum version that would solve the core problem?"
- "If you could only have one part of this, which part?"
- "Could we start with [simpler approach] and add [complex part] later?"
- "Is there a manual workaround that could bridge the gap while we build the full version?"

---

## Question Guidelines

1. **Use the question tool** — never output questions as plain text
2. **Ask 2-3 questions at a time** — don't overwhelm
3. **Adapt based on answers** — skip what's clear, probe what's vague
4. **Use their language** — don't translate to technical jargon
5. **Validate understanding** — repeat back what you heard before moving on
6. **Don't ask what you can infer** — if they said "our customers keep asking for X", don't ask "who's requesting this?"

### When to Stop Probing

Signs you have enough context:
- You can explain the feature back to them and they say "yes, exactly"
- The problem, users, and priority are all clear
- You're hearing the same themes repeated
- They say "I think that covers it"

### Handling Technical Drift

If the stakeholder starts specifying implementation:
- "That's a great thought — I'll note it for the engineering team. For now, let's focus on what the experience should be like."
- "You're thinking about the how — let's make sure the what is solid first."
- Only go technical if they explicitly insist (and warn them first — see Phase 3 in SKILL.md).
