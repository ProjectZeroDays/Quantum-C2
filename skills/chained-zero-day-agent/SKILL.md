---
name: chained-zero-day-agent
description: >
  Chained zero-day exploitation simulation: multi-stage attack chains with AI-assisted optimization, vulnerability correlation, and chain viability scoring. Repo implementation: agents/ChainedZeroDayAgent/ (chained_zero_day.py). Authorized lab engagements only.
triggers:
  - chained-zero-day-agent
  - exploit chain
  - chained exploit
  - zero-day chain
  - multi-stage attack
  - pegasus
  - forcedentry
category: red_teaming
enabled: true
metadata:
  agent: agents/ChainedZeroDayAgent/chained_zero_day.py
  specialized: agents/specialized/ChainedZeroDay/
---

# ChainedZeroDayAgent

Chained zero-day exploitation simulation: multi-stage attack chains with AI-assisted optimization, vulnerability correlation, and chain viability scoring.

## Repo locations
- Implementation + tests + docs: `agents/ChainedZeroDayAgent/`
- Specialized twin: `agents/specialized/ChainedZeroDay/`
- Slash command: `/chained-zero-day-agent` (.opencode/command/chained-zero-day-agent.md)

## Capabilities
- **Chain Building**: Construct multi-stage exploit chains from individual vulnerability components
- **Chain Analysis**: Analyze chain viability, dependencies, and success probability
- **Chain Simulation**: Simulate chain execution against targets (returns `{"status": "simulated"}`)
- **Chain Optimization**: AI-assisted suggestions for improving chain reliability and stealth
- **Real-World Chains**: Reference database of documented exploit chains (Pegasus, FORCEDENTRY, BLASTPASS)
- **CVE Database**: CVE lookup for chain building components
- **Dependency Analysis**: Map inter-stage dependencies and failure modes
- **Success Probability**: Calculate overall chain success probability from individual stage probabilities

## Verify
```bash
python -m pytest agents/ChainedZeroDayAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
