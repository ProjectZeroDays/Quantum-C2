---
name: bdk-create-agent
description: >-
  Scaffold a new BDK agent: short AskQuestion interview, then verify a turn and
  hand off to hillclimb. Use when creating a new agent. Ask only what the
  invoking message left open.
environments:
  - cloud
---
# Create a BDK agent

1. **Interview.** Two `AskQuestion` rounds, then a plan gate.
2. **Scaffold.** `bdk init`, then shape the files.
3. **Verify.** `validate` / `info` / `call`, then a model turn.
4. **Channels.** Slack, GitHub, webhook, or schedule as chosen.
5. **Hillclimb.** `skills/hillclimb/SKILL.md`.

Read `skills/framework-map/SKILL.md` if you have not. CLI is
`bdk`. Public docs:
`node_modules/@cursor/bdk/dist/docs/llms.txt` or `/docs/llms.txt`
on a running host.

## Interview

`AskQuestion`: batched, recommended option first and labeled
`(recommended)`.

- Mine the invoking message. Target: two rounds, then files.
- Round 1 is identity. Round 2 is the surface, tailored by round 1.
- Multi-select for channels, MCP, capabilities. Other where a
  custom answer is plausible.
- Ask decisions, not how to build it. File layout, tool names,
  env prefix, and eval shape are yours.
- If `AskQuestion` is missing or the user skips, state defaults
  in one list and proceed.

<!-- interview:start (generated from the bdk init questions; do not edit by hand) -->
### Round 1: identity

| Question | Options | Guidance |
| --- | --- | --- |
| **Purpose** | chat assistant · PR / repo automation · domain assistant over APIs/tools · scheduled reporter · Other |  |
| **Name** | 2–3 slugs from the purpose + Other | Directory: `[A-Za-z0-9][A-Za-z0-9_-]*`, not `v1`/`playground`/`docs` |
| **Location** | `./<slug>` (default) · another directory |  |

### Round 2: surface

| Question | Options | Guidance |
| --- | --- | --- |
| **Model** | `grok-4.5` + `effort=high`, `fast=true` · Other id | Params, not id suffixes: `{ id: "grok-4.5", params: [{ id: "effort", value: "high" }, { id: "fast", value: "true" }] }` |
| **Channels** (multi) | playground + HTTP (always on) · Slack · GitHub · custom webhook · schedule | Slack: `skills/setup-slack/SKILL.md`. GitHub: `skills/github/SKILL.md`. No Discord/Teams pack; offer custom webhook. |
| **MCP** (multi) | none · remote URL · local stdio · Cursor account connectors · Other | One file under `bot/mcp-connections/`. Account file is `account.ts`, never `cursor.ts`. Named local tools need `advertiseTools: true`. Privileged servers go in `bot/host-connections/`. |
| **Capabilities** (multi) | server tools · agent tools · skills · subagents · hooks · sandbox seeds · evals (recommend) | Always recommend one smoke eval. |
<!-- interview:end -->

Close with the plan and file tree, then "Scaffold it" / "Adjust
something". Write files only after approval.

## Fill the blanks

| Purpose | Shape |
| --- | --- |
| Slack chat | `slackChannel({ envPrefix })` + suggested prompts. `bdk slack create` mints the bot. Prefix: `skills/setup-slack/SKILL.md` |
| PR review with host prep | Channel `callTool` into a trimmed workspace `pr/` tree |
| GitHub automation | `githubChannel()` hooks, replay fixtures |
| Domain assistant | Server tools + one MCP connection + a skill |
| Wrap an existing pipeline | GitHub `{ task }` over a thin `bot/lib/` loop |

Defaults:

- Instructions + 1–2 tools + chosen channels + one smoke eval.
- `local.cwd` stays outside a monorepo checkout (default: a cache
  directory under `~/.cache`) unless the agent must inherit that
  tree.
- `bot/instructions.md`: identity, when to use which tool,
  output shape.
- One tool per file. Prefer `execution: "server"` + zod
  `inputSchema`. Declare `effect: "read"` or `"write"` on each tool.
