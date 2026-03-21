#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_ACTION_REQUIRED = 2

STATUS_PASS = "pass"
STATUS_DRIFT_DETECTED = "drift_detected"
STATUS_BATCH_GENERATED = "batch_generated"
STATUS_BLOCKED = "blocked"
STATUS_BATCH_APPLIED = "batch_applied"
STATUS_APPLY_FAILED = "apply_failed"
STATUS_AUDIT_ERROR = "audit_error"
STATUS_BATCH_ERROR = "batch_error"


class NightlyError(ValueError):
    pass


def _parse_args() -> argparse.Namespace:
    repo_root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(
        description="Run the FCOS nightly fleet audit and produce deterministic remediation artifacts."
    )
    parser.add_argument(
        "--workspace-root",
        default=os.environ.get("FCOS_WORKSPACE_ROOT", str(Path.home() / "ai-society")),
        help="Workspace root containing local repos",
    )
    parser.add_argument(
        "--policy-path",
        default=os.environ.get(
            "FCOS_POLICY_PATH",
            str(Path.home() / "ai-society" / "holdingco" / "governance-kernel" / "governance" / "programs" / "fcos" / "fleet-state.yaml"),
        ),
        help="Path to fleet-state.yaml",
    )
    parser.add_argument(
        "--artifact-root",
        default=os.environ.get(
            "FCOS_AUDIT_ARTIFACT_ROOT",
            str(Path(os.environ.get("XDG_STATE_HOME", str(Path.home() / ".local" / "state"))) / "fcos" / "nightly"),
        ),
        help="Directory under which timestamped nightly artifacts are stored",
    )
    parser.add_argument(
        "--remediation-mode",
        default=os.environ.get("FCOS_REMEDIATION_MODE", "patch"),
        choices=("audit-only", "patch", "apply"),
        help="audit-only = no remediation batch, patch = plan only, apply = run bootstrap actions",
    )
    parser.add_argument(
        "--timestamp",
        default=os.environ.get("FCOS_AUDIT_TIMESTAMP"),
        help="Timestamp for this run (default: current UTC time)",
    )
    parser.add_argument(
        "--audit-script",
        default=os.environ.get("FCOS_AUDIT_SCRIPT", str(repo_root / "scripts" / "audit-fleet.py")),
        help="Path to audit-fleet.py",
    )
    parser.add_argument(
        "--remediation-script",
        default=os.environ.get(
            "FCOS_REMEDIATION_SCRIPT",
            str(repo_root / "scripts" / "open-remediation-batch.sh"),
        ),
        help="Path to open-remediation-batch.sh",
    )
    parser.add_argument(
        "--bootstrap-script",
        default=os.environ.get("FCOS_BOOTSTRAP_SCRIPT"),
        help="Optional path to bootstrap-repo.sh used by remediation apply mode",
    )
    return parser.parse_args()


