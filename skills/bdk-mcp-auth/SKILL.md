---
name: bdk-mcp-auth
description: >-
  Authorize host MCP OAuth for defineConnection({ url, oauth: true }): bdk mcp
  oauth, local tokens, advertiseTools, egress, and the hosted cursorAccount
  path. Use when wiring or debugging MCP auth.
environments:
  - cloud
---
# Host MCP OAuth

Guide: `docs/guides/mcp-oauth.md`.

| Need | Use |
| --- | --- |
| Connector already in the Cursor dashboard | `defineConnection({ cursorAccount: true })` or `servers: "*"` / `servers: […]` |
| Remote URL that speaks OAuth; host holds tokens | `defineConnection({ url, oauth: true })` + this skill |
| Static bearer / API key | `headers` / env on `{ url }` |

`advertiseTools: true` puts named tools on local turns. Host tools
can still call `ctx.host.mcp`.

## Checklist

1. **Declare the connection.** `bot/mcp-connections/<name>.ts`
   with `url` + `oauth: true`. Use `bot/host-connections/` when
   the model must not see it.
2. **Allow egress** on hosted non-bootstrap hosts:
   `hosting.egressDomains`.
3. **Authorize.** Local: `bdk mcp oauth <name>`, or finish
   Connect in the playground so the current process can retry.
   Tokens stay on this machine. Hosted: use a
   `cursorAccount: true` connection and connect the server from
   **Deployed Agents** in the dashboard; its tokens stay on the
   Cursor backend.

```ts
// bot/mcp-connections/inventory.ts
export default defineConnection({
  url: "https://mcp.example.com/inventory",
  oauth: true,
});
```

```bash
bdk mcp oauth <connection>
```

Browser callback: `http://127.0.0.1:8787/callback`. Tokens live in
the CLI config directory (`mcp-auth.json` or
`$AGENT_SERVE_CONFIG_DIR`). URL change drops the old entry; re-run.

| Symptom | Fix |
| --- | --- |
| `must be defineConnection({ url, oauth: true })` | Wrong name or missing `oauth: true` |
| `Unknown MCP connection` | Filename must match the CLI arg |
| Callback hang | Free port 8787; finish the browser flow here |
| Hosted 401 | Local tokens don't reach the deployment. Switch to `cursorAccount: true`; connect from **Deployed Agents** |
| Model invents `mcp_auth` / IDE MCP | `advertiseTools: true` on local turns |

No raw tokens in git.
