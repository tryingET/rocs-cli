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


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def _audit_payload(repo: Path, *, exists: bool = True, missing: list[str] | None = None, drifts: list[str] | None = None) -> dict:
    return {
        "schema_version": 1,
        "workspace_root": str(repo.parents[3]),
        "policy": "/tmp/fleet-state.yaml",
        "summary": {
            "status": "fail" if missing else "pass",
            "requirement_violations": len(missing or []),
            "declaration_drifts": len(drifts or []),
        },
        "exit_code": 2 if missing else 0,
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


if __name__ == "__main__":
    unittest.main()
