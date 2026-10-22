---
name: bdk-hillclimb
description: >-
  Improve one existing BDK agent: pin fixtures, measure, change one lever,
  remeasure, lock the win with an eval. Use when an agent already runs and needs
  better results.
environments:
  - cloud
---
# BDK hillclimb

Measure → change one lever → remeasure. One failure mode per round.

Siblings: `skills/evals/SKILL.md`, `skills/github/SKILL.md`,
`skills/debug/SKILL.md`.

## Preconditions

From the user or the invoking message:

1. **Target.** Path or slug
2. **Fixtures.** Fixed inputs
3. **Success.** What better means this round
4. **Freeze line.** What must not change

Ask before editing if any are missing. A moving fixture is noise.

| Surface | Pin it |
| --- | --- |
| GitHub | `bdk github replay <pr> --dir <project>` (`--dry-run --out fixtures/github`) |
| One tool | `bdk call <tool> --dir <project> --input '{...}'` |
| Chat | `bdk run --dir <project> --message "<fixture>"` |

## Loop

1. **Serve.** `bdk serve --dir <project> --mode single --dev`
   Playground: `http://127.0.0.1:3000/playground`.
2. **Hit it.** Same path a user would. Record status, wall time,
   `sessionId`, output, and `action.result` counts by `toolName`.
3. **Name the failure.** Score correctness, efficiency, harness
   fit. One dominant failure this round.
4. **Change one lever.** Smallest first. Delete the code or prompt
   that caused it. Then instructions / skills, evidence shape,
   host prep (`workspaceFiles`, channel `callTool`) for wandering
   and latency (not formatting or judgment), remove or gate
   wandering tools, framework only if the agent cannot express
   the fix. Hypothesis: *If we X, metric Y should move because Z.*
5. **Remeasure.** Same fixtures. Keep only if the target metric
   improves and the freeze line holds.
6. **Lock.** A kept change gets an eval that would have failed
   before it (`skills/evals/SKILL.md`). Never weaken a gate to
   pass a round.

```markdown
### Hillclimb round N. `<slug>`
- Fixture(s): …
- Hypothesis: …
- Change: …
- Before → after: tools …; wall …; quality …
- Verdict: keep | revert | narrow
- Next failure mode:
```

Do not deploy or post real GitHub reviews unless asked.
