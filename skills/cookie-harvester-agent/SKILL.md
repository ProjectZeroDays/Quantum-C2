---
name: cookie-harvester-agent
description: >
  Cookie theft and session hijacking Repo implementation: agents/CookieHarvesterAgent/ (cookieharvesteragent.py). Authorized lab engagements only.
triggers:
  - cookie-harvester-agent
  - exploit
  - CookieHarvesterAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/CookieHarvesterAgent/cookieharvesteragent.py
  specialized: agents/specialized/CookieHarvester/
---

# CookieHarvesterAgent

Cookie theft and session hijacking

## Repo locations
- Implementation + tests + docs: `agents/CookieHarvesterAgent/`
- Specialized twin: `agents/specialized/CookieHarvester/`
- Slash command: `/cookie-harvester-agent` (.opencode/command/cookie-harvester-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/CookieHarvesterAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
