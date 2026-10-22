---
name: security-scanner-agent
description: >
  Security vulnerability scanning Repo implementation: agents/SecurityScannerAgent/ (securityscanneragent.py). Authorized lab engagements only.
triggers:
  - security-scanner-agent
  - exploit
  - SecurityScannerAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/SecurityScannerAgent/securityscanneragent.py
  specialized: agents/specialized/SecurityScanner/
---

# SecurityScannerAgent

Security vulnerability scanning

## Repo locations
- Implementation + tests + docs: `agents/SecurityScannerAgent/`
- Specialized twin: `agents/specialized/SecurityScanner/`
- Slash command: `/security-scanner-agent` (.opencode/command/security-scanner-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/SecurityScannerAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
