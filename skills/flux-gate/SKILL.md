---
name: flux-gate
description: Validate a staging deployment after merge and promote to production. Runs browser QA or manual review against the staging URL, then creates a promotion PR (staging → production). Triggers on /flux:gate.
user-invocable: true
---

# Staging Gate — Validate & Promote

Validates that a staging deployment is healthy after a PR merge, then creates a promotion PR to production. This is the bridge between "code is merged to staging" and "code ships to production."

## Prerequisites

- `environments.staging` must be configured in `.flux/config.json` (set up via `/flux:setup`)
- A PR must have been recently merged to the staging branch

## Workflow

### Step 1: Read environment config

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
STAGING_BRANCH=$("${PLUGIN_ROOT}/scripts/fluxctl" config get environments.staging.branch --json 2>/dev/null | jq -r '.value // empty')
STAGING_URL=$("${PLUGIN_ROOT}/scripts/fluxctl" config get environments.staging.url --json 2>/dev/null | jq -r '.value // empty')
PROD_BRANCH=$("${PLUGIN_ROOT}/scripts/fluxctl" config get environments.production.branch --json 2>/dev/null | jq -r '.value // empty')
PLATFORM=$("${PLUGIN_ROOT}/scripts/fluxctl" config get environments.platform --json 2>/dev/null | jq -r '.value // empty')
INFRA_CLI=$("${PLUGIN_ROOT}/scripts/fluxctl" config get infrastructure.cli --json 2>/dev/null | jq -r '.value // empty')
```

If `STAGING_BRANCH` or `STAGING_URL` is empty, tell the user:
```
No staging environment configured. Run /flux:setup to set up environments.
```
Stop here.

### Step 2: Verify staging deployment is live

First, check if the deployment is complete (for platforms with CLIs):

```bash
# Vercel
vercel ls --json 2>/dev/null | jq '[.deployments[] | select(.target=="production" and .state=="READY")] | .[0]'

# Railway
railway status 2>/dev/null

# Netlify
netlify api getSite --data '{}' 2>/dev/null | jq '.published_deploy.state'

# Generic fallback
curl -s -o /dev/null -w "%{http_code}" "$STAGING_URL"
```

If the staging URL returns a non-200 status or the platform reports the deployment isn't ready:
- Wait and retry (up to 5 minutes, polling every 30 seconds)
- If still not live after 5 minutes, report failure and stop

Tell the user:
```
Staging deployment is live at {STAGING_URL} ✓
```

### Step 3: Choose testing method

Ask the user how they want to validate staging:

```
Staging is live. How do you want to validate?

1. Agent Browser — automated browser QA against {STAGING_URL}
2. Manual review — I'll show you what to check, you test and report back
```

Use `AskUserQuestion` for this.

### Step 4a: Agent Browser QA (if chosen)

Check if agent-browser is available:
```bash
command -v agent-browser >/dev/null 2>&1 && echo "available" || echo "not found"
```

If not available, tell the user and fall back to manual review (Step 4b).

If available, look for the Browser QA checklist from the most recently completed epic:
```bash
# Find the most recent epic's QA task
LATEST_EPIC=$("${PLUGIN_ROOT}/scripts/fluxctl" list-epics --json 2>/dev/null | jq -r '.[0].id // empty')
```

If a QA checklist exists, run each criterion against the staging URL using agent-browser:

```bash
agent-browser open "$STAGING_URL"
agent-browser wait --load networkidle
# Run through each acceptance criterion from the QA checklist
# Take screenshots as evidence
agent-browser screenshot "/tmp/staging-qa-$(date +%s).png"
```

After testing, report results:
- **All pass**: Continue to Step 5
- **Failures found**: List what failed, ask user if they want to:
  1. Create fix tasks and address issues (new PR to staging)
  2. Proceed anyway (user accepts the issues)
  3. Abort promotion

### Step 4b: Manual Review (if chosen)

Present the QA checklist to the user (or a general checklist if none exists):

```
Please review staging at: {STAGING_URL}

Checklist:
{QA checklist items from epic, or generic items:}
- [ ] App loads without errors
- [ ] Core user flows work (login, main actions, etc.)
- [ ] No console errors in browser dev tools
- [ ] New feature/fix from the merged PR works as expected
- [ ] No visual regressions on key pages

Report back with what you found — "all good" or describe any issues.
```

Wait for the user's response. If issues reported, same options as 4a failures.

### Step 5: Run e2e tests against staging (if available)

Check if the project has e2e tests:
```bash
# Check package.json for e2e/test:e2e scripts
E2E_SCRIPT=$(jq -r '.scripts["test:e2e"] // .scripts["e2e"] // empty' package.json 2>/dev/null)
```

If available, run them against the staging URL:
```bash
BASE_URL="$STAGING_URL" npm run test:e2e 2>&1
# Or if using Playwright:
PLAYWRIGHT_BASE_URL="$STAGING_URL" npx playwright test 2>&1
```

Report results. Failures don't block promotion — the user decides.

### Step 6: Create promotion PR

If validation passes (or user chose to proceed):

```bash
# Ensure we have the latest staging and production branches
git fetch origin "$STAGING_BRANCH" "$PROD_BRANCH"

# Check if there are commits to promote
COMMITS=$(git log "origin/$PROD_BRANCH..origin/$STAGING_BRANCH" --oneline 2>/dev/null)
if [ -z "$COMMITS" ]; then
  echo "No new commits to promote. Staging and production are in sync."
  # Stop here
fi
```

Create the promotion PR:
```bash
gh pr create \
  --base "$PROD_BRANCH" \
  --head "$STAGING_BRANCH" \
  --title "promote: staging → production" \
  --body "$(cat <<'EOF'
## Staging Validation

**Staging URL**: {STAGING_URL}
**Validation method**: {Agent Browser / Manual review}
**Result**: All checks passed ✓

### Changes included
{list of commits being promoted}

### Evidence
{screenshots or test results if available}

---
Merge this PR to deploy to production.
EOF
)"
```

Tell the user:
```
Promotion PR created: {PR_URL}

Merge when ready to deploy to production. Flux will not auto-merge to production.
```

## Update Check (End of Command)

**ALWAYS run at the very end of command execution:**

```bash
PLUGIN_ROOT="${DROID_PLUGIN_ROOT:-${CLAUDE_PLUGIN_ROOT}}"
CURRENT_VERSION=$(jq -r '.version' "${PLUGIN_ROOT}/.claude-plugin/plugin.json" 2>/dev/null)
MARKETPLACE_VERSION=$(jq -r '.plugins[0].version' "${PLUGIN_ROOT}/.claude-plugin/marketplace.json" 2>/dev/null)
if [ "$CURRENT_VERSION" != "$MARKETPLACE_VERSION" ] && [ -n "$MARKETPLACE_VERSION" ]; then
  echo "Update available: v${CURRENT_VERSION} → v${MARKETPLACE_VERSION}. Run /flux:upgrade"
fi
```
