# Autonomous Skill-Building Pipeline

This is the detailed execution pipeline for `flux-skill-builder`. Execute all 4 phases sequentially without human gates.

---

## Phase 1: Research (~2-3 min)

The interactive Skill Builder asks the user 6+ questions. The autonomous version answers them itself by researching.

### Step 1.1: Parse Intent

Extract from the user's input:
- **Core capability**: What should the skill enable the agent to do?
- **Target domain**: What area of the codebase/workflow does this touch?
- **Implicit quality bar**: Is the user describing a quick helper or a production workflow?

### Step 1.2: Scan for Existing Skills

Check for overlap before creating anything new:

```bash
# Check user-installed skills
ls ~/.codex/skills/ 2>/dev/null
ls ~/.claude/skills/ 2>/dev/null
ls .codex/skills/ 2>/dev/null
ls .claude/skills/ 2>/dev/null

# Check Flux built-in skills
ls "$PLUGIN_ROOT/skills/" 2>/dev/null
```

If a skill with overlapping purpose exists:
- Tell the user what exists and ask if they want to extend it or create a separate skill.
- This is the ONE place where you may pause for user input.

### Step 1.3: Research the Problem Space

Answer these questions autonomously through codebase analysis:

| Question | How to Answer |
|----------|--------------|
| What does the default agent get wrong today? | Try the task mentally. What would the default agent do? Where would it fail? Scan brain vault for related corrections. |
| What are 2-3 concrete use cases? | Infer from the description + codebase structure. What files/patterns would trigger this? |
| What tools/dependencies are needed? | Scan the repo for relevant configs, packages, scripts. Check if MCP servers are involved. |
| What are the edge cases? | Think about: empty inputs, large inputs, missing dependencies, permission errors, concurrent execution. |
| What does success look like? | Infer from the domain. A data skill produces reports. A deploy skill produces deployed artifacts. A review skill produces findings. |

### Step 1.4: Classify Category

Determine which category fits best. Do NOT ask the user — infer from the research.

| # | Category | Signal |
|---|----------|--------|
| 1 | Library & API Reference | Skill teaches correct usage of a library/CLI/SDK |
| 2 | Product Verification | Skill tests or verifies code is working |
| 3 | Data Fetching & Analysis | Skill connects to data stacks, runs queries |
| 4 | Business Process & Automation | Skill automates a repetitive workflow |
| 5 | Code Scaffolding & Templates | Skill generates boilerplate for a framework |
| 6 | Code Quality & Review | Skill enforces quality or reviews code |
| 7 | CI/CD & Deployment | Skill handles PR/deploy/release flows |
| 8 | Runbooks | Skill investigates symptoms, produces structured reports |
| 9 | Infrastructure Operations | Skill handles routine ops with guardrails |

If the skill straddles categories, narrow the scope to the higher-value one.

### Step 1.5: Identify Failure Modes

This is the most important research step. Analyze how Claude fails at this task today:

1. **Check brain vault** for related corrections:
   ```bash
   ls .flux/brain/ 2>/dev/null
   ```
   Scan for notes related to the skill's domain.

2. **Check git history** for related bugs/fixes:
   ```bash
   git log --oneline -20 --grep="<relevant keywords>"
   ```

3. **Think adversarially**: What would a naive Claude do wrong? Common failure patterns:
   - Uses outdated API patterns
   - Ignores repo-specific conventions
   - Skips error handling for the happy path
   - Produces output in the wrong format
   - Misses permissions/auth requirements
   - Over-engineers when simplicity is needed

Every failure mode identified here becomes a gotcha in the final skill.

---

## Phase 2: Draft (~3-5 min)

### Step 2.1: Design the File Structure

Choose structure based on complexity:

**Simple skill** (< 200 lines of instruction):
```
.codex/skills/<name>/
└── SKILL.md
```

**Medium skill** (200-400 lines of instruction):
```
.codex/skills/<name>/
├── SKILL.md                   (overview, workflow outline, gotchas)
└── workflow.md                (detailed step-by-step)
```

**Complex skill** (400+ lines of instruction):
```
.codex/skills/<name>/
├── SKILL.md                   (overview, routing, gotchas)
├── workflow.md                (main execution steps)
├── examples.md                (concrete input/output examples)
└── references/                (API docs, templates, etc.)
```

If the skill involves deterministic checks, add:
```
├── scripts/
│   └── validate.sh   (or .py)
```

### Step 2.2: Write the Frontmatter

The description is the most critical field. It determines whether the skill ever fires.

**Template:**
```yaml
---
name: <kebab-case-name>
description: >
  <WHAT it does — 1 sentence>.
  <WHEN to use it — "Use when..." with 3+ specific trigger phrases>.
  <Negative triggers — "Do NOT use for..." to prevent misfires>.
user-invocable: <true if callable via /flux:command, false if internal>
---
```

**Description quality rules:**
- Include the verbs users would actually say ("deploy", "review", "migrate", "set up")
- Include the nouns users would mention ("PR", "database", "tests", "API")
- Be slightly pushy: "Use this skill whenever the user mentions X, Y, or Z, even if they don't explicitly ask for it"
- Add negative triggers for adjacent skills that could misfire
- Stay under 1024 characters

