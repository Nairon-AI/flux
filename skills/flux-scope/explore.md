# Explore Mode Architecture

> "Write ten specs. Test them all. Throw away nine."

Explore mode (`--explore N`) generates N competing approaches, scaffolds each in parallel, and lets you pick the winner with evidence.

## Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                      PROBLEM SPACE                              │
│                    (same as v1 scope)                           │
│  Discover → Define → Problem Statement                          │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   APPROACH GENERATION                           │
│  Generate N fundamentally different approaches                  │
│  User confirms/modifies list                                    │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│              PARALLEL EXPLORATION (N branches)                  │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │Approach A│  │Approach B│  │Approach C│  │Approach D│        │
│  ├──────────┤  ├──────────┤  ├──────────┤  ├──────────┤        │
│  │ Worktree │  │ Worktree │  │ Worktree │  │ Worktree │        │
│  │ Research │  │ Research │  │ Research │  │ Research │        │
│  │ Scaffold │  │ Scaffold │  │ Scaffold │  │ Scaffold │        │
│  │ Preview  │  │ Preview  │  │ Preview  │  │ Preview  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│       ↓             ↓             ↓             ↓               │
│  [Screenshot]  [Screenshot]  [Screenshot]  [Screenshot]         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    COMPARISON MATRIX                            │
│  Side-by-side: screenshots, tradeoffs, scope, risks             │
│  User picks winner (or hybrid, or refine)                       │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       FINALIZE                                  │
│  Merge winner → Create epic + tasks → Cleanup worktrees         │
└─────────────────────────────────────────────────────────────────┘
```

---

## Usage

```bash
# Explore 3 approaches (default)
/flux:scope Add user dashboard --explore

# Explore specific number of approaches
/flux:scope Add permissions system --explore 4

# Combine with deep mode for thorough exploration
/flux:scope Add payment integration --explore 3 --deep
```

---

## Isolation Strategy: Git Worktrees

Each approach gets an isolated git worktree:

```bash
# Create worktrees for exploration
git worktree add .flux/explore/approach-a -b explore/fn-N/approach-a
git worktree add .flux/explore/approach-b -b explore/fn-N/approach-b
git worktree add .flux/explore/approach-c -b explore/fn-N/approach-c
```

**Why worktrees over branches?**
- Full filesystem isolation
- Can run different dev servers simultaneously
- No checkout switching disrupts main work
- Easy cleanup: `git worktree remove`

**Directory structure:**
```
.flux/
├── explore/
│   ├── approach-a/          # Full repo clone via worktree
│   │   ├── src/
│   │   └── ...
│   ├── approach-b/
│   ├── approach-c/
│   └── previews/
│       ├── approach-a.png
│       ├── approach-b.png
│       └── approach-c.png
└── epics/
```

---

## Approach Generation

After Problem Space converges, generate N distinct approaches:

### For Backend/Architecture
```
Approach A: "Extend RBAC"
  - Add finer-grained roles to existing system
  - Tradeoffs: Low risk, limited flexibility
  - Scope: S

Approach B: "Full ABAC migration"  
  - Policy-based authorization
  - Tradeoffs: Flexible, complex migration
  - Scope: L

Approach C: "Hybrid RBAC+ABAC"
  - RBAC for common cases, ABAC for exceptions
  - Tradeoffs: Best of both, more complexity
  - Scope: M

Approach D: "External policy engine"
  - OPA/Cedar for all authorization
  - Tradeoffs: Powerful, operational overhead
  - Scope: M
```

### For Frontend/UI
```
Approach A: "Modal wizard"
  - Step-by-step modal flow
  - Tradeoffs: Familiar, interrupts context
  
Approach B: "Inline expansion"
  - Expand in-place, no modal
  - Tradeoffs: Contextual, limited space

Approach C: "Side panel"
  - Slide-out panel, persistent
  - Tradeoffs: More space, takes screen real estate

Approach D: "Full page"
  - Dedicated page for complex flows
  - Tradeoffs: Most space, navigation required
