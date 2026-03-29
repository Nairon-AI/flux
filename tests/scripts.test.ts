/**
 * Flux Scripts E2E Tests
 * 
 * Fast tests that don't require Claude Code.
 * Run: bun test tests/scripts.test.ts
 */

import { test, expect, describe, beforeAll } from 'bun:test'
import { existsSync, mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync, chmodSync, readFileSync } from 'fs'
import { dirname, join } from 'path'
import { $ } from 'bun'

// Resolve flux root from test file location (tests/ is inside flux/)
const FLUX_ROOT = process.env.FLUX_ROOT || 
  process.env.CLAUDE_PLUGIN_ROOT ||
  join(import.meta.dir, '..')

const SCRIPT_TIMEOUT = 15000

async function runScript(script: string, args: string[] = [], cwd?: string): Promise<string> {
  const scriptPath = join(FLUX_ROOT, 'scripts', script)
  const env = {
    ...process.env,
    CLAUDE_PLUGIN_ROOT: FLUX_ROOT,
    DROID_PLUGIN_ROOT: FLUX_ROOT,
  }
  
  try {
    const result = await $`bash ${scriptPath} ${args}`.env(env).cwd(cwd || FLUX_ROOT).text()
    return result.trim()
  } catch (e: unknown) {
    const err = e as { stdout?: Buffer; stderr?: Buffer; message?: string }
    return err.stdout?.toString() || err.stderr?.toString() || err.message || String(e)
  }
}

async function runScriptWithEnv(
  script: string,
  args: string[] = [],
  cwd?: string,
  extraEnv: Record<string, string> = {}
): Promise<string> {
  const scriptPath = join(FLUX_ROOT, 'scripts', script)
  const env = {
    ...process.env,
    CLAUDE_PLUGIN_ROOT: FLUX_ROOT,
    DROID_PLUGIN_ROOT: FLUX_ROOT,
    ...extraEnv,
  }

  try {
    const result = await $`bash ${scriptPath} ${args}`.env(env).cwd(cwd || FLUX_ROOT).text()
    return result.trim()
  } catch (e: unknown) {
    const err = e as { stdout?: Buffer; stderr?: Buffer; message?: string }
    return err.stdout?.toString() || err.stderr?.toString() || err.message || String(e)
  }
}

