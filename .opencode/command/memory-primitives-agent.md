---
description: Run the MemoryPrimitivesAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/memory-primitives-agent $ARGUMENTS

Operate the MemoryPrimitivesAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/MemoryPrimitivesAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/memory-primitives-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/MemoryPrimitivesAgent/memory_primitives.py` (specialized twin: `agents/specialized/MemoryPrimitives/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
