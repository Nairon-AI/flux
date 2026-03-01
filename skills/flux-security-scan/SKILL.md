---
name: flux-security-scan
description: Analyze code changes for security vulnerabilities using LLM reasoning and threat model patterns. Use for PR reviews, pre-commit checks, or branch comparisons. Triggers on /flux:security-scan.
user-invocable: false
---

# Security Scan

Analyze code changes (commits, PRs, diffs) using LLM-powered reasoning to detect security vulnerabilities. This skill reads code directly and applies patterns from the repository's threat model to identify issues across all STRIDE categories.

Adapted from [Factory AI security-engineer plugin](https://github.com/Factory-AI/factory-plugins).

## When to Use This Skill

- **PR review** - Automated security scan on pull requests
- **Pre-commit check** - Scan staged changes before committing
- **Branch comparison** - Review security of feature branch changes
- **After /flux:work** - Verify task implementation is secure
- **Code review assistance** - Help reviewers spot security issues

## Prerequisites

This skill requires:

1. **Threat model** - `.flux/threat-model.md` must exist
2. **Security config** - `.flux/security-config.json` for severity thresholds

**IMPORTANT: If these files don't exist, you MUST generate them first using the `flux-threat-model` skill before proceeding with the security scan.**

## Inputs

The skill determines what to scan from the user's request:

| Scan Type         | How to Specify             | Example                                      |
| ----------------- | -------------------------- | -------------------------------------------- |
| PR                | "Scan PR #123"             | `Scan PR #456 for security vulnerabilities`  |
| Commit range      | "Scan commits X..Y"        | `Scan commits abc123..def456`                |
| Single commit     | "Scan commit X"            | `Scan commit abc123`                         |
| Staged changes    | "Scan staged changes"      | `Scan my staged changes for security issues` |
| Uncommitted       | "Scan uncommitted changes" | `Scan working directory changes`             |
| Branch comparison | "Scan from X to Y"         | `Scan changes from main to feature-branch`   |
| Last N commits    | "Scan last N commits"      | `Scan the last 3 commits`                    |

If no scope is specified, defaults to scanning staged changes.

## Instructions

Follow these steps in order:

### Step 1: Verify Prerequisites (Auto-Generate if Missing)

Try to read these files:

- `.flux/threat-model.md`
- `.flux/security-config.json`

**If either file is missing or cannot be read:**

1. Inform the user: "The security threat model doesn't exist yet. I'll generate it first - this may take a minute."
2. Invoke the `flux-threat-model` skill to analyze the repository and create both files
3. Once generation completes, continue with Step 2

### Step 2: Get Changed Files

Based on the user's request, get the list of changed files and their diffs using git:

- For PRs: use `gh pr diff`
- For commits/ranges: use `git diff` or `git show`
- For staged changes: use `git diff --cached`

Read the full content of each changed file for context.

### Step 3: Load Threat Model

Read `.flux/threat-model.md` and `.flux/security-config.json` to understand:

- The system's architecture and trust boundaries
- Known vulnerability patterns for this codebase
- Severity thresholds for findings

### Step 4: Analyze for Vulnerabilities

For each changed file, systematically check for STRIDE threats:

#### S - Spoofing Identity

- Missing or weak authentication checks
- Session handling vulnerabilities
- Token/credential exposure in code
- Insecure cookie settings

#### T - Tampering with Data

- **SQL Injection**: String concatenation/interpolation in SQL queries
- **Command Injection**: User input in shell commands, `eval()`, `exec()`
- **XSS**: Unescaped user input in HTML/templates
- **Mass Assignment**: Blind assignment from request to model
- **Path Traversal**: User input in file paths without validation

#### R - Repudiation

- Missing audit logging for sensitive operations
- Insufficient error logging
- Log injection vulnerabilities

#### I - Information Disclosure

- **IDOR**: Direct object access without ownership verification
- Verbose error messages exposing internals
- Hardcoded secrets, API keys, credentials
- Sensitive data in logs or responses
- Debug endpoints exposed

#### D - Denial of Service

- Missing rate limiting on endpoints
- Unbounded resource consumption (file uploads, queries)
- Algorithmic complexity attacks (regex, sorting)
- Missing pagination on list endpoints

#### E - Elevation of Privilege

- Missing authorization checks on endpoints
- Role/permission bypass opportunities
- Privilege escalation through parameter manipulation

### Step 5: Assess Each Finding

For each potential vulnerability:

1. **Trace data flow**: Follow user input from source to sink
2. **Check for existing mitigations**: Validation elsewhere? Framework protections?
3. **Determine severity**: CRITICAL, HIGH, MEDIUM, LOW
4. **Assess confidence**: HIGH (clear pattern), MEDIUM (possible), LOW (suspicious)

### Step 6: Generate Report

Create `.flux/security/security-findings.json` with findings. Present summary to user with:

- Total findings by severity
- STRIDE category breakdown
- Files with issues
- Recommended fixes

## CWE Reference

Common CWE mappings for findings:

| Vulnerability Type       | CWE     |
| ------------------------ | ------- |
| SQL Injection            | CWE-89  |
| Command Injection        | CWE-78  |
| XSS (Reflected/Stored)   | CWE-79  |
| Path Traversal           | CWE-22  |
| IDOR                     | CWE-639 |
| Missing Authentication   | CWE-306 |
| Missing Authorization    | CWE-862 |
| Hardcoded Credentials    | CWE-798 |
| Sensitive Data Exposure  | CWE-200 |
| Mass Assignment          | CWE-915 |

## References

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CWE Top 25](https://cwe.mitre.org/top25/)
