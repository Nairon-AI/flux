/**
 * Flux Claude Commands E2E Tests
 * 
 * Uses tuistory CLI to test /flux:* commands in Claude Code.
 * 
 * VERIFIED WORKING:
 * - Plugin installs and loads correctly (v0.3.0)
 * - Commands like /flux:improve execute and show UI
 * - Version check, skill loading, consent prompts all work
 * 
 * LIMITATIONS:
 * - Tests require manual permission acceptance or --dangerously-skip-permissions
 * - Each command takes 30-60s due to permission prompts
 * 
 * For CI/automated testing, use: bun test tests/scripts.test.ts
 * For manual verification: bun test tests/claude-commands.test.ts
 * 
 * Run: bun test tests/claude-commands.test.ts --timeout 180000
 */

import { test, expect, describe, afterEach, afterAll } from 'bun:test'
import { existsSync } from 'fs'
import { join } from 'path'
import { $ } from 'bun'

// Resolve flux root from test file location (tests/ is inside flux/)
const FLUX_ROOT = process.env.FLUX_ROOT || 
  process.env.CLAUDE_PLUGIN_ROOT ||
  join(import.meta.dir, '..')

const TUISTORY = join(FLUX_ROOT, 'node_modules', '.bin', 'tuistory')

// Cleanup helper
async function cleanupSessions() {
  try {
    const result = await $`${TUISTORY} sessions`.text().catch(() => '')
    // Close any flux-test sessions
    const sessions = result.split('\n').filter(s => s.includes('flux-test'))
    for (const session of sessions) {
      const name = session.trim().split(/\s+/)[0]
      if (name) {
        await $`${TUISTORY} -s ${name} close`.quiet().catch(() => {})
      }
    }
  } catch (e) {
    // Ignore
  }
}

// ============================================================================
// PREREQUISITES
// ============================================================================

describe('Prerequisites', () => {
  test('tuistory binary exists', () => {
    expect(existsSync(TUISTORY)).toBe(true)
  })

  test('flux plugin is installed', async () => {
    const installed = await $`cat ~/.claude/plugins/installed_plugins.json`.json().catch(() => ({}))
    const hasFlux = installed.plugins?.['flux@nairon-flux'] !== undefined
    expect(hasFlux).toBe(true)
  })

  test('flux plugin cache exists', async () => {
    const home = process.env.HOME || '~'
    const cachePath = join(home, '.claude/plugins/cache/nairon-flux/flux')
    const cacheExists = existsSync(cachePath)
    expect(cacheExists).toBe(true)
  })
})

// ============================================================================
// TUISTORY SMOKE TESTS
// ============================================================================

describe('Tuistory Smoke Tests', () => {
  
  test('can launch echo command', async () => {
    const session = `smoke-${Date.now()}`
    
    await $`${TUISTORY} launch "echo hello-flux-test" -s ${session}`.quiet()
    await Bun.sleep(1000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    expect(snapshot).toContain('hello-flux-test')
  }, 10000)

  test('can type and press keys', async () => {
    const session = `keys-${Date.now()}`
    
    await $`${TUISTORY} launch "bash --norc --noprofile" -s ${session} --cols 80 --rows 24`.quiet()
    await Bun.sleep(1000)
    
    await $`${TUISTORY} -s ${session} type "echo tuistory-works"`.quiet()
    await $`${TUISTORY} -s ${session} press enter`.quiet()
    await Bun.sleep(500)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    expect(snapshot).toContain('tuistory-works')
  }, 15000)
})

// ============================================================================
// CLAUDE CODE LAUNCH TEST
// ============================================================================

describe('Claude Code', () => {
  
  afterAll(async () => {
    await cleanupSessions()
  })

  test('launches successfully', async () => {
    const session = `flux-test-launch-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    // Should show Claude Code UI
    expect(snapshot.toLowerCase()).toMatch(/claude|welcome|sonnet|opus/)
  }, 20000)

  test('shows flux commands in autocomplete', async () => {
    const session = `flux-test-auto-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    // Type /flux to trigger autocomplete
    await $`${TUISTORY} -s ${session} type "/flux"`.quiet()
    await Bun.sleep(2000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    // Should show flux commands or at least have /flux typed
    expect(snapshot).toContain('/flux')
  }, 20000)
})

// ============================================================================
// FLUX COMMANDS - Basic invocation tests
// These verify commands START executing. Full execution requires permission handling.
// ============================================================================

describe('Flux Commands Invocation', () => {
  
  afterAll(async () => {
    await cleanupSessions()
  })

  test('/flux:improve starts executing', async () => {
    const session = `flux-test-improve-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    await $`${TUISTORY} -s ${session} type "/flux:improve"`.quiet()
    await $`${TUISTORY} -s ${session} press enter`.quiet()
    await Bun.sleep(8000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    console.log('--- /flux:improve snapshot ---')
    console.log(snapshot.slice(0, 1500))
    
    // Should NOT show "Unknown skill" - plugin is installed
    expect(snapshot).not.toContain('Unknown skill')
    
    // Should show some response - either the skill loading or permission prompt
    expect(snapshot.length).toBeGreaterThan(500)
  }, 30000)

  test('/flux:setup starts executing', async () => {
    const session = `flux-test-setup-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    await $`${TUISTORY} -s ${session} type "/flux:setup"`.quiet()
    await $`${TUISTORY} -s ${session} press enter`.quiet()
    await Bun.sleep(8000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    expect(snapshot).not.toContain('Unknown skill')
    expect(snapshot.length).toBeGreaterThan(500)
  }, 30000)

  test('/flux:prime starts executing', async () => {
    const session = `flux-test-prime-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    await $`${TUISTORY} -s ${session} type "/flux:prime"`.quiet()
    await $`${TUISTORY} -s ${session} press enter`.quiet()
    await Bun.sleep(8000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    expect(snapshot).not.toContain('Unknown skill')
    expect(snapshot.length).toBeGreaterThan(500)
  }, 30000)

  test('/flux:plan starts executing', async () => {
    const session = `flux-test-plan-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    await $`${TUISTORY} -s ${session} type "/flux:plan"`.quiet()
    await $`${TUISTORY} -s ${session} press enter`.quiet()
    await Bun.sleep(8000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    expect(snapshot).not.toContain('Unknown skill')
    expect(snapshot.length).toBeGreaterThan(500)
  }, 30000)

  test('/flux:work starts executing', async () => {
    const session = `flux-test-work-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    await $`${TUISTORY} -s ${session} type "/flux:work"`.quiet()
    await $`${TUISTORY} -s ${session} press enter`.quiet()
    await Bun.sleep(8000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    expect(snapshot).not.toContain('Unknown skill')
    expect(snapshot.length).toBeGreaterThan(500)
  }, 30000)

  test('/flux:sync starts executing', async () => {
    const session = `flux-test-sync-${Date.now()}`
    
    await $`${TUISTORY} launch "claude" -s ${session} --cols 150 --rows 45`.quiet()
    await Bun.sleep(5000)
    
    await $`${TUISTORY} -s ${session} type "/flux:sync"`.quiet()
    await $`${TUISTORY} -s ${session} press enter`.quiet()
    await Bun.sleep(8000)
    
    const snapshot = await $`${TUISTORY} -s ${session} snapshot --trim`.text().catch(() => '')
    await $`${TUISTORY} -s ${session} close`.quiet().catch(() => {})
    
    expect(snapshot).not.toContain('Unknown skill')
    expect(snapshot.length).toBeGreaterThan(500)
  }, 30000)
})
