#!/usr/bin/env bash
set -euo pipefail

# ROCS CI profile wrapper
# Profiles:
#   - local-dev   : offline-first by default (path layers only; workspace refs optional)
#   - branch-ci   : strict refs required (workspace matching defaults strict)
#   - main-strict : strict refs required (authoritative gate; workspace matching defaults strict)

ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-local-dev}"
ROCS_REPO="${ROCS_REPO:-.}"
ROCS_PROFILE="${ROCS_PROFILE:-}"
ROCS_CMD="${ROCS_CMD:-uv run python -m rocs_cli}"
workspace_root="${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}"
workspace_ref_mode="${ROCS_WORKSPACE_REF_MODE:-}"

if [[ -f "$ROCS_REPO/pyproject.toml" ]] && grep -q '^name = "rocs-cli"$' "$ROCS_REPO/pyproject.toml"; then
  uv run --project "$ROCS_REPO" python -m unittest discover -s "$ROCS_REPO/tests" -p 'test_*.py' -q
  exit 0
fi

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
  python3 - "$ROCS_REPO" <<'PY'
import os
import shutil
import stat
import sys
from pathlib import Path

raw = Path(sys.argv[1]).expanduser()
try:
    root = raw.resolve(strict=True)
except OSError as exc:
    raise SystemExit(f"refusing cleanup: ROCS_REPO is not a real directory: {raw} ({exc})")
if root == Path(root.anchor) or not root.is_dir():
    raise SystemExit(f"refusing cleanup: invalid ROCS_REPO root: {root}")
manifests = (root / "ontology/manifest.yaml", root / "ontology/manifest.yml", root / "manifest.yaml", root / "manifest.yml")
has_manifest = any(p.exists() and not p.is_symlink() and stat.S_ISREG(p.stat().st_mode) for p in manifests)
pyproject = root / "pyproject.toml"
is_rocs_source = pyproject.is_file() and not pyproject.is_symlink() and 'name = "rocs-cli"' in pyproject.read_text("utf-8")
if not has_manifest and not is_rocs_source:
    raise SystemExit(f"refusing cleanup: ROCS_REPO is neither an ontology repo nor the rocs-cli source repo: {root}")
targets = []
for lexical in (root / "ontology/dist", root / "dist"):
    # Resolve every target before deleting any, so rejection is preflight-atomic.
    # Resolve the target itself when present, exposing a symlink escape.  For an
    # absent target, resolve its existing parents and retain the final name.
    resolved = lexical.resolve(strict=False)
    try:
        rel = resolved.relative_to(root)
    except ValueError:
        raise SystemExit(f"refusing cleanup: target escapes ROCS_REPO: {lexical} -> {resolved}")
    if not rel.parts:
        raise SystemExit(f"refusing cleanup: target is not strictly beneath ROCS_REPO: {resolved}")
    if lexical.is_symlink():
        raise SystemExit(f"refusing cleanup: cleanup target is a symlink: {lexical}")
    targets.append(lexical)
for lexical in targets:
    if lexical.is_dir():
        shutil.rmtree(lexical)
    elif lexical.exists():
        lexical.unlink()
PY
}

strict_gate() {
  clean_dist
  run_rocs validate "${common_args[@]}" --resolve-refs
  run_rocs build "${common_args[@]}" --resolve-refs
}

case "$ROCS_CI_PROFILE" in
  local-dev)
    # Keep local loops fast/offline unless explicitly requested.
    # Default local-dev runs path layers only so repos with ref layers still validate/build offline.
    # When ROCS_LOCAL_RESOLVE_REFS=1, the default workspace ref mode flips to strict.
    clean_dist
    if [[ "${ROCS_LOCAL_RESOLVE_REFS:-0}" == "1" ]]; then
      run_rocs validate "${common_args[@]}" --resolve-refs
      run_rocs build "${common_args[@]}" --resolve-refs
    else
      run_rocs validate "${common_args[@]}" --only path
      run_rocs build "${common_args[@]}" --only path
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