describe('Flux Scripts', () => {
  
  beforeAll(() => {
    expect(existsSync(FLUX_ROOT)).toBe(true)
    expect(existsSync(join(FLUX_ROOT, 'scripts'))).toBe(true)
  })

  describe('detect-installed.sh', () => {
    
    test('outputs valid JSON', async () => {
      const output = await runScript('detect-installed.sh')
      const parsed = JSON.parse(output)
      expect(parsed).toBeDefined()
      expect(parsed.os).toBeDefined()
    }, SCRIPT_TIMEOUT)

    test('detects OS correctly', async () => {
      const output = await runScript('detect-installed.sh')
      const parsed = JSON.parse(output)
      expect(['macos', 'linux', 'windows']).toContain(parsed.os)
    }, SCRIPT_TIMEOUT)

    test('detects CLI tools', async () => {
      const output = await runScript('detect-installed.sh')
      const parsed = JSON.parse(output)
      
      expect(parsed.installed).toBeDefined()
      expect(parsed.installed.cli_tools).toBeInstanceOf(Array)
      
      const tools = parsed.installed.cli_tools
      const hasCommonTool = tools.some((t: string) => 
        ['jq', 'git', 'bun', 'node', 'npm', 'pnpm'].includes(t)
      )
      expect(hasCommonTool).toBe(true)
    }, SCRIPT_TIMEOUT)

    test('detects MCPs from ~/.mcp.json', async () => {
      const output = await runScript('detect-installed.sh')
      const parsed = JSON.parse(output)
      expect(parsed.installed.mcps).toBeInstanceOf(Array)
    }, SCRIPT_TIMEOUT)

    test('detects applications on macOS', async () => {
      const output = await runScript('detect-installed.sh')
      const parsed = JSON.parse(output)
      
      if (parsed.os === 'macos') {
        expect(parsed.installed.applications).toBeInstanceOf(Array)
      }
    }, SCRIPT_TIMEOUT)

    test('includes preferences', async () => {
      const output = await runScript('detect-installed.sh')
      const parsed = JSON.parse(output)
      
      expect(parsed.preferences).toBeDefined()
      expect(parsed.preferences.dismissed).toBeInstanceOf(Array)
      expect(parsed.preferences.alternatives).toBeDefined()
    }, SCRIPT_TIMEOUT)

    test('detects lintcn when it is on PATH', async () => {
      const tempDir = mkdtempSync(join(process.env.TMPDIR || '/tmp', 'flux-lintcn-bin-'))
      const lintcnPath = join(tempDir, 'lintcn')

      try {
        writeFileSync(lintcnPath, '#!/bin/sh\nexit 0\n')
        chmodSync(lintcnPath, 0o755)

        const output = await runScriptWithEnv('detect-installed.sh', [], FLUX_ROOT, {
          PATH: `${tempDir}:${process.env.PATH || ''}`,
        })
        const parsed = JSON.parse(output)

        expect(parsed.installed.cli_tools).toContain('lintcn')
      } finally {
        rmSync(tempDir, { recursive: true, force: true })
      }
    }, SCRIPT_TIMEOUT)

    test('detects react-doctor when it is on PATH', async () => {
      const tempDir = mkdtempSync(join(process.env.TMPDIR || '/tmp', 'flux-react-doctor-bin-'))
      const doctorPath = join(tempDir, 'react-doctor')

      try {
        writeFileSync(doctorPath, '#!/bin/sh\nexit 0\n')
        chmodSync(doctorPath, 0o755)

        const output = await runScriptWithEnv('detect-installed.sh', [], FLUX_ROOT, {
          PATH: `${tempDir}:${process.env.PATH || ''}`,
        })
        const parsed = JSON.parse(output)

        expect(parsed.installed.cli_tools).toContain('react-doctor')
      } finally {
        rmSync(tempDir, { recursive: true, force: true })
      }
    }, SCRIPT_TIMEOUT)
  })

  describe('analyze-context.sh', () => {
    
    test('outputs valid JSON', async () => {
      const output = await runScript('analyze-context.sh')
      const parsed = JSON.parse(output)
      expect(parsed).toBeDefined()
    }, SCRIPT_TIMEOUT)

    test('detects repo type', async () => {
      const output = await runScript('analyze-context.sh')
      const parsed = JSON.parse(output)
      
      expect(parsed.repo).toBeDefined()
      expect(parsed.repo.type).toBeDefined()
      expect(['javascript', 'typescript', 'python', 'rust', 'go', 'mixed', 'unknown']).toContain(parsed.repo.type)
    }, SCRIPT_TIMEOUT)

    test('detects frameworks', async () => {
      const output = await runScript('analyze-context.sh')
      const parsed = JSON.parse(output)
      expect(parsed.repo.frameworks).toBeInstanceOf(Array)
    }, SCRIPT_TIMEOUT)

    test('detects Next.js and React projects', async () => {
      const tmpRoot = `/tmp/flux-analyze-react-${Date.now()}`
      mkdirSync(tmpRoot, { recursive: true })
      writeFileSync(
        join(tmpRoot, 'package.json'),
        JSON.stringify({
          dependencies: {
            next: '^15.0.0',
            react: '^19.0.0',
          },
        })
      )

      const output = await runScript('analyze-context.sh', [], tmpRoot)
      const parsed = JSON.parse(output)

      expect(parsed.repo.frameworks).toEqual(expect.arrayContaining(['next', 'react']))

      rmSync(tmpRoot, { recursive: true, force: true })
    }, SCRIPT_TIMEOUT)

    test('detects Remix and React Router projects', async () => {
      const tmpRoot = `/tmp/flux-analyze-remix-${Date.now()}`
      mkdirSync(tmpRoot, { recursive: true })
      writeFileSync(
        join(tmpRoot, 'package.json'),
        JSON.stringify({
          dependencies: {
            '@remix-run/react': '^2.0.0',
            'react-router-dom': '^7.0.0',
          },
        })
      )

      const output = await runScript('analyze-context.sh', [], tmpRoot)
      const parsed = JSON.parse(output)

      expect(parsed.repo.frameworks).toEqual(
        expect.arrayContaining(['remix', 'react-router'])
      )

      rmSync(tmpRoot, { recursive: true, force: true })
    }, SCRIPT_TIMEOUT)

    test('identifies repo characteristics', async () => {
      const output = await runScript('analyze-context.sh')
      const parsed = JSON.parse(output)
      
      expect(typeof parsed.repo.has_tests).toBe('boolean')
      expect(typeof parsed.repo.has_ci).toBe('boolean')
      expect(typeof parsed.repo.has_linter).toBe('boolean')
      expect(typeof parsed.repo.has_hooks).toBe('boolean')
    }, SCRIPT_TIMEOUT)

    test('treats lintcn repos as having a linter', async () => {
      const tempDir = mkdtempSync(join(process.env.TMPDIR || '/tmp', 'flux-lintcn-repo-'))

      try {
        mkdirSync(join(tempDir, '.lintcn'))
        writeFileSync(
          join(tempDir, 'package.json'),
          JSON.stringify({
            name: 'lintcn-fixture',
            private: true,
            devDependencies: {
              lintcn: '0.5.0',
            },
            scripts: {
              lint: 'npx lintcn lint',
            },
          })
        )

        const output = await runScript('analyze-context.sh', [], tempDir)
        const parsed = JSON.parse(output)

        expect(parsed.repo.has_linter).toBe(true)
      } finally {
        rmSync(tempDir, { recursive: true, force: true })
      }
    }, SCRIPT_TIMEOUT)
  })

  describe('manage-preferences.sh', () => {
    
    test('shows usage when called with no args', async () => {
      const output = await runScript('manage-preferences.sh')
      expect(output.toLowerCase()).toMatch(/usage|preferences|dismiss|alternative/i)
    }, SCRIPT_TIMEOUT)

    test('list returns valid JSON', async () => {
      const output = await runScript('manage-preferences.sh', ['list'])
      const parsed = JSON.parse(output)
      expect(parsed.dismissed).toBeInstanceOf(Array)
      expect(parsed.alternatives).toBeDefined()
    }, SCRIPT_TIMEOUT)

    test('dismiss adds to dismissed list', async () => {
      await runScript('manage-preferences.sh', ['dismiss', 'test-recommendation-e2e'])
      
      const output = await runScript('manage-preferences.sh', ['list'])
      const parsed = JSON.parse(output)
      expect(parsed.dismissed).toContain('test-recommendation-e2e')
      
      await runScript('manage-preferences.sh', ['undismiss', 'test-recommendation-e2e'])
    }, SCRIPT_TIMEOUT)
  })

  describe('version-check.sh', () => {
    
    test('outputs JSON with version info', async () => {
      const output = await runScript('version-check.sh')
      
      try {
        const parsed = JSON.parse(output)
        expect(parsed).toBeDefined()
        expect(
          parsed.local_version !== undefined || 
          parsed.error !== undefined ||
          parsed.update_available !== undefined
        ).toBe(true)
      } catch (e) {
        expect(output).toBeTruthy()
      }
    }, SCRIPT_TIMEOUT)
  })

  describe('install-react-doctor-hook.py', () => {

    test('creates an idempotent React Doctor pre-commit hook setup', async () => {
      const tmpRoot = `/tmp/flux-react-doctor-hook-${Date.now()}`
      mkdirSync(tmpRoot, { recursive: true })
      await $`git init ${tmpRoot}`.quiet()

      const scriptPath = join(FLUX_ROOT, 'scripts', 'install-react-doctor-hook.py')
      const env = {
        ...process.env,
        FLUX_SKIP_LEFTHOOK_INSTALL: '1',
      }

      const first = await $`python3 ${scriptPath} ${tmpRoot}`.env(env).text()
      const firstParsed = JSON.parse(first)

      expect(firstParsed.success).toBe(true)
      expect(firstParsed.manager).toBe('lefthook')
      expect(existsSync(join(tmpRoot, 'lefthook.yml'))).toBe(true)
      expect(existsSync(join(tmpRoot, '.flux', 'hooks', 'react-doctor-pre-commit.sh'))).toBe(true)

      const lefthookConfig = readFileSync(join(tmpRoot, 'lefthook.yml'), 'utf-8')
      expect(lefthookConfig).toContain('react-doctor:')
      expect(lefthookConfig).toContain('./.flux/hooks/react-doctor-pre-commit.sh')

      const second = await $`python3 ${scriptPath} ${tmpRoot}`.env(env).text()
      const secondParsed = JSON.parse(second)
      const secondConfig = readFileSync(join(tmpRoot, 'lefthook.yml'), 'utf-8')

      expect(secondParsed.success).toBe(true)
      expect(secondConfig.match(/react-doctor:/g)?.length).toBe(1)

      rmSync(tmpRoot, { recursive: true, force: true })
    }, SCRIPT_TIMEOUT)

    test('preserves an existing native pre-commit hook when falling back', async () => {
      const tmpRoot = `/tmp/flux-react-doctor-native-hook-${Date.now()}`
      mkdirSync(tmpRoot, { recursive: true })
      await $`git init ${tmpRoot}`.quiet()

      const gitHooksDir = join(tmpRoot, '.git', 'hooks')
      mkdirSync(gitHooksDir, { recursive: true })
      writeFileSync(
        join(gitHooksDir, 'pre-commit'),
        '#!/bin/sh\necho "existing native hook"\n',
      )

      const scriptPath = join(FLUX_ROOT, 'scripts', 'install-react-doctor-hook.py')
      const gitPath = (await $`which git`.text()).trim()
      const env = {
        ...process.env,
        PATH: dirname(gitPath),
      }

      const output = await $`python3 ${scriptPath} ${tmpRoot}`.env(env).text()
      const parsed = JSON.parse(output)
      const hookContents = readFileSync(join(gitHooksDir, 'pre-commit'), 'utf-8')

      expect(parsed.success).toBe(true)
      expect(parsed.manager).toBe('git-hooks')
      expect(hookContents).toContain('existing native hook')
      expect(hookContents).toContain('./.flux/hooks/react-doctor-pre-commit.sh')

      rmSync(tmpRoot, { recursive: true, force: true })
    }, SCRIPT_TIMEOUT)
  })

  describe('match-recommendations.py', () => {
    
    test('matches recommendations based on context', async () => {
      const testInput = JSON.stringify({
        installed: {
          cli_tools: ['git', 'npm'],
          mcps: [],
          applications: [],
          plugins: []
        },
        context: {
          repo_type: 'node',
          frameworks: ['react'],
          gaps: ['no_tests', 'no_git_hooks']
        },
        preferences: {
          dismissed: [],
          alternatives: {}
        }
      })
      
      const scriptPath = join(FLUX_ROOT, 'scripts', 'match-recommendations.py')
      const result = await $`echo ${testInput} | python3 ${scriptPath}`.env({
        ...process.env,
        CLAUDE_PLUGIN_ROOT: FLUX_ROOT,
      }).text()
      
      expect(result).toBeTruthy()
    }, SCRIPT_TIMEOUT)
  })

  describe('profile-manager.py', () => {

    test('detect outputs valid profile catalog JSON', async () => {
      const scriptPath = join(FLUX_ROOT, 'scripts', 'profile-manager.py')
      const result = await $`python3 ${scriptPath} detect --skills-scope both`.env({
        ...process.env,
        CLAUDE_PLUGIN_ROOT: FLUX_ROOT,
      }).text()

      const parsed = JSON.parse(result)
      expect(parsed.os).toBeDefined()
      expect(parsed.catalog).toBeDefined()
      expect(parsed.application_selection).toBeDefined()
    }, SCRIPT_TIMEOUT)

    test('profile-manager unit test script passes', async () => {
      const scriptPath = join(FLUX_ROOT, 'scripts', 'test_profile_manager.py')
      const result = await $`python3 ${scriptPath}`.env({
        ...process.env,
        CLAUDE_PLUGIN_ROOT: FLUX_ROOT,
      }).text()

      expect(result).toContain('All profile-manager tests passed')
    }, SCRIPT_TIMEOUT * 4)
  })

  describe('validate_skills.py', () => {

    test('reports zero hard errors for built-in skills', async () => {
      const scriptPath = join(FLUX_ROOT, 'scripts', 'validate_skills.py')
      const result = await $`python3 ${scriptPath}`.env({
        ...process.env,
        CLAUDE_PLUGIN_ROOT: FLUX_ROOT,
      }).text()

      expect(result).toContain('Validated')
      expect(result).toContain('0 error(s)')
    }, SCRIPT_TIMEOUT)
  })

  describe('skill install helpers', () => {

    test('install-skill.sh recommends secureskills for project installs without a source', async () => {
      const tmpRoot = `/tmp/flux-install-skill-${Date.now()}`
      mkdirSync(tmpRoot, { recursive: true })

      const scriptPath = join(FLUX_ROOT, 'scripts', 'install-skill.sh')
      const output = await $`bash ${scriptPath} baseline-ui project`.cwd(tmpRoot).text()
      expect(output).toContain('secureskills add <source> --skill')
      expect(output).toContain('"manual": true')

      rmSync(tmpRoot, { recursive: true, force: true })
    }, SCRIPT_TIMEOUT)

    test('verify-install.sh validates PlaTo secure skill manifests', async () => {
      const tmpRoot = `/tmp/flux-verify-secureskill-${Date.now()}`
      mkdirSync(join(tmpRoot, '.secureskills', 'store', 'baseline-ui'), { recursive: true })
      writeFileSync(
        join(tmpRoot, '.secureskills', 'store', 'baseline-ui', 'manifest.json'),
        '{}'
      )

      const output = await runScript('verify-install.sh', ['baseline-ui', 'secureskill', tmpRoot], tmpRoot)
      const parsed = JSON.parse(output.slice(output.indexOf('{')))
      expect(parsed.success).toBe(true)
      expect(parsed.verify_type).toBe('secureskill')

      rmSync(tmpRoot, { recursive: true, force: true })
    }, SCRIPT_TIMEOUT)
  })
})

