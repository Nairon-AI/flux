---
name: flux:dejank
description: React visual-jank audit and diagnosis via the optional Dejank skill installed through /flux:setup.
argument-hint: "[component|path|PR context|visual symptom]"
---

# IMPORTANT: This command should invoke the optional skill `dejank` when it is installed in this repo.

Before invoking the skill, check whether Dejank is available project-locally. Accept any of these as installed:

- `.secureskills/store/dejank/manifest.json`
- `.codex/skills/dejank/SKILL.md`
- `.claude/skills/dejank/SKILL.md`

If Dejank is **not installed**, do **not** improvise a fake `/flux:dejank` workflow. Tell the user plainly:

`Dejank` is not installed in this repo. Install it through `/flux:setup`, or run:

```bash
secureskills add https://github.com/gbasin/dejank --skill dejank
secureskills enable codex
```

If Dejank **is installed**, invoke the `dejank` skill and pass the user request through.

**User request:** $ARGUMENTS

Routing guidance:
- If the request describes a visible symptom like flicker, blink, flash, jump, layout shift, scroll reset, or “feels rebuilt”, pass that complaint through for runtime investigation.
- If the request is empty or general, ask the skill for a preventive static scan of the relevant React UI scope (current branch diff if no narrower scope is given).
