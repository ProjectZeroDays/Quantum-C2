---
name: memory-primitives-agent
description: >
  Memory corruption primitive simulation: buffer overflow, use-after-free, double-free, heap overflow, format string, integer overflow, out-of-bounds, type confusion, TOCTOU race condition, and null pointer dereference. Repo implementation: agents/MemoryPrimitivesAgent/ (memory_primitives.py). Authorized lab engagements only.
triggers:
  - memory-primitives-agent
  - memory corruption
  - buffer overflow
  - use-after-free
  - double free
  - heap overflow
  - format string
category: red_teaming
enabled: true
metadata:
  agent: agents/MemoryPrimitivesAgent/memory_primitives.py
  specialized: agents/specialized/MemoryPrimitives/
---

# MemoryPrimitivesAgent

Memory corruption primitive simulation: buffer overflow, use-after-free, double-free, heap overflow, format string, integer overflow, out-of-bounds, type confusion, TOCTOU race condition, and null pointer dereference.

## Repo locations
- Implementation + tests + docs: `agents/MemoryPrimitivesAgent/`
- Specialized twin: `agents/specialized/MemoryPrimitives/`
- Slash command: `/memory-primitives-agent` (.opencode/command/memory-primitives-agent.md)

## Capabilities
- See agent SKILL.md

## Verify
```bash
python -m pytest agents/MemoryPrimitivesAgent -q
```

## Authorized use only
Lab / contracted-authorization contexts. See agent WhitePaper.md.
