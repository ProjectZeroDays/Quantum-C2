---
description: Run the VulnScannerAgent workflow — verify the agent, then execute the task. Authorized lab use only.
---

/vuln-scanner-agent $ARGUMENTS

Operate the VulnScannerAgent security agent.

## How you must work

1. Verify first: `python -m pytest agents/VulnScannerAgent -q`. Park on failure with the exact error.
2. Load the skill: `skills/vuln-scanner-agent/SKILL.md` for capabilities and triggers.
3. Implementation: `agents/VulnScannerAgent/vulnscanneragent.py` (specialized twin: `agents/specialized/VulnScanner/`).
4. Execute $ARGUMENTS against the agent API (describe/discover, then the requested capability). Never claim results you did not run.
5. Authorized engagements only — lab / contracted scope.
