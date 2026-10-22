---
name: bdk-deploy
description: >-
  Deploy or redeploy an BDK project to Cursor-managed hosting with an attached
  service account. Use when asked to deploy, redeploy, publish, or update a
  hosted BDK agent.
environments:
  - cloud
---
# Deploy an BDK agent

Use this skill only after a person asks for a deployment. It deploys a
pushed Git ref to Cursor-managed hosting. Local files never upload.

Use the exact published `@cursor/bdk` release embedded in the installed
skill. Do not use a floating npm tag or a workspace build of the CLI.

## Gather the target

Resolve these values from the request and checkout:

- Agent directory. Default to the current directory only when it contains
  one BDK project.
- Deployment slug. Default to the normalized directory name.
- Git ref. Default to the exact pushed `HEAD` commit.
- Team. Use the service account's team unless the request names another.
- Cursor-event repositories and CLI-only egress domains.

Ask one focused question when the target or requested ref is ambiguous.
Do not ask for values the checkout or existing deployment supplies.

## Use the attached service account

Continue only when `CURSOR_SERVICE_ACCOUNT_KEY` is present. Never print
the value. Do not run `bdk login`.

On Linux and macOS, run every BDK command through this wrapper:

```bash
CURSOR_JULY_VERSION="__CURSOR_JULY_VERSION__"
case "$CURSOR_JULY_VERSION" in
  __CURSOR_JULY_*__)
    echo "The BDK deploy skill is not bound to a package version." >&2
    exit 1
    ;;
esac

run_agent_sdk() {
  env -u NODE_OPTIONS -u CURSOR_API_KEY \
    CURSOR_API_KEY_FILE=/dev/null \
    npx --yes "@cursor/bdk@$CURSOR_JULY_VERSION" "$@"
}
```

The installed copy pins the release it came from. The wrapper isolates that
published CLI and the attached service account. The presence check prevents a
stored personal login from being used when the attachment is missing.

Verify the principal before any write:

```bash
test -n "${CURSOR_SERVICE_ACCOUNT_KEY:-}" || {
  echo "No attached Cursor service account." >&2
  exit 1
}
run_agent_sdk whoami --json
```

Continue only when `credentialSource` is `service-account`. Record the
team and complete service-account ID for the final report. Stop on an
authentication, team-access, repository-scope, or hosting-entitlement
error.

## Pin pushed source

Find the Git root and commit:

```bash
GIT_ROOT="$(git -C "$AGENT_DIR" rev-parse --show-toplevel)"
SOURCE_REF="$(git -C "$GIT_ROOT" rev-parse HEAD)"
git -C "$GIT_ROOT" status --short
git -C "$GIT_ROOT" branch -r --contains "$SOURCE_REF"
```

Use a ref from the request instead of `SOURCE_REF` when the person names
one. Confirm the selected commit exists on the remote. If intended
changes are uncommitted or unpushed, stop and explain they will not ship.
Do not commit or push unless the request includes that work.

The CLI infers the normalized HTTPS `origin`, agent path, and slug from
`--dir`. Pass `--repo`, `--path`, or `--slug` when the request overrides
the inferred value. Never print a remote URL that contains credentials.

## Preserve deployment inputs

A redeploy replaces its source, Cursor-event repositories, and
CLI-supplied egress domains. Preserve the existing
`cursorEventRepos` and `egressAllowedDomains` unless the request or
project changes them. Reapply each value with:

```text
--cursor-events-repo <owner/repo>
--allow-domain <hostname>
```

Read existing settings through a filter that selects only those two
fields:

```bash
run_agent_sdk deployment "$SLUG" --json |
  node -e '
    let raw = "";
    process.stdin.setEncoding("utf8");
    process.stdin.on("data", (chunk) => { raw += chunk; });
    process.stdin.on("end", () => {
      const value = JSON.parse(raw);
      console.log(JSON.stringify({
        cursorEventRepos: value.cursorEventRepos ?? [],
        egressAllowedDomains: value.egressAllowedDomains ?? [],
      }, null, 2));
    });
  '
```

Never print or save the full response because it can contain short-lived
engine-access headers.

For a new SCM-channel deployment, ask which repositories should wake the
agent when the project does not declare the answer. The source repository
is not always the event repository.

## Validate, deploy, and verify

Validate with the same published package and principal:

```bash
run_agent_sdk validate --dir "$AGENT_DIR"
```

Stop on validation errors. Review hosting warnings about secret names,
egress domains, and channel configuration before continuing.

Deploy the pinned source. Add the preserved or requested repeatable
flags:

```bash
run_agent_sdk deploy \
  --dir "$AGENT_DIR" \
  --ref "$SOURCE_REF"
```

The command waits for a terminal deployment state. Do not treat
`pending`, `accepted`, or `deploying` as success. If the command is
interrupted, resume inspection with:

```bash
run_agent_sdk deployment "$SLUG"
```

A first deployment prints a one-time alias token. Never paste it into
chat or expose it in an agent-captured terminal. Before a first deploy,
ask for a secure destination or ask the person to run the final command
in a private terminal. When writing the token, use mode `0600` and print
only the path. Redeploys do not print the token. JSON deployment output
can also contain credentials, so filter it before display.

Finish only when the deployment reports `running`. Report the slug,
team, generation, pinned ref, and complete service-account ID. On
failure, report the deployment status and sanitized error without
retrying a different ref or principal.
