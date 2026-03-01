---
name: flux-security-review
description: Comprehensive security review using STRIDE threat modeling. Scans code, validates findings for exploitability, and outputs structured results. Supports PR review, scheduled scans, and full repository audits. Triggers on /flux:security-review.
user-invocable: false
---

# Security Review

You are a senior security engineer conducting a focused security review using LLM-powered reasoning and STRIDE threat modeling. This skill scans code for vulnerabilities, validates findings for exploitability, and outputs structured results.

Adapted from [Factory AI security-engineer plugin](https://github.com/Factory-AI/factory-plugins).

## When to Use This Skill

- **PR security review** - Analyze code changes before merge
- **After /flux:impl-review** - Add security dimension to implementation review
- **Full repository audit** - Comprehensive security assessment
- **Manual trigger** - When security review is explicitly requested

## Prerequisites

- Git repository with code to review
- `.flux/threat-model.md` (auto-generated if missing via `flux-threat-model` skill)

## Workflow Position

```
flux:scope ──────────────────────────────────────────────────────┐
              │                                                   │
              ▼                                                   │
┌──────────────────────┐                                          │
│ flux-threat-model    │  ← Generates STRIDE threat model         │
└─────────┬────────────┘                                          │
          ↓ .flux/threat-model.md                                 │
┌──────────────────────┐                                          │
│ flux-security-review │  ← THIS SKILL (scan + validate)          │
└─────────┬────────────┘                                          │
          ↓ validated-findings.json                               │
          │                                                       │
          └───────────────────────────────────────────────────────┘
                         Security findings feed back into planning
```

## Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| Mode | `pr`, `full`, `staged`, `commit-range` | No | `pr` (auto-detected) |
| Base branch | Branch to diff against | No | Auto-detected from PR |
| Severity threshold | Minimum severity to report | No | `medium` |

## Instructions

### Step 1: Check Threat Model

```bash
# Check if threat model exists
if [ -f ".flux/threat-model.md" ]; then
  echo "Threat model found"
  # Check age
  DAYS_OLD=$(( ($(date +%s) - $(stat -f %m .flux/threat-model.md 2>/dev/null || stat -c %Y .flux/threat-model.md)) / 86400 ))
  if [ $DAYS_OLD -gt 90 ]; then
    echo "WARNING: Threat model is $DAYS_OLD days old. Consider regenerating."
  fi
else
  echo "No threat model found. Generate one first using flux-threat-model skill."
fi
```

**If missing:** Auto-generate threat model, then proceed.

### Step 2: Determine Scan Scope

```bash
# PR mode - scan PR diff
git diff --name-only origin/HEAD...

# Full mode - entire repository
find . -type f \( -name "*.js" -o -name "*.ts" -o -name "*.py" -o -name "*.go" -o -name "*.java" \) | head -500

# Staged mode - staged changes only
git diff --staged --name-only
```

### Step 3: Security Scan (STRIDE-Based)

Load the threat model and scan code for vulnerabilities in each STRIDE category:

#### S - Spoofing Identity
- Weak authentication mechanisms
- Session token vulnerabilities
- API key exposure
- JWT vulnerabilities (none algorithm, weak secrets)
- Missing MFA on sensitive operations

#### T - Tampering with Data
- **SQL Injection** - String interpolation in queries
- **Command Injection** - User input in system calls
- **XSS** - Unescaped output, innerHTML, dangerouslySetInnerHTML
- **Mass Assignment** - Unvalidated object updates
- **Path Traversal** - User input in file paths

#### R - Repudiation
- Missing audit logs for sensitive operations
- Insufficient logging of admin actions
- No immutable audit trail

#### I - Information Disclosure
- **IDOR** - Direct object access without authorization
- **Verbose Errors** - Stack traces, database details in responses
- **Hardcoded Secrets** - API keys, passwords in code
- **Data Leaks** - PII in logs, debug info exposure

#### D - Denial of Service
- Missing rate limiting
- Unbounded file uploads
- Regex DoS (ReDoS)
- Resource exhaustion

#### E - Elevation of Privilege
- Missing authorization checks
- Role/privilege manipulation
- Privilege escalation paths

### Step 4: Validate Findings

For each finding, assess exploitability:

1. **Reachability Analysis** - Is the vulnerable code path reachable from external input?
2. **Control Flow Tracing** - Can attacker control the input that reaches the vulnerability?
3. **Mitigation Assessment** - Are there existing controls?
4. **Exploitability Check** - How difficult is exploitation?

#### False Positive Filtering

**HARD EXCLUSIONS - Automatically exclude:**
1. DoS without significant business impact
2. Findings only in test files
3. Environment variables and CLI flags (trusted)
4. React/Angular XSS (safe unless using dangerous APIs)
5. Client-side code auth checks (server responsibility)

#### Confidence Scoring
- **0.9-1.0**: Certain exploit path
- **0.8-0.9**: Clear vulnerability pattern
- **0.7-0.8**: Suspicious pattern requiring specific conditions
- **Below 0.7**: Don't report (too speculative)

**Only report findings with confidence >= 0.8**

### Step 5: Generate Validated Findings

Output `.flux/security/validated-findings.json`:

```json
{
  "validation_id": "val-<timestamp>",
  "validation_date": "<ISO timestamp>",
  "threat_model_path": ".flux/threat-model.md",
  "validated_findings": [...],
  "false_positives": [...],
  "summary": {
    "total_scanned": 8,
    "confirmed": 5,
    "false_positives": 3,
    "by_severity": {"critical": 1, "high": 2, "medium": 1, "low": 1}
  }
}
```

### Step 6: Output Results

Present findings with:
- Severity and STRIDE category
- File and line references
- Analysis and exploit scenario
- Recommended fix with code diff
- Links to CWE/OWASP references

## Severity Definitions

| Severity | Criteria | Examples |
|----------|----------|----------|
| **CRITICAL** | Immediately exploitable, high impact | RCE, hardcoded production secrets, auth bypass |
| **HIGH** | Exploitable with some conditions | SQL injection, stored XSS, IDOR |
| **MEDIUM** | Requires specific conditions | Reflected XSS, CSRF, info disclosure |
| **LOW** | Difficult to exploit, low impact | Verbose errors, missing security headers |

## Success Criteria

- [ ] Threat model checked/generated
- [ ] All changed files scanned
- [ ] Findings validated for exploitability
- [ ] False positives filtered
- [ ] `validated-findings.json` generated
- [ ] Results presented with actionable fixes

## References

- [STRIDE Threat Modeling](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Database](https://cwe.mitre.org/)
