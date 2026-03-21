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


def _manual_reason(row: dict[str, Any]) -> str:
    if not row.get("exists"):
        return "repo path missing; bootstrap batch cannot create missing repo roots"
    if row.get("requirement_violations") and row.get("class") not in ACTIONABLE_CLASSES:
        return "repo class is not bootstrap-managed by this batch generator"
    if row.get("declaration_drifts"):
        return "policy declaration drift requires governance-kernel model update"
    return "no supported automatic remediation for this row"


def _command_for(row: dict[str, Any], bootstrap_script: Path) -> list[str]:
    return [str(bootstrap_script), str(row["resolved_path"]), "--class", str(row["class"])]


def _build_batch(scorecard: dict[str, Any], *, raw_bytes: bytes, batch_id: str | None, bootstrap_script: Path) -> dict[str, Any]:
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

        base_action: dict[str, Any] = {
            "path": row.get("path"),
            "resolved_path": row.get("resolved_path"),
            "repo_class": row.get("class"),
            "exists": bool(row.get("exists")),
            "requirement_violations": missing,
            "declaration_drifts": drifts,
        }

        if missing and row.get("exists") and row.get("class") in ACTIONABLE_CLASSES:
            action = {
                **base_action,
                "kind": "bootstrap_repo",
                "status": "planned",
                "reason": f"missing required capabilities: {', '.join(missing)}",
                "command": _command_for(row, bootstrap_script),
            }
        else:
            action = {
                **base_action,
                "kind": "manual_followup",
                "status": "blocked",
                "reason": _manual_reason(row),
            }
        actions.append(action)

    effective_batch_id = batch_id or _stable_batch_id(raw_bytes)
    planned = sum(1 for action in actions if action["kind"] == "bootstrap_repo")
    blocked = sum(1 for action in actions if action["status"] == "blocked")
    declaration = sum(1 for action in actions if action.get("declaration_drifts"))

    return {
        "schema_version": 1,
        "batch_id": effective_batch_id,
        "mode": "patch",
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
        batch = _build_batch(
            scorecard,
            raw_bytes=raw_bytes,
            batch_id=args.batch_id,
            bootstrap_script=bootstrap_script,
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
