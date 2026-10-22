---
name: bdk-migrate-v2
description: >-
  Migrate a BDK project from hosted architecture v1 to v2: upgrade the package,
  remove v1-only code, and redeploy. Applies only to projects built during the
  early alpha, which depend on @cursor/july, run the agent-sdk CLI, or set
  architecture "v1".
environments:
  - cloud
---
# Migrate a BDK agent to architecture v2

This skill applies only to projects built during the BDK early alpha,
when hosted agents ran on architecture v1. Projects that never deployed
on v1 already run on v2 and need nothing here.

## Confirm the project needs it

Migrate when any of these is true:

- `package.json` depends on `@cursor/july`.
- `agent/agent.ts` sets `architecture: "v1"`.
- `bdk deployment <slug>` for the hosted copy does not print
  `architecture: v2`.

Stop when none is true. Your final message must start with
`Nothing to migrate.` and must name the checks you ran. Open no pull
request.

`bdk migrate` checks `--dir` before it starts an agent. It starts an
agent when it finds any of these: an `@cursor/july` dependency or
import, `architecture: "v1"`, `bot/storage.ts` or `agent/storage.ts`,
`runtime: "grokbot"`, a literal or `() => process.env` SCM credential,
`continuation: ".../v1"`, an anonymous reminder `run` or function
`until`, or a `defineConnection` whose URL comes from a `*_MCP_URL`
secret. When none of those is present it prints `Nothing to migrate.`
and exits. When it cannot read a file, it starts the agent. It does
not run `bdk deployment`. A hosted copy can still be on v1 after the
source has moved. Check with `bdk deployment <slug>`, and deploy when
that output does not show `architecture: v2`.

## Know what changes

A v1 deployment kept one long-lived process per agent. On v2 the platform
starts a short-lived runtime when an event arrives, keeps sessions, KV,
and files in Cursor-managed storage, and stops the runtime when the work
ends. That model changes code in three places:

- Module-scope state and files written outside `ctx.host.files` vanish
  between events. Keep durable state in `ctx.host.kv` or `ctx.host.files`.
- Secrets arrive per request, after modules load. Read `process.env`
  inside the handler, tool, or callback that needs the value.
- SCM webhook channels name their secrets instead of reading them.
  `githubChannel({ credentials })` fields and the `gitlabChannel` /
  `bitbucketChannel` `webhookSecret` take `{ secretName: "NAME" }`, so
  the platform can verify the provider signature at ingestion and flag
  an unset deployment secret before the first API call. A literal or a
  `() => process.env.X` getter is a validation error on v2.
- The deployment URL serves only routes your channels declare. It
  answers `202` at once and runs the handler afterwards, so a route
  cannot send a response body back to its caller.

## Check what v2 supports

| Capability | On v2 |
| --- | --- |
| Slack mentions, DMs, and channel posts | Supported. Provision a new Slack app after the first v2 deploy. |
| GitHub channels, including `cursorAccount` | Supported. Every `credentials` field must be `{ secretName }`. |
| GitLab and Bitbucket channels on Cursor hosting | Rolling out. Trial under a new slug first. `webhookSecret` must be `{ secretName }`. |
| Custom HTTP channel routes | Supported. The caller gets `202`, not the handler's response. |
| Tools, skills, subagents, MCP connections | Supported |
| `ctx.host.kv`, `ctx.host.files`, artifacts | Supported, in platform-selected storage |
| Reminders with `prompt` or a named `handler` | Supported |
| Secrets and `hosting.egressDomains` | Supported. Same-slug deploys copy v1 secrets. |
| `persistent: true` and `hosting.image` | Supported, one persistent deployment per team |
| Local `bdk dev`, `run`, `eval`, and the playground | Supported |
| `defineStorage` in `agent/storage.ts` | Not supported. Delete the file. |
| Reminders with inline `run` or a function `until` | Not supported. Use a named handler. |
| Cron schedules in `agent/schedules/` on Cursor hosting | Supported with `@cursor/bdk` 0.2.14 or newer. Each fire runs in a new runtime and must finish in 26 minutes. |
| Slack tool-approval buttons on Cursor hosting | Not supported yet |
| `bdk mcp oauth --store` for host MCP OAuth | Not supported. Connect Cursor-account MCP servers from **Deployed Agents** in the dashboard. |
| Session, tool, and MCP APIs on the deployment URL | Not reachable |
| Another BDK agent reached through a deployment URL secret | Not supported. Declare `defineConnection({ agent: "<slug>" })`. Both agents must be team-owned and deployed on `@cursor/bdk` 0.2.18 or newer. |
| `--prod` with `chat`, `resume`, `call`, `skill`, `sessions`, `cost`, or `mcp` | Not supported. Use `run --prod`, `logs --prod`, `session --prod`, and `playground --prod`. |
| v1 sessions, KV, and files | Not carried over. v2 starts empty, and deleting v1 deletes them. |

