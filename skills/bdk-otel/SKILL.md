---
name: bdk-otel
description: >-
  Wire OpenTelemetry export (OTLP env, serve({ otel }), traces/metrics/logs,
  ctx.host.otel). Use when adding collector export or custom metrics.
environments:
  - cloud
---
# BDK OpenTelemetry

Push traces and metrics from the serve process to an OTLP
collector. Logs are off until you opt in.

Guide: `docs/guides/opentelemetry.md`.

## Enable

Public surface (use one of these):

1. `OTEL_EXPORTER_OTLP_ENDPOINT` (optional
   `OTEL_SERVICE_NAME`, `OTEL_EXPORTER_OTLP_HEADERS`,
   `OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf|http/json`)
2. `serve(dir, { otel: { … } })`. `otel: false` disables env and
   authored config.

`defineOtel` / `bot/otel.ts` is factory-only
(`@cursor/bdk/internal/otel`). Do not import that path from a
customer agent. Hosted secrets can arrive after startup; env and
`serve({ otel })` are the supported public late-bind.

| Signal | Default |
| --- | --- |
| Traces | on (`agent_sdk.http`; `agent_sdk.turn` → tool / subagent) |
| Metrics | on (`cursor.token.usage`, `cursor.tool.calls`, `cursor.cost.usage`) |
| Logs | off (`logs: true` or `OTEL_LOGS_EXPORTER=otlp`) |

Prompt text and tool payloads stay off the wire unless you set
`OTEL_LOG_USER_PROMPTS` / `OTEL_LOG_TOOL_CONTENT`. A failed tool
span status includes a short failure reason. BDK keeps its own
exporters when the process already has a provider.

## Custom metrics

```ts
ctx.host.otel.setAttributes({ "abc.ticket_id": "INC-123" });
ctx.host.otel.increment("abc.ticket.resolved");
ctx.host.otel.record("abc.approval.duration_ms", 1420);
```

Prefix names with team or agent. No custom spans. Join on
`agent_sdk.session_id` / `cursor.conversation.id` and
`agent_sdk.agent`.
