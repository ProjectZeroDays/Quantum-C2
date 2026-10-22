---
name: memory-corruption-agent
description: >
  Memory corruption exploitation Repo implementation: agents/MemoryCorruptionAgent/ (memorycorruptionagent.py). Authorized lab engagements only.
triggers:
  - memory-corruption-agent
  - exploit
  - MemoryCorruptionAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/MemoryCorruptionAgent/memorycorruptionagent.py
  specialized: agents/specialized/MemoryCorruption/
---

# MemoryCorruptionAgent

Memory corruption exploitation

## Repo locations
- Implementation + tests + docs: `agents/MemoryCorruptionAgent/`
- Specialized twin: `agents/specialized/MemoryCorruption/`
- Slash command: `/memory-corruption-agent` (.opencode/command/memory-corruption-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/MemoryCorruptionAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
