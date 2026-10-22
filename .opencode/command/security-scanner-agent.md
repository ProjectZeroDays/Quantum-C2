---
description: Run the SecurityScannerAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/security-scanner-agent $ARGUMENTS

Operate the SecurityScannerAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/SecurityScannerAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/security-scanner-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/SecurityScannerAgent/securityscanneragent.py` (specialized twin: `agents/specialized/SecurityScanner/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
