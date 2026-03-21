from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "open-remediation-batch.sh"


def _run_script(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _audit_payload(repo: Path, *, exists: bool = True, missing: list[str] | None = None, drifts: list[str] | None = None) -> dict:
    return {
        "schema_version": 1,
        "workspace_root": str(repo.parents[3]),
        "policy": "/tmp/fleet-state.yaml",
        "summary": {
            "status": "fail" if missing or drifts else "pass",
            "requirement_violations": len(missing or []),
            "declaration_drifts": len(drifts or []),
        },
        "exit_code": 2 if missing or drifts else 0,
        "repos": [
            {
                "path": "ai-society/softwareco/owned/app-a",
                "resolved_path": str(repo),
                "class": "required",
                "exists": exists,
                "requirement_violations": list(missing or []),
                "declaration_drifts": list(drifts or []),
            }
        ],
    }


class TestOpenRemediationBatchScript(unittest.TestCase):
    def test_patch_mode_generates_bootstrap_action(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "ai-society" / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            audit_path = Path(td) / "audit.json"
            audit_path.write_text(
                json.dumps(_audit_payload(repo, missing=["rocs_ci_gate"]), indent=2) + "\n",
                "utf-8",
            )

            proc = _run_script("--input", str(audit_path), "--mode", "patch")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["summary"]["planned_bootstrap_actions"], 1)
            self.assertEqual(payload["actions"][0]["kind"], "bootstrap_repo")
            self.assertEqual(payload["actions"][0]["command"][-2:], ["--class", "required"])

    def test_apply_mode_bootstraps_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "ai-society" / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            audit_path = Path(td) / "audit.json"
            audit_path.write_text(
                json.dumps(
                    _audit_payload(
                        repo,
                        missing=["rocs_cli_vendored", "ontology_manifest", "rocs_ci_gate"],
                    ),
                    indent=2,
                ) + "\n",
                "utf-8",
            )

            proc = _run_script("--input", str(audit_path), "--mode", "apply")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["summary"]["applied_actions"], 1)
            self.assertTrue((repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json").is_file())
            self.assertTrue((repo / "ontology" / "manifest.yaml").is_file())
            self.assertTrue((repo / "scripts" / "ci" / "full.sh").is_file())

    def test_missing_repo_path_is_reported_as_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "ai-society" / "softwareco" / "owned" / "app-a"
            audit_path = Path(td) / "audit.json"
            audit_path.write_text(
                json.dumps(_audit_payload(repo, exists=False, missing=["rocs_ci_gate"]), indent=2) + "\n",
                "utf-8",
            )

            proc = _run_script("--input", str(audit_path), "--mode", "patch")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["summary"]["blocked_actions"], 1)
            self.assertEqual(payload["actions"][0]["status"], "blocked")
            self.assertIn("missing repo roots", payload["actions"][0]["reason"])

    def test_declaration_drift_is_blocked_for_manual_followup(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "ai-society" / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            audit_path = Path(td) / "audit.json"
            audit_path.write_text(
                json.dumps(_audit_payload(repo, drifts=["rocs_cli_vendored"]), indent=2) + "\n",
                "utf-8",
            )

            proc = _run_script("--input", str(audit_path), "--mode", "patch")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["summary"]["blocked_actions"], 1)
            self.assertEqual(payload["actions"][0]["kind"], "manual_followup")
            self.assertIn("declaration drift", payload["actions"][0]["reason"])

    def test_apply_mode_recomputes_paths_inside_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = workspace / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            outside = Path(td) / "outside-scope-target"
            audit = _audit_payload(repo, missing=["rocs_ci_gate"])
            audit["repos"][0]["resolved_path"] = str(outside)
            audit_path = Path(td) / "audit.json"
            audit_path.write_text(json.dumps(audit, indent=2) + "\n", "utf-8")

            proc = _run_script("--input", str(audit_path), "--mode", "apply")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            action = payload["actions"][0]
            self.assertTrue(action["resolved_path_mismatch"])
            self.assertEqual(action["resolved_path"], str(repo))
            self.assertFalse(outside.exists())
            self.assertTrue((repo / "scripts" / "ci" / "full.sh").is_file())

    def test_blank_policy_path_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "ai-society" / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            audit = _audit_payload(repo, missing=["rocs_ci_gate"])
            audit["repos"][0]["path"] = ""
            audit_path = Path(td) / "audit.json"
            audit_path.write_text(json.dumps(audit, indent=2) + "\n", "utf-8")

            proc = _run_script("--input", str(audit_path), "--mode", "patch")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["actions"][0]["status"], "blocked")
            self.assertIn("workspace root", payload["actions"][0]["reason"])


if __name__ == "__main__":
    unittest.main()
