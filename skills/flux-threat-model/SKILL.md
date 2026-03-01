---
name: flux-threat-model
description: Generate a STRIDE-based security threat model for a repository. Use when setting up security monitoring, after architecture changes, during /flux:scope, or for security audits. Triggers on /flux:threat-model.
user-invocable: false
---

# Threat Model Generation

Generate a comprehensive security threat model for a repository using the STRIDE methodology. This skill analyzes the codebase architecture and produces an LLM-optimized threat model document that other security skills can reference.

Adapted from [Factory AI security-engineer plugin](https://github.com/Factory-AI/factory-plugins).

## When to Use This Skill

- **First-time setup** - New repository needs initial threat model
- **During /flux:scope** - Evaluate security of PRDs and technical plans
- **Architecture changes** - Significant changes to components, APIs, or data flows
- **Security audit** - Periodic review or compliance requirement
- **Manual request** - Security team requests updated threat model

## Inputs

Before running this skill, gather or confirm:

| Input                   | Description                                             | Required                         |
| ----------------------- | ------------------------------------------------------- | -------------------------------- |
| Repository path         | Root directory to analyze                               | Yes (default: current directory) |
| Existing threat model   | Path to existing `.flux/threat-model.md` if updating    | No                               |
| Compliance requirements | Frameworks to consider (SOC2, GDPR, HIPAA, etc.)        | No                               |
| Security contacts       | Email addresses for security team notifications         | No                               |

## Instructions

Follow these steps in order:

### Step 1: Analyze Repository Structure

Scan the codebase to understand the system:

1. **Identify languages and frameworks**

   - Check `package.json`, `requirements.txt`, `go.mod`, `Cargo.toml`, etc.
   - Note the primary tech stack (e.g., Next.js, Django, Go microservices)

2. **Map components and services**

   - Look for `apps/`, `services/`, `packages/` directories
   - Identify entry points: API routes, CLI commands, web handlers
   - Note databases, caches, message queues

3. **Identify external interfaces**

   - HTTP endpoints (REST, GraphQL)
   - File upload handlers
   - Webhook receivers
   - OAuth/SSO integrations
   - CLI commands that accept user input

4. **Trace data flows**
   - How does user input enter the system?
   - Where is sensitive data stored?
   - What external services are called?

### Step 2: Identify Trust Boundaries

Define security zones:

1. **Public Zone** (untrusted)

   - All external HTTP endpoints
   - Public APIs without authentication
   - User-uploaded files

2. **Authenticated Zone** (partially trusted)

   - Endpoints requiring valid session/token
   - User-specific data access
   - Rate-limited APIs

3. **Internal Zone** (trusted)
   - Service-to-service communication
   - Admin-only endpoints
   - Database connections
   - Secrets management

Document where trust boundaries exist and what validates transitions between zones.

### Step 3: Inventory Critical Assets

Classify data by sensitivity:

1. **PII (Personally Identifiable Information)**

   - User emails, names, addresses, phone numbers
   - Document protection measures

2. **Credentials & Secrets**

   - Password hashes, API keys, OAuth tokens
   - JWT signing keys, encryption keys
   - Document rotation policies

3. **Business-Critical Data**
   - Transaction records, customer data
   - Proprietary algorithms, trade secrets
   - Document access controls

### Step 4: Apply STRIDE Analysis

For each major component, analyze threats in all six categories:

#### S - Spoofing Identity

- Can attackers impersonate users or services?
- Are authentication mechanisms secure?
- Look for: weak session handling, API key exposure, missing MFA

#### T - Tampering with Data

- Can attackers modify data in transit or at rest?
- Look for: SQL injection, XSS, mass assignment, missing input validation

#### R - Repudiation

- Can users deny actions they performed?
- Look for: missing audit logs, insufficient logging, no immutable trails

#### I - Information Disclosure

- Can attackers access data they shouldn't?
- Look for: IDOR, verbose errors, hardcoded secrets, data leaks in logs

#### D - Denial of Service

- Can attackers disrupt service availability?
- Look for: missing rate limits, resource exhaustion, algorithmic complexity

#### E - Elevation of Privilege

- Can attackers gain unauthorized access levels?
- Look for: missing authorization checks, role manipulation, privilege escalation

For each identified threat:

- Describe the attack scenario
- List vulnerable components
- Show code patterns to look for
- Note existing mitigations
- Identify gaps
- Assign severity (CRITICAL/HIGH/MEDIUM/LOW) and likelihood

### Step 5: Document Vulnerability Patterns

Create a library of code patterns specific to this codebase's tech stack. See `references/stride-template.md` for the full template structure.

### Step 6: Generate Output Files

Create two files:

#### 1. `.flux/threat-model.md`

Use the template in `references/stride-template.md` to generate a comprehensive threat model with:

- System overview with architecture description
- Trust boundaries and security zones
- Attack surface inventory
- Critical assets classification
- STRIDE threat analysis for each component
- Vulnerability pattern library
- Security testing strategy
- Assumptions and accepted risks
- Version changelog

The document should be written in **natural language** with code examples, optimized for LLM comprehension.

#### 2. `.flux/security-config.json`

Generate configuration metadata:

```json
{
  "threat_model_version": "1.0.0",
  "last_updated": "<ISO timestamp>",
  "security_team_contacts": [],
  "compliance_requirements": [],
  "scan_frequency": "on_commit",
  "severity_thresholds": {
    "block_merge": ["CRITICAL"],
    "require_review": ["HIGH", "CRITICAL"],
    "notify_security_team": ["CRITICAL"]
  },
  "vulnerability_patterns": {
    "enabled": [
      "sql_injection",
      "xss",
      "command_injection",
      "path_traversal",
      "auth_bypass",
      "idor"
    ],
    "custom_patterns_path": null
  }
}
```

## Success Criteria

The skill is complete when:

- [ ] `.flux/threat-model.md` exists with all sections populated
- [ ] `.flux/security-config.json` exists with valid JSON
- [ ] All major components have STRIDE analysis
- [ ] Vulnerability patterns match the tech stack
- [ ] Document is written in natural language (LLM-readable)
- [ ] No placeholder text remains

## Verification

Run these checks before completing:

```bash
# Verify threat model exists and is non-empty
test -s .flux/threat-model.md && echo "Threat model exists"

# Verify config is valid JSON
cat .flux/security-config.json | jq . > /dev/null && echo "Config is valid JSON"

# Check threat model has key sections
grep -q "## 1. System Overview" .flux/threat-model.md && echo "Has System Overview"
grep -q "## 5. Threat Analysis" .flux/threat-model.md && echo "Has Threat Analysis"
grep -q "## 6. Vulnerability Pattern Library" .flux/threat-model.md && echo "Has Pattern Library"
```

## Integration with /flux:scope

When called during `/flux:scope`, this skill:

1. Analyzes the proposed feature/change from the PRD
2. Identifies potential security implications
3. Adds security requirements to the epic's acceptance criteria
4. Flags any HIGH/CRITICAL threats that need mitigation in the plan

## References

- [STRIDE Threat Modeling](https://docs.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [OWASP Threat Modeling](https://owasp.org/www-community/Threat_Modeling)
- Template: `references/stride-template.md`
