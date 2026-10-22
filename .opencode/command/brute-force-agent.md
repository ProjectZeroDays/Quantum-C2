---
description: Run the BruteForceAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/brute-force-agent $ARGUMENTS

Operate the BruteForceAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/BruteForceAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/brute-force-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/BruteForceAgent/bruteforceagent.py` (specialized twin: `agents/specialized/BruteForce/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
