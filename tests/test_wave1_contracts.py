from __future__ import annotations

import argparse
import contextlib
import hashlib
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
from unittest.mock import patch

from rocs_cli import __version__

from rocs_cli.cli import build_parser, cmd_contracts
from rocs_cli.contracts import COMMANDS, RUNTIME_FACT_KEYS, command_contract, evaluate_effects


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
        first["commands"]["fleet.observe"]["effect_rules"][0]["effect"] = "ontology"
        self.assertEqual(command_contract()["commands"]["fleet.observe"]["effect_rules"][0]["effect"], "artifact")
        for declaration in command_contract()["commands"].values():
            self.assertIn(2, declaration["exit_codes"])
            self.assertNotIn("mutates", declaration)

    def test_contract_command_emits_verified_identity(self) -> None:
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            self.assertEqual(cmd_contracts(object()), 0)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["tool"]["name"], "rocs-cli")
        self.assertRegex(payload["tool"]["version"], r"^\d+\.\d+\.\d+")

    def test_schema_three_closes_effects_and_preserves_proposal_authority_separation(self) -> None:
        contract = command_contract()
        self.assertEqual(contract["schema_version"], 3)
        self.assertEqual(contract["vocabulary"]["effects"],
                         ["none", "artifact", "cache", "repository", "fleet", "ontology"])
        for name in ("proposal.validate", "proposal.compile", "repair-market",
                     "constitution.validate", "constitution.challenge", "constitution.differential", "constitution.mutate"):
            effects = {rule["effect"] for rule in contract["commands"][name]["effect_rules"]}
            self.assertNotIn("ontology", effects)
            self.assertNotIn("repository", effects)
        self.assertEqual({r["effect"] for r in contract["commands"]["transaction.rollback"]["effect_rules"]}, {"ontology"})
        self.assertEqual(contract["commands"]["lint"]["effect_rules"],
                         [{"effect": "cache", "condition": "runtime-feature",
                           "feature": "index_cache_enabled", "enabled": True}])
        self.assertIn({"effect": "ontology", "condition": "argument", "argument": "fix", "equals": True},
                      contract["commands"]["check-inverses"]["effect_rules"])

    def test_generic_declaration_evaluator_covers_every_condition_class(self) -> None:
        facts = {key: False for key in RUNTIME_FACT_KEYS}
        self.assertEqual(evaluate_effects("lint", {}, facts), ("none",))
        self.assertEqual(evaluate_effects("proposal.compile", {}, facts), ("artifact",))
        self.assertEqual(evaluate_effects("fleet.observe", {"json": None, "markdown": "-"}, facts), ("none",))
        self.assertEqual(evaluate_effects("fleet.observe", {"json": "/tmp/report", "markdown": "-"}, facts), ("artifact",))
        self.assertEqual(evaluate_effects("fleet.run", {"mode": "patch", "json": None}, facts), ("none",))
        self.assertEqual(evaluate_effects("fleet.run", {"mode": "apply", "json": None}, facts), ("fleet",))
        self.assertEqual(evaluate_effects("normalize", {"apply": False}, facts), ("none",))
        self.assertEqual(evaluate_effects("normalize", {"apply": True}, facts), ("ontology",))
        self.assertEqual(evaluate_effects("validate", {}, {**facts, "authority_receipt_enabled": True}), ("artifact",))
        self.assertEqual(evaluate_effects("validate", {}, {**facts, "index_cache_enabled": True}), ("cache",))
        self.assertEqual(evaluate_effects("benchmark", {}, {**facts, "index_cache_enabled": True}), ("artifact", "cache"))
        with self.assertRaises(ValueError):
            evaluate_effects("lint", {}, {"authority_receipt_enabled": False})
        with self.assertRaises(TypeError):
            COMMANDS["lint"]["effect_rules"][0]["effect"] = "ontology"
        self.assertEqual(evaluate_effects("lint", {}, facts), ("none",))

    def test_effect_rule_arguments_are_real_parser_destinations_and_modes(self) -> None:
        parser = build_parser()
        root = next(a for a in parser._actions if isinstance(a, argparse._SubParsersAction))
        for operation, declaration in command_contract()["commands"].items():
            parts = operation.split(".")
            child = root.choices[parts[0]]
            if len(parts) == 2:
                nested = next(a for a in child._actions if isinstance(a, argparse._SubParsersAction))
                child = nested.choices[parts[1]]
            actions = {a.dest: a for a in child._actions}
            for rule in declaration["effect_rules"]:
                argument = rule.get("argument")
                if argument:
                    self.assertIn(argument, actions, operation)
                if rule["condition"] == "mode":
                    self.assertTrue(set(rule["values"]).issubset(set(actions[argument].choices)), operation)

    def test_executable_resolve_conditional_effect_and_parser_exit(self) -> None:
        root = Path(__file__).resolve().parents[1]
        fixture = root / "tests/fixtures/standalone-consumer"
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(fixture, repo)
            before = {p.relative_to(repo): p.read_bytes() for p in repo.rglob("*") if p.is_file()}
            base = [sys.executable, "-m", "rocs_cli", "resolve", "--repo", str(repo), "--json"]
            env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "ROCS_CACHE_DIR": str(Path(td) / "cache")}
            result = subprocess.run(base, cwd=root, env=env, text=True, capture_output=True)
            self.assertIn(result.returncode, command_contract()["commands"]["resolve"]["exit_codes"])
            self.assertEqual(before, {p.relative_to(repo): p.read_bytes() for p in repo.rglob("*") if p.is_file()})
            result = subprocess.run([*base, "--write-dist"], cwd=root, env=env, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            writes = {p.relative_to(repo).as_posix() for p in repo.rglob("*") if p.is_file()} - {p.as_posix() for p in before}
            self.assertEqual(writes, {"ontology/dist/resolve.json"})
            rejected = subprocess.run([sys.executable, "-m", "rocs_cli", "resolve", "--bogus"], cwd=root, env=env)
            self.assertEqual(rejected.returncode, 2)

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

    def test_installed_bootstrap_without_commit_provenance_retains_schema_two(self) -> None:
        from rocs_cli.wave1 import bootstrap

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "consumer"
            shutil.copytree(root / "tests/fixtures/standalone-consumer", repo)
            with patch("rocs_cli.wave1._source_commit", return_value=None):
                result = bootstrap(repo, "required")
            receipt = json.loads(
                (repo / "tools/rocs-cli/VENDORED_HASHES.json").read_text("utf-8")
            )
            self.assertEqual(result["schema_version"], 2)
            self.assertEqual(receipt["schema_version"], 2)

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
            self.assertEqual(manifest["schema_version"], 3)
            self.assertEqual(manifest["upstream_version"], "9.8.7-test")
            self.assertEqual(
                manifest["source_commit"],
                subprocess.run(
                    ["git", "-C", str(root), "rev-parse", "--verify", "HEAD^{commit}"],
                    check=True,
                    text=True,
                    capture_output=True,
                ).stdout.strip(),
            )
            self.assertEqual(
                manifest["uv_lock_sha256"],
                hashlib.sha256((target / "uv.lock").read_bytes()).hexdigest(),
            )
            self.assertRegex(manifest["bundle_manifest_digest"], r"^sha256:[0-9a-f]{64}$")
            with self.assertRaises(ValueError):
                vendor(root, root / "nested-artifact", dry_run=True)

    def test_vendor_excludes_machine_local_cache_directories(self) -> None:
        from rocs_cli.wave1 import vendor, verify

        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            source = base / "source"
            package = source / "src/rocs_cli"
            shutil.copytree(root / "src/rocs_cli", package)
            for name in ("pyproject.toml", "README.md", "uv.lock"):
                shutil.copy2(root / name, source / name)
            subprocess.run(["git", "init", "-q", str(source)], check=True)
            subprocess.run(["git", "-C", str(source), "add", "."], check=True)
            subprocess.run(
                [
                    "git", "-C", str(source), "-c", "user.name=ROCS Test",
                    "-c", "user.email=rocs-test@example.invalid", "commit", "-qm", "fixture",
                ],
                check=True,
            )

            for cache_name in (".ruff_cache", ".mypy_cache", ".pytest_cache"):
                cache = package / "_bootstrap_assets" / cache_name
                cache.mkdir(parents=True)
                (cache / "machine-local").write_text("ignored\n", "utf-8")

            artifact = base / "artifact"
            vendor(source, artifact)
            cache_names = {".ruff_cache", ".mypy_cache", ".pytest_cache"}
            self.assertFalse(any(cache_names.intersection(path.parts) for path in artifact.rglob("*")))
            payload, code = verify(artifact)
            self.assertEqual(code, 0, payload)
            self.assertTrue(payload["ok"])

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
            self.assertIn(f"rocs-cli {__version__}", result.stdout)
