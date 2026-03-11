# Flux Scope Phases

> "We optimized software development for speed for twenty years. Now AI agents can prototype faster than any team ever could, and the bottleneck has flipped."

The Double Diamond process has two spaces, each with diverge and converge phases. **Teams used to skip the first diamond because they couldn't afford it.** Now they can.

## Why This Matters

**Old way:** Weeks of architecture discussions, one RFC, arguments in Slack, someone picks an approach because they read a blog post. You build it, discover edge cases during code review, ship with a TODO.

**New way:** Explore the problem space properly. Surface blind spots. Consider alternatives. Then execute with clarity.

The scarce resource has always been clarity — knowing what to build, defining boundaries, making implicit knowledge explicit. Execution just used to be scarce too, so we optimized for that instead.

## Overview

```
START -> DISCOVER -> DEFINE -> DEVELOP -> DELIVER -> HANDOFF
```

At all times, Flux should persist:
- objective kind: feature, bug, or refactor
- scope mode: shallow or deep
- technical level
- implementation target
- current phase, step, and next action

Use `fluxctl scope-status` to render a progress card after each major transition.

---

## START

**Purpose**: Establish the workflow envelope before asking deeper questions.

**Always capture**:
- feature, bug, or refactor
- shallow or deep
- technical level
- self with AI or engineer handoff

**Why this matters**:
- Shallow and deep mode should feel different.
- Non-technical users should get stronger defaults.
- Engineer handoff should produce richer deliverables than self-build mode.

---

## PROBLEM SPACE

### DISCOVER Phase (Diverge)

**Purpose**: Explore the problem broadly before narrowing down.

**Steps**:
| Step | Focus | Key Question |
|------|-------|--------------|
| Core Desire | WHY | "Why is this being requested?" |
| Reasoning Chain | LOGIC | "Does the logic hold?" |
| User Perspective | WHO | "How will users experience this?" |
| Blind Spots | GAPS | "What are we missing?" |
| Risks | DANGER | "What could go wrong?" |

**Exit Signal**: Diminishing returns — you're circling, not discovering new angles.

**Output**: Clusters of problem angles, assumptions, user insights, risks.

---

### DEFINE Phase (Converge)

**Purpose**: Narrow down to one clear problem statement.

**Process**:
1. Synthesize findings from Discover
2. Identify key themes and tensions
3. Make the call on what problem to solve
4. Articulate in one sentence
5. Validate: "Can you defend this to stakeholders?"

**Exit Signal**: Can articulate the problem in one sentence and defend it.

**Output**: One clear problem statement.

---

## SOLUTION SPACE

### DEVELOP Phase (Diverge)

**Purpose**: Explore solution options, states, edge cases, engineering constraints, and trade-offs before committing.

**Steps**:
| Scout | What It Finds |
|-------|---------------|
| repo-scout | Existing patterns, file refs |
| practice-scout | Best practices, pitfalls |
| docs-scout | External documentation |
| epic-scout | Dependencies on other epics |
| docs-gap-scout | Docs that need updating |
| github-scout | Cross-repo patterns (optional) |
| memory-scout | Project memory (optional) |

**Exit Signal**: Clear understanding of existing code, patterns to follow, and risks.

**Output**: Proposed approach, edge cases, risks, states, and supporting research.

---

### DELIVER Phase (Converge)

**Purpose**: Produce the implementation-ready package.

**Process**:
1. Summarize the chosen problem and solution
2. Convert the approach into an epic + tasks
3. Persist phase artifacts and decisions
4. Prepare next action for implementation or engineer handoff

**Exit Signal**: Epic + tasks are ready, next action is explicit, and the user knows what happens next.

**Output**: Epic + tasks in `.flux/`, plus Deliver artifact and next action.

---

### HANDOFF Phase

**Purpose**: Route the scoped objective into implementation or engineer-facing handoff.

**Outputs**:
- `/flux:work <task>` or `/flux:work <epic>` recommendation for self-build
- engineer handoff summary for handoff mode
- persisted handoff artifact for resumability

---

## Mode Differences

### Shallow Mode (~10 min)

| Phase | Time | Depth |
|-------|------|-------|
| Discover | 3-5 min | 5-8 questions total |
| Define | 1-2 min | Quick synthesis |
| Develop | 2-3 min | Focus on obvious solution, key risks only |
| Deliver | 2-3 min | Short implementation package |

**Use when**: Clear feature, narrow bug, or straightforward refactor.

### Deep Mode (~45 min)

| Phase | Time | Depth |
|-------|------|-------|
| Discover | 15-20 min | 15-20 questions, thorough |
| Define | 5 min | Careful synthesis |
| Develop | 10-15 min | Alternatives, states, trade-offs |
| Deliver/Handoff | 10-15 min | Rich package + stronger gates |

**Use when**: High-stakes feature, significant ambiguity, complex integration.

---

## Anti-Patterns

### Problem Space

- **Skipping discovery**: "I already know what to build" — you probably don't
- **No convergence**: Endless exploration without committing to a problem
- **Solution-first**: Jumping to "how" before understanding "why"

### Solution Space

- **No research**: Writing tasks without understanding the codebase
- **Over-planning**: Writing implementation code in specs
- **Under-sizing**: Creating L tasks that should be split
- **Over-splitting**: Creating 10 S tasks that should be 3 M tasks

---

## Transition Points

### Define → Deliver Handoff

After DEFINE, create the epic immediately and start persisting structured workflow state:
```bash
$FLUXCTL epic create --title "<from problem statement>" --json
$FLUXCTL epic set-context <id> --kind feature --scope-mode shallow --activate
$FLUXCTL epic set-workflow <id> --phase define --step problem-statement --status in_progress
$FLUXCTL epic set-plan <id> --file - <<'EOF'
# Problem Statement
<one sentence>

# Context
<discover findings>
EOF
```

This anchors the remaining workflow to the defined problem.

### Deliver → Work Handoff

After DELIVER, the epic is ready for `/flux:work`:
```
Next: /flux:work <epic-id>
```

Tasks are already sized and specced, and `fluxctl session-state` should now route future prompts correctly.