The steps below rewrite `defineStorage`, inline reminders, SCM channel
credentials, secret reads, and peer calls that use a URL secret. Stop and
ask before migrating an agent that depends on Slack tool-approval buttons,
`mcp oauth --store`, or an
HTTP route whose caller reads the response body. Name the row and the
file that uses it.

## Update the project

Keep the diff to the migration. Leave an `agent/` root in place; it
still loads.

1. **Upgrade the package.** Replace `@cursor/july` with the latest
   `@cursor/bdk` in `package.json`, then install with the project's
   package manager:

   ```bash
   npm uninstall @cursor/july
   npm install @cursor/bdk@latest
   ```

   Commit the lockfile the install writes, since deploys build from Git.
   Rewrite every `@cursor/july` import to `@cursor/bdk`; subpaths such as
   `/channels/slack`, `/evals`, and `/reminders` keep their names. Replace
   `agent-sdk` with `bdk` in scripts, CI jobs, and READMEs.

   The new types are stricter. `ctx.session.continuationKey` is
   `string | null`, so guard with `typeof key === "string"`, not
   `!== undefined`. Typecheck with `npx tsc --noEmit` even when the
   project has no script for it.

2. **Drop the v1 opt-in.** Delete `architecture: "v1"` from
   `defineAgent`. v2 is the default, so do not add `architecture: "v2"`.

3. **Delete `agent/storage.ts`.** v2 selects storage itself, and
   `ctx.host.kv` calls keep working against it. Data in a backend you
   run stays there. Data in Cursor-hosted storage is deleted with the v1
   deployment, so export what the agent still needs before deploying.

4. **Name inline reminders.** Move each inline `run` into
   `agent/reminders/<name>.ts` and pass that module as `handler` with
   serializable `args`. A named handler takes no `until`. Move a function
   `until` check into the handler and call `cancel()` when it holds.

   ```ts
   // agent/reminders/ci_recheck.ts
   import { defineReminder } from "@cursor/bdk/reminders";

   export default defineReminder({
     async run({ args, followup }) {
       await followup({ message: `Recheck CI on ${String(args.headSha)}` });
       return { action: "delivered" };
     },
   });
   ```

   ```ts
   // agent/tools/watch_ci.ts, inside execute
   await ctx.host.reminders?.create({
     purpose: "ci_recheck",
     channelId: ctx.session.channelId,
     continuationToken: key,
     delay: "2h",
     handler: ciRecheck, // import ciRecheck from "../reminders/ci_recheck.js"
     args: { headSha },
   });
   ```

5. **Rewrite `/v1` continuation selectors.** Delete an explicit
   `continuation: "<kind>.<scope>/v1"` on a channel so v2 picks its
   default, or change the suffix to `/v2`. By default, GitHub PR events,
   Slack threads, and deployment events still continue one session per
   PR, thread, or deployment.

6. **Name SCM channel credentials.** Replace every literal and
   `() => process.env.NAME` getter in `githubChannel({ credentials })`
   with `{ secretName: "NAME" }`, and do the same for the `webhookSecret`
   of `gitlabChannel` and `bitbucketChannel`. Keep the name the getter
   read; the channel reads that environment variable locally and the
   deployment secret of that name on Cursor hosting. A field you omit
   keeps its default name (`GITHUB_WEBHOOK_SECRET`, `GITHUB_TOKEN`,
   `GITHUB_APP_ID`, `GITHUB_APP_PRIVATE_KEY`), a numeric `appId` stays a
   number, and `cursorAccount` needs no credentials.

   ```ts
   // before (v1)
   credentials: {
     webhookSecret: () => process.env.GITHUB_WEBHOOK_SECRET,
     appId: () => process.env.GITHUB_APP_ID,
     privateKey: () => process.env.GITHUB_APP_PRIVATE_KEY,
   },

   // after (v2)
   credentials: {
     webhookSecret: { secretName: "GITHUB_WEBHOOK_SECRET" },
     appId: { secretName: "GITHUB_APP_ID" },
     privateKey: { secretName: "GITHUB_APP_PRIVATE_KEY" },
   },
   ```

   `bdk validate` lists each field still in the old shape. While
   `architecture: "v1"` is set the finding is a warning, so you can run
   it before step 2 to see the full list; after step 2 the same finding
   is an error and blocks `deploy`. Do not set the values: a same-slug
   deploy copies the v1 secrets, and a new slug takes
   `bdk secrets set <new-slug> NAME` after the deploy.

