# Remediation Templates

Templates for fixing agent readiness gaps. Focus on what helps agents work effectively: fast local feedback, clear commands, documented conventions.

**Priority order:**
1. **Critical**: CLAUDE.md, .env.example, lint/format commands
2. **High**: Pre-commit hooks, test command, runtime version
3. **Medium**: Build scripts, .gitignore entries
4. **Low/Bonus**: Devcontainer, Docker (nice-to-have, not essential)

**NOT offered** (team governance, not agent readiness):
- CONTRIBUTING.md, PR templates, issue templates, CODEOWNERS, LICENSE

---

## Critical: Documentation

### Create CLAUDE.md

Location: `CLAUDE.md` (repo root)

**Why**: Agents need to know project conventions, commands, and structure. Without this, they guess.

Template (adapt based on detected stack):

```markdown
# Project Name

## Quick Commands

```bash
# Install dependencies
[detected package manager] install

# Run development server
[detected dev command]

# Run tests
[detected test command]

# Build for production
[detected build command]

# Lint code
[detected lint command]

# Format code
[detected format command]
```

## Project Structure

```
[detected structure - key directories only]
```

## Code Conventions

- [Detected naming convention]
- [Detected file organization]
- [Patterns from existing code]

## Things to Avoid

- [Common pitfalls for this stack]
```

### Create .env.example

Location: `.env.example` (repo root)

**Why**: Agents waste cycles guessing env vars. This documents what's required.

Process:
1. Scan code for env var usage (process.env.*, os.environ, etc.)
2. Create template with detected vars
3. Add placeholder values and comments

Template:

```bash
# Required for [feature]
VAR_NAME=your_value_here

# Optional: [description]
OPTIONAL_VAR=default_value
```

---

## High: Fast Local Feedback

### Add Pre-commit Hooks (JavaScript/TypeScript)

**Why**: Agents get instant feedback instead of waiting 10min for CI.

If husky not installed, add to package.json devDependencies:

```json
{
  "devDependencies": {
    "husky": "^9.0.0",
    "lint-staged": "^15.0.0"
  },
  "lint-staged": {
    "*.{js,ts,tsx}": ["eslint --fix", "prettier --write"],
    "*.{json,md}": ["prettier --write"]
  }
}
```

Then run:
```bash
npx husky init
echo "npx lint-staged" > .husky/pre-commit
```

### Add Pre-commit Hooks (Python)

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.3.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

### Add Linter Config (if NO linter detected)

**Important**: Only offer if NO linter exists. ESLint, Biome, oxlint, Ruff are all valid. Don't replace one with another.

Recommend based on project:
- **Biome** (recommended for new projects): fast, does lint + format
- **ESLint** (established projects): wide ecosystem
- **oxlint** (performance-critical): very fast
- **Ruff** (Python): very fast

Example ESLint - `eslint.config.js`:

```javascript
import js from '@eslint/js';

export default [
  js.configs.recommended,
];
```

Example Biome - `biome.json`:

```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "linter": { "enabled": true },
  "formatter": { "enabled": true }
}
```

### Add Formatter Config (if NO formatter detected)

**Important**: Only offer if NO formatter exists. Biome handles both lint + format. Prettier, Black, gofmt are all valid.

Example Prettier - `.prettierrc`:

```json
{
  "semi": true,
  "singleQuote": true,
  "tabWidth": 2
}
```

Note: If Biome is already configured, it handles formatting. Don't add Prettier.

### Add Runtime Version File

For Node.js, create `.nvmrc`:
```
20
```

For Python, create `.python-version`:
```
3.12
```

---

## Medium: Build & Environment

### Add .gitignore Entries

Append to `.gitignore` if missing:

```
# Environment
.env
.env.local
.env.*.local

# Build outputs
dist/
build/
.next/
out/

# Dependencies
node_modules/

# IDE
.idea/
.vscode/
*.swp
```

### Add Test Config (if test framework detected but no config)

Jest - create `jest.config.js`:

```javascript
/** @type {import('jest').Config} */
const config = {
  testEnvironment: 'node',
  testMatch: ['**/*.test.js', '**/*.test.ts'],
};

module.exports = config;
```

Vitest - create `vitest.config.ts`:

```typescript
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
  },
});
```

pytest - create `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --tb=short
```

---

## Low/Bonus: Optional Enhancements

These are nice-to-have but NOT essential for agent readiness. Only offer if user explicitly wants them.

### Create Devcontainer (Bonus)

Create `.devcontainer/devcontainer.json`:

```json
{
  "name": "[Project Name]",
  "image": "mcr.microsoft.com/devcontainers/[language]:latest",
  "features": {},
  "postCreateCommand": "[install command]"
}
```

### Add Basic CI Workflow (Bonus)

**Note**: Agents benefit more from pre-commit hooks (instant feedback) than CI (slow feedback). Only add if user wants CI.

Create `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Setup [runtime]
        uses: actions/setup-[runtime]@v4
      - name: Install
        run: [install command]
      - name: Lint
        run: [lint command]
      - name: Test
        run: [test command]
```

