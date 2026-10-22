---
name: a-p-i-sniffer-agent
description: >
  API traffic interception and analysis Repo implementation: agents/APISnifferAgent/ (apisnifferagent.py). Authorized lab engagements only.
triggers:
  - a-p-i-sniffer-agent
  - exploit
  - APISnifferAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/APISnifferAgent/apisnifferagent.py
  specialized: agents/specialized/APISniffer/
---

# APISnifferAgent

API traffic interception and analysis

## Repo locations
- Implementation + tests + docs: `agents/APISnifferAgent/`
- Specialized twin: `agents/specialized/APISniffer/`
- Slash command: `/a-p-i-sniffer-agent` (.opencode/command/a-p-i-sniffer-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/APISnifferAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
