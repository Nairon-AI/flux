---
name: flux:release
description: Cut a Flux release with synced manifests, changelog, tag, and release notes.
argument-hint: "<version> [--title \"Release title\"]"
---

# IMPORTANT: This command MUST invoke the skill `flux-release`

The ONLY purpose of this command is to call the `flux-release` skill. You MUST use that skill now.

**User request:** $ARGUMENTS

Pass the user request to the skill. The skill handles version syncing, changelog updates, tagging, and GitHub release publication.