---

## Infrastructure MCPs & CLIs

When the prime assessment detects infrastructure providers in the codebase, recommend the corresponding MCPs or CLIs. These let agents deploy, query databases, check logs, and manage infrastructure directly — without the user switching to provider dashboards.

**Only recommend tools for providers actually detected in the codebase.** Never suggest tools for providers the project doesn't use.

### Hosting & Deployment

| Provider | Detection Signals | MCP/CLI | Install | What Agents Can Do |
|----------|-------------------|---------|---------|-------------------|
| **Vercel** | `vercel.json`, `@vercel/*` deps, `VERCEL_*` env | Vercel MCP | `npx @vercel/mcp@latest` (follow setup) | Manage deployments, check build logs, manage env vars, query analytics |
| **Netlify** | `netlify.toml`, `NETLIFY_*` env | Netlify CLI | `npm i -g netlify-cli && netlify login` | Deploy, check build status, manage sites, view function logs |
| **Railway** | `railway.json`, `railway.toml`, `RAILWAY_*` env | Railway CLI | `npm i -g @railway/cli && railway login` | Deploy, view logs, manage services, check deployments |
| **Fly.io** | `fly.toml`, `FLY_*` env | Fly CLI | `brew install flyctl && fly auth login` | Deploy, scale, view logs, manage secrets |
| **Render** | `render.yaml`, `RENDER_*` env | Render CLI | `brew install render` | Deploy, manage services, view logs |
| **Cloudflare Workers** | `wrangler.toml`, `wrangler.jsonc`, `@cloudflare/workers-*` deps | Cloudflare MCP | `npx @anthropic-ai/mcp@latest cloudflare` (follow setup) | Deploy workers, manage KV/D1/R2, check analytics |
| **AWS** | `@aws-sdk/*` deps, `AWS_*` env, `amplify.yml` | AWS MCP | `npx @anthropic-ai/mcp@latest aws` (follow setup) | Manage S3, Lambda, CloudFormation, view CloudWatch logs |

### Databases

| Provider | Detection Signals | MCP/CLI | Install | What Agents Can Do |
|----------|-------------------|---------|---------|-------------------|
| **Neon** | `@neondatabase/*` deps, `NEON_*` env, `DATABASE_URL.*neon` | Neon MCP | `npx @anthropic-ai/mcp@latest neon` (follow setup) | Create/manage databases, run SQL, manage branches |
| **Supabase** | `supabase/` dir, `@supabase/*` deps, `SUPABASE_*` env | Supabase MCP | `npx @anthropic-ai/mcp@latest supabase` (follow setup) | Manage tables, run SQL, manage auth, check edge functions |
| **PlanetScale** | `@planetscale/*` deps, `PLANETSCALE_*` env | PlanetScale CLI | `brew install planetscale/tap/pscale && pscale auth login` | Create branches, run schema changes, query databases |
| **Turso** | `@libsql/*` deps, `TURSO_*` env | Turso CLI | `brew install tursodatabase/tap/turso && turso auth login` | Manage databases, create replicas, run SQL |
| **Upstash** | `@upstash/*` deps, `UPSTASH_*` env | Upstash MCP | `npx @anthropic-ai/mcp@latest upstash` (follow setup) | Manage Redis/Kafka instances, check metrics |

### Services & APIs

| Provider | Detection Signals | MCP/CLI | Install | What Agents Can Do |
|----------|-------------------|---------|---------|-------------------|
| **Stripe** | `stripe` dep, `STRIPE_*` env | Stripe MCP | `npx @anthropic-ai/mcp@latest stripe` (follow setup) | Test webhooks, manage products, check payments, view logs |
| **Resend** | `resend` dep, `RESEND_*` env | Resend MCP | Configure in Claude MCP settings | Send test emails, manage domains, check delivery status |
| **Firebase** | `firebase.json`, `.firebaserc`, `firebase-admin` dep | Firebase CLI | `npm i -g firebase-tools && firebase login` | Deploy functions, manage Firestore, check hosting |
| **Doppler** | `doppler.yaml`, `DOPPLER_*` env | Doppler CLI | `brew install dopplerhq/cli/doppler && doppler login` | Manage secrets across environments, sync env vars |

### Installation Rules

1. **MCP over CLI** — If both exist, prefer the MCP (richer integration with agents)
2. **Auth required** — Most tools need authentication. Tell the user which ones need `login` after install
3. **Verify install** — After each install, verify with `which <tool>` or the tool's `--version` flag
4. **Don't auto-configure MCP settings** — MCPs that need Claude Desktop/Code config should tell the user what to add, not modify config files directly
5. **Group if many** — If >4 providers detected, group into "Hosting", "Database", "Services" questions

---

## Application Rules

1. **Detect before creating** - Check if file exists first
2. **Preserve existing content** - Merge with existing configs when possible
3. **Match project style** - Use detected indent (tabs/spaces), quote style
4. **Don't add unused features** - Only add what the project needs
5. **Explain changes** - Tell user what was created and why
6. **Respect user choices** - Never force changes without consent
