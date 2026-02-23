<!-- BEGIN NBENCH -->
## N-bench

This project uses N-bench for task tracking. Use `.nbench/bin/nbenchctl` instead of markdown TODOs or TodoWrite.

**Quick commands:**
```bash
.nbench/bin/nbenchctl list                # List all epics + tasks
.nbench/bin/nbenchctl epics               # List all epics
.nbench/bin/nbenchctl tasks --epic fn-N   # List tasks for epic
.nbench/bin/nbenchctl ready --epic fn-N   # What's ready
.nbench/bin/nbenchctl show fn-N.M         # View task
.nbench/bin/nbenchctl start fn-N.M        # Claim task
.nbench/bin/nbenchctl done fn-N.M --summary-file s.md --evidence-json e.json
```

**Rules:**
- Use `.nbench/bin/nbenchctl` for ALL task tracking
- Do NOT create markdown TODOs or use TodoWrite
- Re-anchor (re-read spec + status) before every task

**More info:** `.nbench/bin/nbenchctl --help` or read `.nbench/usage.md`
<!-- END NBENCH -->