```

---

## Parallel Execution

Use Task tool to spawn N parallel agents:

```
Task 1: "Scaffold approach A in worktree"
  - subagent_type: "general"
  - workdir: .flux/explore/approach-a
  - prompt: "Implement approach A: [spec]"

Task 2: "Scaffold approach B in worktree"
  - subagent_type: "general"
  - workdir: .flux/explore/approach-b
  - prompt: "Implement approach B: [spec]"

... (parallel)
```

**Constraints:**
- Timeout: 10 minutes per approach
- Scope: Minimal viable prototype (not production-ready)
- Goal: Enough to evaluate, not enough to ship

---

## UI Preview Generation

For frontend variations, generate visual previews:

### Option 1: Live Screenshot (preferred)
```bash
# Start dev server in worktree
cd .flux/explore/approach-a && npm run dev &

# Capture screenshot
agent-browser open http://localhost:3001/preview
agent-browser wait --load networkidle
agent-browser screenshot .flux/explore/previews/approach-a.png
agent-browser close
```

### Option 2: Static HTML Preview
If dev server unavailable, generate standalone HTML:
```html
<!-- .flux/explore/approach-a/preview.html -->
<html>
<head><style>/* Extracted component styles */</style></head>
<body>
  <!-- Rendered component markup -->
</body>
</html>
```

### Option 3: ASCII Wireframe (fallback)
```
┌─────────────────────────────────┐
│ ┌─────────────────────────────┐ │
│ │      Modal: Step 1/3        │ │
│ │  ┌───────────────────────┐  │ │
│ │  │ Name: [___________]   │  │ │
│ │  │ Email: [__________]   │  │ │
│ │  └───────────────────────┘  │ │
│ │        [Back] [Next →]      │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

---

## Comparison Matrix

Present all approaches for evaluation:

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPROACH COMPARISON                          │
├─────────────┬─────────────┬─────────────┬─────────────┐         │
│  Approach A │  Approach B │  Approach C │  Approach D │         │
│ Modal Wizard│ Inline      │ Side Panel  │ Full Page   │         │
├─────────────┼─────────────┼─────────────┼─────────────┤         │
│             │             │             │             │         │
│ [Preview A] │ [Preview B] │ [Preview C] │ [Preview D] │         │
│             │             │             │             │         │
├─────────────┼─────────────┼─────────────┼─────────────┤         │
│ + Familiar  │ + Context   │ + Persistent│ + Most space│         │
│ - Interrupts│ - Limited   │ - Takes     │ - Navigation│         │
│             │   space     │   screen    │   required  │         │
├─────────────┼─────────────┼─────────────┼─────────────┤         │
│ Scope: M    │ Scope: S    │ Scope: M    │ Scope: L    │         │
│ Risk: Low   │ Risk: Low   │ Risk: Med   │ Risk: Med   │         │
├─────────────┼─────────────┼─────────────┼─────────────┤         │
│ Files: 3    │ Files: 2    │ Files: 4    │ Files: 5    │         │
└─────────────┴─────────────┴─────────────┴─────────────┘         │
                                                                   │
Which approach? (a/b/c/d/hybrid/refine)                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## User Selection Options

### Pick Winner
```
> a

Merging Approach A (Modal Wizard)...
- Creating epic fn-5-user-dashboard
- Creating tasks from approach spec
- Cleaning up exploration worktrees
- Recording decision rationale

Done. Run /flux:work fn-5 to start building.
```

### Request Hybrid
```
> hybrid a+c

Describe the hybrid:
> "Modal for initial setup, side panel for editing"

Creating hybrid approach...
- Taking modal flow from A
- Taking persistent panel from C
- Scaffolding hybrid in new worktree
- Generating preview

[New comparison with hybrid included]
```

### Refine Approach
```
> refine b

What should change?
> "Make the inline expansion taller, add tabs for sections"

Updating approach B...
- Modifying scaffold
- Regenerating preview

[Updated comparison]
```

