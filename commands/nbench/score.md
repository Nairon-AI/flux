---
name: nbench:score
description: Compute AI-native capability score from Claude Code session data
argument-hint: "[--since YYYY-MM-DD] [--until YYYY-MM-DD] [--format table|json|yaml] [--export FILE]"
---

# N-bench Score

Compute your AI-native capability score from Claude Code session data.

## Usage

Run the scoring script:

```bash
python3 "${CLAUDE_PLUGIN_ROOT:-${DROID_PLUGIN_ROOT}}/scripts/nbench-score.py" $ARGUMENTS
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
