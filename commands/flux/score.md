---
name: flux:score
description: Compute AI-native capability score from Claude Code session data
argument-hint: "[--since YYYY-MM-DD] [--until YYYY-MM-DD] [--format table|json|yaml] [--export FILE]"
---

# Flux Score

Compute your AI-native capability score from Claude Code session data.

## Usage

Run the scoring script. The plugin root is detected automatically:

```bash
# Detect plugin root (Claude Code doesn't always set CLAUDE_PLUGIN_ROOT)
PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}"
if [ -z "$PLUGIN_ROOT" ]; then
  # Fallback: find latest version in plugin cache
  PLUGIN_ROOT=$(ls -td ~/.claude/plugins/cache/nairon-flux/flux/*/ 2>/dev/null | head -1)
fi

python3 "${PLUGIN_ROOT}/scripts/flux-score.py" $ARGUMENTS
```

## Arguments

- `--since YYYY-MM-DD` - Only analyze sessions from this date
- `--until YYYY-MM-DD` - Only analyze sessions until this date  
- `--format table|json|yaml` - Output format (default: table)
- `--export FILE` - Export score to YAML file for recruiting/evidence

## Dimensions

| Dimension | Weight | What it measures |
|-----------|--------|------------------|
| Interview Depth | 25% | Exploration before implementation |
| Pushback Ratio | 20% | Critical evaluation of AI suggestions |
| Prompt Quality | 25% | Specificity, file refs, requirements |
| Iteration Efficiency | 15% | Prompts-to-completion, error rate |
| Tool Breadth | 15% | Diversity across SDLC phases |

## Grades

- **S** (90+): Elite AI-native engineer
- **A** (80-89): Strong AI collaboration skills
- **B** (70-79): Good fundamentals, room to grow
- **C** (60-69): Developing AI workflow
- **D** (50-59): Early stages
- **F** (<50): Needs significant improvement
