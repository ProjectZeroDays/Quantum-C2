---
name: bdk-evals
description: >-
  Author and run defineEval cases. Use when writing, fixing, seeding, or
  hillclimbing evals. Ask whether to generate samples or take uploaded data.
  Materialize API-backed fixtures first.
environments:
  - cloud
---
# BDK evals

Fixed input, model turn, gates on the trajectory. Files live at
project-root `evals/**/*.eval.ts`. `bot/evals/` is ignored.
Guide: `docs/evals.md`.

Observing production: hooks. Tool logic without a model:
`bdk call <tool> --input '{...}'`.

```bash
bdk eval --dir . --list
bdk eval --dir . --json
bdk eval --dir . weather/nyc
bdk eval --dir . --tag smoke
```

| Form | Case id |
| --- | --- |
| `evals/weather.eval.ts` + `test` | `weather` |
| `evals/weather/nyc.eval.ts` + `test` | `weather/nyc` |
| `evals/weather.eval.ts` + `{ id: "nyc" }` | `weather/nyc` |
| `evals/sql.eval.ts` exporting an array of `defineEval` calls | `sql/0000`, `sql/0001`, ... |

`eval` boots an ephemeral server and a temp state root. `--url`
points at a running agent. Model turns need a Cursor credential
(`CURSOR_API_KEY`, then `CURSOR_API_KEY_FILE`, then
`CURSOR_SERVICE_ACCOUNT_KEY`, then `bdk login`); `--list` does
not. Node 22.13+, never Bun.

## Seeding

Creating or expanding cases: `AskQuestion` first.

| Question | Options |
| --- | --- |
| **How should we get eval samples?** | Generate test eval samples for me `(recommended)` · I will add / upload the data manually |

1. **Manual.** They provide files or paste. Show the shape below.
   Do not invent cases. Then `eval --list` and wire gates.
   API-backed pointers (PR URLs, SHAs, gold labels): materialize
   under `fixtures/` first.
2. **Generated.** Ask count (`3` recommended). Append to an
   existing `cases` array when it fits. Never overwrite or weaken
   a datapoint. Create `evals/evals.config.ts` if missing
   (`maxConcurrency: 20`; cap 200).

## API

```ts
import { defineEval, includes, satisfies } from "@cursor/bdk/evals";

export default defineEval({
  tags: ["smoke", "weather"],
  cases: [
    {
      id: "nyc",
      description: "NYC temperature.",
      async test(t) {
        await t.send("What's the temperature in NYC?");
        t.succeeded();
        t.calledTool("get_weather");
        t.notCalledTool("save_weather_note");
        t.check(t.reply, includes(/°|[FC]/));
      },
    },
  ],
});
```

```ts
import { defineEvalConfig } from "@cursor/bdk/evals";

export default defineEvalConfig({
  maxConcurrency: 20,
});
```

Either `test(t)` or `cases`, not both. `t.send` waits for the turn to
settle (complete or fail) and returns it; `turn.calledTool(...)`
reads only that turn, `t.*` reads the whole run. First-send options:
`workspaceFiles`, `workspaceDir`.

Gates: `t.succeeded()`,
`calledTool(name, { input, output, status, count })` / `notCalledTool`,
`toolOrder`, `maxToolCalls`, `taggedArtifact`, `event` / `notEvent`,
`t.check(value, includes | equals | matches | similarity | satisfies)`.
Records: `t.metric`, `t.log`, `t.score` (soft 0-1).

Severity is on the handle: default gate; `.soft()` tracked;
`.atLeast(0.8)` soft with a bar (verdict `scored`, exit 1 only under
`--strict`); `.gate(0.8)` hard. `t.judge.factuality`, `summarizes`,
`closedQA`, and `sql` are soft by default and need a judge model
(`judge` in `evals.config.ts`, on the eval or case, or per-call
`{ model }`).

## Side effects

Eval sessions run real tools. Guard actuation with
`ctx.session.purpose === "eval"` in the tool or hook
and return a shaped result so `calledTool` can still assert the
decision.

## What to gate

Decisions and shape, not prose.

1. `t.succeeded()` first
2. Intended tool + the tempting wrong one
3. A shape regex or `satisfies` on parsed fields
4. If formatting keeps failing, tighten instructions. Do not move
   rendering into a host tool.

Anti-patterns: exact phrasing; more than ~5 gates (split); live
drifting inputs (pin them).

| Surface | Fixture |
| --- | --- |
| Chat | One frozen prompt |
| Tool-heavy | `bdk call` first, then the prompt |
| GitHub | `github replay … --dry-run --out fixtures/github` |
| Host-prep PR review | A team-owned PR; gate findings shape, not counts |
| Workspace | `workspaceFiles` in `t.send` |
| Dataset | `loadJson` / `loadJsonl` / `loadYaml` from `@cursor/bdk/evals/loaders`, paths from the project root |

## Debug and CI

A failed local run leaves `evals/<case-id>.json` (assertions, inputs,
tool I/O, final text, logs) under `evals/<stamp>/` in the project state
directory (the CLI prints the path); read it before editing the eval.
`--state-root <path>` keeps the raw session events too.

CI: `bdk eval --dir . --json --no-stream --junit reports/evals.xml`.
Exit `1` on a failed gate, `2` when nothing matched, `--strict` to fail
on `scored`.

Every kept hillclimb change lands an eval that would have failed
before it. Never weaken a gate to pass a round.
