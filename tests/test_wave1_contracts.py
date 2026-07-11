from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rocs_cli.cli import build_parser, cmd_contracts
from rocs_cli.contracts import command_contract


class Wave1ContractTests(unittest.TestCase):
    def test_contract_exactly_matches_public_parser_operations(self) -> None:
        first = command_contract()
        parser = build_parser()
        root_action = next(action for action in parser._actions if isinstance(action, argparse._SubParsersAction))
        operations: set[str] = set()
        for name, child in root_action.choices.items():
            nested = [action for action in child._actions if isinstance(action, argparse._SubParsersAction)]
            if nested:
                operations.update(f"{name}.{subname}" for subname in nested[0].choices)
            else:
                operations.add(name)
        self.assertEqual(set(first["commands"]), operations)
        self.assertEqual(list(first["commands"]), sorted(first["commands"]))
        first["commands"]["fleet.observe"]["mutates"] = True
        self.assertFalse(command_contract()["commands"]["fleet.observe"]["mutates"])

    def test_contract_command_emits_verified_identity(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cmd_contracts(object()), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["tool"]["name"], "rocs-cli")
        self.assertRegex(payload["tool"]["version"], r"^\d+\.\d+\.\d+")

    def test_fleet_protocol_rejects_unknown_operation(self) -> None:
        parser = build_parser()
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            parser.parse_args(["fleet", "destroy"])
        self.assertEqual(raised.exception.code, 2)

    def test_fleet_observe_maps_arguments(self) -> None:
        args = build_parser().parse_args(
            ["fleet", "observe", "--workspace-root", "/tmp/ws", "--policy", "/tmp/policy", "--json"]
        )
        self.assertEqual(args.fleet_cmd, "observe")
        self.assertEqual(args.json, "-")

    def test_scheduler_assets_parse_to_closed_fleet_run_contract(self) -> None:
        import shlex

        root = Path(__file__).resolve().parents[1]
        cron = (root / "scripts/cron/fcos-fleet-audit-nightly.cron").read_text("utf-8")
        command = next(line for line in cron.splitlines() if line and not line.startswith("#"))
        cron_argv = shlex.split(command)[5:]
        service = (root / "scripts/systemd/fcos-fleet-audit-nightly.service").read_text("utf-8")
        exec_argv = shlex.split(next(line.removeprefix("ExecStart=") for line in service.splitlines()
                                   if line.startswith("ExecStart=")))
        for argv in (cron_argv, exec_argv):
            self.assertIn("fleet", argv)
            self.assertIn("run", argv)
            self.assertIn("--workspace-root", argv)
            self.assertIn("--policy", argv)

    def test_bootstrap_fresh_rerun_dry_run_and_class_behavior(self) -> None:
        from rocs_cli.wave1 import bootstrap

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            for repo_class in ("required", "optional", "ontology_repo"):
                repo = Path(td) / repo_class
                shutil.copytree(root / "tests/fixtures/standalone-consumer", repo)
                before = sorted((p.relative_to(repo), p.read_bytes()) for p in repo.rglob("*") if p.is_file())
                preview = bootstrap(repo, repo_class, dry_run=True)
                after = sorted((p.relative_to(repo), p.read_bytes()) for p in repo.rglob("*") if p.is_file())
                self.assertEqual(before, after)
                self.assertEqual(preview["class"], repo_class)
                first = bootstrap(repo, repo_class)
                snapshot = sorted((p.relative_to(repo), p.read_bytes()) for p in repo.rglob("*") if p.is_file())
                second = bootstrap(repo, repo_class, converge=True)
                self.assertEqual(snapshot, sorted((p.relative_to(repo), p.read_bytes()) for p in repo.rglob("*") if p.is_file()))
                self.assertEqual((first["class"], second["operation"]), (repo_class, "converge"))

    def test_installed_bootstrap_seed_tracks_release_identity(self) -> None:
        from rocs_cli import __version__

        root = Path(__file__).resolve().parents[1]
        assets = root / "src/rocs_cli/_bootstrap_assets"
        seed_lock = (assets / "uv.lock").read_text("utf-8")
        root_lock = (root / "uv.lock").read_text("utf-8")
        normalize_header = lambda text: re.sub(r'(?m)^exclude-newer = .+$', 'exclude-newer = "<normalized>"', text)
        self.assertEqual(normalize_header(seed_lock), normalize_header(root_lock))
        self.assertIn(f'version = "{__version__}"', (assets / "pyproject.toml").read_text("utf-8"))

    def test_vendor_dry_run_version_and_target_boundaries(self) -> None:
        from rocs_cli.wave1 import vendor

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = base / "artifact"
            result = vendor(root, target, version="9.8.7-test", dry_run=True)
            self.assertEqual(result["version"], "9.8.7-test")
            self.assertFalse(target.exists())
            vendor(root, target, version="9.8.7-test")
            self.assertIn('version = "9.8.7-test"', (target / "pyproject.toml").read_text("utf-8"))
            self.assertIn('name = "rocs-cli"\nversion = "9.8.7-test"', (target / "uv.lock").read_text("utf-8"))
            manifest = json.loads((target / "VENDORED_HASHES.json").read_text("utf-8"))
            self.assertEqual(manifest["upstream_version"], "9.8.7-test")
            with self.assertRaises(ValueError):
                vendor(root, root / "nested-artifact", dry_run=True)

    def test_self_contained_artifact_rejects_unlocked_root_files(self) -> None:
        from rocs_cli.wave1 import vendor, verify

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            artifact = Path(td) / "artifact"
            vendor(root, artifact)
            (artifact / "rogue.txt").write_text("not locked\n", "utf-8")
            payload, code = verify(artifact)
            self.assertEqual(code, 1)
            self.assertFalse(payload["ok"])
            self.assertTrue(any("unexpected: rogue.txt" in error for error in payload["errors"]))
            (artifact / "rogue.txt").unlink()
            os.mkfifo(artifact / "rogue.pipe")
            payload, code = verify(artifact)
            self.assertEqual(code, 1)
            self.assertTrue(any("invalid file type: rogue.pipe" in error for error in payload["errors"]))

    def test_fleet_observe_plan_and_boundary_behaviors(self) -> None:
        from rocs_cli import fleet
        from rocs_cli.wave1 import bootstrap

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            workspace = base / "workspace"
            repo = workspace / "repo"
            workspace.mkdir()
            shutil.copytree(root / "tests/fixtures/standalone-consumer", repo)
            bootstrap(repo, "required")
            policy = base / "fleet.yaml"
            policy.write_text(
                """schema:
  repo_entry_required_fields: [path, scope, class, state, owner, capabilities]
repo_classes:
  required:
    required_capabilities: {rocs_cli_vendored: true, ontology_manifest: true, rocs_ci_gate: true}
fleet:
  repos:
    - path: repo
      scope: core
      class: required
      state: active
      owner: core
      capabilities: {rocs_cli_vendored: true, ontology_manifest: true, rocs_ci_gate: true}
""",
                "utf-8",
            )
            first, first_code = fleet.observe(workspace, policy)
            second, second_code = fleet.observe(workspace, policy)
            self.assertEqual((first_code, first), (second_code, second))
            self.assertEqual(first["summary"]["status"], "pass")

            original_policy = policy.read_text("utf-8")
            policy.write_text(original_policy.replace(
                "owner: core\n      capabilities: {rocs_cli_vendored: true, ontology_manifest: true, rocs_ci_gate: true}",
                "owner: core\n      capabilities: {rocs_cli_vendored: false, ontology_manifest: true, rocs_ci_gate: true}"), "utf-8")
            declaration, declaration_code = fleet.observe(workspace, policy)
            self.assertEqual(declaration_code, 2)
            self.assertEqual(declaration["summary"]["status"], "action_required")
            declaration_plan, plan_code = fleet.plan(workspace, policy)
            self.assertEqual(plan_code, 2)
            self.assertEqual(declaration_plan["actions"][0]["action"], "manual-governance-followup")
            nightly, nightly_code = fleet.run(workspace, policy, mode="audit-only")
            self.assertEqual(nightly_code, 2)
            patched, patched_code = fleet.apply(workspace, policy, dry_run=True)
            self.assertEqual(patched_code, 2)
            self.assertTrue(patched["results"][0]["blocked"])
            policy.write_text(original_policy, "utf-8")

            (repo / "tools/rocs-cli/README.md").write_text("tampered\n", "utf-8")
            drift, drift_code = fleet.observe(workspace, policy)
            self.assertEqual(drift_code, 2)
            self.assertIn("rocs_cli_vendored", drift["repos"][0]["requirement_violations"])
            plan, plan_code = fleet.plan(workspace, policy)
            self.assertEqual(plan_code, 2)
            self.assertEqual(plan["actions"][0]["action"], "converge")

            escaped = policy.read_text("utf-8").replace("path: repo", "path: ../outside")
            policy.write_text(escaped, "utf-8")
            with self.assertRaises(fleet.PolicyError):
                fleet.observe(workspace, policy)

    def test_fleet_report_only_output_malformed_apply_and_run_outcomes(self) -> None:
        from rocs_cli import fleet

        with tempfile.TemporaryDirectory() as td:
            base = Path(td); workspace = base / "workspace"; workspace.mkdir()
            policy = base / "fleet.yaml"
            policy.write_text("not: [valid", "utf-8")
            with self.assertRaises(fleet.PolicyError):
                fleet.observe(workspace, policy)
            policy.write_text(
                "schema:\n  repo_entry_required_fields: [path, scope, class, state, owner, capabilities]\n"
                "repo_classes:\n  optional:\n    required_capabilities: {rocs_cli_vendored: false, ontology_manifest: false, rocs_ci_gate: false}\n"
                "fleet:\n  repos: []\n", "utf-8")
            observed, code = fleet.observe(workspace, policy, report_only=True)
            self.assertEqual(code, 0); self.assertTrue(observed["report_only"])
            rendered = fleet._render_markdown(observed)
            self.assertIn("report_only: `true`", rendered)
            applied, apply_code = fleet.apply(workspace, policy, dry_run=True)
            self.assertEqual((apply_code, applied["results"]), (0, []))
            run, run_code = fleet.run(workspace, policy, mode="audit-only")
            self.assertEqual(run_code, 0); self.assertEqual(run["final"]["operation"], "observe")

    def test_pinned_artifact_runs_in_isolated_consumer(self) -> None:
        from rocs_cli.wave1 import vendor

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            consumer = base / "consumer"
            artifact = consumer / "tools/rocs-cli"
            shutil.copytree(root / "tests/fixtures/standalone-consumer", consumer)
            vendor(root, artifact)
            env = {
                "PATH": "/usr/bin:/bin",
                "HOME": str(base / "home"),
                "PYTHONPATH": "",
                "ROCS_CACHE_DIR": str(base / "cache"),
                "PYTHONDONTWRITEBYTECODE": "1",
            }
            commands = [
                ["verify", str(artifact)],
                ["doctor", "--repo", str(consumer)],
                ["validate", "--repo", str(consumer), "--json"],
                ["build", "--repo", str(consumer), "--json"],
                ["version"],
            ]
            for command in commands:
                result = subprocess.run(
                    [sys.executable, "-S", str(artifact / "rocs.py"), *command],
                    cwd=consumer,
                    env=env,
                    text=True,
                    capture_output=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("rocs-cli 0.1.4", result.stdout)
