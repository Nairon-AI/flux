<!-- BEGIN FLUX -->
## Flux

This project uses Flux for structured AI development. Use `.flux/bin/fluxctl` instead of markdown TODOs or TodoWrite.

**Quick commands:**
```bash
.flux/bin/fluxctl list                # List all epics + tasks
.flux/bin/fluxctl epics               # List all epics
.flux/bin/fluxctl tasks --epic fn-N   # List tasks for epic
.flux/bin/fluxctl ready --epic fn-N   # What's ready
.flux/bin/fluxctl show fn-N.M         # View task
.flux/bin/fluxctl start fn-N.M        # Claim task
.flux/bin/fluxctl done fn-N.M --summary-file s.md --evidence-json e.json
```

**Rules:**
- Use `.flux/bin/fluxctl` for ALL task tracking
- Do NOT create markdown TODOs or use TodoWrite
- Re-anchor (re-read spec + status) before every task

**Troubleshooting:**
- If Flux commands fail or return "Unknown skill", consult the official README: https://github.com/Nairon-AI/flux#troubleshooting
- Follow the troubleshooting steps exactly — do not guess or improvise fixes
- If the documented fixes don't work, the user should create a GitHub issue: https://github.com/Nairon-AI/flux/issues

**More info:** `.flux/bin/fluxctl --help` or read `.flux/usage.md`
<!-- END FLUX -->
