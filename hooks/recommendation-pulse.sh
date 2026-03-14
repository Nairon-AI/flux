#!/bin/bash
# Recommendation Pulse — lightweight session health check
# Runs at session start to surface: (1) new tool recommendations, (2) brain vault maintenance needs.
# Rate-limited to once per day. Fails gracefully — never blocks session start.

set -euo pipefail

PULSE_FILE="$HOME/.flux/last_pulse"
MEDITATE_FILE="$HOME/.flux/last_meditate"
RECS_DIR="$HOME/.flux/recommendations"
NOW_TS=$(date +%s)

# --- Rate limit: once per day ---
if [ -f "$PULSE_FILE" ]; then
  LAST_PULSE=$(cat "$PULSE_FILE" 2>/dev/null || echo "0")
  LAST_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_PULSE" +%s 2>/dev/null || date -d "$LAST_PULSE" +%s 2>/dev/null || echo "0")
  ELAPSED=$(( NOW_TS - LAST_TS ))
  if [ "$ELAPSED" -lt 86400 ]; then
    exit 0  # Already pulsed today
  fi
fi

# --- Ensure .flux dir exists ---
mkdir -p "$HOME/.flux"

NUDGES=""

# === Part 1: Recommendation Pulse ===
# Quick pull of recommendations repo (cached, <1s if up to date)
if [ -d "$RECS_DIR/.git" ]; then
  git -C "$RECS_DIR" pull --ff-only -q 2>/dev/null || true
fi
# Don't clone on first run — that's /flux:improve's job. Just check if cached.

if [ -d "$RECS_DIR" ]; then
  # Count recommendations added since last pulse
  if [ -f "$PULSE_FILE" ]; then
    LAST_PULSE_DATE=$(cat "$PULSE_FILE" 2>/dev/null || echo "1970-01-01")
    # Find YAML files modified after last pulse (new recommendations)
    NEW_RECS=$(find "$RECS_DIR" -name "*.yaml" -not -path "*/pending/*" -not -name "schema.yaml" -not -name "accounts.yaml" -newer "$PULSE_FILE" 2>/dev/null | wc -l | tr -d ' ')
  else
    NEW_RECS=0
  fi

  if [ "${NEW_RECS:-0}" -gt 0 ]; then
    NUDGES="${NUDGES}• ${NEW_RECS} new recommendation(s) available — run \`/flux:improve\` to review\n"
  fi
fi

# Quick check: has /flux:improve ever been run?
IMPROVE_FILE="$HOME/.flux/last_improve"
if [ ! -f "$IMPROVE_FILE" ]; then
  NUDGES="${NUDGES}• You haven't run \`/flux:improve\` yet — it analyzes your workflow and recommends tools for your stack\n"
else
  # Check if it's been > 14 days
  LAST_IMPROVE=$(cat "$IMPROVE_FILE" 2>/dev/null || echo "1970-01-01T00:00:00Z")
  IMPROVE_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_IMPROVE" +%s 2>/dev/null || date -d "$LAST_IMPROVE" +%s 2>/dev/null || echo "0")
  IMPROVE_AGO=$(( (NOW_TS - IMPROVE_TS) / 86400 ))
  if [ "$IMPROVE_AGO" -ge 14 ]; then
    NUDGES="${NUDGES}• It's been ${IMPROVE_AGO} days since last \`/flux:improve\` — new tools may have been added\n"
  fi
fi

# === Part 2: Brain Vault Health Check ===
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
PITFALLS_DIR="$REPO_ROOT/brain/pitfalls"

if [ -d "$PITFALLS_DIR" ]; then
  # Count total pitfall files
  PITFALL_COUNT=$(find "$PITFALLS_DIR" -name "*.md" 2>/dev/null | wc -l | tr -d ' ')

  # Count pitfall files added since last meditate
  if [ -f "$MEDITATE_FILE" ]; then
    LAST_MED_DATE=$(cat "$MEDITATE_FILE" 2>/dev/null || echo "1970-01-01")
    NEW_PITFALLS=$(find "$PITFALLS_DIR" -name "*.md" -newer "$MEDITATE_FILE" 2>/dev/null | wc -l | tr -d ' ')
    MED_TS=$(date -j -f "%Y-%m-%dT%H:%M:%SZ" "$LAST_MED_DATE" +%s 2>/dev/null || date -d "$LAST_MED_DATE" +%s 2>/dev/null || echo "0")
    MED_AGO=$(( (NOW_TS - MED_TS) / 86400 ))
  else
    NEW_PITFALLS="$PITFALL_COUNT"
    MED_AGO=999
  fi

  # Suggest meditate if: 5+ new pitfalls since last meditate, OR never meditated and 10+ pitfalls exist
  if [ "${NEW_PITFALLS:-0}" -ge 5 ]; then
    NUDGES="${NUDGES}• Brain vault has ${NEW_PITFALLS} new pitfalls since last meditation — run \`/flux:meditate\` to prune and promote\n"
  elif [ "$MED_AGO" -ge 999 ] && [ "${PITFALL_COUNT:-0}" -ge 10 ]; then
    NUDGES="${NUDGES}• Brain vault has ${PITFALL_COUNT} pitfalls but has never been meditated — run \`/flux:meditate\` to audit\n"
  elif [ "$MED_AGO" -ge 30 ] && [ "${PITFALL_COUNT:-0}" -ge 5 ]; then
    NUDGES="${NUDGES}• It's been ${MED_AGO} days since last \`/flux:meditate\` — brain vault may need pruning\n"
  fi
fi

# === Output ===
if [ -n "$NUDGES" ]; then
  echo ""
  echo "Session health check:"
  echo -e "$NUDGES"
fi

# Update pulse timestamp
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$PULSE_FILE"
