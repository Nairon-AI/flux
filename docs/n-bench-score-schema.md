# N-bench Score Schema

AI-native capability scoring system built on Claude Code session data.

## Overview

N-bench measures how effectively an engineer works with AI coding agents. The score is computed from observable session data—not self-reported surveys or vibes.

**Primary use case**: CTOs verifying AI-native capability before hiring or promoting.

## Data Sources

Built on [ccql](https://github.com/douglance/ccql) tables:

| Table | What it captures |
|-------|------------------|
| `history` | User prompts with timestamps and project context |
| `transcripts` | Full conversation logs: user messages, tool calls, tool results |
| `todos` | Task tracking within sessions |

## Raw Metrics

### From `history` table

```sql
-- Prompt volume and patterns
SELECT 
  COUNT(*) as total_prompts,
  AVG(LENGTH(display)) as avg_prompt_length,
  COUNT(DISTINCT DATE(timestamp/1000, 'unixepoch')) as active_days
FROM history
WHERE timestamp > :window_start;
```

### From `transcripts` table

```sql
-- Session structure analysis
SELECT 
  _session_id,
  COUNT(*) FILTER (WHERE type = 'user') as user_messages,
  COUNT(*) FILTER (WHERE type = 'tool_use') as tool_calls,
  COUNT(DISTINCT tool_name) as tools_used,
  MIN(timestamp) as session_start,
  MAX(timestamp) as session_end
FROM transcripts
GROUP BY _session_id;
```

```sql
-- Tool usage patterns
SELECT 
  tool_name,
  COUNT(*) as usage_count
FROM transcripts 
WHERE type = 'tool_use'
GROUP BY tool_name
ORDER BY usage_count DESC;
```

## Computed Dimensions

### 1. Interview Depth (`interview_score`: 0-100)

Measures whether the engineer uses structured problem exploration before implementation.

**Signals**:
- Presence of interview/planning phases before code generation
- Number of clarifying questions asked
- Edge cases surfaced during planning
- Requirements validated before implementation

```sql
-- Detect interview-style sessions
SELECT 
  _session_id,
  COUNT(*) FILTER (WHERE content LIKE '%edge case%' OR content LIKE '%what if%' OR content LIKE '%consider%') as exploration_signals,
  COUNT(*) FILTER (WHERE tool_name = 'TodoWrite') as planning_signals
FROM transcripts
WHERE type = 'user' OR type = 'tool_use'
GROUP BY _session_id;
```

**Scoring**:
- 0-20: No planning, jumps straight to "implement X"
- 21-50: Some questions, but shallow
- 51-80: Structured exploration, surfaces edge cases
- 81-100: Comprehensive interview with documented requirements

### 2. Pushback Ratio (`pushback_score`: 0-100)

Measures whether the engineer critically evaluates AI suggestions vs. rubber-stamping.

**Signals**:
- Disagreements with AI suggestions
- Requests for alternatives
- "No, instead..." or "Actually..." patterns
- Iteration after reviewing AI output

```sql
-- Detect pushback patterns
SELECT 
  _session_id,
  COUNT(*) FILTER (WHERE 
    content LIKE '%no,%' OR 
    content LIKE '%instead%' OR 
    content LIKE '%actually%' OR
    content LIKE '%wrong%' OR
    content LIKE '%different approach%'
  ) as pushback_count,
  COUNT(*) FILTER (WHERE type = 'user') as total_user_messages
FROM transcripts
GROUP BY _session_id;
```

**Scoring**:
- 0-20: Accepts everything (red flag)
- 21-40: Rare pushback
- 51-70: Healthy skepticism
- 71-100: Active collaboration with corrections

### 3. Prompt Specificity (`prompt_quality_score`: 0-100)

Measures precision and context in prompts vs. vague requests.

**Signals**:
- Prompt length distribution
- File/line references included
- Acceptance criteria specified
- Context provided upfront

```sql
-- Prompt quality indicators
SELECT 
  _session_id,
  AVG(LENGTH(content)) as avg_prompt_length,
  COUNT(*) FILTER (WHERE content LIKE '%file%' OR content LIKE '%.ts%' OR content LIKE '%.py%') as file_references,
  COUNT(*) FILTER (WHERE content LIKE '%should%' OR content LIKE '%must%' OR content LIKE '%criteria%') as requirement_signals
FROM transcripts
WHERE type = 'user'
GROUP BY _session_id;
```

**Scoring**:
- 0-20: "fix it", "make it work" (no context)
- 21-50: Some context, but vague goals
- 51-80: Clear context and acceptance criteria
- 81-100: Comprehensive specs with edge cases

### 4. Iteration Efficiency (`efficiency_score`: 0-100)

Measures prompts-to-completion ratio and rework cycles.

**Signals**:
- Messages per completed todo
- Tool error recovery patterns
- Rework/undo frequency
- Session completion rate

```sql
-- Efficiency metrics per session
SELECT 
  t._session_id,
  COUNT(*) FILTER (WHERE t.type = 'user') as prompts,
  COUNT(*) FILTER (WHERE td.status = 'completed') as completed_todos,
  COUNT(*) FILTER (WHERE t.type = 'tool_result' AND t.tool_output LIKE '%error%') as errors
FROM transcripts t
LEFT JOIN todos td ON t._session_id = td._workspace_id
GROUP BY t._session_id;
```

**Scoring**:
- 0-20: Many prompts, few completions, high error rate
- 21-50: Average efficiency
- 51-80: Good prompt-to-completion ratio
- 81-100: Minimal prompts, clean execution

### 5. Tool Breadth (`tool_score`: 0-100)

Measures appropriate tool usage across SDLC phases.

**Signals**:
- Diversity of tools used
- Context-appropriate tool selection
- MCP usage for external context
- Structured outputs (TodoWrite, etc.)

```sql
-- Tool diversity
SELECT 
  _session_id,
  COUNT(DISTINCT tool_name) as unique_tools,
  COUNT(*) FILTER (WHERE tool_name IN ('Read', 'Grep', 'Glob')) as research_tools,
  COUNT(*) FILTER (WHERE tool_name IN ('Edit', 'Write')) as implementation_tools,
  COUNT(*) FILTER (WHERE tool_name = 'Bash') as execution_tools,
  COUNT(*) FILTER (WHERE tool_name = 'TodoWrite') as planning_tools
FROM transcripts
WHERE type = 'tool_use'
GROUP BY _session_id;
```

**Scoring**:
- 0-20: Single tool reliance
- 21-50: Basic tool usage
- 51-80: Appropriate tool selection per task
- 81-100: Full toolchain mastery

## Composite Score

```
N-bench Score = (
  interview_score * 0.25 +
  pushback_score * 0.20 +
  prompt_quality_score * 0.25 +
  efficiency_score * 0.15 +
  tool_score * 0.15
)
```

Weights emphasize **thinking quality** over raw productivity.

## Output Format

### Summary Card

```yaml
engineer: obaid@nairon.ai
period: 2026-02-01 to 2026-02-23
sessions_analyzed: 47

score: 78
grade: A-

dimensions:
  interview_depth: 82
  pushback_ratio: 71
  prompt_quality: 85
  iteration_efficiency: 68
  tool_breadth: 74

strengths:
  - Strong problem exploration before implementation
  - High-quality, specific prompts with context
  - Good tool diversity across SDLC phases

growth_areas:
  - Could push back more on AI suggestions
  - Some sessions show high rework cycles

percentile: 89  # vs. other N-bench users
```

### Evidence Export (for CTOs)

```yaml
evidence:
  sample_sessions:
    - id: ses_abc123
      score: 92
      highlights:
        - "Surfaced 4 edge cases during interview phase"
        - "Pushed back on initial architecture suggestion"
        - "Clean 6-prompt feature completion"
    - id: ses_def456
      score: 58
      concerns:
        - "No planning phase, jumped to implementation"
        - "12 prompts for simple feature"
  
  raw_metrics:
    total_sessions: 47
    avg_prompts_per_session: 8.3
    tool_call_distribution: { Read: 234, Edit: 189, Bash: 145, ... }
    pushback_rate: 0.23
```

## Privacy & Data Handling

- All analysis runs **locally** on user's machine
- Raw session data never leaves device
- Only aggregate scores shared (opt-in)
- CTOs see evidence exports only with engineer consent

## Integration Points

### CLI

```bash
# Generate your score
nbench score

# Export evidence for job application
nbench export --period 30d --format yaml > evidence.yaml

# Compare against benchmarks
nbench compare --percentile
```

### CI/CD (Team Mode)

```yaml
# .github/workflows/nbench.yml
- name: Team N-bench report
  run: nbench team-report --output report.md
  env:
    NBENCH_TEAM_KEY: ${{ secrets.NBENCH_KEY }}
```

## Roadmap

1. **v1**: Local scoring from ccql data
2. **v2**: Team aggregation with privacy controls
3. **v3**: Recruiting integration (Qua pilot)
4. **v4**: Real-time session coaching
