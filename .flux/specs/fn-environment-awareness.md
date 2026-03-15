# Environment Awareness — Plan

> **Goal**: Make Flux aware of deployment infrastructure (staging, production, preview environments) so it can target PRs at the right branch, run browser QA against staging URLs after merge, and agentically interact with infrastructure via CLIs/MCPs.

---

## Why This Matters

Without environment awareness, Flux assumes a single-branch workflow: feature → main → done. But most production teams have:

- **Staging environments** — where code is tested before production
- **Preview environments** — per-PR previews (Vercel, Netlify, Railway)
- **Multiple deployment targets** — AWS, Vercel, Railway, Fly.io, self-hosted

Flux can't help with deployment testing, staging validation, or production monitoring if it doesn't know these exist. And it creates PRs against `main` when the team actually wants PRs against `staging`.

---

## The Full Picture

```
┌──────────────────────────────────────────────────────────────┐
│                    /flux:setup (new questions)                │
│                                                              │
│  1. Auto-detect deployment platform from codebase            │
│     (vercel.json? railway.toml? fly.toml? Dockerfile?        │
│      serverless.yml? netlify.toml? .github/workflows/deploy?)│
│                                                              │
│  2. Confirm: "Looks like you deploy to Vercel. Right?"       │
│     Install CLI/MCP if missing. Guide auth.                  │
│     Verify: "vercel whoami" or equivalent.                   │
│                                                              │
│  3. Query platform for environments (via CLI):               │
│     vercel ls / railway environment ls / netlify env:list    │
│     Discover staging, production, preview URLs automatically │
│                                                              │
│  4. Present findings:                                        │
│     "Found 2 environments:                                   │
│       • staging → staging.myapp.com (branch: staging)        │
│       • production → myapp.com (branch: main)                │
│       • preview URLs: enabled (auto per PR)                  │
│      Correct?"                                               │
│                                                              │
│  5. User confirms or corrects. Only ask manually if CLI      │
│     query returned nothing or auth failed.                   │
│                                                              │
│  6. Detect git branch → environment mapping:                 │
│     Check CI deploy workflows, platform config, or ask.      │
└──────────────────────────────────────────────────────────────┘
```

### Config stored in `.flux/config.json`

```json
{
  "environments": {
    "platform": "vercel",
    "staging": {
      "branch": "staging",
      "url": "https://staging.myapp.com",
      "auto_deploy": true
    },
    "production": {
      "branch": "main",
      "url": "https://myapp.com",
      "auto_deploy": true
    },
    "preview": {
      "enabled": true,
      "provider": "vercel",
      "url_pattern": "https://{branch}--myapp.vercel.app"
    }
  },
  "infrastructure": {
    "cli": "vercel",
    "mcp": null,
    "authenticated": true
  }
}
```

---

## How It Changes the Workflow

### 1. `/flux:setup` — New "Infrastructure" section

**Auto-detection** (runs before asking questions):

```bash
# Check for deployment platform markers
[ -f vercel.json ]        && PLATFORM="vercel"
[ -f railway.toml ]       && PLATFORM="railway"
[ -f fly.toml ]           && PLATFORM="fly"
[ -f netlify.toml ]       && PLATFORM="netlify"
[ -f serverless.yml ]     && PLATFORM="aws-serverless"
[ -f terraform/ ]         && PLATFORM="aws-terraform"
# Cloudflare — distinguish Pages vs Workers
if [ -f wrangler.toml ] || [ -f wrangler.json ] || [ -f wrangler.jsonc ]; then
  grep -q 'pages_build_output_dir' wrangler.toml wrangler.json wrangler.jsonc 2>/dev/null \
    && PLATFORM="cloudflare-pages" || PLATFORM="cloudflare-workers"
fi
[ -z "$PLATFORM" ] && [ -f _routes.json ] && PLATFORM="cloudflare-pages"
[ -f docker-compose.yml ] && PLATFORM="docker"
[ -f Dockerfile ]         && PLATFORM="docker"
# Check GitHub Actions for deploy workflows
grep -rl "aws-actions\|vercel/action\|railway\|cloudflare/wrangler-action\|cloudflare/pages-action" .github/workflows/ 2>/dev/null
# Check env files for cloud URLs
grep -r "VERCEL\|RAILWAY\|AWS_\|CF_API_TOKEN\|CLOUDFLARE_" .env* 2>/dev/null
```