### Start Over
```
> discard

Discarding all approaches. Let's try different directions.

What other approaches should we consider?
> "What about a command palette approach like VS Code?"

Generating new approaches...
```

---

## Cleanup

After selection, cleanup exploration artifacts:

```bash
# Remove worktrees
git worktree remove .flux/explore/approach-a --force
git worktree remove .flux/explore/approach-b --force
git worktree remove .flux/explore/approach-c --force

# Delete exploration branches (optional, keep for reference)
# git branch -D explore/fn-N/approach-a

# Keep previews for documentation
# .flux/explore/previews/ → moved to epic spec
```

---

## fluxctl Commands

### Exploration Lifecycle

```bash
# Initialize exploration after approach selection (Step 6.5)
$FLOWCTL explore init --epic <epic-id> \
  --approaches "a:Modal wizard,b:Side panel,c:Full page" \
  --json

# Record worktree paths (Step 6.6)
$FLOWCTL explore set-worktrees --epic <epic-id> \
  --worktree "a:.flux/explore/approach-a" \
  --worktree "b:.flux/explore/approach-b" \
  --json

# Record scaffold results (Step 6.7)
$FLOWCTL explore set-results --epic <epic-id> \
  --result 'a:{"status":"success","effort":"M","files":["src/Modal.tsx"]}' \
  --result 'b:{"status":"partial","effort":"S"}' \
  --json

# Record previews (Step 6.8)
$FLOWCTL explore set-previews --epic <epic-id> \
  --preview "a:.flux/explore/previews/approach-a.png" \
  --preview "b:.flux/explore/previews/approach-b.html" \
  --json
```

### Status & Inspection

```bash
# List active explorations
$FLOWCTL explore list --json

# Get exploration status
$FLOWCTL explore status <epic-id> --json
# Returns: approaches, worktrees, results, previews, selected

# Show comparison data
$FLOWCTL explore compare <epic-id> --json
```

### Selection & Completion

```bash
# Pick winning approach (Step 6.10)
$FLOWCTL explore pick <epic-id> --approach a --json
# Marks approach as selected, prepares for merge

# Create hybrid from multiple approaches
$FLOWCTL explore hybrid <epic-id> \
  --from a,c \
  --spec "Modal flow from A, persistent panel from C" \
  --json

# Merge winner to main branch
$FLOWCTL explore merge <epic-id> --json
# Merges selected approach branch, creates epic/tasks from scaffold

# Cleanup after selection (Step 6.11)
$FLOWCTL explore cleanup <epic-id> --json
# Removes non-selected worktrees, optionally deletes branches
```

### Recovery

```bash
# Resume interrupted exploration
$FLOWCTL explore resume <epic-id> --json

# Discard exploration entirely
$FLOWCTL explore discard <epic-id> --json
# Removes all worktrees, branches, and exploration state
```

---

## Integration with v1 Scope

Explore mode extends v1, doesn't replace it:

```
/flux:scope <idea>              # v1: Single approach
/flux:scope <idea> --explore    # v2: Multiple approaches (default 3)
/flux:scope <idea> --explore 5  # v2: Specific number of approaches
```

The Problem Space phase is identical. Explore mode adds:
- Approach generation step (after problem statement)
- Parallel workspace scaffolding
- Preview generation
- Comparison and selection UX

---

## Constraints and Limits

| Constraint | Value | Reason |
|------------|-------|--------|
| Max approaches | 5 | More than 5 is overwhelming to evaluate |
| Scaffold timeout | 10 min | Prototypes, not production code |
| Preview timeout | 2 min | Just need a screenshot |
| Worktree disk | ~100MB each | Full repo copy |

---

## Error Handling

### Scaffold Fails
```
Approach B scaffolding failed: npm install error

Options:
1) Skip approach B, continue with A, C, D
2) Retry approach B
3) Abort exploration
```

### Preview Fails
```
Could not capture screenshot for Approach A (dev server not running)

Falling back to ASCII wireframe...
```

### User Timeout
```
No selection made in 30 minutes.

Exploration saved. Resume with:
/flux:scope --resume fn-N
```
