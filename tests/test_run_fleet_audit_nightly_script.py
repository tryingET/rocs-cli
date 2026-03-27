from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_SCRIPT = REPO_ROOT / "scripts" / "run-fleet-audit-nightly.py"
SHELL_WRAPPER = REPO_ROOT / "scripts" / "run-fleet-audit-nightly.sh"


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def _mk_repo(workspace_root: Path, rel: str, *, ci_gate: bool) -> Path:
    repo = workspace_root / rel
    repo.mkdir(parents=True, exist_ok=True)
    _write(
        repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json",
        json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n",
    )
    _write(repo / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")
    if ci_gate:
        _write(
            repo / ".githooks" / "pre-push",
            "#!/usr/bin/env bash\nset -euo pipefail\nROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n",
        )
        (repo / ".githooks" / "pre-push").chmod(0o755)
        _write(
            repo / "scripts" / "ci" / "full.sh",
            "#!/usr/bin/env bash\nset -euo pipefail\nexport ROCS_WORKSPACE_ROOT=\"${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}\"\nexport ROCS_WORKSPACE_REF_MODE=\"${ROCS_WORKSPACE_REF_MODE:-loose}\"\n",
        )
    return repo


def _policy_for(path: str, *, declared_vendored: bool = True) -> dict:
    return {
        "schema_version": 2,
        "schema": {
            "repo_entry_required_fields": [
                "path",
                "scope",
                "class",
                "state",
                "capabilities",
                "owner",
            ]
        },
        "kill_switch": {"fcos_enforcement": {"mode": "advisory"}},
        "repo_classes": {
            "required": {
                "required_capabilities": {
                    "rocs_cli_vendored": True,
                    "ontology_manifest": True,
                    "rocs_ci_gate": True,
                }
            }
        },
        "fleet": {
            "repos": [
                {
                    "path": path,
                    "scope": "repo",
                    "class": "required",
                    "state": "inventoried",
                    "capabilities": {
                        "rocs_cli_vendored": declared_vendored,
                        "ontology_manifest": True,
                        "rocs_ci_gate": True,
                    },
                    "owner": "test",
                }
            ]
        },
    }


def _run_nightly(*, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(PYTHON_SCRIPT)],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


class TestRunFleetAuditNightlyScript(unittest.TestCase):
    def test_emits_scorecards_and_remediation_batch_when_required_drift_detected(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=False)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(_policy_for("ai-society/softwareco/owned/app-a"), sort_keys=False),
                "utf-8",
            )
            artifact_root = Path(td) / "artifacts"

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "patch",
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000000Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)

            run_dir = artifact_root / "20260321T000000Z"
            self.assertTrue((run_dir / "scorecard.json").is_file())
            self.assertTrue((run_dir / "scorecard.md").is_file())
            self.assertTrue((run_dir / "remediation-batch.json").is_file())

            summary = json.loads((run_dir / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["audit_exit_code"], 2)
            self.assertEqual(summary["status"], "batch_generated")
            self.assertEqual(summary["remediation_generated"], True)

    def test_declaration_drift_only_returns_action_required(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=True)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(
                    _policy_for("ai-society/softwareco/owned/app-a", declared_vendored=False),
                    sort_keys=False,
                ),
                "utf-8",
            )
            artifact_root = Path(td) / "artifacts"

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "patch",
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000100Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            summary = json.loads((artifact_root / "20260321T000100Z" / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["audit_exit_code"], 0)
            self.assertEqual(summary["drift_counts"]["declaration_drifts"], 1)
            self.assertEqual(summary["status"], "blocked")
            self.assertEqual(summary["remediation_generated"], True)

    def test_apply_failure_still_writes_summary(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=False)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(_policy_for("ai-society/softwareco/owned/app-a"), sort_keys=False),
                "utf-8",
            )
            artifact_root = Path(td) / "artifacts"
            fail_bootstrap = Path(td) / "fail-bootstrap.sh"
            fail_bootstrap.write_text("#!/usr/bin/env bash\nexit 7\n", "utf-8")
            fail_bootstrap.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "apply",
                    "FCOS_BOOTSTRAP_SCRIPT": str(fail_bootstrap),
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000200Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            summary = json.loads((artifact_root / "20260321T000200Z" / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["status"], "apply_failed")
            self.assertEqual(summary["batch_exit_code"], 2)
            self.assertTrue((artifact_root / "20260321T000200Z" / "remediation-batch.json").is_file())

    def test_summary_json_escapes_quoted_paths(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=True)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(_policy_for("ai-society/softwareco/owned/app-a"), sort_keys=False),
                "utf-8",
            )
            artifact_root = Path(td) / 'with"quote'

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "audit-only",
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000300Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            summary = json.loads((artifact_root / "20260321T000300Z" / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["status"], "pass")

    def test_mixed_apply_result_stays_blocked_when_manual_followup_remains(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=False)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(
                    _policy_for("ai-society/softwareco/owned/app-a", declared_vendored=False),
                    sort_keys=False,
                ),
                "utf-8",
            )
            artifact_root = Path(td) / "artifacts"
            bootstrap = Path(td) / "bootstrap.sh"
            bootstrap.write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "target=\"$1\"\n"
                "mkdir -p \"$target/scripts/ci\"\n"
                "printf '#!/usr/bin/env bash\\nset -euo pipefail\\n' > \"$target/scripts/ci/full.sh\"\n",
                "utf-8",
            )
            bootstrap.chmod(0o755)

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "apply",
                    "FCOS_BOOTSTRAP_SCRIPT": str(bootstrap),
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000350Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            summary = json.loads((artifact_root / "20260321T000350Z" / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["status"], "blocked")
            batch = json.loads((artifact_root / "20260321T000350Z" / "remediation-batch.json").read_text("utf-8"))
            self.assertEqual(batch["summary"]["applied_actions"], 1)
            self.assertEqual(batch["summary"]["blocked_actions"], 1)
            self.assertTrue((repo / "scripts" / "ci" / "full.sh").is_file())

    def test_audit_only_does_not_require_remediation_script(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=True)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(_policy_for("ai-society/softwareco/owned/app-a"), sort_keys=False),
                "utf-8",
            )
            artifact_root = Path(td) / "artifacts"

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "audit-only",
                    "FCOS_REMEDIATION_SCRIPT": str(Path(td) / "missing-remediation.py"),
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000400Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            summary = json.loads((artifact_root / "20260321T000400Z" / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["status"], "pass")

    def test_stale_batch_file_is_cleared_before_clean_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=True)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(_policy_for("ai-society/softwareco/owned/app-a"), sort_keys=False),
                "utf-8",
            )
            artifact_root = Path(td) / "artifacts"
            run_dir = artifact_root / "20260321T000450Z"
            run_dir.mkdir(parents=True, exist_ok=True)
            (run_dir / "remediation-batch.json").write_text('{"stale": true}\n', "utf-8")

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "audit-only",
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000450Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertFalse((run_dir / "remediation-batch.json").exists())
            summary = json.loads((run_dir / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["remediation_generated"], False)
            self.assertNotIn("remediation_batch", summary)

    def test_stale_batch_directory_is_cleared_before_clean_pass(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(workspace, "softwareco/owned/app-a", ci_gate=True)
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(
                yaml.safe_dump(_policy_for("ai-society/softwareco/owned/app-a"), sort_keys=False),
                "utf-8",
            )
            artifact_root = Path(td) / "artifacts"
            run_dir = artifact_root / "20260321T000451Z"
            (run_dir / "remediation-batch.json").mkdir(parents=True, exist_ok=True)

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(policy_path),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "audit-only",
                    "FCOS_AUDIT_TIMESTAMP": "20260321T000451Z",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertFalse((run_dir / "remediation-batch.json").exists())
            summary = json.loads((run_dir / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["status"], "pass")
            self.assertEqual(summary["remediation_generated"], False)

    def test_invalid_timestamp_is_rejected_into_invalid_artifact_bucket(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            workspace.mkdir(parents=True, exist_ok=True)
            artifact_root = Path(td) / "artifacts"

            env = os.environ.copy()
            env.update(
                {
                    "FCOS_WORKSPACE_ROOT": str(workspace),
                    "FCOS_POLICY_PATH": str(Path(td) / "missing-policy.yaml"),
                    "FCOS_AUDIT_ARTIFACT_ROOT": str(artifact_root),
                    "FCOS_REMEDIATION_MODE": "audit-only",
                    "FCOS_AUDIT_TIMESTAMP": "../escape",
                }
            )

            proc = _run_nightly(env=env)
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            summary = json.loads((artifact_root / "_invalid" / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["status"], "audit_error")
            self.assertIn("invalid timestamp", summary["error"])

    def test_shell_wrapper_uses_repo_managed_runtime(self) -> None:
        proc = subprocess.run(
            ["bash", str(SHELL_WRAPPER), "--help"],
            cwd=REPO_ROOT,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("Run the FCOS nightly fleet audit", proc.stdout)


if __name__ == "__main__":
    unittest.main()
