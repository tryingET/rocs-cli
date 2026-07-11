from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import threading
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from rocs_cli.wave1 import bootstrap
from tests.test_workspace_resolution import _init_workspace_repo

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/standalone-consumer"


def fingerprint(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink()}


class Wave6ConsumerAdoptionTests(unittest.TestCase):
    def _run(self, repo: Path, command: str, profile: str, *, cwd: Path | None = None,
             workspace: Path | None = None) -> subprocess.CompletedProcess[str]:
        env = {
            "PATH": "/must/not/be/executed", "HOME": str(repo.parent / "empty-home"),
            "PYTHONPATH": "/must/not/be/imported", "PYTHONDONTWRITEBYTECODE": "1",
            "ROCS_CACHE_DIR": str(repo.parent / "empty-cache"),
            "ROCS_CI_PROFILE": profile,
        }
        if workspace is not None:
            env["ROCS_WORKSPACE_ROOT"] = str(workspace)
        return subprocess.run(["/bin/bash", str(repo / command)], cwd=cwd or repo, env=env,
                              text=True, capture_output=True)

    def test_generated_gate_and_hook_execute_hermetically_for_required_and_root_layout(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            for repo_class, profile in (("required", "local-dev"), ("ontology_repo", "main-strict")):
                with self.subTest(repo_class=repo_class):
                    repo = Path(td) / repo_class
                    if repo_class == "required":
                        shutil.copytree(FIXTURE, repo)
                    else:
                        repo.mkdir(); (repo / "manifest.yaml").write_text(
                            "rocs:\n  layers:\n    - name: repo\n      path: src\n", "utf-8")
                        (repo / "src").mkdir(); (repo / "src/unmanaged.md").write_bytes(b"keep\x00me")
                    unmanaged = (repo / "src/unmanaged.md").read_bytes() if repo_class == "ontology_repo" else None
                    bootstrap(repo, repo_class)
                    self.assertFalse((repo / "ontology").exists() if repo_class == "ontology_repo" else False)
                    first = fingerprint(repo)
                    bootstrap(repo, repo_class, converge=True)
                    self.assertEqual(first, fingerprint(repo))
                    if unmanaged is not None:
                        self.assertEqual((repo / "src/unmanaged.md").read_bytes(), unmanaged)
                    self.assertEqual(self._run(repo, "scripts/ci/full.sh", profile).returncode, 0)
                    self.assertEqual(self._run(repo, ".githooks/pre-push", profile,
                                               cwd=repo.parent).returncode, 0)

    def test_persistent_lock_is_reported_preflighted_and_keeps_inode(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo)
            preview = bootstrap(repo, "required", dry_run=True)
            self.assertEqual(preview["coordination_paths"], [])
            lock = Path(preview["external_coordination_paths"][0])
            self.assertEqual(lock, repo.parent / ".repo.rocs-bootstrap.lock")
            bootstrap(repo, "required")
            self.assertFalse((repo / "tools/.rocs-cli.vendor.lock").exists())
            inode = lock.stat().st_ino
            bootstrap(repo, "required", converge=True)
            self.assertEqual(lock.stat().st_ino, inode)
            lock.unlink()
            lock.symlink_to(repo / "outside")
            with self.assertRaisesRegex(ValueError, "regular file"):
                bootstrap(repo, "required", dry_run=True)


    def test_stage_setup_failure_releases_external_lock(self) -> None:
        import fcntl

        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"; shutil.copytree(FIXTURE, repo)
            with mock.patch("rocs_cli.wave1.tempfile.mkdtemp", side_effect=OSError("no stage")):
                with self.assertRaisesRegex(OSError, "no stage"):
                    bootstrap(repo, "required")
            lock = repo.parent / ".repo.rocs-bootstrap.lock"
            with lock.open("a+b") as lock_file:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_concurrent_bootstraps_serialize_on_stable_external_lock(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"; shutil.copytree(FIXTURE, repo)
            lock = repo.parent / ".repo.rocs-bootstrap.lock"
            lock.touch(); inode = lock.stat().st_ino
            errors: list[BaseException] = []
            def run() -> None:
                try: bootstrap(repo, "required", converge=True)
                except BaseException as exc: errors.append(exc)
            threads = [threading.Thread(target=run) for _ in range(2)]
            for thread in threads: thread.start()
            for thread in threads: thread.join(60)
            self.assertFalse(errors)
            self.assertTrue(all(not thread.is_alive() for thread in threads))
            self.assertEqual(lock.stat().st_ino, inode)
            self.assertFalse((repo / "tools/.rocs-cli.vendor.lock").exists())
            self.assertTrue((repo / "tools/rocs-cli/VENDORED_HASHES.json").is_file())

    def test_repeated_vendoring_does_not_nest_bootstrap_assets(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"; shutil.copytree(FIXTURE, repo)
            bootstrap(repo, "required")
            first = fingerprint(repo / "tools/rocs-cli")
            bootstrap(repo, "required", converge=True)
            artifact = repo / "tools/rocs-cli"
            self.assertEqual(first, fingerprint(artifact))
            nested = list(artifact.glob("src/rocs_cli/_bootstrap_assets/src/**"))
            self.assertEqual(nested, [])
            declared = set(json.loads((artifact / "VENDORED_HASHES.json").read_text())["files"])
            actual = {p.relative_to(artifact).as_posix() for p in artifact.rglob("*")
                      if p.is_file() and p.name != "VENDORED_HASHES.json"}
            self.assertEqual(actual, declared)

    def test_generated_profiles_enforce_path_only_and_strict_local_refs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = base / "repo"
            shutil.copytree(FIXTURE, repo)
            manifest = repo / "ontology/manifest.yaml"
            manifest.write_text("rocs:\n  layers:\n    - name: dep\n      ref: '<repo:core/dep@v1>'\n"
                                "    - name: core\n      path: ontology/src\n", "utf-8")
            bootstrap(repo, "required")
            local = self._run(repo, "scripts/ci/full.sh", "local-dev")
            self.assertEqual(local.returncode, 0, local.stdout + local.stderr)
            workspace = base / "workspace"
            _init_workspace_repo(workspace / "core/dep", project_path="core/dep",
                                 tag="v1", make_mismatch=True)
            for profile in ("main-strict", "branch-ci"):
                strict = self._run(repo, "scripts/ci/full.sh", profile, workspace=workspace)
                self.assertNotEqual(strict.returncode, 0)
                self.assertIn("mismatch in strict mode", strict.stdout + strict.stderr)

    def test_generated_gate_fails_closed_for_tampered_runtime_and_lock(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            for relative in ("src/rocs_cli/__init__.py", "VENDORED_HASHES.json"):
                with self.subTest(relative=relative):
                    repo = Path(td) / relative.replace("/", "-")
                    shutil.copytree(FIXTURE, repo); bootstrap(repo, "required")
                    target = repo / "tools/rocs-cli" / relative
                    target.write_bytes(target.read_bytes() + b"\nTAMPERED\n")
                    result = self._run(repo, "scripts/ci/full.sh", "local-dev")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("bundled runtime", result.stderr)

    def test_valid_but_forged_lock_cannot_bless_tampered_runtime(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo); bootstrap(repo, "required")
            artifact = repo / "tools/rocs-cli"
            runtime = artifact / "src/rocs_cli/__init__.py"
            runtime.write_bytes(runtime.read_bytes() + b"\nFORGED\n")
            lock = artifact / "VENDORED_HASHES.json"
            payload = json.loads(lock.read_text("utf-8"))
            payload["files"]["src/rocs_cli/__init__.py"] = hashlib.sha256(runtime.read_bytes()).hexdigest()
            lock.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")
            result = self._run(repo, "scripts/ci/full.sh", "local-dev")
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("trust anchor", result.stderr)


if __name__ == "__main__":
    unittest.main()
