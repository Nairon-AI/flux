---
name: flux:login
description: Connect Flux to your Universe profile via device flow
argument-hint: ""
---

# Flux Login

Connect your local Flux install to Universe using device authentication.

## Usage

Run login, then run score once to seed initial Universe stats sync:

```bash
# Detect plugin root (Claude Code doesn't always set CLAUDE_PLUGIN_ROOT)
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"
if [ -z "$PLUGIN_ROOT" ]; then
  # Fallback: find latest version in plugin cache
  PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
fi

python3 "${PLUGIN_ROOT}/scripts/flux-auth.py" login
LOGIN_EXIT=$?
if [ $LOGIN_EXIT -ne 0 ]; then
  exit $LOGIN_EXIT
fi

echo "Running first score + sync..."
python3 "${PLUGIN_ROOT}/scripts/flux-score.py"
```

## What happens

1. Flux requests a device code from Universe
2. Flux opens your browser to Universe sign-in
3. You approve access in browser
4. Flux saves a local `flux_` token for automatic sync
5. Flux runs one score pass immediately so Universe receives first stats snapshot
