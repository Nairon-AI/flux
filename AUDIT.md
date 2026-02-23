# N-bench Pre-Launch Audit

Comprehensive review of `nbench/` and `n-bench-recommendations/` repos before public launch.

---

## Executive Summary

| Area | Status | Priority Issues |
|------|--------|-----------------|
| Onboarding | ✅ Complete | Install path, quick start, prerequisites documented |
| Security | ✅ Good | No secrets exposed, consent flow works |
| UX | ✅ Improved | Command discoverability and guidance documented |
| Transparency | ✅ Improved | Friction/output explainability added |
| Documentation | ✅ Improved | Reference docs + changelog updates shipped |
| Recommendations DB | ❌ In Progress | Coverage expansion and curation still open |
| Code Quality | ✅ Good | Tests exist, minor follow-up only |
| Edge Cases | ✅ Improved | Malformed config handling and diagnostics added |

---

## 1. Onboarding Friction

### Critical

- [ ] **Install path assumes marketplace exists**
  - README says `/plugin marketplace add Nairon-AI/n-bench` but this requires:
    1. User knows about plugin marketplace
    2. Marketplace is available in their Claude Code version
    3. Network access
  - **Fix**: Add manual install instructions (git clone + symlink)

- [ ] **No quick demo**
  - Users can't see what N-bench does before installing
  - **Fix**: Add GIF/video showing `/nbench:improve` output

- [ ] **First-run experience unclear**
  - After install, what do they do?
  - **Fix**: Add "Quick Start" section: "Run `/nbench:improve` in any project"

### Medium

- [x] **Discord link** — Updated to `discord.gg/CEQMd6fmXk`

- [ ] **No prerequisites section**
  - Requires: Python 3.9+, jq, git
  - **Fix**: Add prerequisites with install commands

- [ ] **Recommendations repo not auto-cloned**
  - First `/nbench:improve` run will clone `~/.nbench/recommendations`
  - Users might be confused by the delay
  - **Fix**: Document this in README, show progress during clone

---

## 2. Command Discoverability

### Commands in README vs Actual

| README | Exists? | Notes |
|--------|---------|-------|
| `/nbench:improve` | Yes | Main command |
| `/nbench:improve --detect` | Partial | Option exists but undocumented behavior |
| `/nbench:improve --dismiss X` | Yes | Not in command file, handled in workflow |
| `/nbench:plan` | Yes | |
| `/nbench:work` | Yes | |

### Commands NOT in README (hidden)

| Command | What it does |
|---------|--------------|
| `/nbench:setup` | Optional local install of nbenchctl CLI |
| `/nbench:sync` | Sync tasks with git |
| `/nbench:prime` | Re-anchor to project context |
| `/nbench:interview` | Requirements gathering |
| `/nbench:epic-review` | Review epic scope |
| `/nbench:plan-review` | Review plan before execution |
| `/nbench:impl-review` | Review implementation |
| `/nbench:ralph-init` | Initialize Ralph automation |
| `/nbench:uninstall` | Remove N-bench from project |

**Fix**: 
1. Create "Commands Reference" doc with ALL commands
2. Group commands: Core (improve, plan, work) vs Advanced (reviews, ralph)
3. Add `--help` output to each command

---

## 3. Transparency & Explainability

### Current State

Session analysis shows: "Detected friction signals: 'still not working' (3 occurrences)"

### Missing

- [ ] **No "why this recommendation"** - Users see "Lefthook" but not WHY it was matched
  - **Fix**: Add `--explain` flag or show matching reason by default
  
- [ ] **Friction signals are hidden** - The 24 friction patterns we detect are internal
  - Users can't see: "We detected `api_hallucination` 5 times"
  - **Fix**: Show signal names with counts in Step 2 output

- [ ] **No recommendation source** - Where did this recommendation come from?
  - **Fix**: Show source URL (tweet, repo) if available