7. **Move secret reads.** Replace module-scope `process.env.NAME` reads
   with reads inside the function that uses them. Give MCP connections a
   `${NAME}` header or env template instead. A URL that points at another
   BDK agent's deployment is not one of those secrets. Step 8 replaces
   that connection, including a URL you templated here.

8. **Rewrite peer calls that use a URL secret.** Do this in the migration
   pull request. The deployment URL does not serve MCP, so a connection
   left on that URL fails after deploy.

   Treat the call as a peer when its URL comes from a `*_MCP_URL` secret
   or a similar name, a `${NAME}` template, `process.env.NAME`, or a
   string built from a deployment URL or slug, and the target is another
   BDK agent. Leave a third-party MCP server as a URL connection and
   apply step 7 to its secrets.

   Use a slug only when the repo states it: the URL path, a `--slug`
   value, a sibling directory that deploy would use as the slug, or a
   comment that names the deployment. A secret name is a hint. Use
   `BUILDER_MCP_URL` as `builder` only when something else in the repo
   confirms that slug. When nothing confirms it, keep the URL connection
   and add a TODO that names the secret and asks for the slug. Name that
   TODO in the pull request body.

   ```ts
   // before (v1), agent/mcp-connections/builder.ts
   import { defineConnection } from "@cursor/bdk/connections";

   export default defineConnection({
     url: process.env.BUILDER_MCP_URL,
     headers: { authorization: `Bearer ${process.env.BUILDER_TOKEN}` },
   });

   // after (v2)
   import { defineConnection } from "@cursor/bdk/connections";

   export default defineConnection({
     agent: "builder",
     description: "Ask the builder agent to handle this work.",
   });
   ```

   `agent` is the peer's lowercase deployment slug. Keep an existing
   connection file in place. When the project has no connection file,
   add `bot/mcp-connections/<name>.ts`, or
   `agent/mcp-connections/<name>.ts` when the project root is `agent/`.
   Use `host-connections/` only when host code calls the peer and the
   model must not see it. The filename is the connection name.

   Hosting authenticates the peer call. Remove the URL, its headers, and
   any token this call was the only reader of. Point host code that
   called the deployment URL at
   `ctx.host.mcp.callTool("<name>", "ask", { message })`. The peer
   project needs no matching file. Do not edit a peer that sits outside
   this folder.

   Remove the unused URL secret from code and from `hosting.secretNames`
   on `defineAgent`, and from an extension `hosting` block that declares
   it. Leave every secret something else still reads.

   Do not change deployment secrets, and do not run `bdk secrets unset`.
   In the pull request body, list each secret this step stopped using,
   with the command `bdk secrets unset <slug> NAME`, so the user can
   unset it after both agents are deployed.

   Both agents must be team-owned and deployed with `@cursor/bdk` 0.2.18
   or newer before the connection resolves. This pull request does not
   deploy them.

9. **Stop answering from HTTP routes.** A custom route that returned
   computed data must deliver it another way, such as a callback URL or a
   tool the turn calls. Return `new Response(null, { status: 202 })` so
   local runs match the hosted response.

## Verify locally

Run the project's installed CLI. Prefix each command with `npx` when
`bdk` is not on `PATH`.

```bash
bdk validate --dir .
bdk info --dir . --json
bdk run --dir . --message "<a representative request>"
bdk eval --dir .
```

Fix every validation error, but never change `runtime` to pass
validation; stop and report instead. An error ending in `requires a
named secret` names a channel credential step 6 missed; it quotes the
`{ secretName }` value to use. `run` and `eval` need a Cursor
credential. When none is set, skip them and say so in the pull request.
Run the project's own typecheck and tests.

## Open the pull request

Describe each removed or changed behavior, each unsupported row the
agent touched, and the deploy steps. For each peer URL you rewrote, name
the slug and the connection file. List every secret name the rewrite
left unused, and the `bdk secrets unset <slug> NAME` command for it.
Name each TODO whose slug you could not determine. Do not deploy from
the pull request branch, and do not change deployment secrets.