def _timestamp_now() -> str:
    import datetime as _dt

    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _run_json_command(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(command, check=False, capture_output=True, text=True)


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text("utf-8"))
    except FileNotFoundError as exc:
        raise NightlyError(f"missing JSON artifact: {path}") from exc
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NightlyError(f"invalid JSON artifact {path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise NightlyError(f"JSON artifact root must be an object: {path}")
    return payload


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")


def _summary_counts(scorecard: dict[str, Any]) -> dict[str, int]:
    summary = scorecard.get("summary", {})
    return {
        "requirement_violations": int(summary.get("requirement_violations", 0) or 0),
        "declaration_drifts": int(summary.get("declaration_drifts", 0) or 0),
        "missing_entries": int(summary.get("missing_entries", 0) or 0),
    }


def _derive_status(
    *,
    remediation_mode: str,
    drift_detected: bool,
    batch: dict[str, Any] | None,
    batch_exit_code: int | None,
) -> tuple[str, int]:
    if not drift_detected:
        return STATUS_PASS, EXIT_OK
    if remediation_mode == "audit-only":
        return STATUS_DRIFT_DETECTED, EXIT_ACTION_REQUIRED
    if batch is None:
        return STATUS_BATCH_ERROR, EXIT_ERROR

    summary = batch.get("summary", {})
    blocked_actions = int(summary.get("blocked_actions", 0) or 0)
    apply_failures = int(summary.get("apply_failures", 0) or 0)
    applied_actions = int(summary.get("applied_actions", 0) or 0)

    if remediation_mode == "patch":
        if blocked_actions:
            return STATUS_BLOCKED, EXIT_ACTION_REQUIRED
        return STATUS_BATCH_GENERATED, EXIT_ACTION_REQUIRED

    if batch_exit_code not in (EXIT_OK, EXIT_ACTION_REQUIRED):
        return STATUS_BATCH_ERROR, EXIT_ERROR
    if apply_failures:
        return STATUS_APPLY_FAILED, EXIT_ACTION_REQUIRED
    if blocked_actions and applied_actions == 0:
        return STATUS_BLOCKED, EXIT_ACTION_REQUIRED
    return STATUS_BATCH_APPLIED, EXIT_ACTION_REQUIRED


def main() -> int:
    args = _parse_args()
    workspace_root = Path(args.workspace_root).expanduser().resolve()
    policy_path = Path(args.policy_path).expanduser().resolve()
    artifact_root = Path(args.artifact_root).expanduser().resolve()
    audit_script = Path(args.audit_script).expanduser().resolve()
    remediation_script = Path(args.remediation_script).expanduser().resolve()
    bootstrap_script = Path(args.bootstrap_script).expanduser().resolve() if args.bootstrap_script else None
    timestamp = args.timestamp or _timestamp_now()

    run_dir = artifact_root / timestamp
    scorecard_json = run_dir / "scorecard.json"
    scorecard_markdown = run_dir / "scorecard.md"
    remediation_batch = run_dir / "remediation-batch.json"
    summary_path = run_dir / "run-summary.json"
    run_dir.mkdir(parents=True, exist_ok=True)

    summary: dict[str, Any] = {
        "schema_version": 1,
        "timestamp": timestamp,
        "workspace_root": str(workspace_root),
        "policy_path": str(policy_path),
        "run_dir": str(run_dir),
        "scorecard_json": str(scorecard_json),
        "scorecard_markdown": str(scorecard_markdown),
        "remediation_mode": args.remediation_mode,
    }

    if not audit_script.is_file():
        summary.update({"status": STATUS_AUDIT_ERROR, "exit_code": EXIT_ERROR, "error": f"audit script not found: {audit_script}"})
        _write_json(summary_path, summary)
        return EXIT_ERROR
    if not remediation_script.is_file():
        summary.update({"status": STATUS_BATCH_ERROR, "exit_code": EXIT_ERROR, "error": f"remediation script not found: {remediation_script}"})
        _write_json(summary_path, summary)
        return EXIT_ERROR
    if bootstrap_script is not None and not bootstrap_script.is_file():
        summary.update({"status": STATUS_BATCH_ERROR, "exit_code": EXIT_ERROR, "error": f"bootstrap script not found: {bootstrap_script}"})
        _write_json(summary_path, summary)
        return EXIT_ERROR

    audit_proc = _run_json_command(
        [
            sys.executable,
            str(audit_script),
            "--workspace-root",
            str(workspace_root),
            "--policy",
            str(policy_path),
            "--json",
            str(scorecard_json),
            "--markdown",
            str(scorecard_markdown),
        ]
    )
    summary["audit_exit_code"] = audit_proc.returncode
    if audit_proc.stderr.strip():
        summary["audit_stderr"] = audit_proc.stderr.splitlines()
    if audit_proc.stdout.strip():
        summary["audit_stdout"] = audit_proc.stdout.splitlines()

    if audit_proc.returncode not in (EXIT_OK, EXIT_ACTION_REQUIRED):
        summary.update({"status": STATUS_AUDIT_ERROR, "exit_code": audit_proc.returncode})
        _write_json(summary_path, summary)
        return audit_proc.returncode

    try:
        scorecard = _load_json(scorecard_json)
    except NightlyError as exc:
        summary.update({"status": STATUS_AUDIT_ERROR, "exit_code": EXIT_ERROR, "error": str(exc)})
        _write_json(summary_path, summary)
        return EXIT_ERROR

    drift_counts = _summary_counts(scorecard)
    drift_detected = bool(drift_counts["requirement_violations"] or drift_counts["declaration_drifts"])
    summary["drift_counts"] = drift_counts
    summary["drift_detected"] = drift_detected

    batch_payload: dict[str, Any] | None = None
    batch_exit_code: int | None = None

    if drift_detected and args.remediation_mode != "audit-only":
        batch_command = [
            sys.executable,
            str(remediation_script),
            "--input",
            str(scorecard_json),
            "--mode",
            args.remediation_mode,
            "--output",
            str(remediation_batch),
            "--workspace-root",
            str(workspace_root),
        ]
        if bootstrap_script is not None:
            batch_command.extend(["--bootstrap-script", str(bootstrap_script)])
        batch_proc = _run_json_command(batch_command)
        batch_exit_code = batch_proc.returncode
        summary["batch_exit_code"] = batch_exit_code
        if batch_proc.stderr.strip():
            summary["batch_stderr"] = batch_proc.stderr.splitlines()
        if batch_proc.stdout.strip():
            summary["batch_stdout"] = batch_proc.stdout.splitlines()
        if remediation_batch.is_file():
            try:
                batch_payload = _load_json(remediation_batch)
            except NightlyError as exc:
                summary.update({"status": STATUS_BATCH_ERROR, "exit_code": EXIT_ERROR, "error": str(exc)})
                _write_json(summary_path, summary)
                return EXIT_ERROR
            summary["remediation_batch"] = str(remediation_batch)
            summary["batch_summary"] = batch_payload.get("summary", {})

    status, exit_code = _derive_status(
        remediation_mode=args.remediation_mode,
        drift_detected=drift_detected,
        batch=batch_payload,
        batch_exit_code=batch_exit_code,
    )
    summary["status"] = status
    summary["exit_code"] = exit_code

    if status == STATUS_PASS:
        summary["remediation_generated"] = False
    else:
        summary["remediation_generated"] = remediation_batch.is_file()

    _write_json(summary_path, summary)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