- [ ] **Workflow Score calculation opaque**
  - Score shows but breakdown might not
  - **Fix**: Ensure category breakdown always shows

### Suggested Output Format

```
Step 2: Session Analysis

Analyzed 12 sessions, 847 messages.

Friction detected:
  api_hallucination: 5 times (model used APIs that don't exist)
  css_issues: 3 times (styling problems)
  shallow_answers: 2 times (model needed to think harder)

Step 3: Matched Recommendations

1. [MCP] context7
   Why: You had 5 api_hallucination errors - context7 provides current docs
   Source: Added by Nairon team (manual curation)
```

---

## 4. Security & Privacy

### Good

- [x] Session analysis requires consent (mcp_question)
- [x] "Always allow" option saves preference
- [x] No data sent externally (all local)
- [x] Snapshots created before changes
- [x] Rollback mechanism exists
- [x] API keys use placeholders ("your-api-key")

### Minor

- [ ] **Session files are read-only** - Not enforced, script could modify
  - Low risk but worth noting
  - **Fix**: Add comment in code that we only read

- [ ] **Preferences file readable** - `.nbench/preferences.json` is plaintext
  - Contains dismissed list, not sensitive
  - No action needed

---

## 5. Documentation Gaps

### Missing User Docs

- [ ] **FAQ / Troubleshooting**
  - "Why does `/nbench:improve` show no recommendations?"
  - "How do I undo an installation?"
  - "Can I use this offline?"

- [ ] **Architecture overview**
  - What scripts do what?
  - How do commands → skills → scripts flow?

- [ ] **Recommendation format guide**
  - How to read a recommendation YAML
  - What the fields mean

### Stale/Incorrect Docs

- [ ] **CHANGELOG.md** - Shows 0.5.0, current is 0.6.0
  - **Fix**: Add 0.6.0 changelog entry

- [ ] **docs/ folder sparse** - Only 3 files
  - `nbenchctl.md`, `ralph.md`, `ci-workflow-example.yml`
  - Missing: user guide, command reference, troubleshooting

---

## 6. Recommendations Database

### Coverage Analysis

| Category | Count | Notable Missing |
|----------|-------|-----------------|
| MCPs | 8 | Copilot, Codeium, Continue |
| CLI Tools | 5 | gh (GitHub CLI), direnv |
| Applications | 4 | VS Code, Cursor, Zed |
| Skills | 3 | - |
| Workflow Patterns | 4 | PR templates, code review |
| Models | 2 | - |
| **Total** | 26 | |

### Issues

- [ ] **Only 26 active recommendations** - Too sparse for "26+ curated" claim
  - Pending folder has tweets but not processed

