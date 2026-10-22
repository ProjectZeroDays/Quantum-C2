---
name: messaging-r-c-e-agent
description: >
  Messaging protocol RCE exploitation Repo implementation: agents/MessagingRCEAgent/ (messagingrceagent.py). Authorized lab engagements only.
triggers:
  - messaging-r-c-e-agent
  - exploit
  - MessagingRCEAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/MessagingRCEAgent/messagingrceagent.py
  specialized: agents/specialized/MessagingRCE/
---

# MessagingRCEAgent

Messaging protocol RCE exploitation

## Repo locations
- Implementation + tests + docs: `agents/MessagingRCEAgent/`
- Specialized twin: `agents/specialized/MessagingRCE/`
- Slash command: `/messaging-r-c-e-agent` (.opencode/command/messaging-r-c-e-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/MessagingRCEAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
