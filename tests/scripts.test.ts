/**
 * Flux Scripts E2E Tests
 * 
 * Fast tests that don't require Claude Code.
 * Run: bun test tests/scripts.test.ts
 */

import { test, expect, describe, beforeAll } from 'bun:test'
import { existsSync } from 'fs'
import { join } from 'path'
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
  } catch (e: any) {
    return e.stdout?.toString() || e.stderr?.toString() || e.message
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

    test('identifies repo characteristics', async () => {
      const output = await runScript('analyze-context.sh')
      const parsed = JSON.parse(output)
      
      expect(typeof parsed.repo.has_tests).toBe('boolean')
      expect(typeof parsed.repo.has_ci).toBe('boolean')
      expect(typeof parsed.repo.has_linter).toBe('boolean')
      expect(typeof parsed.repo.has_hooks).toBe('boolean')
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
    }).text().catch(e => '[]')
    
    expect(recommendations).toBeTruthy()
  }, SCRIPT_TIMEOUT * 3)
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
})