### Step 2.3: Write the Body

Follow this structure (adapt sections as needed):

```markdown
# [Skill Name]

[1-3 sentences: what this does and why it exists.]

## Session Phase Tracking
[Standard fluxctl phase set/reset block]

## Input
Full request: $ARGUMENTS
[What formats are accepted, what to do if empty]

## Workflow
[Step-by-step instructions OR link to workflow.md]
[Each step: what to do, what success looks like, what to do on failure]

## Gotchas
[Every failure mode from Phase 1.5, formatted as:]
- **[Failure mode]**: [Why it happens] → [What to do instead]

## Update Check (End of Command)
[Standard version-check block]
```

**Writing rules:**
- Use imperative form: "Run the script" not "You should run the script"
- Explain the WHY, not just the WHAT. "Check permissions first because the deploy script silently succeeds with wrong creds" beats "Check permissions first"
- Do not state the obvious. Skip "read the file first" or "make sure the function works." Spend tokens on non-obvious constraints.
- Include error handling for each major step. What does the agent do when the API returns 500? When the file doesn't exist? When the test fails?
- Reference supporting files with clear guidance: "Read workflow.md for the detailed step-by-step. Read it now if this is your first time running this skill."

### Step 2.4: Write Supporting Files

For each supporting file:
- Keep it focused on one concern
- Include a brief header explaining what this file covers and when to read it
- Link back to SKILL.md for context

### Step 2.5: Write Scripts (if applicable)

If the skill involves any of these, write a script instead of prose instructions:
- Validation checks (does the output match a schema?)
- File generation from templates
- Environment verification (are dependencies installed?)
- Data transformation (parse X into Y format)

Scripts go in `scripts/` and must be executable and tested.

---

## Phase 3: Validate (~1 min)

### Step 3.1: Run the Validator

```bash
python3 "$PLUGIN_ROOT/scripts/validate_skills.py" .codex/skills/<name>/  # loose fallback path
```

**If errors**: Fix them automatically. Common fixes:
- `frontmatter.name doesn't match folder` → fix the name field
- `SKILL.md exceeds 500 lines` → move content to supporting files
- `missing YAML frontmatter` → add it

**If warnings**: Fix these too unless there's a good reason not to:
- `description not trigger-oriented` → add "Use when..." language
- `missing Gotchas section` → add one (research Phase 1.5 should have produced failure modes)
- `long skill has no supporting files` → split into progressive disclosure

### Step 3.2: Self-Review Checklist

Before delivering, verify:

**Description:**
- [ ] Includes WHAT, WHEN, and key capabilities
- [ ] Has 3+ specific trigger phrases a real user would say
- [ ] Slightly pushy to combat undertriggering
- [ ] Has negative triggers for adjacent skills
- [ ] Under 1024 characters
- [ ] No XML tags

**Body:**
- [ ] Instructions are specific and actionable (exact commands, not vague guidance)
- [ ] The WHY is explained, not just the WHAT
- [ ] Error handling for each major step
- [ ] Progressive disclosure used (SKILL.md under 350 lines ideal, 500 hard max)
- [ ] Examples use realistic trigger phrases and real outputs
- [ ] Gotchas section has substantive, specific entries (not generic advice)

**Anti-patterns to catch:**
- [ ] No obvious information Claude already knows (remove it)
- [ ] No over-rigid instructions that prevent adaptation
- [ ] No vague language ("validate things properly", "handle errors appropriately")
- [ ] No keyword-stuffed description that reads like SEO spam
- [ ] No missing edge case handling

Fix any issues found. Do not present known problems to the user.

---

## Phase 4: Deliver (~1 min)

### Step 4.1: Install (always project-scoped)

Skills are always installed at project scope. Do not prompt the user for install location.

```bash
mkdir -p .codex/skills/<name>/
# Write the generated skill files into .codex/skills/<name>/ first, then install them
# into the current project:
"$PLUGIN_ROOT/scripts/install-skill.sh" "<name>" ".codex/skills/<name>" project
```

### Step 4.2: Generate Trigger Report

Present a summary showing the skill is ready:

```
## Skill Created: <name>

**Category**: <category from Phase 1.4>
**Location**: `.codex/skills/<name>/` (mirror to `.claude/skills/<name>/` when the repo supports Claude)
**Files**: <list of files created>

### What it does
<1-2 sentence summary>

### Trigger phrases (should activate)
- "<phrase 1>"
- "<phrase 2>"
- "<phrase 3>"

### Anti-triggers (should NOT activate)
- "<near-miss phrase 1>"
- "<near-miss phrase 2>"

### Failure modes captured
- <gotcha 1>
- <gotcha 2>
- <gotcha 3>
```

### Step 4.3: Offer Next Steps

```
**Next steps:**
- Test it: try saying one of the trigger phrases in a new conversation
- Edit it: the skill is source code in <path> — modify freely
- Validate it: `python3 scripts/validate_skills.py <path>`
```
