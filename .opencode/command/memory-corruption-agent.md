---
description: Run the MemoryCorruptionAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/memory-corruption-agent $ARGUMENTS

Operate the MemoryCorruptionAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/MemoryCorruptionAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/memory-corruption-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/MemoryCorruptionAgent/memorycorruptionagent.py` (specialized twin: `agents/specialized/MemoryCorruption/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
