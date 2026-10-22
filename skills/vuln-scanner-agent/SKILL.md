---
name: vuln-scanner-agent
description: >
  CVE vulnerability scanning Repo implementation: agents/VulnScannerAgent/ (vulnscanneragent.py). Authorized lab engagements only.
triggers:
  - vuln-scanner-agent
  - exploit
  - VulnScannerAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/VulnScannerAgent/vulnscanneragent.py
  specialized: agents/specialized/VulnScanner/
---

# VulnScannerAgent

CVE vulnerability scanning

## Repo locations
- Implementation + tests + docs: `agents/VulnScannerAgent/`
- Specialized twin: `agents/specialized/VulnScanner/`
- Slash command: `/vuln-scanner-agent` (.opencode/command/vuln-scanner-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/VulnScannerAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
