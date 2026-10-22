---
name: bdk-framework-map
description: >-
  Orient on BDK layout, local runtime, sessions, and invariants (Node not Bun,
  root evals/, typecheck after tsx, memory in host.kv). Use when creating,
  editing, or running a project with bot/agent.ts.
environments:
  - cloud
---
# BDK framework map

`@cursor/bdk` discovers files under `bot/` and serves the agent
over HTTP, Slack, and GitHub. Markdown is prose. TypeScript is typed
behavior. Ground truth: package `README.md` and `AGENTS.md`.

CLI is `bdk` (Node, never Bun).

Public docs: `node_modules/@cursor/bdk/dist/docs/llms.txt` or
`/docs/llms.txt` on a running host.

## Invariants

1. **Node 22.13+, never Bun.** Bun corrupts harness tool-result
   streams (`NGHTTP2_FRAME_SIZE_ERROR`).
2. **Evals live at project-root `evals/`.** `bot/evals/` is ignored.
3. **tsx does not typecheck.** Tool `execute` must return JSON-shaped
   values: object literals or `type` aliases, not `interface` types.
4. **Nested git checkouts.** Discovery sets `local.cwd` to a
   per-project cache directory under `~/.cache`. Point cwd at a
   checkout only when the agent must inherit that tree.
5. **Attached MCP is nameless** until `advertiseTools: true`.
6. **Model turns need a Cursor credential** (`CURSOR_API_KEY`, then
   `CURSOR_API_KEY_FILE`, then `CURSOR_SERVICE_ACCOUNT_KEY`, then
   `bdk login`). `validate`,
   `info`, `call`, and `serve` bring-up do not.
7. **Memory is `ctx.host.kv`.** On Cursor hosting, a later event
   can run in a new process. Module `Map`s, globals, and local files
   do not carry over.

## Folder structure

Path is identity. Full list: README "Folder structure".

| Path | Role |
| --- | --- |
| `bot/agent.ts` | `defineAgent({ model?, local? })` |
| `bot/instructions.md` | Always-on system prompt (required) |
| `bot/tools/<name>.ts` | One tool. `execution: "server"` or `"agent"` |
| `bot/skills/*` | On-demand procedures |
| `bot/mcp-connections/<name>.ts` | MCP. Never name an account file `cursor.ts`. `advertiseTools: true` for named local tools |
| `bot/host-connections/<name>.ts` | Privileged MCP for `ctx.host.mcp` / `mcp oauth` |
| `bot/subagents/<id>/` | Child agent (`description` required) |
| `bot/extensions/<ns>.ts` | Mounted extension or Cursor plugin (`cursorPlugin`); contributions are `<ns>__<name>` |
| `bot/channels/*.ts` | Slack / GitHub / custom HTTP |
| `bot/hooks/*.ts` | Observe-only |
| `bot/artifacts.ts` | Durable tagged outputs (`defineArtifacts`) |
| `bot/otel.ts` | Factory-only OpenTelemetry (`defineOtel`) |
| `bot/schedules/*` | Cron. Never auto-fire under `--dev` |
| `bot/sandbox/workspace/` | Session seed files (local only) |
| `bot/lib/` | Import-only. Never discovered |
| `evals/**/*.eval.ts` | Case id is the path under `evals/` |

Discovery rejects `bot/result.ts`. To act on a turn's decision, record it with
an authored tool and act on it from a `turn.completed` hook.

## Runtime

Turns run on the serve host. Server tools, agent tools, skills, and
sandbox seeds are available there.

## Sessions

- **continuationToken** continues a conversation. HTTP follow-ups
  rotate it. Stale tokens return `409`.
- **sessionId** is the inspect handle
  (`GET /v1/session/:id/stream?startIndex=N`).

A follow-up to a busy HTTP/MCP session interrupts the in-flight
turn. Slack coalesces. Routes: `docs/reference/http-api.md`.
Session files live under the project state directory
(`--state-root`).

## Memory

Anything you need to remember goes in `ctx.host.kv`: coalesce,
dedupe, cursors, a decision a later turn must see. `get`, `put`,
and `delete`. Values are JSON.

On Cursor hosting, the platform can replace the serve process at
any time. The next hook, tool call, or channel event can run in a
new process, so do not assume this one is still up.

- The store is shared by every session of the agent. Prefix keys
  with `ctx.session.id` for per-session memory.
- There is no TTL. Store `exp` on the value. On read, `delete`
  the key once `exp` is past.
- The agent-facing API has no compare-and-swap. A lost race may
  do the work twice. Make that work safe to repeat.
- File-shaped bytes (evidence, reports) go in `ctx.host.files`.
  `ctx.stateRoot` and any other local path are wiped when a
  hosted deployment is replaced.

A variable that exists only for the current call is fine. If
another request or another process must see it, write it to kv
before you return.

## Where logic belongs

Code: side-effect gates, write dedupe (the record lives in
`ctx.host.kv`), auth, evidence seeding, hard API caps. Model:
formatting, summarizing, classification, replies.
Budget: `skills/create-agent/SKILL.md`.

Loop: `validate` / `info` / `call` / `run` / `eval` / `serve`. Serve
only this agent's directory.

| Task | Skill |
| --- | --- |
| Scaffold | `skills/create-agent/SKILL.md` |
| Evals | `skills/evals/SKILL.md` |
| OpenTelemetry | `skills/otel/SKILL.md` |
| GitHub | `skills/github/SKILL.md` |
| Slack | `skills/setup-slack/SKILL.md` |
| Host MCP OAuth | `skills/mcp-auth/SKILL.md` |
| Managed deployment | `skills/deploy/SKILL.md` |
| Local triage | `skills/debug/SKILL.md` |
| Measured improvement | `skills/hillclimb/SKILL.md` |
