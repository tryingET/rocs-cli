from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "run-fleet-audit-nightly.sh"


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
            repo / "gitlab" / "ci" / "rocs.yml",
            "stages:\n  - validate\n\nrocs:validate:\n  stage: validate\n  script:\n    - ROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n",
        )
        _write(repo / ".gitlab-ci.yml", "include:\n  - local: 'gitlab/ci/rocs.yml'\n")
        _write(
            repo / "scripts" / "ci" / "full.sh",
            "#!/usr/bin/env bash\nset -euo pipefail\nexport ROCS_WORKSPACE_ROOT=\"${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}\"\nexport ROCS_WORKSPACE_REF_MODE=\"${ROCS_WORKSPACE_REF_MODE:-loose}\"\n",
        )
    return repo


def _policy_for(path: str) -> dict:
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
                        "rocs_cli_vendored": True,
                        "ontology_manifest": True,
                        "rocs_ci_gate": True,
                    },
                    "owner": "test",
                }
            ]
        },
    }


class TestRunFleetAuditNightlyScript(unittest.TestCase):
    def test_emits_scorecards_and_remediation_batch_when_drift_detected(self) -> None:
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

            proc = subprocess.run(
                ["bash", str(SCRIPT)],
                cwd=REPO_ROOT,
                env=env,
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)

            run_dir = artifact_root / "20260321T000000Z"
            self.assertTrue((run_dir / "scorecard.json").is_file())
            self.assertTrue((run_dir / "scorecard.md").is_file())
            self.assertTrue((run_dir / "remediation-batch.json").is_file())

            summary = json.loads((run_dir / "run-summary.json").read_text("utf-8"))
            self.assertEqual(summary["audit_exit_code"], 2)
            self.assertEqual(summary["remediation_generated"], True)


if __name__ == "__main__":
    unittest.main()
