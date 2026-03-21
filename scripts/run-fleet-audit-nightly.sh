#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

workspace_root="${FCOS_WORKSPACE_ROOT:-$HOME/ai-society}"
policy_path="${FCOS_POLICY_PATH:-$workspace_root/holdingco/governance-kernel/governance/programs/fcos/fleet-state.yaml}"
artifact_root="${FCOS_AUDIT_ARTIFACT_ROOT:-${XDG_STATE_HOME:-$HOME/.local/state}/fcos/nightly}"
remediation_mode="${FCOS_REMEDIATION_MODE:-patch}"
timestamp="${FCOS_AUDIT_TIMESTAMP:-$(date -u +%Y%m%dT%H%M%SZ)}"
run_dir="$artifact_root/$timestamp"
json_path="$run_dir/scorecard.json"
markdown_path="$run_dir/scorecard.md"
batch_path="$run_dir/remediation-batch.json"
summary_path="$run_dir/run-summary.json"

case "$remediation_mode" in
  audit-only|patch|apply) ;;
  *)
    echo "error: invalid FCOS_REMEDIATION_MODE: $remediation_mode (expected audit-only|patch|apply)" >&2
    exit 1
    ;;
esac

mkdir -p "$run_dir"

set +e
python3 "$ROOT/scripts/audit-fleet.py" \
  --workspace-root "$workspace_root" \
  --policy "$policy_path" \
  --json "$json_path" \
  --markdown "$markdown_path"
audit_code=$?
set -e

if [[ "$audit_code" -ne 0 && "$audit_code" -ne 2 ]]; then
  printf '{"audit_exit_code": %s, "remediation_mode": "%s", "run_dir": "%s", "status": "audit_error"}\n' \
    "$audit_code" "$remediation_mode" "$run_dir" > "$summary_path"
  exit "$audit_code"
fi

needs_batch="$(python3 - "$json_path" <<'PY'
from __future__ import annotations
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text('utf-8'))
summary = payload.get('summary', {})
need = bool(summary.get('requirement_violations', 0) or summary.get('declaration_drifts', 0))
print('yes' if need else 'no')
PY
)"

if [[ "$remediation_mode" != "audit-only" && "$needs_batch" == "yes" ]]; then
  "$ROOT/scripts/open-remediation-batch.sh" \
    --input "$json_path" \
    --mode "$remediation_mode" \
    --output "$batch_path"
  remediation_generated=true
else
  remediation_generated=false
fi

printf '{"audit_exit_code": %s, "needs_batch": %s, "remediation_generated": %s, "remediation_mode": "%s", "run_dir": "%s", "scorecard_json": "%s", "scorecard_markdown": "%s"%s}\n' \
  "$audit_code" \
  "$([[ "$needs_batch" == "yes" ]] && echo true || echo false)" \
  "$([[ "$remediation_generated" == true ]] && echo true || echo false)" \
  "$remediation_mode" \
  "$run_dir" \
  "$json_path" \
  "$markdown_path" \
  "$([[ -f "$batch_path" ]] && printf ', "remediation_batch": "%s"' "$batch_path")" > "$summary_path"

exit "$audit_code"
