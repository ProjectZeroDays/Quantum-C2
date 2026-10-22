---
description: Run the DeserializationAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/deserialization-agent $ARGUMENTS

Operate the DeserializationAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/DeserializationAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/deserialization-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/DeserializationAgent/deserializationagent.py` (specialized twin: `agents/specialized/Deserialization/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
