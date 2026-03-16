---
name: flux:login
description: Connect Flux to your Universe profile and activate Pro license
argument-hint: ""
---

# Flux Login

Connect your local Flux install to Universe and optionally activate Flux Pro.

## Usage

```bash
# Detect plugin root (Claude Code doesn't always set CLAUDE_PLUGIN_ROOT)
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"
if [ -z "$PLUGIN_ROOT" ]; then
  # Fallback: find latest version in plugin cache
  PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
fi
```

### Step 1: Flux Pro License (optional)

Ask the user if they have a Flux Pro license key:

```
Do you have a Flux Pro license key?

  [y] Yes, I have a key
  [n] No / Skip

Flux Pro unlocks stack-aware recommendations ranked by community data.
Start your free 1-week trial ($10/mo after):
→ https://buy.polar.sh/polar_cl_mvTstXLrEX4XyDe0dzS7WMdpnaSCmxPkIVjq01dbj0D
```

**If yes**: Ask them to paste their key, then activate:

```bash
python3 "${PLUGIN_ROOT}/scripts/flux-license.py" activate "$LICENSE_KEY"
```

**If no**: Continue without Pro. Display:

```
No problem! You can start a free trial anytime:
→ https://buy.polar.sh/polar_cl_mvTstXLrEX4XyDe0dzS7WMdpnaSCmxPkIVjq01dbj0D
After checkout, check your email for the license key, then run /flux:login

Continuing with Universe login...
```

### Step 2: Universe Login (device flow)

```bash
python3 "${PLUGIN_ROOT}/scripts/flux-auth.py" login
LOGIN_EXIT=$?
if [ $LOGIN_EXIT -ne 0 ]; then
  exit $LOGIN_EXIT
fi
```

### Step 3: Initial Score Sync

```bash
echo "Running first score + sync..."
python3 "${PLUGIN_ROOT}/scripts/flux-score.py"
```

### Step 4: Summary

Display connection summary:

```
Setup complete!

Universe: Connected as @<handle>
License:  <Pro (active) | Free>

Next steps:
  /flux:improve  — Get workflow recommendations
  /flux:score    — Check your workflow score
  /flux:plan     — Plan your next feature
```

## What happens

1. (Optional) User pastes Flux Pro license key → validated via Polar API → stored locally
2. Flux requests a device code from Universe
3. Flux opens your browser to Universe sign-in
4. You approve access in browser
5. Flux saves a local `flux_` token for automatic sync
6. Flux runs one score pass immediately so Universe receives first stats snapshot