Copy this post-merge checklist into the pull request body. One
`bdk deploy --dir <agent-folder>` per agent. Do not use `bdk deploy --all`.
Then `bdk slack create --prod --dir <agent-folder> [--team <team-id>]`
for each agent that uses Slack. Then `bdk secrets unset <slug> NAME` for
each unused peer URL secret, and `bdk secrets list <slug>` plus
`bdk secrets set <slug> NAME` when the slug is new. Do not tell the user
to deploy again after Slack setup or after `bdk secrets set`. The server
redeploys after Slack setup, and a secret is injected on the next
request.

## Deploy after merge

Deploy from a pushed ref. `bdk deploy` reads Git and never uploads the
working tree.

When the folder contains one agent:

```bash
bdk login
bdk validate --dir .
bdk deploy --dir . --slug <existing-slug> \
  --cursor-events-repo <owner/repo> \
  --allow-domain <domain>
```

When the folder contains more than one agent, deploy each agent alone.
Run the command one time for each agent folder. A `bdk deploy` on the
parent folder prints those commands and does not deploy. Do not run
`bdk deploy --all`. Repeat `bdk slack create --prod` for each agent
folder too.
The app slug is the folder name, so that name must match the deployed
slug.

```bash
bdk deploy --dir <agent-folder> --slug <that-agent-slug> \
  --cursor-events-repo <owner/repo> \
  --allow-domain <domain>
```

When this migration declares `defineConnection({ agent: "<slug>" })`,
deploy the caller and the peer. Both deployments must be team-owned and
must run `@cursor/bdk` 0.2.18 or newer. The connection file is already
in the merged source. The caller reaches the peer after the peer
deployment is running. The peer needs no matching file. After both
deploys are running, unset each URL secret the pull request lists:

```bash
bdk secrets unset <slug> NAME
```

Pass every `--cursor-events-repo` and `--allow-domain` value the v1
deployment used. Domains already in `hosting.egressDomains` need no
flag. Print only those two fields, because the full output holds
credentials:

```bash
bdk deployment <slug> --json | jq '{cursorEventRepos, egressAllowedDomains}'
```

Choose a cutover before you deploy:

- **Same slug.** One command, and it can't be undone. The deploy copies
  the v1 secrets, switches traffic once v2 is running, then deletes the
  v1 deployment along with its Cursor-hosted sessions, KV, files, and
  eval runs. Slack and webhook traffic stops until you finish the steps
  below. If the command reports that same-slug replacement is
  unavailable, use a new slug.
- **New slug.** v1 keeps serving while you test. Set secrets with
  `bdk secrets set <new-slug> NAME`. Both deployments act on events from
  the same repositories, so point the trial at a test repository with
  `--cursor-events-repo`. Then move senders over and run
  `bdk delete <old-slug>`, which deletes v1's hosted data the same way.

Prefer a new slug when the agent serves Slack, receives webhooks, or
keeps data in `ctx.host.kv`.

After the deploy is running:

- Store the alias token the deploy prints. Point every webhook sender
  and HTTP caller at the new alias URL.
- For Slack, log in as a person. A team service-account key cannot
  create the app. Run `bdk slack create --prod --dir <agent-folder>`
  once per agent (`--team <team-id>` selects the Cursor team that owns
  the deployment). The server redeploys by itself. Do not deploy again
  for Slack. The new app is a different bot. Uninstall the old Slack app
  and invite the new bot to the channels the old one joined. The copied
  v1 Slack secrets go unused.
- For secrets, a same-slug deploy copies the v1 secrets. A new slug
  needs `bdk secrets set <slug> NAME`. Check with
  `bdk secrets list <slug> [--team <team-id>]`. `deploy` warns when a
  declared secret is unset. A secret is injected on the next request.
  Do not deploy again after `bdk secrets set`.
- Reconnect Cursor-account MCP servers from **Deployed Agents** in the
  dashboard.
- Start a turn with `bdk run --prod --slug <slug> --message "..."`. It
  prints a `deliveryId`, not a session. Find the `ses_...` header in
  `bdk logs --prod --once --slug <slug>`, then read the turn with
  `bdk session <ses_...> --prod --slug <slug>` until the latest run
  finishes.

The [deploy skill](../deploy/SKILL.md) covers deploys with an attached
service account.
