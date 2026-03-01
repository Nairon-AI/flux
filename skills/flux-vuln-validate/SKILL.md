---
name: flux-vuln-validate
description: Validate security findings by assessing exploitability, filtering false positives, and generating proof-of-concept exploits. Use after running flux-security-scan to confirm vulnerabilities. Triggers on /flux:vuln-validate.
user-invocable: false
---

# Vulnerability Validation

Validate security findings by assessing whether they are actually exploitable in the context of this codebase. This skill filters false positives, confirms real vulnerabilities, and generates proof-of-concept exploits.

Adapted from [Factory AI security-engineer plugin](https://github.com/Factory-AI/factory-plugins).

## When to Use This Skill

- **After flux-security-scan** - Validate findings before blocking PRs
- **HIGH/CRITICAL findings** - Prioritize validation of severe findings
- **Before patching** - Confirm vulnerability is real before investing in fixes
- **Security review** - Deep-dive validation of specific findings

## Prerequisites

- `.flux/threat-model.md` must exist (from `flux-threat-model` skill)
- `.flux/security/security-findings.json` must exist (from `flux-security-scan` skill)

## Inputs

| Input           | Description                                      | Required | Default                    |
| --------------- | ------------------------------------------------ | -------- | -------------------------- |
| Findings file   | Path to `security-findings.json`                 | Yes      | `.flux/security/security-findings.json` |
| Threat model    | Path to threat model                             | No       | `.flux/threat-model.md`    |
| Finding IDs     | Specific findings to validate (comma-separated)  | No       | All findings               |
| Severity filter | Only validate findings at or above this severity | No       | All severities             |

## Instructions

Follow these steps for each finding to validate:

### Step 1: Load Context

1. Read `.flux/security/security-findings.json` from `flux-security-scan`
2. Read `.flux/threat-model.md` for system context
3. Identify which findings to validate based on inputs

### Step 2: Reachability Analysis

For each finding, determine if the vulnerable code is reachable:

1. **Trace entry points**
   - Can external users reach this code path?
   - What HTTP endpoints, CLI commands, or event handlers lead here?
   - Is authentication required to reach this code?

2. **Map the call chain**
   - Starting from the entry point, trace the path to the vulnerable code
   - Document each function call in the chain
   - Note any branching conditions that must be satisfied

3. **Classify reachability**
   - `EXTERNAL` - Reachable from unauthenticated external input
   - `AUTHENTICATED` - Requires valid user session
   - `INTERNAL` - Only reachable from internal services
   - `UNREACHABLE` - Dead code or blocked by conditions

### Step 3: Control Flow Analysis

Determine if an attacker can control the vulnerable input:

1. **Identify the source** - Where does the tainted data originate?
2. **Trace data flow** - Follow from source to sink, note transformations
3. **Assess attacker control** - Can they fully control the input?

### Step 4: Mitigation Assessment

Check if existing security controls prevent exploitation:

1. **Input validation** - Is input validated before reaching vulnerable code?
2. **Framework protections** - ORM parameterization, React XSS escaping, etc.
3. **Security middleware** - WAF rules, rate limiting, CSP headers
4. **Reference threat model** - Check existing mitigations section

### Step 5: Exploitability Assessment

| Rating            | Criteria                                                            |
| ----------------- | ------------------------------------------------------------------- |
| `EASY`            | No special conditions, standard tools, publicly known technique     |
| `MEDIUM`          | Requires specific conditions, timing, or chained vulnerabilities    |
| `HARD`            | Requires insider knowledge, rare conditions, or advanced techniques |
| `NOT_EXPLOITABLE` | Theoretical vulnerability but not practically exploitable           |

### Step 6: Generate Proof-of-Concept

For confirmed vulnerabilities, create a proof-of-concept:

```json
{
  "proof_of_concept": {
    "payload": "' OR '1'='1",
    "request": "GET /api/users?search=' OR '1'='1",
    "expected_behavior": "Returns users matching search term",
    "actual_behavior": "Returns all users due to SQL injection"
  }
}
```

### Step 7: Calculate CVSS Score

Assign a CVSS 3.1 score based on:

| Metric                   | Options                                            |
| ------------------------ | -------------------------------------------------- |
| Attack Vector (AV)       | Network (N), Adjacent (A), Local (L), Physical (P) |
| Attack Complexity (AC)   | Low (L), High (H)                                  |
| Privileges Required (PR) | None (N), Low (L), High (H)                        |
| User Interaction (UI)    | None (N), Required (R)                             |
| Scope (S)                | Unchanged (U), Changed (C)                         |
| Confidentiality (C)      | None (N), Low (L), High (H)                        |
| Integrity (I)            | None (N), Low (L), High (H)                        |
| Availability (A)         | None (N), Low (L), High (H)                        |

### Step 8: Classify Finding

| Status                | Meaning                                        |
| --------------------- | ---------------------------------------------- |
| `CONFIRMED`           | Vulnerability is real and exploitable          |
| `LIKELY`              | Probably exploitable but couldn't fully verify |
| `FALSE_POSITIVE`      | Not actually a vulnerability (document why)    |
| `NEEDS_MANUAL_REVIEW` | Requires human security expert review          |

### Step 9: Generate Output

Create `.flux/security/validated-findings.json`:

```json
{
  "validation_id": "val-<timestamp>",
  "validation_date": "<ISO timestamp>",
  "scan_id": "<from security-findings.json>",
  "validated_findings": [
    {
      "id": "VULN-001",
      "status": "CONFIRMED",
      "validated_severity": "HIGH",
      "exploitability": "EASY",
      "reachability": "EXTERNAL",
      "exploitation_path": ["Step 1", "Step 2", "..."],
      "proof_of_concept": {...},
      "cvss_vector": "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:N",
      "cvss_score": 9.1
    }
  ],
  "false_positives": [
    {
      "id": "VULN-003",
      "reason": "Input validated by schema in middleware",
      "evidence": "See src/middleware/validation.js:45"
    }
  ],
  "summary": {
    "total_analyzed": 10,
    "confirmed": 5,
    "likely": 2,
    "false_positives": 2,
    "needs_manual_review": 1
  }
}
```

## Success Criteria

- [ ] All specified findings have been analyzed
- [ ] Each finding has a status
- [ ] Confirmed findings have exploitation paths documented
- [ ] Confirmed findings have proof-of-concept exploits
- [ ] False positives have clear reasoning
- [ ] CVSS scores calculated for confirmed findings

## References

- [CVSS 3.1 Calculator](https://www.first.org/cvss/calculator/3.1)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)
