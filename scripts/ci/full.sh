#!/usr/bin/env bash
set -euo pipefail

# ROCS CI profile wrapper
# Profiles:
#   - local-dev   : offline-first by default (refs optional)
#   - branch-ci   : strict refs required
#   - main-strict : strict refs required (authoritative gate)

ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-local-dev}"
ROCS_REPO="${ROCS_REPO:-.}"
ROCS_PROFILE="${ROCS_PROFILE:-}"
ROCS_CMD="${ROCS_CMD:-uv run python -m rocs_cli}"

common_args=(--repo "$ROCS_REPO")
if [[ -n "$ROCS_PROFILE" ]]; then
  common_args+=(--profile "$ROCS_PROFILE")
fi

run_rocs() {
  # shellcheck disable=SC2086
  $ROCS_CMD "$@"
}

strict_gate() {
  run_rocs validate "${common_args[@]}" --resolve-refs
  run_rocs build "${common_args[@]}" --resolve-refs --clean
}

case "$ROCS_CI_PROFILE" in
  local-dev)
    # Keep local loops fast/offline unless explicitly requested.
    if [[ "${ROCS_LOCAL_RESOLVE_REFS:-0}" == "1" ]]; then
      run_rocs validate "${common_args[@]}" --resolve-refs
      run_rocs build "${common_args[@]}" --resolve-refs --clean
    else
      run_rocs validate "${common_args[@]}"
      run_rocs build "${common_args[@]}" --clean
    fi
    ;;

  branch-ci)
    : "${ROCS_GITLAB_TIMEOUT_S:=30}"
    : "${ROCS_GITLAB_RETRIES:=3}"
    export ROCS_GITLAB_TIMEOUT_S ROCS_GITLAB_RETRIES
    strict_gate
    ;;

  main-strict)
    : "${ROCS_GITLAB_TIMEOUT_S:=60}"
    : "${ROCS_GITLAB_RETRIES:=3}"
    export ROCS_GITLAB_TIMEOUT_S ROCS_GITLAB_RETRIES
    strict_gate
    ;;

  *)
    echo "unknown ROCS_CI_PROFILE: $ROCS_CI_PROFILE (expected: local-dev|branch-ci|main-strict)" >&2
    exit 1
    ;;
esac
