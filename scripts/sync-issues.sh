#!/usr/bin/env bash
# scripts/sync-issues.sh — import scripts/github-project.yaml into repo issues.
# Requires: gh auth + yq. Idempotent: issues labeled qc-sync are updated, not duplicated.
# Usage: ./scripts/sync-issues.sh [--apply]   (default is a dry run; --apply writes)
set -euo pipefail

REPO="${QC_REPO:-ProjectZeroDays/Quantum-CLI}"
YAML="$(dirname "$0")/github-project.yaml"
APPLY=0
[[ "${1:-}" == "--apply" ]] && APPLY=1

command -v yq >/dev/null || { echo "yq is required (https://github.com/mikefarah/yq)"; exit 1; }
command -v gh  >/dev/null || { echo "gh CLI is required"; exit 1; }

# 1. labels (idempotent)
if [[ $APPLY -eq 1 ]]; then
  yq -r '.labels[] | [.name, .color, .desc] | @tsv' "$YAML" \
  | while IFS=$'\t' read -r name color desc; do
      gh label create "$name" --repo "$REPO" --color "${color#\#}" --description "$desc" --force 2>/dev/null || true
    done
  gh label create "qc-sync" --repo "$REPO" --color "000000" --description "managed by sync-issues.sh" --force 2>/dev/null || true
fi

# 2. issues (epic-prefixed, idempotent via qc-sync search)
yq -r '.epics[] | .title as $e | .issues[] | [$e, .title, (.labels // [] | join(",")), (.body // "")] | @tsv' "$YAML" \
| while IFS=$'\t' read -r epic title labels body; do
    full_body="Epic: **${epic}**"$'\n'"${body}"
    if [[ $APPLY -eq 0 ]]; then
      echo "[dry-run] $title"
      continue
    fi
    existing=$(gh issue list --repo "$REPO" --search "in:title \"$title\" label:qc-sync" --json number --jq '.[0].number // empty')
    if [[ -n "$existing" ]]; then
      gh issue edit "$existing" --repo "$REPO" --body "$full_body" >/dev/null
      echo "[updated] #$existing $title"
    else
      label_args="qc-sync"
      IFS=',' read -ra extra <<< "$labels"
      for l in "${extra[@]}"; do
        [[ -n "$l" ]] && label_args+=",$l"
      done
      gh issue create --repo "$REPO" --title "$title" --label "$label_args" --body "$full_body" >/dev/null
      echo "[created] $title"
    fi
  done
