<!-- BEGIN FLUX -->
## Flux

This project uses Flux for task tracking. Use `.flux/bin/nbenchctl` instead of markdown TODOs or TodoWrite.

**Quick commands:**
```bash
.flux/bin/nbenchctl list                # List all epics + tasks
.flux/bin/nbenchctl epics               # List all epics
.flux/bin/nbenchctl tasks --epic fn-N   # List tasks for epic
.flux/bin/nbenchctl ready --epic fn-N   # What's ready
.flux/bin/nbenchctl show fn-N.M         # View task
.flux/bin/nbenchctl start fn-N.M        # Claim task
.flux/bin/nbenchctl done fn-N.M --summary-file s.md --evidence-json e.json
```

**Rules:**
- Use `.flux/bin/nbenchctl` for ALL task tracking
- Do NOT create markdown TODOs or use TodoWrite
- Re-anchor (re-read spec + status) before every task

**More info:** `.flux/bin/nbenchctl --help` or read `.flux/usage.md`
<!-- END FLUX -->