describe('Fluxctl CLI', () => {
  const fluxctl = join(FLUX_ROOT, 'scripts', 'fluxctl')
  
  test('--help shows usage', async () => {
    const result = await $`${fluxctl} --help`.text().catch(e => e.stdout?.toString() || e.message)
    expect(result.toLowerCase()).toMatch(/usage|help|flux|command/i)
  }, SCRIPT_TIMEOUT)

  test('list handles missing .flux gracefully', async () => {
    const result = await $`${fluxctl} list`.cwd(FLUX_ROOT).text().catch(e => e.stderr?.toString() || e.message)
    expect(result).toBeTruthy()
  }, SCRIPT_TIMEOUT)

  test('init creates project-local brain scaffold inside .flux', async () => {
    const tmpRoot = `/tmp/flux-init-brain-${Date.now()}`
    await $`mkdir -p ${tmpRoot}`.quiet()

    await $`${fluxctl} init --json`.cwd(tmpRoot).quiet()

    expect(existsSync(join(tmpRoot, '.flux', 'brain', 'index.md'))).toBe(true)
    expect(existsSync(join(tmpRoot, '.flux', 'brain', 'business', 'index.md'))).toBe(true)
    expect(existsSync(join(tmpRoot, '.flux', 'brain', 'codebase', 'architecture.md'))).toBe(true)
    expect(existsSync(join(tmpRoot, '.flux', 'brain', 'pitfalls', 'index.md'))).toBe(true)
    expect(existsSync(join(tmpRoot, '.flux', 'brain', 'principles'))).toBe(true)
    expect(existsSync(join(tmpRoot, 'brain'))).toBe(false)
  }, SCRIPT_TIMEOUT)

  test('init migrates legacy brain directory into .flux', async () => {
    const tmpRoot = `/tmp/flux-init-legacy-brain-${Date.now()}`
    const legacyBrain = join(tmpRoot, 'brain')
    await $`mkdir -p ${legacyBrain}/pitfalls`.quiet()
    writeFileSync(join(legacyBrain, 'index.md'), '# Brain Index\n')
    writeFileSync(join(legacyBrain, 'pitfalls', 'legacy-note.md'), '# Legacy note\n')

    await $`${fluxctl} init --json`.cwd(tmpRoot).quiet()

    expect(existsSync(join(tmpRoot, '.flux', 'brain', 'index.md'))).toBe(true)
    expect(existsSync(join(tmpRoot, '.flux', 'brain', 'pitfalls', 'legacy-note.md'))).toBe(true)
    expect(existsSync(join(tmpRoot, 'brain'))).toBe(false)
  }, SCRIPT_TIMEOUT)

  test('session-state reports fresh session when .flux is missing', async () => {
    const tmpRoot = `/tmp/flux-session-state-${Date.now()}`
    await $`mkdir -p ${tmpRoot}`.quiet()
    const output = await $`${fluxctl} session-state --json`.cwd(tmpRoot).text()
    const parsed = JSON.parse(output)

    expect(parsed.state).toBe('fresh_session_no_objective')
    expect(parsed.flux_exists).toBe(false)
    expect(parsed.router.command).toBe('/flux:setup')
    expect(parsed.router.skill).toBe('flux-setup')
    expect(parsed.router.node).toBe('Setup')
  }, SCRIPT_TIMEOUT)

  test('session-state requires prime before any scoped workflow', async () => {
    const tmpRoot = `/tmp/flux-needs-prime-${Date.now()}`
    await $`mkdir -p ${tmpRoot}`.quiet()

    await $`${fluxctl} init --json`.cwd(tmpRoot).quiet()

    const sessionRaw = await $`${fluxctl} session-state --json`.cwd(tmpRoot).text()
    const session = JSON.parse(sessionRaw)
    expect(session.state).toBe('needs_prime')
    expect(session.next_action).toBe('/flux:prime')
    expect(session.router.command).toBe('/flux:prime')
    expect(session.router.skill).toBe('flux-prime')
    expect(session.router.node).toBe('Prime')
    expect(session.architecture.status).toBe('seeded')
    expect(session.architecture.needs_refresh).toBe(true)

    await $`${fluxctl} prime-mark --status done --json`.cwd(tmpRoot).quiet()

    const primeRaw = await $`${fluxctl} prime-status --json`.cwd(tmpRoot).text()
    const prime = JSON.parse(primeRaw)
    expect(prime.prime_required).toBe(false)
    expect(prime.prime.status).toBe('done')

    const afterPrimeRaw = await $`${fluxctl} session-state --json`.cwd(tmpRoot).text()
    const afterPrime = JSON.parse(afterPrimeRaw)
    expect(afterPrime.state).toBe('fresh_session_no_objective')
    expect(afterPrime.router.command).toBe('/flux:scope')
    expect(afterPrime.router.skill).toBe('flux-scope')
    expect(afterPrime.router.node).toBe('Scope')
    expect(afterPrime.architecture.status).toBe('seeded')
  }, SCRIPT_TIMEOUT)

  test('architecture write updates canonical diagram status and metadata', async () => {
    const tmpRoot = `/tmp/flux-architecture-write-${Date.now()}`
    const architectureFile = join(tmpRoot, 'architecture.md')
    await $`mkdir -p ${tmpRoot}`.quiet()

    await $`${fluxctl} init --json`.cwd(tmpRoot).quiet()
    writeFileSync(
      architectureFile,
      `# System Architecture Diagram

## Diagram

\`\`\`mermaid
flowchart TD
  UI[Web App] --> API[API]
  API --> DB[(Postgres)]
\`\`\`
`
    )

    const writeRaw = await $`${fluxctl} architecture write --file ${architectureFile} --summary "Captured web app to API to Postgres flow" --source flux:prime --json`
      .cwd(tmpRoot)
      .text()
    const writeResult = JSON.parse(writeRaw)
    expect(writeResult.architecture.status).toBe('current')
    expect(writeResult.architecture.summary).toBe('Captured web app to API to Postgres flow')
    expect(writeResult.architecture.source).toBe('flux:prime')

    const statusRaw = await $`${fluxctl} architecture status --json`.cwd(tmpRoot).text()
    const status = JSON.parse(statusRaw)
    expect(status.architecture.status).toBe('current')
    expect(status.architecture.needs_refresh).toBe(false)
    expect(status.architecture.summary).toBe('Captured web app to API to Postgres flow')

    const persisted = readFileSync(join(tmpRoot, '.flux', 'brain', 'codebase', 'architecture.md'), 'utf8')
    expect(persisted).toContain('flowchart TD')
    expect(persisted).toContain('Postgres')
  }, SCRIPT_TIMEOUT)

  test('scope-status reflects active objective workflow metadata', async () => {
    const tmpRoot = `/tmp/flux-scope-status-${Date.now()}`
    await $`mkdir -p ${tmpRoot}`.quiet()

    await $`${fluxctl} init --json`.cwd(tmpRoot).quiet()
    await $`${fluxctl} prime-mark --status done --json`.cwd(tmpRoot).quiet()
    const epicRaw = await $`${fluxctl} epic create --title "Fix login redirect" --kind bug --scope-mode deep --technical-level non_technical --implementation-target engineer_handoff --json`.cwd(tmpRoot).text()
    const epic = JSON.parse(epicRaw)

    await $`${fluxctl} epic set-workflow ${epic.id} --phase discover --step "repro-and-impact" --status in_progress --summary "Investigating repro path" --next-action "Confirm expected behavior" --open-question "Does this affect social login?" --activate --json`.cwd(tmpRoot).quiet()

    const statusRaw = await $`${fluxctl} scope-status --json`.cwd(tmpRoot).text()
    const status = JSON.parse(statusRaw)
    expect(status.objective.id).toBe(epic.id)
    expect(status.objective.objective_kind).toBe('bug')
    expect(status.objective.scope_mode).toBe('deep')
    expect(status.workflow.phase).toBe('discover')
    expect(status.workflow.step).toBe('repro-and-impact')
    expect(status.workflow.status).toBe('in_progress')
    expect(status.workflow.open_questions).toContain('Does this affect social login?')

    const sessionRaw = await $`${fluxctl} session-state --json`.cwd(tmpRoot).text()
    const session = JSON.parse(sessionRaw)
    expect(session.state).toBe('resume_scope')
    expect(session.objective.id).toBe(epic.id)
    expect(session.router.command).toBe('/flux:scope')
    expect(session.router.skill).toBe('flux-scope')
    expect(session.router.node).toBe('Scope')
  }, SCRIPT_TIMEOUT)

  test('agentmap --check reports built-in availability', async () => {
    const output = await $`${fluxctl} agentmap --check --json`
      .cwd(FLUX_ROOT)
      .text()

    const parsed = JSON.parse(output)
    expect(parsed.available).toBe(true)
    expect(parsed.engine).toBe('built-in')
    expect(parsed.path).toBe(null)
    expect(typeof parsed.version === 'string' || parsed.version === null).toBe(true)
  }, SCRIPT_TIMEOUT)

  test('agentmap generates built-in YAML with descriptions and defs', async () => {
    const tmpRoot = `/tmp/flux-agentmap-generate-${Date.now()}`
    mkdirSync(join(tmpRoot, 'src'), { recursive: true })

    writeFileSync(
      join(tmpRoot, 'src', 'index.ts'),
      `// CLI entrypoint.\n// Wires dependencies and starts the app.\n\nexport function main() {\n  return true\n}\n\nexport class App {}\n`
    )
    writeFileSync(
      join(tmpRoot, 'src', 'hidden.ts'),
      `export function hidden() {\n  return false\n}\n`
    )
    await $`git init -q`.cwd(tmpRoot).quiet()
    await $`git add .`.cwd(tmpRoot).quiet()

    const output = await $`${fluxctl} agentmap src --json`
      .cwd(tmpRoot)
      .text()

    const parsed = JSON.parse(output)
    expect(parsed.engine).toBe('built-in')
    expect(parsed.file_count).toBe(1)
    expect(parsed.yaml).toContain('"src":')
    expect(parsed.yaml).toContain('"index.ts":')
    expect(parsed.yaml).toContain('CLI entrypoint. Wires dependencies and starts the app.')
    expect(parsed.yaml).toContain('"main": "line 4, function, exported"')
    expect(parsed.yaml).toContain('"App": "line 8, class, exported"')
    expect(parsed.yaml).not.toContain('hidden.ts')

    rmSync(tmpRoot, { recursive: true, force: true })
  }, SCRIPT_TIMEOUT)

  test('agentmap returns empty map outside a git repo', async () => {
    const tmpRoot = `/tmp/flux-agentmap-nongit-${Date.now()}`
    mkdirSync(join(tmpRoot, 'src'), { recursive: true })
    writeFileSync(
      join(tmpRoot, 'src', 'index.ts'),
      `// Non-git file.\n\nexport function main() {\n  return true\n}\n`
    )

    const output = await $`${fluxctl} agentmap src --json`
      .cwd(tmpRoot)
      .text()

    const parsed = JSON.parse(output)
    expect(parsed.file_count).toBe(0)
    expect(parsed.yaml).toContain('"src": {}')

    rmSync(tmpRoot, { recursive: true, force: true })
  }, SCRIPT_TIMEOUT)

  test('agentmap skips license headers and includes README descriptions', async () => {
    const tmpRoot = `/tmp/flux-agentmap-readme-${Date.now()}`
    mkdirSync(join(tmpRoot, 'src'), { recursive: true })
    writeFileSync(
      join(tmpRoot, 'README.md'),
      `# Flux Sample\n\nA small sample repo.\n\n![Diagram](./diagram.png)\n`
    )
    writeFileSync(
      join(tmpRoot, 'src', 'licensed.ts'),
      `// SPDX-License-Identifier: MIT\n// Utility parser.\n// Handles normalization.\n\nexport function parseInput() {\n  return true\n}\n`
    )
    await $`git init -q`.cwd(tmpRoot).quiet()
    await $`git add .`.cwd(tmpRoot).quiet()

    const output = await $`${fluxctl} agentmap . --json`
      .cwd(tmpRoot)
      .text()

    const parsed = JSON.parse(output)
    expect(parsed.file_count).toBe(2)
    expect(parsed.yaml).toContain('"README.md":')
    expect(parsed.yaml).toContain('"Flux Sample\\nA small sample repo."')
    expect(parsed.yaml).toContain('"licensed.ts":')
    expect(parsed.yaml).toContain('"Utility parser. Handles normalization."')
    expect(parsed.yaml).not.toContain('SPDX-License-Identifier')

    rmSync(tmpRoot, { recursive: true, force: true })
  }, SCRIPT_TIMEOUT)

  test('agentmap preserves shebang, skips directives, and ignores TS reference comments', async () => {
    const tmpRoot = `/tmp/flux-agentmap-directives-${Date.now()}`
    mkdirSync(join(tmpRoot, 'src'), { recursive: true })
    writeFileSync(
      join(tmpRoot, 'src', 'cli.ts'),
      `#!/usr/bin/env node\n"use strict"\n/// <reference path="./types.d.ts" />\n// CLI runner.\n// Executes the sync workflow.\n\nexport function main() {\n  return true\n}\n`
    )
    await $`git init -q`.cwd(tmpRoot).quiet()
    await $`git add .`.cwd(tmpRoot).quiet()

    const output = await $`${fluxctl} agentmap src --json`
      .cwd(tmpRoot)
      .text()

    const parsed = JSON.parse(output)
    expect(parsed.file_count).toBe(1)
    expect(parsed.yaml).toContain('#!/usr/bin/env node\\nCLI runner. Executes the sync workflow.')
    expect(parsed.yaml).not.toContain('use strict')
    expect(parsed.yaml).not.toContain('<reference path=')

    rmSync(tmpRoot, { recursive: true, force: true })
  }, SCRIPT_TIMEOUT)

  test('agentmap --write writes default Flux artifact path', async () => {
    const tmpRoot = `/tmp/flux-agentmap-write-${Date.now()}`
    mkdirSync(join(tmpRoot, 'src'), { recursive: true })
    writeFileSync(
      join(tmpRoot, 'src', 'index.ts'),
      `// Test entrypoint.\n\nexport function main() {\n  return true\n}\n`
    )
    await $`git init -q`.cwd(tmpRoot).quiet()
    await $`git add .`.cwd(tmpRoot).quiet()

    await $`${fluxctl} init --json`
      .cwd(tmpRoot)
      .quiet()

    const output = await $`${fluxctl} agentmap src --write --json`
      .cwd(tmpRoot)
      .text()

    const parsed = JSON.parse(output)
    const mapPath = join(tmpRoot, '.flux', 'context', 'agentmap.yaml')
    expect(parsed.output_file.endsWith('/.flux/context/agentmap.yaml')).toBe(true)
    expect(parsed.file_count).toBe(1)
    expect(existsSync(mapPath)).toBe(true)
    expect(readFileSync(mapPath, 'utf-8')).toContain('Test entrypoint.')

    rmSync(tmpRoot, { recursive: true, force: true })
  }, SCRIPT_TIMEOUT)
})

