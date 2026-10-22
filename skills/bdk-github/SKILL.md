---
name: bdk-github
description: >-
  Build and test GitHub-driven BDK agents: githubChannel hooks (auth turn vs
  host task), cursorAccount / --cursor-events, and local test tiers (fixtures,
  replay, forward). Use when wiring GitHub events or debugging delivery.
environments:
  - cloud
---
# GitHub channels in the BDK

Author `bot/channels/github.ts`. Production wakes:
`cursorAccount` + `serve --cursor-events`. No public webhook URL.
Use the HTTP route for fixtures, replay, and hosts that already
terminate GitHub webhooks.

Guide: `docs/guides/github.md`.

```ts
import { defaultGitHubAuth, githubChannel } from "@cursor/bdk/channels/github";

export default githubChannel({
  botName: "my-agent",
  cursorAccount: { repos: ["owner/repo"] }, // permissions?: "read" | "pr-write" | "contents-write"

  onPullRequest: (ctx, pr) => {
    if (pr.action !== "opened") {
      return null;
    }
    return { auth: defaultGitHubAuth(ctx) };
  },
  onCheckSuite: (ctx, suite) => {
    if (suite.conclusion !== "failure") {
      return null;
    }
    return { task: () => triage(ctx) };
  },
});
```

Hooks: `onPullRequest`, `onComment`, `onIssue`, `onCheckSuite`,
`onCheckRun`, `onWorkflowRun`, `onStatus`, plus `onEvent` and
`onStart`/`onStop`.

| Return     | Meaning                                                                          |
| ---------- | -------------------------------------------------------------------------------- |
| `{ auth }` | Model turn. Session shows in the playground. `workspaceFiles` can be a function. |
| `{ task }` | Host work. No chat session. Use when the work can outlive a webhook timeout.     |
| `null`     | Skip                                                                             |

To keep repo scope in deploy config, use `cursorAccount: true`
and pass `--repo owner/name` at serve / `--cursor-events-repo`
at deploy. Repos must share one GitHub owner.

## Event sources

| Source                                                       | When                                                                                                                                                                                       |
| ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `cursorAccount` + `serve --cursor-events`                    | Preferred. Signed-in host (`bdk login`, `CURSOR_API_KEY`, or `CURSOR_SERVICE_ACCOUNT_KEY`). Repos from the channel and from repeatable `--repo owner/name`. Cap 20, one GitHub owner |
| HTTP `POST /<slug>/v1/channels/github` with a webhook secret | `allowAll()` + `X-Hub-Signature-256`                                                                                                                                                       |
| HTTP, no secret                                              | Loopback only. `serve --dev` also admits unsigned loopback (fixtures / forward)                                                                                                            |

`permissions`: `"read"` inspect; `"pr-write"` (default) comments /
PR writes; `"contents-write"` push or merge-box checks.
`progress.commitStatus` needs check-write; see the GitHub guide.
Set `checks: true` when channel code posts its own Checks API
runs through `ctx.github.createCheck`. The flag grants access.
It does not post a check.

Without `cursorAccount`, outbound calls prefer App installation
tokens (`GITHUB_APP_ID` + `GITHUB_APP_PRIVATE_KEY`). Local tests
can use `GITHUB_TOKEN` / `gh auth login`.

## Credentials

Name secrets; never read them. Each `credentials` field
(`webhookSecret`, `token`, `installationToken`, `appId`,
`privateKey`) takes `{ secretName: "NAME" }`: the env var locally,
the deployment secret of that name on Cursor hosting. The platform
verifies `X-Hub-Signature-256` against the named secret before any
compute starts and `deploy` warns when a named secret is unset.

```ts
credentials: {
  webhookSecret: { secretName: "GITHUB_WEBHOOK_SECRET" },
  appId: { secretName: "GITHUB_APP_ID" },
  privateKey: { secretName: "GITHUB_APP_PRIVATE_KEY" },
},
```

A literal or `() => process.env.X` getter fails `bdk validate` on
architecture v2 (the default) with `requires a named secret`; the
message quotes the `{ secretName }` to use. Omit a field to keep its
default name; a numeric `appId` is allowed. Only `architecture: "v1"`
still accepts getters, and `validate` warns there.

The Cursor stream is metadata, not full webhook bodies. Re-read
the PR from GitHub.

## Test locally

1. **Fixtures** (offline, `--dev`, no signature):

```bash
curl -s -X POST http://127.0.0.1:3000/<slug>/v1/channels/github \
  -H 'content-type: application/json' \
  -H 'x-github-event: pull_request' \
  -d @fixtures/github/pull_request.synchronize.json
```

2. **Replay** (hillclimb tier; pull access is enough):

```bash
bdk github replay owner/repo#123 --dir <project>
bdk github replay owner/repo#123 --dir <project> --events '*' --dry-run --out fixtures/github
```

3. **Forward** (live; repo admin). One forwarder per repo. Blank
   `GITHUB_TOKEN`/`GH_TOKEN` or every delivery 401s:

```bash
bdk github doctor --install
GITHUB_TOKEN= GH_TOKEN= bdk github forward --dir <project>
```

4. **Cursor pull** (same as production):

```bash
bdk serve --dir <project> --cursor-events --repo owner/repo
```

Volume, debounce, and `progress.commitStatus` / `progress.banner`
live in `docs/guides/github.md`. Do not preinstall them.
