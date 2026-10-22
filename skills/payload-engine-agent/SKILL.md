---
name: payload-engine-agent
description: >
  Payload generation and obfuscation Repo implementation: agents/PayloadEngineAgent/ (payloadengineagent.py). Authorized lab engagements only.
triggers:
  - payload-engine-agent
  - exploit
  - PayloadEngineAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/PayloadEngineAgent/payloadengineagent.py
  specialized: agents/specialized/PayloadEngine/
---

# PayloadEngineAgent

Payload generation and obfuscation

## Repo locations
- Implementation + tests + docs: `agents/PayloadEngineAgent/`
- Specialized twin: `agents/specialized/PayloadEngine/`
- Slash command: `/payload-engine-agent` (.opencode/command/payload-engine-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/PayloadEngineAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