- Long prompts: `prompt\`…\`` / `prompt.lines\`…\`` from
  `@cursor/bdk`.
- Host prep is for evidence (`callTool`, `workspaceFiles`), not
  judgment, formatting, or replies.
- Remembered state is `ctx.host.kv`. On Cursor hosting, a later
  event can run in a new process, where a module `Map` starts empty.
  File bytes that must outlive the process go in `ctx.host.files`.
  See `skills/framework-map/SKILL.md`.

### Deterministic-path budget

Default to instructions and skills. Promote to TypeScript only
when it earns the left column:

| Code owns | Model owns |
| --- | --- |
| Side-effect gates (approve, deploy, post) | Human-facing output to a stated shape |
| Dedupe of external writes (`ctx.host.kv`) | Summarizing, classifying, wording |
| Auth and signature checks | What to do next from ground truth |
| Evidence seeding | Soft-failure retries |
| Hard API caps | Formatting under those caps |

Smells: prose builders in `.ts` (write `.md`); `bot/lib/` +
`tools/` dwarfing instructions + skills on a first cut.

## Scaffold

```bash
bdk init ./<slug>
```

`init` writes the project, runs `npm install`, and may wait on
`login`. Then shape it:

1. `defineAgent` with the chosen model.
2. Real `instructions.md`. Replace `echo.ts`.
3. Chosen `channels/`, `mcp-connections/`, `skills/`,
   `subagents/<id>/` (needs `description`), `schedules/`, `hooks/`.
   Slack: `bdk slack create --dir ./<slug> --name "<Name>"`,
   not a hand-written channel. Manual Slack app:
   `bdk slack init --manual` (Slack CLI, or paste at
   api.slack.com).
4. `evals/evals.config.ts` with `maxConcurrency: 20` (required;
   cap 200) plus `evals/**/*.eval.ts`. Assert `t.succeeded()` +
   `t.calledTool(...)`. API: `skills/evals/SKILL.md`.

Stay on deps the BDK already ships (`zod`,
`@modelcontextprotocol/sdk`, `tsx`).

## Verify

```bash
bdk validate --dir ./<slug>
bdk info --dir ./<slug> --json
bdk call <tool> --dir ./<slug> --input '{…}'
bdk eval --dir ./<slug> --list
npx tsc --noEmit -p ./<slug>
```

tsx does not typecheck. Tool `execute` must return JSON-shaped
values: object literals or `type` aliases, not `interface` types.

Model turns need a Cursor credential (`CURSOR_API_KEY`, then `CURSOR_API_KEY_FILE`, then `CURSOR_SERVICE_ACCOUNT_KEY`, then `bdk login`). Without one, finish the
key-free checks, confirm `run` fails with only the API-key error,
and hand these over:

```bash
bdk run --dir ./<slug> --message "<fixture prompt>"
bdk serve --dir ./<slug> --mode single --dev
# http://127.0.0.1:3000/playground
bdk eval --dir ./<slug>
```

Serve only this agent's directory. Session files land in the
project state directory (`--state-root`). That is not harness cwd.

## Channel setup

- **Slack.** `skills/setup-slack/SKILL.md`
- **GitHub.** `skills/github/SKILL.md`
- **Custom webhook.** `POST /v1/channels/<id>/<route>`.
  Loopback-only until you add `bearerAuth(...)`. Hosted callers
  get an empty `202` before the handler runs, so return
  `new Response(null, { status: 202 })` and deliver results from
  the channel's `events`.
- **Schedules.** Never auto-fire under `--dev`.
  `POST /v1/dev/schedules/<id>`.

## Hillclimb handoff

Once a smoke turn passes, agree fixtures, success criteria, and a
freeze line, then follow `skills/hillclimb/SKILL.md`. Seed from
the smoke session under the project state directory. GitHub:
snapshot `bdk github replay ... --dry-run --out fixtures/github`.

Do not deploy or post to real Slack/GitHub beyond the smoke the
user asked for. If the plan grows past ~10 files, cut scope.
Re-check the budget at hand-off.