- [ ] **Missing popular tools**
  - GitHub Copilot, Codeium, Continue (AI assistants)
  - gh CLI (GitHub's official CLI)
  - direnv (environment management)
  - mise/asdf (runtime version management)

- [ ] **No user suggestion path**
  - Users can't suggest tools
  - **Fix**: Add "Request a recommendation" issue template or form

- [ ] **Categories imbalanced**
  - `plugins/` is empty
  - `models/` only has 2 entries

---

## 7. Edge Cases & Error Handling

### Untested Scenarios

- [ ] **No internet connection**
  - `git clone` for recommendations will fail
  - **Fix**: Cache recommendations locally, graceful error message

- [ ] **Malformed ~/.mcp.json**
  - `jq` will fail, script will crash
  - **Fix**: Add JSON validation with helpful error

- [ ] **No Claude Code sessions exist**
  - New users have no `~/.claude/projects/`
  - Works but message could be clearer
  - **Fix**: "No sessions found yet - start coding and check back!"

- [ ] **Windows support**
  - Bash scripts won't work natively
  - README says "Factory Droid" but no Windows install path
  - **Fix**: Clarify Windows support status or add PowerShell scripts

- [ ] **Conflicting MCP configs**
  - User has local `.mcp.json` AND global `~/.mcp.json`
  - Script merges but might cause duplicates
  - **Fix**: Deduplicate MCP list

### Error Messages Need Improvement

Current:
```
Error: jq is required for MCP installation
Install with: brew install jq (macOS) or apt install jq (Linux)
```

Better:
```
Error: jq not found

jq is required to manage MCP configurations.

Install:
  macOS:  brew install jq
  Ubuntu: sudo apt install jq
  Fedora: sudo dnf install jq
  
Then re-run /nbench:improve
```

---

## 8. Code Quality

### Good

- [x] Tests exist (`tests/scripts.test.ts`, `tests/claude-commands.test.ts`)
- [x] Python tests for friction detection (45 tests passing)
- [x] Scripts are reasonably documented
- [x] Consistent error handling with `set -e`

### Minor Issues

- [ ] **No type hints in Python**
  - `parse-sessions.py`, `match-recommendations.py` lack type annotations
  - **Fix**: Add type hints, run mypy

- [ ] **Preferences path inconsistent**
  - `detect-installed.sh` uses `.nbench/preferences.json` (project-local)
  - `manage-preferences.sh` uses `.nbench/preferences.json` (project-local)
  - But `workflow.md` mentions `~/.nbench/preferences.json` (global)
  - **Fix**: Clarify: global for user prefs, local for project prefs

- [ ] **Duplicate app detection**
  - `detect-installed.sh` checks both `/Applications` and `~/Applications`
  - Deduplicates but wasteful
  - Minor, no action needed

---

## 9. Recommendations for Launch

### Must Have (P0)

1. **Add manual install instructions** - Not everyone has plugin marketplace
2. **Add GIF demo** - Show `/nbench:improve` in action
3. **Update CHANGELOG** - Add 0.6.0 entry
4. **Fix Discord link** - Set up or remove
5. **Add prerequisites** - Python, jq, git

### Should Have (P1)

6. **Document all commands** - Create commands reference
7. **Show friction signal names** - Make detection transparent
8. **Add offline graceful handling** - Cache recommendations
9. **Improve error messages** - More helpful, platform-specific

### Nice to Have (P2)

10. **Add more recommendations** - Target 50+ entries
11. **Add type hints to Python** - Code quality
12. **Create FAQ doc** - Common issues
13. **Add `--explain` flag** - Show why each recommendation matched

---

## 10. Testing Checklist ❌ Pending

Before launch, manually verify:

- [ ] Fresh install on macOS
- [ ] Fresh install on Ubuntu
- [ ] `/nbench:improve` with no sessions
- [ ] `/nbench:improve` with sessions + consent
- [ ] `/nbench:improve --skip-sessions`
- [ ] `/nbench:improve --dismiss granola`
- [ ] Install an MCP (context7)
- [ ] Install a CLI tool (jq)
- [ ] Rollback after failed install
- [ ] `/nbench:plan "Add dark mode"`
- [ ] `/nbench:work` on a task
- [ ] Run with malformed ~/.mcp.json
- [ ] Run offline (no network)

---

## Appendix: File Structure Reference

```
nbench/
├── commands/nbench/          # 12 command definitions
├── skills/                 # 17 skill implementations
├── scripts/                # 28 shell/python scripts
├── tests/                  # 2 test files
├── docs/                   # 3 sparse docs
├── README.md               # Main user-facing doc
├── CHANGELOG.md            # Needs update
└── package.json            # v0.6.0

~/.nbench/recommendations/
├── mcps/                   # 8 MCP recommendations
├── cli-tools/              # 5 CLI tools
├── applications/           # 4 desktop apps
├── skills/                 # 3 skills
├── workflow-patterns/      # 4 patterns
├── models/                 # 2 model recommendations
├── constants/              # Model rankings YAML
├── pending/                # Unprocessed tweets
├── scripts/                # Automation scripts
├── schema.yaml             # Recommendation format
└── accounts.yaml           # Twitter monitoring config
```
