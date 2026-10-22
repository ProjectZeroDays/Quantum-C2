---
description: Run the APISnifferAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/a-p-i-sniffer-agent $ARGUMENTS

Operate the APISnifferAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/APISnifferAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/a-p-i-sniffer-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/APISnifferAgent/apisnifferagent.py` (specialized twin: `agents/specialized/APISniffer/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
