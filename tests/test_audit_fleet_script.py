from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "audit-fleet.py"


def _run_audit(*args: str) -> subprocess.CompletedProcess[str]:
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


def _mk_repo(
    workspace_root: Path,
    rel: str,
    *,
    vendored: bool,
    manifest: bool,
    ci_gate: bool,
    ci_contract: str = "current",
) -> Path:
    repo = workspace_root / rel
    repo.mkdir(parents=True, exist_ok=True)

    if vendored:
        _write(
            repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json",
            json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n",
        )

    if manifest:
        _write(repo / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")

    if ci_gate:
        if ci_contract == "current":
            _write(
                repo / "gitlab" / "ci" / "rocs.yml",
                "\n".join(
                    [
                        "stages:",
                        "  - validate",
                        "",
                        "rocs:validate:",
                        "  stage: validate",
                        "  script:",
                        "    - ROCS_CMD='uvx -n --from ./tools/rocs-cli rocs' ROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh",
                        "",
                    ]
                ),
            )
            _write(repo / "scripts" / "ci" / "full.sh", "#!/usr/bin/env bash\nset -euo pipefail\n")
        else:
            _write(repo / "gitlab" / "ci" / "rocs.yml", "stages:\n  - validate\n")
        _write(repo / ".gitlab-ci.yml", "include:\n  - local: 'gitlab/ci/rocs.yml'\n")

    return repo


def _policy_for(paths: list[str]) -> dict:
    repos = []
    for p in paths:
        repos.append(
            {
                "path": p,
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
        )

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
        "fleet": {"repos": repos},
    }


class TestAuditFleetScript(unittest.TestCase):
    def test_detects_required_violations_with_stable_exit_2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=False,
            )

            policy = _policy_for(["ai-society/softwareco/owned/app-a"])
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)

            payload = json.loads(proc.stdout)
            self.assertEqual(payload["summary"]["requirement_violations"], 1)
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["rocs_ci_gate"])
            self.assertTrue(payload["repos"][0]["exists"])

    def test_report_only_forces_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=False,
                ci_gate=False,
            )

            policy = _policy_for(["ai-society/softwareco/owned/app-a"])
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
                "--report-only",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["summary"]["status"], "fail")
            self.assertEqual(payload["exit_code"], 0)

    def test_writes_json_and_markdown_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
            )

            policy = _policy_for(["ai-society/softwareco/owned/app-a"])
            policy_path = Path(td) / "fleet-state.yaml"
            json_out = Path(td) / "scorecard.json"
            md_out = Path(td) / "scorecard.md"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
                str(json_out),
                "--markdown",
                str(md_out),
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertTrue(json_out.is_file())
            self.assertTrue(md_out.is_file())

            payload = json.loads(json_out.read_text("utf-8"))
            self.assertEqual(payload["summary"]["status"], "pass")

            md = md_out.read_text("utf-8")
            self.assertIn("# FCOS Fleet Audit Scorecard", md)
            self.assertIn("## Repo Results", md)

    def test_stale_legacy_ci_gate_does_not_count_as_current_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
                ci_contract="legacy",
            )

            policy = _policy_for(["ai-society/softwareco/owned/app-a"])
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            self.assertEqual(payload["summary"]["requirement_violations"], 1)
            evidence = payload["repos"][0]["evidence"]["rocs_ci_gate"]
            self.assertEqual(evidence["wrapper_hits"], [])
            self.assertEqual(evidence["wrapper_call_present"], False)
            self.assertEqual(evidence["profile_contract_present"], False)

    def test_comment_only_ci_markers_do_not_count_as_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = workspace / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            _write(repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n")
            _write(repo / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")
            _write(repo / "gitlab" / "ci" / "rocs.yml", "# ROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n")
            _write(repo / ".gitlab-ci.yml", "# include:\n#   - local: 'gitlab/ci/rocs.yml'\n")
            _write(repo / "scripts" / "ci" / "full.sh", "#!/usr/bin/env bash\nset -euo pipefail\n")

            policy = _policy_for(["ai-society/softwareco/owned/app-a"])
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            evidence = payload["repos"][0]["evidence"]["rocs_ci_gate"]
            self.assertEqual(evidence["include_present"], False)
            self.assertEqual(evidence["wrapper_call_present"], False)
            self.assertEqual(evidence["profile_contract_present"], False)

    def test_profile_export_in_separate_job_does_not_satisfy_wrapper_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = workspace / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            _write(repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n")
            _write(repo / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")
            _write(
                repo / "gitlab" / "ci" / "rocs.yml",
                "\n".join(
                    [
                        "stages:",
                        "  - validate",
                        "set-profile:",
                        "  script:",
                        "    - export ROCS_CI_PROFILE=branch-ci",
                        "run-wrapper:",
                        "  script:",
                        "    - bash scripts/ci/full.sh",
                        "",
                    ]
                ),
            )
            _write(repo / ".gitlab-ci.yml", "include:\n  - local: 'gitlab/ci/rocs.yml'\n")
            _write(repo / "scripts" / "ci" / "full.sh", "#!/usr/bin/env bash\nset -euo pipefail\n")

            policy = _policy_for(["ai-society/softwareco/owned/app-a"])
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
            )
            self.assertEqual(proc.returncode, 2, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            evidence = payload["repos"][0]["evidence"]["rocs_ci_gate"]
            self.assertEqual(evidence["include_present"], True)
            self.assertEqual(evidence["wrapper_call_present"], True)
            self.assertEqual(evidence["profile_contract_present"], False)

    def test_output_is_deterministic_across_repeated_runs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
            )
            _mk_repo(
                workspace,
                "softwareco/owned/app-b",
                vendored=False,
                manifest=False,
                ci_gate=False,
            )

            policy = _policy_for([
                "ai-society/softwareco/owned/app-a",
                "ai-society/softwareco/owned/app-b",
            ])
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            json_a = Path(td) / "a.json"
            md_a = Path(td) / "a.md"
            json_b = Path(td) / "b.json"
            md_b = Path(td) / "b.md"

            first = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
                str(json_a),
                "--markdown",
                str(md_a),
                "--report-only",
            )
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            second = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
                str(json_b),
                "--markdown",
                str(md_b),
                "--report-only",
            )
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)

            self.assertEqual(json_a.read_text("utf-8"), json_b.read_text("utf-8"))
            self.assertEqual(md_a.read_text("utf-8"), md_b.read_text("utf-8"))

    def test_invalid_policy_returns_exit_1(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            workspace.mkdir(parents=True)
            bad_policy = Path(td) / "bad.yaml"
            bad_policy.write_text("fleet: {}\n", "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(bad_policy),
                "--json",
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("error:", proc.stderr)


if __name__ == "__main__":
    unittest.main()