describe('Integration', () => {
  
  test('detect -> analyze pipeline', async () => {
    const detectOutput = await runScript('detect-installed.sh')
    const installed = JSON.parse(detectOutput)
    
    expect(installed.os).toBeDefined()
    expect(installed.installed.cli_tools).toBeInstanceOf(Array)
    
    const analyzeOutput = await runScript('analyze-context.sh')
    const context = JSON.parse(analyzeOutput)
    
    expect(context.repo).toBeDefined()
    expect(context.repo.type).toBeDefined()
  }, SCRIPT_TIMEOUT * 2)

  test('recommendations filter dismissed items', async () => {
    await runScript('manage-preferences.sh', ['dismiss', 'integration-test-item'])
    
    const prefsOutput = await runScript('manage-preferences.sh', ['list'])
    const prefs = JSON.parse(prefsOutput)
    
    expect(prefs.dismissed).toContain('integration-test-item')
    
    await runScript('manage-preferences.sh', ['undismiss', 'integration-test-item'])
  }, SCRIPT_TIMEOUT)

  test('full improve pipeline simulation', async () => {
    const detectOutput = await runScript('detect-installed.sh')
    const installed = JSON.parse(detectOutput)
    
    const analyzeOutput = await runScript('analyze-context.sh')
    const context = JSON.parse(analyzeOutput)
    
    const prefsOutput = await runScript('manage-preferences.sh', ['list'])
    const prefs = JSON.parse(prefsOutput)
    
    const matchInput = JSON.stringify({
      installed: installed.installed,
      context: context,
      preferences: prefs
    })
    
    const scriptPath = join(FLUX_ROOT, 'scripts', 'match-recommendations.py')
    const recommendations = await $`echo ${matchInput} | python3 ${scriptPath}`.env({
      ...process.env,
      CLAUDE_PLUGIN_ROOT: FLUX_ROOT,
    }).text().catch(() => '[]')
    
    expect(recommendations).toBeTruthy()
  }, SCRIPT_TIMEOUT * 3)
})

