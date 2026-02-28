# Flux Contributor Feedback Loop

Set up a fast feedback loop for testing and improving Flux.

## For Flux Developers/Testers

Add this to your project's `AGENTS.md` or `CLAUDE.md` when testing Flux:

```markdown
## Flux Testing Mode

This project is being used to test the Flux plugin.

**When you encounter a Flux issue:**

1. Determine if it's a genuine Flux bug (not user error)
2. If genuine bug, immediately create a PR to fix it:
   - Clone Nairon-AI/flux to /tmp/flux-fix-<timestamp>
   - Create branch: fix/<issue-slug>
   - Make the minimal fix
   - Push and create PR with `gh pr create`
3. Report the PR URL so it can be reviewed and merged
4. After merge, upgrade: `/plugin marketplace update nairon-flux`

**What counts as a Flux bug:**
- Command fails unexpectedly
- Skill has incorrect instructions
- Missing file or broken path
- Documentation doesn't match behavior

**What's NOT a Flux bug:**
- User provides wrong arguments
- Prerequisites not installed
- Unrelated project issues
```

## Quick Commands

```bash
# Explicitly report an issue
/flux:contribute "Description of the issue"

# After PR is merged, upgrade
/plugin marketplace update nairon-flux
```

## Workflow Diagram

```
┌─────────────────┐
│ Test Flux       │
│ in fresh repo   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Encounter issue │────▶│ Is it a Flux    │
└─────────────────┘     │ bug?            │
                        └────────┬────────┘
                                 │
                    ┌────────────┴────────────┐
                    ▼                         ▼
              ┌──────────┐              ┌──────────┐
              │ Yes      │              │ No       │
              └────┬─────┘              └────┬─────┘
                   │                         │
                   ▼                         ▼
         ┌─────────────────┐         ┌─────────────────┐
         │ Create PR       │         │ Fix usage or    │
         │ /flux:contribute│         │ explain solution│
         └────────┬────────┘         └─────────────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Review & Merge  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Upgrade plugin  │
         │ /plugin update  │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │ Fixed!          │
         └─────────────────┘
```

## For External Contributors

If you don't have write access to Nairon-AI/flux:

1. The `/flux:contribute` command will fork the repo
2. Create PR from your fork
3. Maintainers review and merge

## Environment Setup

Ensure `gh` CLI is authenticated:
```bash
gh auth status
# If not logged in:
gh auth login
```
