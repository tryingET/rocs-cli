#!/usr/bin/env bash
set -euo pipefail

# ROCS CI profile wrapper
# Profiles:
#   - local-dev   : offline-first by default (refs optional; workspace matching defaults loose)
#   - branch-ci   : strict refs required (workspace matching defaults strict)
#   - main-strict : strict refs required (authoritative gate; workspace matching defaults strict)

ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-local-dev}"
ROCS_REPO="${ROCS_REPO:-.}"
ROCS_PROFILE="${ROCS_PROFILE:-}"
ROCS_CMD="${ROCS_CMD:-uv run python -m rocs_cli}"
workspace_root="${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}"
workspace_ref_mode="${ROCS_WORKSPACE_REF_MODE:-}"

profile_default_workspace_ref_mode() {
  case "$ROCS_CI_PROFILE" in
    local-dev)
      if [[ "${ROCS_LOCAL_RESOLVE_REFS:-0}" == "1" ]]; then
        echo "strict"
      else
        echo "loose"
      fi
      ;;
    branch-ci|main-strict)
      echo "strict"
      ;;
    *)
      echo "loose"
      ;;
  esac
}

if [[ -z "$workspace_ref_mode" ]]; then
  workspace_ref_mode="$(profile_default_workspace_ref_mode)"
fi

export ROCS_AUTHORITY_AGGREGATE=1
export ROCS_WORKSPACE_ROOT="$workspace_root"
export ROCS_WORKSPACE_REF_MODE="$workspace_ref_mode"

common_args=(--repo "$ROCS_REPO")
if [[ -n "$ROCS_PROFILE" ]]; then
  common_args+=(--profile "$ROCS_PROFILE")
fi

run_rocs() {
  # shellcheck disable=SC2086
  ROCS_WORKSPACE_ROOT="$workspace_root" ROCS_WORKSPACE_REF_MODE="$workspace_ref_mode" $ROCS_CMD "$@"
}

clean_dist() {
  rm -rf "$ROCS_REPO/ontology/dist"
}

strict_gate() {
  clean_dist
  run_rocs validate "${common_args[@]}" --resolve-refs
  run_rocs build "${common_args[@]}" --resolve-refs
}

case "$ROCS_CI_PROFILE" in
  local-dev)
    # Keep local loops fast/offline unless explicitly requested.
    # When ROCS_LOCAL_RESOLVE_REFS=1, the default workspace ref mode flips to strict.
    clean_dist
    if [[ "${ROCS_LOCAL_RESOLVE_REFS:-0}" == "1" ]]; then
      run_rocs validate "${common_args[@]}" --resolve-refs
      run_rocs build "${common_args[@]}" --resolve-refs
    else
      run_rocs validate "${common_args[@]}"
      run_rocs build "${common_args[@]}"
    fi
    ;;

  branch-ci)
    strict_gate
    ;;

  main-strict)
    strict_gate
    ;;

  *)
    echo "unknown ROCS_CI_PROFILE: $ROCS_CI_PROFILE (expected: local-dev|branch-ci|main-strict)" >&2
    exit 1
    ;;
esac
