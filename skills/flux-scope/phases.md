# Flux Scope Phases

> "We optimized software development for speed for twenty years. Now AI agents can prototype faster than any team ever could, and the bottleneck has flipped."

The Double Diamond process has two spaces, each with diverge and converge phases. **Teams used to skip the first diamond because they couldn't afford it.** Now they can.

## Why This Matters

**Old way:** Weeks of architecture discussions, one RFC, arguments in Slack, someone picks an approach because they read a blog post. You build it, discover edge cases during code review, ship with a TODO.

**New way:** Explore the problem space properly. Surface blind spots. Consider alternatives. Then execute with clarity.

The scarce resource has always been clarity — knowing what to build, defining boundaries, making implicit knowledge explicit. Execution just used to be scarce too, so we optimized for that instead.

## Overview

```
┌─────────────────────────────────┬─────────────────────────────────┐
│       PROBLEM SPACE             │       SOLUTION SPACE            │
├─────────────────────────────────┼─────────────────────────────────┤
│                                 │                                 │
│   DISCOVER        DEFINE        │   RESEARCH        PLAN          │
│   (diverge)      (converge)     │   (diverge)      (converge)     │
│                                 │                                 │
│      ╱╲             │           │      ╱╲              │          │
│     ╱  ╲            │           │     ╱  ╲             │          │
│    ╱    ╲           │           │    ╱    ╲            │          │
│   ╱      ╲          ▼           │   ╱      ╲           ▼          │
│                                 │                                 │
│   Explore      One problem      │   Explore       Epic +          │
│   broadly      statement        │   solutions     tasks           │
│                                 │                                 │
└─────────────────────────────────┴─────────────────────────────────┘
```

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

### RESEARCH Phase (Diverge)

**Purpose**: Explore the codebase and best practices before committing to approach.

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

**Output**: Research findings with file refs, reuse points, and gaps.

---

### PLAN Phase (Converge)

**Purpose**: Create actionable tasks from research.

**Process**:
1. Run gap analysis on research + problem statement
2. Design task breakdown (target M-sized tasks)
3. Minimize file overlap for parallel work
4. Set dependencies between tasks
5. Write task specs (what, not how)
6. Validate epic structure

**Exit Signal**: Validated epic with sized tasks, clear acceptance criteria.

**Output**: Epic + tasks in `.flux/`

---

## Mode Differences

### Quick Mode (~10 min)

| Phase | Time | Depth |
|-------|------|-------|
| Discover | 3-5 min | 5-8 questions total |
| Define | 1-2 min | Quick synthesis |
| Research | 2-3 min | All scouts, brief analysis |
| Plan | 2-3 min | Short task descriptions |

**Use when**: Clear feature, low ambiguity, want to start building quickly.

### Deep Mode (~45 min)

| Phase | Time | Depth |
|-------|------|-------|
| Discover | 15-20 min | 15-20 questions, thorough |
| Define | 5 min | Careful synthesis |
| Research | 10-15 min | Deep analysis, alternatives |
| Plan | 10-15 min | Detailed specs, phased approach |

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

### Problem → Solution Handoff

After DEFINE, create the epic immediately:
```bash
$FLOWCTL epic create --title "<from problem statement>" --json
$FLOWCTL epic set-plan <id> --file - <<'EOF'
# Problem Statement
<one sentence>

# Context
<discover findings>
EOF
```

This anchors the Solution Space to the defined problem.

### Solution → Work Handoff

After PLAN, the epic is ready for `/flux:work`:
```
Next: /flux:work <epic-id>
```

Tasks are already sized and specced. Implementation begins.