**Flow** (detect first, ask only what's missing):

1. "Detected **Vercel** deployment. Is that correct?" → confirm or override
2. Install CLI if missing (`npm i -g vercel`), guide auth (`vercel login`), verify (`vercel whoami`)
3. Query platform via CLI for environments, URLs, and branch mappings:
   ```bash
   # Vercel — list projects and their domains
   vercel project ls --json 2>/dev/null
   vercel domains ls --json 2>/dev/null
   # Railway — list environments
   railway environment ls 2>/dev/null
   # Netlify — list deploy contexts and site info
   netlify api getSite --data '{}' 2>/dev/null | jq '.ssl_url, .deploy_url'
   # Fly.io — list apps (staging is often a separate app)
   fly apps list --json 2>/dev/null
   # Cloudflare Pages — list projects and branch deploys
   wrangler pages project list 2>/dev/null
   # Cloudflare Workers — list deployments and named environments
   wrangler deployments list 2>/dev/null
   ```
4. Present findings: "Found staging (staging.myapp.com, branch: staging) and production (myapp.com, branch: main). Preview URLs enabled. Correct?"
5. User confirms or corrects
6. **Manual fallback** — only if CLI query fails or returns nothing:
   - "Do you have a staging environment?" → branch name, URL
   - "Production URL?"
   - "Preview URLs for PRs?"

**Fresh project (no infra yet)**:
- Detect this case: no deployment markers, no env files, no CI deploy workflows
- Tell user: "No deployment infrastructure detected — that's fine. Flux will work with your local setup. When you add deployment later, run `/flux:setup` again to configure environments."
- Skip all environment questions

### 2. `/flux:work` — PR targets staging branch

When `environments.staging` is configured:
- The Submit phase creates PRs against `staging` branch instead of `main`
- Commit messages and PR descriptions stay the same
- The PR template notes: "This PR targets staging. After merge + staging validation, promote to production."

When no staging is configured:
- Current behavior (PR against `main`)

### 3. `/flux:gate` — New skill: staging validation

**Trigger**: User runs `/flux:gate` after a staging PR is merged, OR a GitHub Action triggers it automatically.

**What it does**:

```
1. Verify staging deployment is live
   → Hit staging URL, check for 200 response
   → If platform CLI available: check deployment status
     (e.g., `vercel ls --scope staging` or `railway status`)

2. Run browser QA against staging URL
   → Re-use the Browser QA checklist from epic-review
   → But test against staging URL instead of localhost
   → agent-browser navigates staging URL, runs all acceptance criteria

3. Run smoke tests
   → If the project has e2e tests, run them against staging URL
   → BASE_URL=https://staging.myapp.com npm run test:e2e

4. Report results
   → All pass: "Staging validated. Ready to promote to production."
     Auto-create PR: staging → main (production)
   → Failures: Create fix tasks, user decides whether to fix or revert

5. Production promotion (if staging passes)
   → Create PR: staging → main
   → PR body includes staging test evidence (screenshots, test results)
   → User merges when ready (Flux doesn't auto-merge to production)
```

### 4. Preview environment integration

When `environments.preview.enabled`:
- After creating a PR, wait for preview URL to be available
- Check platform for preview deployment status:
  ```bash
  # Vercel
  vercel ls --meta pullRequestId=$PR_NUMBER 2>&1
  # Netlify
  netlify api listSiteDeploys --data '{"site_id":"..."}' | jq '.[0].deploy_ssl_url'
  # Cloudflare Pages — branch deploy preview URLs (always on)
  # URL pattern: https://{branch}.{project-name}.pages.dev
  wrangler pages deployment list --project-name "$PROJECT_NAME" 2>/dev/null | head -3
  # Note: Cloudflare Workers don't have automatic preview URLs — they use [env.*] named environments
  ```
- Run browser QA against preview URL (lightweight smoke test)
- Comment preview QA results on the PR

### 5. GitHub Action for auto-staging-test

Template workflow that Flux installs during setup:

```yaml
name: Staging Gate
on:
  push:
    branches: [staging]

jobs:
  gate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Wait for deployment
        run: |
          # Poll staging URL until 200 or timeout
          for i in $(seq 1 30); do
            STATUS=$(curl -s -o /dev/null -w "%{http_code}" ${{ vars.STAGING_URL }})
            [ "$STATUS" = "200" ] && exit 0
            sleep 10
          done
          exit 1
      - name: Run e2e tests against staging
        run: BASE_URL=${{ vars.STAGING_URL }} npm run test:e2e
      - name: Create production PR
        if: success()
        run: |
          gh pr create --base main --head staging \
            --title "promote: staging → production" \
            --body "Staging tests passed. Ready for production deployment."
```

---

## Platform Support Matrix

| Platform | Auto-detect | CLI | MCP | Preview URLs | Auth command |
|----------|------------|-----|-----|-------------|-------------|
| Vercel | `vercel.json` | `vercel` | — | Yes (auto) | `vercel login` |
| Railway | `railway.toml` | `railway` | `railway-mcp` | Yes (via CLI) | `railway login` |
| Netlify | `netlify.toml` | `netlify` | — | Yes (auto) | `netlify login` |
| Fly.io | `fly.toml` | `fly` | — | No | `fly auth login` |
| AWS | `serverless.yml`, `terraform/` | `aws` | `aws-mcp` | No | `aws configure` |
| Docker/self-hosted | `Dockerfile`, `docker-compose.yml` | `docker` | — | No | N/A |
| Render | `render.yaml` | `render` | — | Yes (via API) | `render login` |
| Cloudflare Pages | `wrangler.{toml,json,jsonc}` + `pages_build_output_dir`, `_routes.json` | `wrangler` | — | Yes (branch deploys: `{branch}.{project}.pages.dev`) | `wrangler login` |
| Cloudflare Workers | `wrangler.{toml,json,jsonc}` (no `pages_build_output_dir`) | `wrangler` | — | No (use `[env.*]` named environments) | `wrangler login` |

---

## Implementation Tasks

### Task 1: Add environment detection to `/flux:setup`
- Add auto-detection script (`scripts/detect-environment.sh`)
- Add environment questions to setup workflow (after existing questions)
- Store config in `.flux/config.json` under `environments` key
- Install relevant CLI/MCP and verify auth
- Handle fresh-project case (no infra)

### Task 2: Update `/flux:work` Submit phase
- Read `environments.staging.branch` from config
- If set, PR base branch = staging branch (not main)
- If not set, current behavior (PR against main)
- Add note in PR body about staging workflow

### Task 3: Create `/flux:gate` skill
- New skill at `skills/flux-gate/`
- Verify staging deployment is live
- Run browser QA against staging URL
- Run e2e tests if available
- Report results and optionally create promotion PR (staging → production)

### Task 4: Add preview environment support
- Detect preview URL after PR creation
- Run lightweight smoke test against preview
- Comment results on PR

### Task 5: Add staging gate GitHub Action template
- Template workflow at `templates/staging-gate.yml`
- Install during setup if staging is configured
- Runs e2e tests on push to staging branch
- Auto-creates promotion PR on success

### Task 6: Update README and architecture diagram
- Add environment-aware workflow to the diagram
- Document the staging → production flow
- Add `/flux:gate` to the phase table

---

## QA Testing: Always Offer Manual Fallback

Every QA checkpoint (local, preview, staging) asks the developer:

```
Testing checkpoint reached. How do you want to verify?

1. 🤖 Agent Browser — automated browser QA against {URL}
2. 👤 Manual review — I'll wait while you test, then report back

Pick [1] or [2]:
```

**Why**: Agent Browser might not be installed, might not work with the app (auth walls, SSR issues, complex SPAs), or the developer might just prefer to eyeball it. The fallback is always "you test, tell me what you found."

**Manual flow**:
1. Tell the developer the URL and what to check (the QA checklist)
2. Wait for their response
3. They report: "all good" or "X is broken"
4. If broken: create fix tasks, same as automated failure path

This applies at every QA touchpoint:
- **Local dev** (after implementation, before PR) — browser QA or manual
- **Preview URL** (after PR created) — browser QA or manual
- **Staging** (after merge to staging) — browser QA or manual

---

## Pre-commit Hooks & CI Guardrails (Prime Pillar)

### The Problem

The #1 cause of deployment crashes: code that doesn't compile or has type errors gets merged. Locally it "works" because the dev server hot-reloads around errors. But the production build fails.

### Pre-commit Hooks (Local Guard)

`/flux:prime` should detect the project stack and install appropriate pre-commit hooks via Lefthook (already offered in setup):

**Auto-detection**:
```bash
# TypeScript project
[ -f tsconfig.json ] && CHECKS+=("tsc --noEmit")
# ESLint
[ -f .eslintrc* ] || grep -q '"eslint"' package.json && CHECKS+=("eslint --max-warnings=0 .")
# Prettier
[ -f .prettierrc* ] || grep -q '"prettier"' package.json && CHECKS+=("prettier --check .")
# Python
[ -f pyproject.toml ] && CHECKS+=("ruff check ." "mypy .")
# Go
[ -f go.mod ] && CHECKS+=("go vet ./..." "go build ./...")
# Rust
[ -f Cargo.toml ] && CHECKS+=("cargo check" "cargo clippy")
# Build step (always if available)
grep -q '"build"' package.json && CHECKS+=("npm run build")
```

**Lefthook config** (`.lefthook.yml`):
```yaml
pre-commit:
  parallel: true
  commands:
    typecheck:
      run: npx tsc --noEmit
      glob: "*.{ts,tsx}"
    lint:
      run: npx eslint --max-warnings=0 {staged_files}
      glob: "*.{ts,tsx,js,jsx}"
    format:
      run: npx prettier --check {staged_files}
      glob: "*.{ts,tsx,js,jsx,json,css,md}"

pre-push:
  commands:
    build:
      run: npm run build
```

**Why pre-commit AND pre-push**: Quick checks (lint, typecheck) on commit. Slow checks (full build) on push. Catches errors at the earliest possible moment without slowing down normal development.

### CI Guardrails (Remote Guard)

`/flux:prime` should also check for (and offer to create) a CI workflow that runs on every PR:

```yaml
name: CI
on:
  pull_request:
    branches: [main, staging]

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version-file: '.node-version'
          cache: 'npm'
      - run: npm ci
      - run: npm run build
      - run: npx tsc --noEmit
      - run: npm run lint
      - run: npm test
```

**Why both hooks AND CI**: Belt and suspenders.
- Hooks catch errors before they leave the developer's machine (fast feedback)
- CI catches errors when hooks are bypassed (`--no-verify`), when a different machine has different dependencies, or when two PRs individually pass but conflict when merged

### Prime Integration

Add a new check to the Prime readiness audit:

**Pillar: Deployment Safety** (or add to existing "Tooling" pillar)

| Criterion | Check | Auto-fix |
|-----------|-------|----------|
| Pre-commit hooks configured | `.lefthook.yml` or `.husky/` exists | Offer to create Lefthook config |
| Typecheck in hooks | Hook runs `tsc --noEmit` (for TS projects) | Add to Lefthook config |
| Lint in hooks | Hook runs linter | Add to Lefthook config |
| Build check | Pre-push or CI runs `npm run build` | Add to Lefthook or CI |
| CI on PRs | `.github/workflows/` has PR-triggered check | Offer to create workflow |
| CI checks build | CI runs `npm run build` | Add step to workflow |
| CI checks types | CI runs `tsc --noEmit` | Add step to workflow |
| CI runs tests | CI runs `npm test` or equivalent | Add step to workflow |

---

## Answers to Design Questions

### Branch strategy
Feature → `staging` → `main` (two environments). Arbitrary environment chains (dev → staging → prod) deferred to future. Config structure supports it — just add more entries under `environments`.

### Who promotes staging → production?
`/flux:gate` creates the PR (staging → main) after staging tests pass. User merges manually — Flux never auto-merges to production.

### Merge detection
Two paths:
- **In-session**: User runs `/flux:gate` manually after seeing the staging merge
- **CI**: GitHub Action on push to staging branch auto-runs tests and creates promotion PR

### Preview environments
Supported for Vercel/Netlify/Render/Cloudflare Pages (auto-detect). Cloudflare Workers use named environments (`[env.staging]`) instead of preview URLs. Flux runs lightweight smoke test against preview URL and comments on the PR.

### Failure path
Staging test failures → Flux creates fix tasks in the current epic. User fixes on a new branch → PR against staging → re-test. No auto-revert (too risky). The staging environment exists precisely so problems can be found and fixed there.

### Fresh projects
No deployment markers detected → skip all environment questions. Tell user to re-run `/flux:setup` when they add deployment. No broken state.

### Infrastructure auth
Flux guides the user through auth for their specific platform. Verifies connection works before moving on. If auth fails, setup continues but marks `infrastructure.authenticated: false` — staging/production features are disabled until auth is resolved.
