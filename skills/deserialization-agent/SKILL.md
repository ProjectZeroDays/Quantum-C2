---
name: deserialization-agent
description: >
  Deserialization vulnerability exploitation Repo implementation: agents/DeserializationAgent/ (deserializationagent.py). Authorized lab engagements only.
triggers:
  - deserialization-agent
  - exploit
  - DeserializationAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/DeserializationAgent/deserializationagent.py
  specialized: agents/specialized/Deserialization/
---

# DeserializationAgent

Deserialization vulnerability exploitation

## Repo locations
- Implementation + tests + docs: `agents/DeserializationAgent/`
- Specialized twin: `agents/specialized/Deserialization/`
- Slash command: `/deserialization-agent` (.opencode/command/deserialization-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/DeserializationAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