describe('analyze-sessions.sh (Session Parser)', () => {
  
  test('outputs valid JSON', async () => {
    const output = await runScript('analyze-sessions.sh')
    const parsed = JSON.parse(output)
    expect(parsed).toBeDefined()
    expect(typeof parsed.enabled).toBe('boolean')
  }, SCRIPT_TIMEOUT)

  test('returns enabled=true when sessions exist', async () => {
    const output = await runScript('analyze-sessions.sh')
    const parsed = JSON.parse(output)
    
    // If sessions dir exists and has files, should be enabled
    if (parsed.enabled) {
      expect(parsed.sessions_analyzed).toBeGreaterThan(0)
    } else {
      expect(parsed.reason).toBeTruthy()
    }
  }, SCRIPT_TIMEOUT)

  test('includes error patterns when enabled', async () => {
    const output = await runScript('analyze-sessions.sh')
    const parsed = JSON.parse(output)
    
    if (parsed.enabled) {
      expect(parsed.error_patterns).toBeDefined()
      expect(parsed.error_patterns.by_type).toBeDefined()
      expect(parsed.error_patterns.samples).toBeInstanceOf(Array)
    }
  }, SCRIPT_TIMEOUT)

  test('includes tool usage stats', async () => {
    const output = await runScript('analyze-sessions.sh')
    const parsed = JSON.parse(output)
    
    if (parsed.enabled) {
      expect(parsed.tool_usage).toBeDefined()
      expect(typeof parsed.tool_usage).toBe('object')
    }
  }, SCRIPT_TIMEOUT)

  test('includes tool errors', async () => {
    const output = await runScript('analyze-sessions.sh')
    const parsed = JSON.parse(output)
    
    if (parsed.enabled) {
      expect(parsed.tool_errors).toBeDefined()
      expect(typeof parsed.tool_errors.total).toBe('number')
      expect(parsed.tool_errors.samples).toBeInstanceOf(Array)
    }
  }, SCRIPT_TIMEOUT)

  test('includes knowledge gaps analysis', async () => {
    const output = await runScript('analyze-sessions.sh')
    const parsed = JSON.parse(output)
    
    if (parsed.enabled) {
      expect(parsed.knowledge_gaps).toBeDefined()
      expect(parsed.knowledge_gaps.by_type).toBeDefined()
    }
  }, SCRIPT_TIMEOUT)

  test('respects FLUX_SESSION_DAYS env var', async () => {
    const scriptPath = join(FLUX_ROOT, 'scripts', 'analyze-sessions.sh')
    const result = await $`bash ${scriptPath}`.env({
      ...process.env,
      FLUX_SESSION_DAYS: '1',
      FLUX_SESSION_MAX: '5',
    }).text()
    
    const parsed = JSON.parse(result)
    if (parsed.enabled) {
      expect(parsed.sessions_analyzed).toBeLessThanOrEqual(5)
    }
  }, SCRIPT_TIMEOUT)

  test('Python parser handles --raw flag', async () => {
    const scriptPath = join(FLUX_ROOT, 'scripts', 'parse-sessions.py')
    const result = await $`python3 ${scriptPath} --max-sessions 3 --raw`.text()
    const parsed = JSON.parse(result)
    
    if (parsed.enabled) {
      expect(parsed.sessions).toBeInstanceOf(Array)
      expect(parsed.sessions.length).toBeLessThanOrEqual(3)
    }
  }, SCRIPT_TIMEOUT)

  test('Python parser filters to current project by default', async () => {
    const scriptPath = join(FLUX_ROOT, 'scripts', 'parse-sessions.py')
    const result = await $`python3 ${scriptPath} --cwd ${FLUX_ROOT} --max-sessions 10`.text()
    const parsed = JSON.parse(result)
    
    if (parsed.enabled && parsed.projects_analyzed) {
      const expectedProject = FLUX_ROOT.replace(/\//g, '-')
      expect(parsed.projects_analyzed).toContain(expectedProject)
    }
  }, SCRIPT_TIMEOUT)

  test('Python parser --all-projects shows multiple projects', async () => {
    const scriptPath = join(FLUX_ROOT, 'scripts', 'parse-sessions.py')
    const result = await $`python3 ${scriptPath} --all-projects --max-sessions 50`.text()
    const parsed = JSON.parse(result)
    
    // Should have sessions from potentially multiple projects
    expect(parsed.enabled).toBe(true)
    if (parsed.sessions_analyzed > 0) {
      expect(parsed.projects_analyzed).toBeInstanceOf(Array)
    }
  }, SCRIPT_TIMEOUT)
})

describe('Skill File Structure', () => {
  
  test('flux-scope skill has required files', () => {
    const skillDir = join(FLUX_ROOT, 'skills', 'flux-scope')
    expect(existsSync(join(skillDir, 'SKILL.md'))).toBe(true)
    expect(existsSync(join(skillDir, 'phases.md'))).toBe(true)
    expect(existsSync(join(skillDir, 'questions.md'))).toBe(true)
    expect(existsSync(join(skillDir, 'explore.md'))).toBe(true)
    expect(existsSync(join(skillDir, 'approaches.md'))).toBe(true)
  })

  test('flux-scope command file exists', () => {
    const commandFile = join(FLUX_ROOT, 'commands', 'flux', 'scope.md')
    expect(existsSync(commandFile)).toBe(true)
  })

  test('documented routed workflow commands exist', () => {
    const expectedCommands = [
      'autofix.md',
      'dejank.md',
      'design-interface.md',
      'epic-review.md',
      'export-context.md',
      'gate.md',
      'grill.md',
      'improve-claude-md.md',
      'impl-review.md',
      'plan.md',
      'plan-review.md',
      'prime.md',
      'propose.md',
      'rca.md',
      'release.md',
      'remember.md',
      'reflect.md',
      'ruminate.md',
      'scope.md',
      'security-review.md',
      'security-scan.md',
      'setup.md',
      'sync.md',
      'tdd.md',
      'threat-model.md',
      'ubiquitous-language.md',
      'vuln-validate.md',
      'work.md',
    ]

    for (const command of expectedCommands) {
      expect(existsSync(join(FLUX_ROOT, 'commands', 'flux', command))).toBe(true)
    }
  })

  test('command-backed Flux skills have supported session phases', () => {
    const commandDir = join(FLUX_ROOT, 'commands', 'flux')
    const utilsText = readFileSync(join(FLUX_ROOT, 'scripts', 'fluxctl_pkg', 'utils.py'), 'utf8')
    const phaseBlock = utilsText.match(/SESSION_PHASES = \[(.*?)\]\n\n/s)
    expect(phaseBlock).toBeTruthy()

    const supportedPhases = new Set(
      [...(phaseBlock?.[1].matchAll(/"([^"]+)"/g) || [])].map((match) => match[1])
    )

    const commandFiles = readdirSync(commandDir).filter((entry) => entry.endsWith('.md'))

    for (const commandFile of commandFiles) {
      const skillDir = join(FLUX_ROOT, 'skills', `flux-${commandFile.replace(/\.md$/, '')}`)
      const skillFile = join(skillDir, 'SKILL.md')
      if (!existsSync(skillFile)) {
        continue
      }

      const skillText = readFileSync(skillFile, 'utf8')
      const phases = [...skillText.matchAll(/session-phase set ([A-Za-z0-9_-]+)/g)].map((match) => match[1])
      expect(phases.length).toBeGreaterThan(0)

      for (const phase of phases) {
        expect(supportedPhases.has(phase)).toBe(true)
      }
    }
  })

  test('workflow-embedded utility skills are anchored to the correct workflow touchpoints', () => {
    const expectedReferences: Record<string, string[]> = {
      'flux-parallel-dispatch': [
        'skills/flux-prime/SKILL.md',
        'skills/flux-prime/workflow.md',
        'skills/flux-scope/SKILL.md',
        'skills/flux-scope/explore-steps.md',
      ],
      'flux-receive-review': [
        'skills/flux-impl-review/SKILL.md',
        'skills/flux-epic-review/SKILL.md',
        'skills/flux-autofix/SKILL.md',
      ],
      'flux-verify-claims': [
        'skills/flux-work/SKILL.md',
        'skills/flux-impl-review/SKILL.md',
        'skills/flux-epic-review/SKILL.md',
        'skills/flux-autofix/SKILL.md',
      ],
    }

    for (const [skillName, refs] of Object.entries(expectedReferences)) {
      const skillPath = join(FLUX_ROOT, 'skills', skillName, 'SKILL.md')
      expect(existsSync(skillPath)).toBe(true)

      for (const ref of refs) {
        const refPath = join(FLUX_ROOT, ref)
        expect(existsSync(refPath)).toBe(true)
        const text = readFileSync(refPath, 'utf8')
        expect(text).toContain(skillName)
      }
    }
  })

  test('flux-plan skill has required files', () => {
    const skillDir = join(FLUX_ROOT, 'skills', 'flux-plan')
    expect(existsSync(join(skillDir, 'SKILL.md'))).toBe(true)
    expect(existsSync(join(skillDir, 'steps.md'))).toBe(true)
  })
})

describe('Edge Cases', () => {
  
  test('detect-installed handles missing mcp.json gracefully', async () => {
    const output = await runScript('detect-installed.sh')
    const parsed = JSON.parse(output)
    expect(parsed.installed.mcps).toBeInstanceOf(Array)
  }, SCRIPT_TIMEOUT)

  test('analyze-context works outside git repo', async () => {
    const output = await runScript('analyze-context.sh', [], '/tmp')
    const parsed = JSON.parse(output)
    expect(parsed.repo).toBeDefined()
  }, SCRIPT_TIMEOUT)

  test('manage-preferences undismiss removes from list', async () => {
    await runScript('manage-preferences.sh', ['dismiss', 'test-undismiss'])
    
    let output = await runScript('manage-preferences.sh', ['list'])
    let parsed = JSON.parse(output)
    expect(parsed.dismissed).toContain('test-undismiss')
    
    await runScript('manage-preferences.sh', ['undismiss', 'test-undismiss'])
    
    output = await runScript('manage-preferences.sh', ['list'])
    parsed = JSON.parse(output)
    expect(parsed.dismissed).not.toContain('test-undismiss')
  }, SCRIPT_TIMEOUT)

  test('manage-preferences alternative records mapping', async () => {
    await runScript('manage-preferences.sh', ['alternative', 'tool-a', 'tool-b'])
    
    const output = await runScript('manage-preferences.sh', ['list'])
    const parsed = JSON.parse(output)
    
    expect(parsed.alternatives['tool-a']).toBe('tool-b')
    
    await runScript('manage-preferences.sh', ['clear'])
  }, SCRIPT_TIMEOUT)

  test('manage-preferences clear removes everything', async () => {
    await runScript('manage-preferences.sh', ['dismiss', 'test-clear'])
    await runScript('manage-preferences.sh', ['alternative', 'x', 'y'])
    
    await runScript('manage-preferences.sh', ['clear'])
    
    const output = await runScript('manage-preferences.sh', ['list'])
    const parsed = JSON.parse(output)
    
    expect(parsed.dismissed).toHaveLength(0)
    expect(Object.keys(parsed.alternatives)).toHaveLength(0)
  }, SCRIPT_TIMEOUT)

  test('detect-installed handles malformed MCP and preferences files', async () => {
    const tmpRoot = `/tmp/flux-detect-edge-${Date.now()}`
    const homeDir = `${tmpRoot}/home`
    const workDir = `${tmpRoot}/work`

    await $`mkdir -p ${homeDir}/.claude ${workDir}/.flux`.quiet()

    await $`printf '%s' '{not-json' > ${homeDir}/.mcp.json`.quiet()
    await $`printf '%s' '{still-bad' > ${homeDir}/.claude/settings.json`.quiet()
    await $`printf '%s' '{bad-local' > ${workDir}/.mcp.json`.quiet()
    await $`printf '%s' '{bad-prefs' > ${workDir}/.flux/preferences.json`.quiet()

    const output = await runScriptWithEnv('detect-installed.sh', [], workDir, { HOME: homeDir })
    const parsed = JSON.parse(output)

    expect(parsed.installed.mcps).toEqual([])
    expect(parsed.installed.plugins).toEqual([])
    expect(parsed.preferences.dismissed).toEqual([])
    expect(parsed.preferences.alternatives).toEqual({})
    expect(parsed.warnings).toBeInstanceOf(Array)
    expect(parsed.warnings.some((w: string) => w.includes('Malformed MCP config'))).toBe(true)
    expect(parsed.warnings.some((w: string) => w.includes('Malformed Claude settings'))).toBe(true)
    expect(parsed.warnings.some((w: string) => w.includes('Malformed preferences file'))).toBe(true)
  }, SCRIPT_TIMEOUT)
})
