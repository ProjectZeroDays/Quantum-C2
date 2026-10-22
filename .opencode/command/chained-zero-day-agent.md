---
description: Run the ChainedZeroDayAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/chained-zero-day-agent $ARGUMENTS

Operate the ChainedZeroDayAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/ChainedZeroDayAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/chained-zero-day-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/ChainedZeroDayAgent/chained_zero_day.py` (specialized twin: `agents/specialized/ChainedZeroDay/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
