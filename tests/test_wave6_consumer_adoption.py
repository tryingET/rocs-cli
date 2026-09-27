from __future__ import annotations

import hashlib
import fcntl
import json
import os
import signal
import shutil
import subprocess
import threading
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from rocs_cli.wave1 import bootstrap
from rocs_cli.vendored import verify_vendored_hashes, write_materialization_receipt
from rocs_cli.verified_runtime import render_ci_wrapper, render_cli_wrapper
from rocs_cli import __version__
from tests.test_workspace_resolution import _init_workspace_repo, _validate_receipt

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/standalone-consumer"


def fingerprint(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and not p.is_symlink()}


class Wave6ConsumerAdoptionTests(unittest.TestCase):
    def _environment(self, repo: Path, profile: str, *, workspace: Path | None = None,
                     extra_env: dict[str, str] | None = None) -> dict[str, str]:
        env = {
            "PATH": "/must/not/be/executed", "HOME": str(repo.parent / "empty-home"),
            "PYTHONPATH": "/must/not/be/imported", "PYTHONDONTWRITEBYTECODE": "1",
            "ROCS_CACHE_DIR": str(repo.parent / "empty-cache"),
            "ROCS_CI_PROFILE": profile,
        }
        if workspace is not None:
            env["ROCS_WORKSPACE_ROOT"] = str(workspace)
        if extra_env is not None:
            env.update(extra_env)
        return env

    def _run(self, repo: Path, command: str, profile: str, *, cwd: Path | None = None,
             workspace: Path | None = None, extra_env: dict[str, str] | None = None,
             arguments: list[str] | None = None, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
        env = self._environment(repo, profile, workspace=workspace, extra_env=extra_env)
        return subprocess.run(["/bin/bash", str(repo / command), *(arguments or [])],
                              cwd=cwd or repo, env=env, text=True, capture_output=True,
                              input=input_text)

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

    def test_generated_generic_launcher_preserves_cli_and_fixed_gate_separation(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo)
            bootstrap(repo, "required")
            launcher = repo / "scripts/rocs.sh"
            self.assertTrue(launcher.stat().st_mode & 0o111)
            version = self._run(repo, "scripts/rocs.sh", "local-dev", arguments=["version"])
            self.assertEqual((version.returncode, version.stdout, version.stderr),
                             (0, f"rocs-cli {__version__}\n", ""))
            version_flag = self._run(repo, "scripts/rocs.sh", "local-dev", arguments=["--version"])
            self.assertEqual((version_flag.returncode, version_flag.stdout, version_flag.stderr),
                             (0, f"rocs-cli {__version__}\n", ""))
            contracts = self._run(repo, "scripts/rocs.sh", "local-dev", arguments=["contracts"])
            self.assertEqual(contracts.returncode, 0, contracts.stderr)
            self.assertEqual(json.loads(contracts.stdout)["tool"]["version"], __version__)
            doctor = self._run(
                repo, "scripts/rocs.sh", "local-dev",
                arguments=["doctor", "--repo", str(repo)],
            )
            self.assertEqual(doctor.returncode, 0, doctor.stdout + doctor.stderr)
            for arguments in ([], ["--which"], ["--doctor"]):
                with self.subTest(arguments=arguments):
                    result = self._run(
                        repo, "scripts/rocs.sh", "local-dev", arguments=arguments
                    )
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("usage:", result.stderr)
            fixed = self._run(
                repo, "scripts/ci/full.sh", "local-dev", arguments=["version"]
            )
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)
            self.assertNotIn(f"rocs-cli {__version__}", fixed.stdout)
            self.assertTrue((repo / "ontology/dist/summary.json").is_file())

    def test_generated_generic_launcher_preserves_exact_argv_stdin_and_exit(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo)
            bootstrap(repo, "required")
            artifact = repo / "tools/rocs-cli"
            receipt_path = artifact / "VENDORED_HASHES.json"
            receipt = json.loads(receipt_path.read_text("utf-8"))
            probe = (
                "from __future__ import annotations\n"
                "import hashlib, json, sys\n"
                "def main():\n"
                "    data = sys.stdin.buffer.read()\n"
                "    print(json.dumps(sys.argv[1:], ensure_ascii=False))\n"
                "    print(hashlib.sha256(data).hexdigest(), file=sys.stderr)\n"
                "    raise SystemExit(37)\n"
            )
            (artifact / "src/rocs_cli/__main__.py").write_text(probe, "utf-8")
            write_materialization_receipt(
                artifact,
                upstream_version=receipt["upstream_version"],
                source_commit=receipt["source_commit"],
            )
            digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            (repo / "scripts/rocs.sh").write_text(render_cli_wrapper(digest), "utf-8")
            arguments = ["", "two words", "*?[x]", "--", "-n", "line1\nline2", "λ"]
            input_text = "stdin\x00payload\n"
            result = self._run(
                repo, "scripts/rocs.sh", "local-dev",
                arguments=arguments, input_text=input_text,
            )
            self.assertEqual(result.returncode, 37)
            self.assertEqual(json.loads(result.stdout), arguments)
            self.assertEqual(
                result.stderr.strip(), hashlib.sha256(input_text.encode()).hexdigest()
            )

    def test_generated_generic_launcher_discovers_enclosing_workspace_for_refs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "workspace"
            _init_workspace_repo(workspace / "core/dep", project_path="core/dep",
                                 tag="v1", make_mismatch=False)
            manifest = ("rocs:\n  layers:\n    - name: dep\n      ref: '<repo:core/dep@v1>'\n"
                        "    - name: core\n      path: ontology/src\n")
            inside = workspace / "team/repo"
            outside = Path(td) / "outside/repo"
            for repo in (inside, outside):
                shutil.copytree(FIXTURE, repo)
                (repo / "ontology/manifest.yaml").write_text(manifest, "utf-8")
                bootstrap(repo, "required")
            resolved = self._run(inside, "scripts/rocs.sh", "local-dev",
                                 arguments=["validate", "--repo", str(inside)])
            self.assertEqual(resolved.returncode, 0, resolved.stdout + resolved.stderr)
            opted_out = self._run(inside, "scripts/rocs.sh", "local-dev",
                                  arguments=["validate", "--repo", str(inside)],
                                  extra_env={"ROCS_RESOLVE_REFS": "0"})
            self.assertNotEqual(opted_out.returncode, 0)
            self.assertIn("--resolve-refs", opted_out.stdout + opted_out.stderr)
            path_only = self._run(outside, "scripts/rocs.sh", "local-dev",
                                  arguments=["validate", "--repo", str(outside), "--only", "path"])
            self.assertEqual(path_only.returncode, 0, path_only.stdout + path_only.stderr)
            missing = self._run(outside, "scripts/rocs.sh", "local-dev",
                                arguments=["validate", "--repo", str(outside)])
            self.assertNotEqual(missing.returncode, 0)
            self.assertIn("local ref not available", missing.stdout + missing.stderr)

    def test_generated_gate_routes_all_outputs_to_marked_external_root(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo)
            bootstrap(repo, "required")
            result = self._run(
                repo,
                "scripts/ci/full.sh",
                "local-dev",
                extra_env={"ROCS_OUTPUT_ROOT": "governance/ontology-dist"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = repo / "governance/ontology-dist"
            self.assertTrue((output / ".rocs-output-root.json").is_file())
            aggregate = json.loads((output / "authority-receipt.json").read_text("utf-8"))
            self.assertEqual(sorted(aggregate["commands"]), ["build", "validate"])
            self.assertEqual(aggregate["repo"], str(repo.resolve()))
            self.assertEqual(aggregate["output_root"], "governance/ontology-dist")
            self.assertFalse((repo / "ontology/dist").exists())

    def test_generated_root_layout_gate_routes_externally(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "ontology"
            repo.mkdir()
            (repo / "manifest.yaml").write_text(
                "rocs:\n  layers:\n    - name: repo\n      path: src\n", "utf-8"
            )
            (repo / "src").mkdir()
            (repo / "src/system4d.yaml").write_text("system4d: {}\n", "utf-8")
            bootstrap(repo, "ontology_repo")
            result = self._run(
                repo,
                "scripts/ci/full.sh",
                "local-dev",
                extra_env={"ROCS_OUTPUT_ROOT": "governance/ontology-dist"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue((repo / "governance/ontology-dist/summary.json").is_file())
            self.assertFalse((repo / "dist").exists())

    def test_generated_gate_keeps_default_standalone_receipt_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo)
            bootstrap(repo, "required")
            result = self._run(repo, "scripts/ci/full.sh", "local-dev")
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            output = repo / "ontology/dist"
            aggregate = json.loads((output / "authority-receipt.json").read_text("utf-8"))
            self.assertEqual(sorted(aggregate["commands"]), ["build"])
            self.assertFalse((output / "authority-receipt.validate.json").exists())
            self.assertFalse((output / ".rocs-output-root.json").exists())

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
            self.assertTrue(any(path.endswith(".py") for path in declared))
            self.assertTrue(any(path.endswith(".so") for path in declared))
            self.assertTrue(any(path.endswith(".typed") for path in declared))
            receipt = json.loads((artifact / "VENDORED_HASHES.json").read_text("utf-8"))
            self.assertEqual(receipt["upstream_version"], __version__)
            self.assertEqual(
                receipt["uv_lock_sha256"], hashlib.sha256((artifact / "uv.lock").read_bytes()).hexdigest()
            )
            self.assertIn(f'version = "{__version__}"', (artifact / "pyproject.toml").read_text("utf-8"))
            self.assertIn(
                f'name = "rocs-cli"\nversion = "{__version__}"',
                (artifact / "uv.lock").read_text("utf-8"),
            )

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
            (workspace / "core/dep/ontology/src/system4d.yaml").write_text("system4d: {moved: true}\n", "utf-8")
            subprocess.run(["git", "-C", str(workspace / "core/dep"), "commit", "-qam", "moved past v1"], check=True)
            for profile in ("main-strict", "branch-ci"):
                # A checkout whose ontology moved past the pinned tag resolves the tag's exact bytes.
                strict = self._run(repo, "scripts/ci/full.sh", profile, workspace=workspace)
                self.assertEqual(strict.returncode, 0, strict.stdout + strict.stderr)
                receipt = _validate_receipt(repo)
                self.assertEqual([layer["source"] for layer in receipt["layer_sources"] if layer["name"] == "dep"],
                                 ["workspace_ref_snapshot"])
            missing = base / "workspace-without-tag"
            _init_workspace_repo(missing / "core/dep", project_path="core/dep",
                                 tag="v0", make_mismatch=True)
            for profile in ("main-strict", "branch-ci"):
                # A workspace that lacks the pinned ref still fails closed.
                strict = self._run(repo, "scripts/ci/full.sh", profile, workspace=missing)
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

    def test_generated_gate_runs_only_captured_private_bytes_after_consumer_rename(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            for relative in ("rocs.py", "src/rocs_cli/__main__.py"):
                with self.subTest(relative=relative):
                    repo = Path(td) / relative.replace("/", "-")
                    shutil.copytree(FIXTURE, repo)
                    bootstrap(repo, "required")
                    sentinel = repo.parent / f"executed-{repo.name}"
                    env = self._environment(repo, "local-dev")
                    process = subprocess.Popen(
                        ["/bin/bash", str(repo / "scripts/ci/full.sh")],
                        cwd=repo, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                    )
                    deadline = time.monotonic() + 30
                    private_archive: Path | None = None
                    descriptor_root = Path(f"/proc/{process.pid}/fd")
                    while time.monotonic() < deadline:
                        try:
                            descriptors = list(descriptor_root.iterdir())
                        except FileNotFoundError:
                            descriptors = []
                        for descriptor in descriptors:
                            try:
                                target_name = os.readlink(descriptor)
                            except FileNotFoundError:
                                continue
                            if "memfd:rocs-verified-archive" in target_name:
                                try:
                                    probe_fd = os.open(descriptor, os.O_RDONLY)
                                    seals = fcntl.fcntl(probe_fd, 1034)  # Linux F_GET_SEALS
                                except OSError:
                                    continue
                                finally:
                                    if "probe_fd" in locals():
                                        os.close(probe_fd)
                                        del probe_fd
                                if seals & 15 == 15:  # SEAL, SHRINK, GROW, WRITE
                                    private_archive = descriptor
                                    break
                        if private_archive is not None or process.poll() is not None:
                            break
                        time.sleep(0.001)
                    if private_archive is None:
                        process.kill()
                        stdout, stderr = process.communicate()
                        self.fail(f"sealed private runtime barrier not observed: {stdout}{stderr}")
                    private_fd = os.open(private_archive, os.O_RDWR)
                    try:
                        with self.assertRaises(OSError):
                            os.write(private_fd, b"UNVERIFIED")
                    finally:
                        os.close(private_fd)
                    target = repo / "tools/rocs-cli" / relative
                    target.rename(target.with_name(target.name + ".captured-original"))
                    target.write_text(
                        "from pathlib import Path\n"
                        f"Path({str(sentinel)!r}).write_text('UNVERIFIED', encoding='utf-8')\n"
                        "raise SystemExit(91)\n",
                        "utf-8",
                    )
                    stdout, stderr = process.communicate(timeout=60)
                    self.assertEqual(process.returncode, 0, stdout + stderr)
                    self.assertFalse(sentinel.exists())
                    self.assertTrue((repo / "ontology/dist/summary.json").is_file())
                    self.assertFalse(descriptor_root.exists())

    def test_generated_gate_loads_resource_and_native_package_from_sealed_descriptors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo)
            bootstrap(repo, "required")
            artifact = repo / "tools/rocs-cli"
            receipt_path = artifact / "VENDORED_HASHES.json"
            original_receipt = json.loads(receipt_path.read_text("utf-8"))

            python_bin = shutil.which("python3", path="/usr/local/bin:/usr/bin:/bin")
            self.assertIsNotNone(python_bin)
            native_result = subprocess.run(
                [python_bin, "-I", "-S", "-B", "-c", "import _bisect; print(_bisect.__file__)"],
                text=True, capture_output=True, check=True,
            )
            native_origin = Path(native_result.stdout.strip())
            self.assertTrue(native_origin.name.startswith("_bisect"))
            native_package = artifact / "runtime/_bisect"
            native_package.mkdir()
            native_suffix = native_origin.name.removeprefix("_bisect")
            shutil.copy2(native_origin, native_package / f"__init__{native_suffix}")

            resource_text = "SEALED RESOURCE\n"
            (artifact / "src/rocs_cli/_sealed_probe.txt").write_text(resource_text, "utf-8")
            main_path = artifact / "src/rocs_cli/__main__.py"
            probe_path = repo.parent / "sealed-proof.txt"
            probe_source = (
                "import importlib.resources as _sealed_resources\n"
                "import os as _sealed_os\n"
                "from pathlib import Path as _SealedPath\n"
                "import _bisect as _sealed_native\n"
                "_sealed_data = _sealed_resources.files('rocs_cli').joinpath('_sealed_probe.txt').read_text(encoding='utf-8')\n"
                "_SealedPath(_sealed_os.environ['ROCS_SEALED_PROBE']).write_text(\n"
                "    _sealed_data + _sealed_native.__file__ + '\\n' + str(hasattr(_sealed_native, '__path__')) + '\\n',\n"
                "    encoding='utf-8',\n"
                ")\n"
            )
            main_text = main_path.read_text("utf-8")
            main_path.write_text(
                main_text.replace(
                    "from __future__ import annotations\n",
                    "from __future__ import annotations\n\n" + probe_source,
                    1,
                ),
                "utf-8",
            )
            write_materialization_receipt(
                artifact,
                upstream_version=original_receipt["upstream_version"],
                source_commit=original_receipt["source_commit"],
            )
            ok, errors = verify_vendored_hashes(artifact)
            self.assertTrue(ok, errors)
            receipt_digest = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
            (repo / "scripts/ci/full.sh").write_text(
                render_ci_wrapper(receipt_digest), "utf-8"
            )
            result = self._run(
                repo, "scripts/ci/full.sh", "local-dev",
                extra_env={"ROCS_SEALED_PROBE": str(probe_path)},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            proof = probe_path.read_text("utf-8").splitlines()
            self.assertEqual(proof[0], resource_text.strip())
            self.assertRegex(proof[1], r"^/proc/self/fd/[0-9]+$")
            self.assertEqual(proof[2], "True")

    def test_generated_and_library_verifiers_reject_hardlinked_bundle_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            for relative in ("VENDORED_HASHES.json", "rocs.py", "src/rocs_cli/__main__.py"):
                with self.subTest(relative=relative):
                    repo = Path(td) / relative.replace("/", "-")
                    shutil.copytree(FIXTURE, repo)
                    bootstrap(repo, "required")
                    artifact = repo / "tools/rocs-cli"
                    target = artifact / relative
                    alias = repo.parent / f"alias-{repo.name}"
                    os.link(target, alias)
                    self.assertEqual(target.stat().st_nlink, 2)
                    ok, errors = verify_vendored_hashes(artifact)
                    self.assertFalse(ok)
                    self.assertTrue(any("multiply linked" in error for error in errors), errors)
                    result = self._run(repo, "scripts/ci/full.sh", "local-dev")
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn("multiply linked file", result.stderr)
                    self.assertFalse((repo / "ontology/dist").exists())

    def test_generated_gate_signal_exit_leaves_no_private_runtime_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            shutil.copytree(FIXTURE, repo)
            bootstrap(repo, "required")
            process = subprocess.Popen(
                ["/bin/bash", str(repo / "scripts/ci/full.sh")],
                cwd=repo, env=self._environment(repo, "local-dev"),
                text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
            descriptor_root = Path(f"/proc/{process.pid}/fd")
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    names = [os.readlink(path) for path in descriptor_root.iterdir()]
                except (FileNotFoundError, OSError):
                    names = []
                if any("memfd:rocs-verified-archive" in name for name in names):
                    break
                if process.poll() is not None:
                    self.fail("gate exited before sealed runtime was observable")
                time.sleep(0.001)
            else:
                process.kill()
                process.communicate()
                self.fail("sealed private runtime barrier not observed")
            children_path = Path(f"/proc/{process.pid}/task/{process.pid}/children")
            active_children: list[int] = []
            deadline = time.monotonic() + 30
            while time.monotonic() < deadline:
                try:
                    active_children = [int(value) for value in children_path.read_text().split()]
                except FileNotFoundError:
                    active_children = []
                if active_children:
                    break
                if process.poll() is not None:
                    self.fail("gate exited before an active command child was observable")
                time.sleep(0.001)
            self.assertTrue(active_children)
            process.send_signal(signal.SIGTERM)
            process.communicate(timeout=30)
            self.assertEqual(process.returncode, 128 + signal.SIGTERM)
            self.assertFalse(descriptor_root.exists())
            self.assertTrue(all(not Path(f"/proc/{child}").exists() for child in active_children))


if __name__ == "__main__":
    unittest.main()
