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
    manifest_text: str | None = None,
    workspace_contract: bool = True,
    manifest_relpath: str = "ontology/manifest.yaml",
) -> Path:
    repo = workspace_root / rel
    repo.mkdir(parents=True, exist_ok=True)

    if vendored:
        _write(
            repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json",
            json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n",
        )

    if manifest:
        _write(repo / manifest_relpath, manifest_text or "rocs:\n  layer: repo\n")

    if ci_gate:
        if ci_contract == "current":
            _write(
                repo / ".githooks" / "pre-push",
                "\n".join(
                    [
                        "#!/usr/bin/env bash",
                        "set -euo pipefail",
                        "ROCS_CMD='uvx -n --from ./tools/rocs-cli rocs' ROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh",
                        "",
                    ]
                ),
            )
            (repo / ".githooks" / "pre-push").chmod(0o755)
            wrapper = "#!/usr/bin/env bash\nset -euo pipefail\n"
            if workspace_contract:
                wrapper += "export ROCS_WORKSPACE_ROOT=\"${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}\"\nexport ROCS_WORKSPACE_REF_MODE=\"${ROCS_WORKSPACE_REF_MODE:-loose}\"\n"
            _write(repo / "scripts" / "ci" / "full.sh", wrapper)
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
            self.assertEqual(evidence["hook_hits"], [])
            self.assertNotEqual(evidence["legacy_gate_hits"], [])
            self.assertEqual(evidence["wrapper_call_present"], False)
            self.assertEqual(evidence["profile_contract_present"], False)

    def test_comment_only_hook_markers_do_not_count_as_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = workspace / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            _write(repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n")
            _write(repo / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")
            _write(repo / ".githooks" / "pre-push", "# ROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n")
            (repo / ".githooks" / "pre-push").chmod(0o755)
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
            self.assertEqual(evidence["hook_hits"], [".githooks/pre-push"])
            self.assertEqual(evidence["wrapper_call_present"], False)
            self.assertEqual(evidence["profile_contract_present"], False)

    def test_hook_without_profile_assignment_does_not_satisfy_wrapper_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = workspace / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            _write(repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n")
            _write(repo / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")
            _write(repo / ".githooks" / "pre-push", "#!/usr/bin/env bash\nset -euo pipefail\nbash scripts/ci/full.sh\n")
            (repo / ".githooks" / "pre-push").chmod(0o755)
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
            self.assertEqual(evidence["wrapper_call_present"], True)
            self.assertEqual(evidence["profile_contract_present"], False)

    def test_non_executable_hook_does_not_count_as_ci_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
            )
            (repo / ".githooks" / "pre-push").chmod(0o644)

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
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["rocs_ci_gate"])
            self.assertEqual(evidence["hook_exec_required"], True)
            self.assertEqual(evidence["hook_exec_present"], False)
            self.assertEqual(evidence["hook_exec_checked"], {".githooks/pre-push": False})

    def test_symlinked_hook_does_not_count_as_checked_in_ci_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
            )
            outside = Path(td) / "external-pre-push"
            outside.write_text(
                "#!/usr/bin/env bash\nset -euo pipefail\nROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n",
                "utf-8",
            )
            outside.chmod(0o755)
            (repo / ".githooks" / "pre-push").unlink()
            (repo / ".githooks" / "pre-push").symlink_to(outside)

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
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["rocs_ci_gate"])
            self.assertEqual(evidence["hook_hits"], [])
            self.assertEqual(evidence["hook_blocked_hits"], [{"path": ".githooks/pre-push", "reason": "path is a symlink"}])

    def test_unreadable_manifest_is_reported_as_a_violation_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
            )
            manifest = repo / "ontology" / "manifest.yaml"
            manifest.chmod(0)
            try:
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
                self.assertEqual(proc.stderr, "")
                payload = json.loads(proc.stdout)
                evidence = payload["repos"][0]["evidence"]["ontology_manifest"]
                self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["ontology_manifest"])
                self.assertEqual(evidence["locator_kind"], "invalid")
                self.assertIn("could not read ontology manifest", evidence["parse_error"])
            finally:
                manifest.chmod(0o644)

    def test_template_hook_does_not_count_as_active_ci_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = workspace / "softwareco" / "owned" / "app-a"
            repo.mkdir(parents=True, exist_ok=True)
            _write(repo / "tools" / "rocs-cli" / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n")
            _write(repo / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")
            _write(repo / ".githooks" / "pre-push.j2", "#!/usr/bin/env bash\nset -euo pipefail\nROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n")
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
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["rocs_ci_gate"])
            self.assertEqual(evidence["hook_hits"], [])
            self.assertEqual(evidence["hook_template_hits"], [".githooks/pre-push.j2"])
            self.assertEqual(evidence["wrapper_hits"], ["scripts/ci/full.sh"])

    def test_symlinked_wrapper_does_not_count_as_checked_in_ci_gate(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
            )
            outside = Path(td) / "external-full.sh"
            outside.write_text(
                "#!/usr/bin/env bash\nset -euo pipefail\nexport ROCS_WORKSPACE_ROOT=\"${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}\"\nexport ROCS_WORKSPACE_REF_MODE=\"${ROCS_WORKSPACE_REF_MODE:-loose}\"\n",
                "utf-8",
            )
            outside.chmod(0o755)
            (repo / "scripts" / "ci" / "full.sh").unlink()
            (repo / "scripts" / "ci" / "full.sh").symlink_to(outside)

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
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["rocs_ci_gate"])
            self.assertEqual(evidence["wrapper_hits"], [])
            self.assertEqual(evidence["wrapper_workspace_blocked_hits"], [{"path": "scripts/ci/full.sh", "reason": "path is a symlink"}])

    def test_repo_locators_require_workspace_aware_wrapper_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
                manifest_text="\n".join(
                    [
                        "rocs:",
                        "  layers:",
                        "    - name: core",
                        "      ref: '<repo:core/ontology-kernel@main>'",
                        "    - name: company",
                        "      ref: '<repo:softwareco/ontology@main>'",
                        "",
                    ]
                ) + "\n",
                workspace_contract=False,
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
            evidence = payload["repos"][0]["evidence"]["rocs_ci_gate"]
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["rocs_ci_gate"])
            self.assertEqual(evidence["workspace_contract_required"], True)
            self.assertEqual(evidence["workspace_root_present"], False)
            self.assertEqual(evidence["workspace_ref_mode_present"], False)

    def test_commented_wrapper_tokens_do_not_count_as_workspace_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            repo = _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
                manifest_text="\n".join(
                    [
                        "rocs:",
                        "  layers:",
                        "    - name: core",
                        "      ref: '<repo:core/ontology-kernel@main>'",
                        "",
                    ]
                ) + "\n",
            )
            (repo / "scripts" / "ci" / "full.sh").write_text(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "# export ROCS_WORKSPACE_ROOT=\"${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}\"\n"
                "# export ROCS_WORKSPACE_REF_MODE=\"${ROCS_WORKSPACE_REF_MODE:-strict}\"\n",
                "utf-8",
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
            evidence = payload["repos"][0]["evidence"]["rocs_ci_gate"]
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["rocs_ci_gate"])
            self.assertEqual(evidence["workspace_root_present"], False)
            self.assertEqual(evidence["workspace_ref_mode_present"], False)

    def test_legacy_gitlab_locators_fail_manifest_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
                manifest_text="\n".join(
                    [
                        "rocs:",
                        "  layers:",
                        "    - name: core",
                        "      ref: '<gitlab:ai-society/core/ontology-kernel@v0.1.0>'",
                        "    - name: company",
                        "      ref: '<gitlab:ai-society/softwareco/ontology@v0.1.0>'",
                        "",
                    ]
                ) + "\n",
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
            evidence = payload["repos"][0]["evidence"]["ontology_manifest"]
            self.assertEqual(payload["violations"]["required_capabilities"][0]["missing"], ["ontology_manifest"])
            self.assertEqual(evidence["locator_kind"], "gitlab")
            self.assertEqual(evidence["contract_reason"], "legacy_gitlab_locators")

    def test_commented_legacy_locator_does_not_fail_manifest_contract(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/owned/app-a",
                vendored=True,
                manifest=True,
                ci_gate=True,
                manifest_text="# migration note: <gitlab:ai-society/core/ontology-kernel@v0.1.0>\nrocs:\n  layer: repo\n",
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
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            evidence = payload["repos"][0]["evidence"]["ontology_manifest"]
            self.assertEqual(evidence["locator_kind"], "none")
            self.assertEqual(payload["summary"]["status"], "pass")

    def test_root_layout_manifest_counts_as_ontology_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            _mk_repo(
                workspace,
                "softwareco/ontology",
                vendored=True,
                manifest=True,
                ci_gate=True,
                manifest_relpath="manifest.yaml",
                manifest_text="rocs:\n  layer: company\n  depends_on:\n    - layer: core\n      ref: '<repo:core/ontology-kernel@main>'\n",
            )

            policy = _policy_for(["ai-society/softwareco/ontology"])
            policy_path = Path(td) / "fleet-state.yaml"
            policy_path.write_text(yaml.safe_dump(policy, sort_keys=False), "utf-8")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(policy_path),
                "--json",
            )
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads(proc.stdout)
            evidence = payload["repos"][0]["evidence"]["ontology_manifest"]
            self.assertEqual(evidence["primary_hit"], "manifest.yaml")
            self.assertEqual(evidence["locator_kind"], "repo")
            self.assertEqual(payload["summary"]["status"], "pass")

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

    def test_repo_path_escape_is_treated_as_missing_and_out_of_scope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            workspace.mkdir(parents=True, exist_ok=True)
            outside = Path(td) / "outside-repo"
            outside.mkdir(parents=True, exist_ok=True)
            _write(outside / "tools" / "rocs-cli" / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": {}}, indent=2) + "\n")
            _write(outside / "ontology" / "manifest.yaml", "rocs:\n  layer: repo\n")
            _write(outside / ".githooks" / "pre-push", "#!/usr/bin/env bash\nset -euo pipefail\nROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh\n")
            (outside / ".githooks" / "pre-push").chmod(0o755)
            _write(
                outside / "scripts" / "ci" / "full.sh",
                "#!/usr/bin/env bash\nset -euo pipefail\nexport ROCS_WORKSPACE_ROOT=\"${ROCS_WORKSPACE_ROOT:-$HOME/ai-society}\"\nexport ROCS_WORKSPACE_REF_MODE=\"${ROCS_WORKSPACE_REF_MODE:-loose}\"\n",
            )

            policy = _policy_for(["../outside-repo"])
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
            self.assertEqual(payload["summary"]["requirement_violations"], 3)
            self.assertFalse(payload["repos"][0]["exists"])
            self.assertEqual(
                payload["repos"][0]["evidence"]["path_boundary"]["reason"],
                "resolved path escapes workspace root",
            )

    def test_invalid_utf8_policy_returns_exit_1_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "ai-society"
            workspace.mkdir(parents=True)
            bad_policy = Path(td) / "bad.yaml"
            bad_policy.write_bytes(b"\xff\xfe\x00")

            proc = _run_audit(
                "--workspace-root",
                str(workspace),
                "--policy",
                str(bad_policy),
                "--json",
            )
            self.assertEqual(proc.returncode, 1)
            self.assertIn("not valid utf-8", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)

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
