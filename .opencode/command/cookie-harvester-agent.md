---
description: Run the CookieHarvesterAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/cookie-harvester-agent $ARGUMENTS

Operate the CookieHarvesterAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/CookieHarvesterAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/cookie-harvester-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/CookieHarvesterAgent/cookieharvesteragent.py` (specialized twin: `agents/specialized/CookieHarvester/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
