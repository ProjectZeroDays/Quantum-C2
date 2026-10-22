---
name: bdk-debug
description: >-
  Diagnose a misbehaving local BDK agent: blank playground, missing sessions,
  failed reads, webhook 401s, 403/409. Use when a project runs but behaves wrong
  locally.
environments:
  - cloud
---
# Debugging the BDK locally

Local `bdk serve`. Hosted start failures:
`docs/troubleshooting.md` and `docs/deployment.md`.

1. **Validate.** `bdk validate --dir <project>`
2. **Info.** `curl -s http://127.0.0.1:3000/<slug>/v1/info | jq .`
3. **Trace.** Session events under the project state directory.
   Then match the table.

| Symptom | Fix |
| --- | --- |
| Playground blank / "no agents" | Start `serve`. A built SPA with no backend serves nothing. |
| Playground UI edits do not show | Open the URL `serve --dev` prints as `playground`, not `:3000`. |
| Sessions on disk, empty playground list | List is the calling principal. `--dev` or `--allow-anonymous` shows all. Or `?sessionId=ses_...`. |
| Built-in read/grep fail; retry loops | Bun. Rerun under Node. The tell is `NGHTTP2_FRAME_SIZE_ERROR`. |
| `github forward` 401s; hook created | Blank `GITHUB_TOKEN`/`GH_TOKEN`. Relay uses `gh` login. |
| `Hook already exists` | One forwarder per repo. `forward --dir <parent>`. |
| Answers cite ancestor `AGENTS.md` | Nested checkout. Default `local.cwd` is a cache directory under `~/.cache`. |
| Model lists IDE `cursor` tools, never MCP | `advertiseTools: true`. Check `GET /v1/info`. |
| Port 3000 in use | `lsof -iTCP:3000 -sTCP:LISTEN` and kill that pid. |
| Schedule / reminder silent under `--dev` | Dev never auto-fires. `POST /<slug>/v1/dev/schedules/<id>`. |
| `409` on follow-up | Stale `continuationToken`, busy session, or a task session. |
| `409 session_busy` on `call --session` | Wait, or drop `--session`. |
| `403` on stream | Wrong principal. Same auth as create; beyond loopback send `--bearer-token`. |
| Works on loopback, blocked via tunnel | `localDevStrict()` rejects forwarded headers. Use `--bearer-token`. Never `--allow-anonymous` with account MCP. |
| Slack `channel idle … missing credentials` | Expected. `slack doctor --prefix <PREFIX>`. |
| Immediate API-key error | Model turns need a Cursor credential (`CURSOR_API_KEY`, then `CURSOR_API_KEY_FILE`, then `CURSOR_SERVICE_ACCOUNT_KEY`, then `bdk login`). |
| `validate` clean, CI typecheck fails | tsx skipped types. JSON-shaped returns; `type` not `interface`. |
| `validate`: `architecture "v2" requires a named secret` | Getter or literal SCM credential. Use the quoted `{ secretName: "NAME" }`; `secrets set <slug> NAME` after deploy. |

Count `action.result` by `toolName` before blaming latency.
`turn.failed` + `"turn interrupted"` is a follow-up or stop, not a
crash. `bdk trajectory --events <file>` renders a saved
trace.
