#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_APPLY_PARTIAL = 2

ACTIONABLE_CLASSES = {"required", "ontology_repo"}


class RemediationError(ValueError):
    pass


def _parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Generate or apply deterministic remediation batches from FCOS audit scorecards."
    )
    parser.add_argument("--input", required=True, help="Path to audit-fleet JSON scorecard")
    parser.add_argument(
        "--mode",
        required=True,
        choices=("patch", "apply"),
        help="patch = generate batch only, apply = run bootstrap actions",
    )
    parser.add_argument(
        "--output",
        nargs="?",
        const="-",
        default="-",
        metavar="PATH",
        help="Write remediation batch JSON (stdout when PATH omitted)",
    )
    parser.add_argument(
        "--batch-id",
        default=None,
        help="Optional explicit batch id (default: deterministic hash from input payload)",
    )
    parser.add_argument(
        "--bootstrap-script",
        default=str(repo_root / "scripts" / "bootstrap-repo.sh"),
        help="Path to bootstrap-repo.sh",
    )
    parser.add_argument(
        "--workspace-root",
        default=None,
        help="Authoritative workspace root. Defaults to scorecard.workspace_root.",
    )
    return parser.parse_args()


def _load_scorecard(path: Path) -> tuple[dict[str, Any], bytes]:
    if not path.is_file():
        raise RemediationError(f"input not found: {path}")
    raw_bytes = path.read_bytes()
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RemediationError(f"invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise RemediationError("input root must be an object")
    repos = payload.get("repos")
    if not isinstance(repos, list):
        raise RemediationError("input.repos must be a list")
    return payload, raw_bytes


def _stable_batch_id(raw_bytes: bytes) -> str:
    digest = hashlib.sha256(raw_bytes).hexdigest()[:12]
    return f"fcos-remediate-{digest}"


def _normalize_policy_repo_path(workspace_root: Path, policy_path: str) -> Path:
    p = Path(policy_path)
    if p.is_absolute():
        return p.resolve()

    direct = (workspace_root / p).resolve()
    if direct.exists():
        return direct

    parts = p.parts
    if parts and parts[0] == workspace_root.name:
        return workspace_root.joinpath(*parts[1:]).resolve()

    return direct


def _is_within_workspace(workspace_root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(workspace_root)
        return True
    except ValueError:
        return False


def _workspace_root_from(scorecard: dict[str, Any], explicit: str | None) -> Path:
    source = explicit or scorecard.get("workspace_root")
    if not isinstance(source, str) or not source.strip():
        raise RemediationError("workspace root missing (pass --workspace-root or include scorecard.workspace_root)")
    root = Path(source).expanduser().resolve()
    if not root.is_dir():
        raise RemediationError(f"workspace root not found: {root}")
    return root


def _manual_reason(*, exists: bool, repo_class: str, drifts: list[str], in_workspace: bool, safe_target: bool) -> str:
    if not safe_target:
        return "repo path is empty or resolves to workspace root"
    if not in_workspace:
        return "resolved path escapes workspace root"
    if not exists:
        return "repo path missing; bootstrap batch cannot create missing repo roots"
    if repo_class not in ACTIONABLE_CLASSES:
        return "repo class is not bootstrap-managed by this batch generator"
    if drifts:
        return "policy declaration drift requires governance-kernel model update"
    return "no supported automatic remediation for this row"


def _command_for(resolved_path: Path, row: dict[str, Any], bootstrap_script: Path) -> list[str]:
    return [str(bootstrap_script), str(resolved_path), "--class", str(row["class"])]


def _build_batch(
    scorecard: dict[str, Any], *, raw_bytes: bytes, batch_id: str | None, bootstrap_script: Path, workspace_root: Path
) -> dict[str, Any]:
    repos = scorecard["repos"]
    actions: list[dict[str, Any]] = []

    for row_any in sorted(repos, key=lambda item: str(item.get("path", ""))):
        if not isinstance(row_any, dict):
            raise RemediationError("input.repos entries must be objects")
        row = row_any
        missing = list(row.get("requirement_violations") or [])
        drifts = list(row.get("declaration_drifts") or [])
        if not missing and not drifts:
            continue

        declared_caps = row.get("declared_capabilities") if isinstance(row.get("declared_capabilities"), dict) else {}
        observed_caps = row.get("observed_capabilities") if isinstance(row.get("observed_capabilities"), dict) else {}
        governance_drift_keys = [
            key for key in drifts
            if declared_caps.get(key) is False and observed_caps.get(key) is True
        ]

        policy_path = str(row.get("path") or "")
        normalized_resolved_path = _normalize_policy_repo_path(workspace_root, policy_path)
        in_workspace = _is_within_workspace(workspace_root, normalized_resolved_path)
        safe_target = bool(policy_path.strip()) and normalized_resolved_path != workspace_root
        exists = normalized_resolved_path.is_dir()
        scorecard_resolved_path = str(row.get("resolved_path") or "")

        base_action: dict[str, Any] = {
            "path": policy_path,
            "resolved_path": str(normalized_resolved_path),
            "scorecard_resolved_path": scorecard_resolved_path,
            "resolved_path_mismatch": bool(scorecard_resolved_path) and scorecard_resolved_path != str(normalized_resolved_path),
            "repo_class": row.get("class"),
            "exists": exists,
            "workspace_root": str(workspace_root),
        }

        planned_bootstrap = False
        if missing and exists and safe_target and in_workspace and row.get("class") in ACTIONABLE_CLASSES:
            actions.append(
                {
                    **base_action,
                    "kind": "bootstrap_repo",
                    "status": "planned",
                    "reason": f"missing required capabilities: {', '.join(missing)}",
                    "requirement_violations": missing,
                    "declaration_drifts": [],
                    "command": _command_for(normalized_resolved_path, row, bootstrap_script),
                }
            )
            planned_bootstrap = True

        if governance_drift_keys:
            drift_reason = "policy declaration drift requires governance-kernel model update"
            if missing and not planned_bootstrap:
                drift_reason += f"; unresolved required capabilities: {', '.join(missing)}"
            actions.append(
                {
                    **base_action,
                    "kind": "manual_followup",
                    "status": "blocked",
                    "reason": drift_reason,
                    "requirement_violations": [] if planned_bootstrap else missing,
                    "declaration_drifts": governance_drift_keys,
                }
            )
            continue

        if not planned_bootstrap:
            actions.append(
                {
                    **base_action,
                    "kind": "manual_followup",
                    "status": "blocked",
                    "reason": _manual_reason(
                        exists=exists,
                        repo_class=str(row.get("class") or ""),
                        drifts=drifts,
                        in_workspace=in_workspace,
                        safe_target=safe_target,
                    ),
                    "requirement_violations": missing,
                    "declaration_drifts": drifts,
                }
            )

    effective_batch_id = batch_id or _stable_batch_id(raw_bytes)
    planned = sum(1 for action in actions if action["kind"] == "bootstrap_repo")
    blocked = sum(1 for action in actions if action["status"] == "blocked")
    declaration = sum(1 for action in actions if action.get("declaration_drifts"))

    return {
        "schema_version": 1,
        "batch_id": effective_batch_id,
        "mode": "patch",
        "workspace_root": str(workspace_root),
        "source_audit": {
            "policy": scorecard.get("policy"),
            "workspace_root": scorecard.get("workspace_root"),
            "status": scorecard.get("summary", {}).get("status"),
            "exit_code": scorecard.get("exit_code"),
        },
        "summary": {
            "total_actions": len(actions),
            "planned_bootstrap_actions": planned,
            "blocked_actions": blocked,
            "declaration_drift_actions": declaration,
        },
        "actions": actions,
    }


def _write_output(dest: str, payload: str) -> None:
    if dest == "-":
        sys.stdout.write(payload)
        return
    path = Path(dest).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, "utf-8")


def _apply_batch(batch: dict[str, Any]) -> tuple[dict[str, Any], int]:
    actions = batch["actions"]
    apply_results: list[dict[str, Any]] = []
    exit_code = EXIT_OK

    for action in actions:
        if action.get("kind") != "bootstrap_repo":
            apply_results.append(
                {
                    "path": action.get("path"),
                    "status": action.get("status"),
                    "reason": action.get("reason"),
                }
            )
            continue

        command = [str(x) for x in action.get("command") or []]
        proc = subprocess.run(command, check=False, capture_output=True, text=True)
        result: dict[str, Any] = {
            "path": action.get("path"),
            "resolved_path": action.get("resolved_path"),
            "status": "applied" if proc.returncode == 0 else "apply_failed",
            "exit_code": proc.returncode,
        }
        if proc.stdout.strip():
            try:
                result["bootstrap_report"] = json.loads(proc.stdout)
            except json.JSONDecodeError:
                result["stdout"] = proc.stdout.splitlines()
        if proc.stderr.strip():
            result["stderr"] = proc.stderr.splitlines()
        apply_results.append(result)
        if proc.returncode != 0:
            exit_code = EXIT_APPLY_PARTIAL

    batch["mode"] = "apply"
    batch["apply_results"] = apply_results
    batch["summary"] = {
        **batch["summary"],
        "applied_actions": sum(1 for row in apply_results if row.get("status") == "applied"),
        "apply_failures": sum(1 for row in apply_results if row.get("status") == "apply_failed"),
    }
    return batch, exit_code


def main() -> int:
    args = _parse_args()
    input_path = Path(args.input).expanduser().resolve()
    bootstrap_script = Path(args.bootstrap_script).expanduser().resolve()

    if not bootstrap_script.is_file():
        print(f"error: bootstrap script not found: {bootstrap_script}", file=sys.stderr)
        return EXIT_ERROR

    try:
        scorecard, raw_bytes = _load_scorecard(input_path)
        workspace_root = _workspace_root_from(scorecard, args.workspace_root)
        batch = _build_batch(
            scorecard,
            raw_bytes=raw_bytes,
            batch_id=args.batch_id,
            bootstrap_script=bootstrap_script,
            workspace_root=workspace_root,
        )
    except RemediationError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    exit_code = EXIT_OK
    if args.mode == "apply":
        batch, exit_code = _apply_batch(batch)

    payload = json.dumps(batch, indent=2, sort_keys=True) + "\n"
    _write_output(args.output, payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
