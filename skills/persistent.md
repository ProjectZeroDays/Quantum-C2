---
id: persistent
name: Persistent
description: >
  Continuously work until all previously requested tasks are completed in full.
  Never stops until every task in TASKS.md is verified. Runs autonomously with
  /Swarm /goal /never-ask /improve /Persistent /Debug /Docs /Push cycle.
triggers: ["/Persistent", "persistent", "never stop", "finish all tasks"]
---

# Persistent Skill

When active, the agent loops: scan remaining tasks → implement → test → update docs → /Push, until TASKS.md shows 100% verified.

## Usage
```
/Persistent         # enable continuous loop
/finish             # single command: runs all modes
```

## Invariants
- Does not weaken checks to make tests pass (AGENTS.md #1)
- Never claims verified when only built (current: Phase 0 verified, rest deferred)
- Updates docs/task files after every prompt delivery
