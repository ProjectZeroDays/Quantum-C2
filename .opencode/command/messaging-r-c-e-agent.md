---
description: Run the MessagingRCEAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/messaging-r-c-e-agent $ARGUMENTS

Operate the MessagingRCEAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/MessagingRCEAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/messaging-r-c-e-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/MessagingRCEAgent/messagingrceagent.py` (specialized twin: `agents/specialized/MessagingRCE/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
