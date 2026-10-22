---
name: brute-force-agent
description: >
  GPU-accelerated brute force and password cracking Repo implementation: agents/BruteForceAgent/ (bruteforceagent.py). Authorized lab engagements only.
triggers:
  - brute-force-agent
  - exploit
  - BruteForceAgent
  - attack
  - vulnerability
category: red_teaming
enabled: true
metadata:
  agent: agents/BruteForceAgent/bruteforceagent.py
  specialized: agents/specialized/BruteForce/
---

# BruteForceAgent

GPU-accelerated brute force and password cracking

## Repo locations
- Implementation + tests + docs: `agents/BruteForceAgent/`
- Specialized twin: `agents/specialized/BruteForce/`
- Slash command: `/brute-force-agent` (.opencode/command/brute-force-agent.md)

## Capabilities
- Vulnerability scanning and exploitation
- Payload generation and delivery
- Post-exploitation and persistence
- Evasion techniques

## Verify
```bash
python -m pytest agents/BruteForceAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
