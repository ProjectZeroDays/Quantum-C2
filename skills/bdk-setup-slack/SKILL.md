---
name: bdk-setup-slack
description: >-
  Wire Slack to an BDK agent. Mint a dedicated Socket Mode app with slack
  create, then doctor and smoke. Use slack init --manual only when the user owns
  the Slack app. Use when adding Slack.
environments:
  - cloud
---
# Setup Slack for the BDK

Dedicated Socket Mode bot. `bdk slack create` opens the
signed-in dashboard wizard. Tokens land in `.env.local` and as
deployment secrets. Never print token values.

Do not generate manifests or ask anyone to paste tokens unless
they asked for `slack init --manual`.

Existing `<PREFIX>_SLACK_BOT_TOKEN` + `_SLACK_APP_TOKEN` in
`.env.local` keep working. Do not force those onto the wizard.

Guide: `docs/guides/slack.md`.

## 1. Wizard (default)

```bash
bdk login
bdk slack create --dir .
```

Same Cursor account in the browser. **Add Slack to this agent**,
approve Slack, pick the bot name. CLI writes
`<PREFIX>_SLACK_BOT_TOKEN` / `<PREFIX>_SLACK_APP_TOKEN` and runs
`doctor`.

Prefix is the directory basename in upper snake (`jenny` →
`JENNY`, `pr-approver` → `PR_APPROVER` → `PR_APPROVER_SLACK_*`).
`--prefix` / `--no-prefix` override. Dev and prod are separate
apps; `--prod` is the prod app. `--name` / `--icon` /
`--channel-posts` / `--slack-team` prefill the wizard.

If Slack needs workspace-admin approval, keep the CLI running.
Open the **Request approval** link it prints. Managed install
does not file the request. After approval, **Retry** in the
wizard.

`create` scaffolds `bot/channels/slack.ts` when missing:

```ts
export default slackChannel({
  envPrefix: "JENNY",
  suggestedPrompts: [{ title: "Help", message: "How can you help me?" }],
});
```

Return from dispatch handlers. Do not await long work in the
handler.

A second `slack create` for the same agent and env overwrites the
app (same Slack app id, new manifest and tokens).
`bdk slack destroy` deletes it.

Local serve does not need a hosted engine. Next
`bdk deploy` injects the stored secrets.

## 2. Manual (`slack init --manual`)

Only when they own the app. Preferred: Slack CLI
(`~/.slack/bin/slack`). Paste at api.slack.com if the CLI is
missing. Never `slack deploy`; BDK serve owns Socket Mode.

```bash
bdk slack init --manual --dir . --name "My Agent"
# --slack-team T0123ABCD when several workspaces are logged in
# --no-install to scaffold only
```

Writes `bot/channels/slack.ts` (`envPrefix` from the directory),
manifests, a `.slack/` project (`get-manifest` → those JSON files),
and `env.example`. `--channel-posts` subscribes `message.channels`
/ `message.groups`. If Slack CLI is logged in, this installs the
app. `--install` fails when that cannot run.

Human gates, one at a time. Stop after each.

1. **Install the app.** If `next` starts with "Ask the user to
   install this Slack app", stop and prompt them. Slack CLI: they
   run `slack login --no-prompt`, send `/slackauthticket <ticket>`,
   then `slack login --ticket <ticket> --challenge <code>`, then
   `slack app install --environment local --team <T> --force`.
   Prod: `SLACK_ENV=deployed slack app install --environment
   deployed --team <T> --force`. Fallback: Create New App → From a
   manifest, start with `.slack/manifest.dev.json`.
2. **Tokens.** Slack CLI leaves xoxb / xapp in that process only.
   Copy the bot token from the app's OAuth page. Mint an app-level
   token with `connections:write`. Put both in `.env.local` using
   `env.example` names. If Slack CLI wrote `SLACK_*` to `.env`,
   copy those values to the prefixed keys.
3. **Doctor.**

## 3. Doctor and smoke

```bash
bdk slack doctor --prefix JENNY
bdk serve --dir . --dev
```

Green: `app_token`, `connections_open`, `bot_token`, `auth_test`.
Log: `[bdk/slack] Socket Mode connected`. Missing tokens
idle the channel; `serve` continues.

1. Invite the bot
2. `@mention` or DM
3. Thinking / Working, then a threaded reply
4. Logs: `inbound kind=app_mention`, `session start`,
   `reply delivered via postMessage|stream`

## Watch channels (opt-in)

Default is mentions + DMs only. To wake on new posts:

```ts
export default slackChannel({
  envPrefix: "JENNY",
  engagement: {
    channelPosts: {
      allow: ["C0123ABCDEF", "#alerts"], // ≥1 channel id required, ≤10 ids
      posts: "top-level",
    },
  },
  onChannelPost: async (ctx, message) => ({}), // null = skip
});
```

Pass `--channel-posts` on `create` / `init --manual`. Invite the
bot to each watched channel. Mentions stay on `app_mention`; a
later mention continues the watch thread.
