from __future__ import annotations

import hashlib
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rocs_cli.capabilities import CAPABILITY_NAMES, CAPABILITY_REGISTRY_VERSION, CLASS_REQUIREMENTS, class_policy
from rocs_cli.wave1 import bootstrap

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "scripts/ci/full.sh"


def tree_fingerprint(root: Path) -> dict[str, tuple[int, str]]:
    result = {}
    if not root.exists():
        return result
    for path in sorted(root.rglob("*")):
        rel = str(path.relative_to(root))
        mode = stat.S_IMODE(path.lstat().st_mode)
        data = (
            path.read_bytes()
            if path.is_file() and not path.is_symlink()
            else os.readlink(path).encode()
            if path.is_symlink()
            else b""
        )
        result[rel] = (mode, hashlib.sha256(data).hexdigest())
    return result


class TestWave0Safety(unittest.TestCase):
    def run_full(self, repo: Path) -> subprocess.CompletedProcess[str]:
        env = {**os.environ, "ROCS_REPO": str(repo), "ROCS_CMD": "true", "ROCS_CI_PROFILE": "local-dev"}
        return subprocess.run(["bash", str(FULL)], cwd=ROOT, env=env, text=True, capture_output=True)

    def test_cleanup_accepts_spaces_and_removes_only_dist(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo with spaces"
            (repo / "ontology/dist").mkdir(parents=True)
            (repo / "ontology/manifest.yaml").write_text("rocs: {}\n")
            (repo / "dist").mkdir()
            self.assertEqual(self.run_full(repo).returncode, 0)
            self.assertFalse((repo / "dist").exists())

    def test_cleanup_rejects_root_outside_symlink_and_missing_manifest(self) -> None:
        self.assertNotEqual(self.run_full(Path("/")).returncode, 0)
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = base / "repo"
            outside = base / "outside"
            repo.mkdir()
            outside.mkdir()
            (repo / "ontology/dist").mkdir(parents=True)
            (repo / "ontology/manifest.yaml").write_text("rocs: {}\n")
            sentinel = repo / "ontology/dist/sentinel"
            sentinel.write_bytes(b"must survive failed preflight")
            (repo / "dist").symlink_to(outside, target_is_directory=True)
            self.assertNotEqual(self.run_full(repo).returncode, 0)
            self.assertEqual(sentinel.read_bytes(), b"must survive failed preflight")
            (repo / "dist").unlink()
            (repo / "ontology/manifest.yaml").unlink()
            self.assertNotEqual(self.run_full(repo).returncode, 0)
            self.assertNotEqual(self.run_full(base / "missing").returncode, 0)

    def test_bootstrap_rolls_back_after_vendor_and_managed_failures(self) -> None:
        for point in ("vendor", "managed", "prepublish", "publish", "after_publish"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as td:
                repo = Path(td) / "repo"
                repo.mkdir()
                marker = repo / "marker"
                marker.write_bytes(b"preimage\x00")
                marker.chmod(0o640)
                before = tree_fingerprint(repo)
                env = {**os.environ, "ROCS_BOOTSTRAP_FAIL_AFTER": point}
                proc = subprocess.run(
                    [sys.executable, "-m", "rocs_cli", "bootstrap", str(repo), "--class", "required"],
                    cwd=ROOT,
                    env=env,
                    text=True,
                    capture_output=True,
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertEqual(tree_fingerprint(repo), before)
                preview = bootstrap(repo, "required", dry_run=True)
                self.assertEqual(preview["coordination_paths"], [])
                lock = Path(preview["external_coordination_paths"][0])
                self.assertTrue(lock.is_file())
                self.assertEqual(stat.S_IMODE(lock.stat().st_mode), 0o644)

    def test_bootstrap_rejects_managed_symlink_without_touching_target(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td); repo = base / "repo"; outside = base / "outside.sh"
            repo.mkdir(); outside.write_text("outside\n", "utf-8")
            (repo / "scripts/ci").mkdir(parents=True)
            (repo / "scripts/ci/full.sh").symlink_to(outside)
            before = outside.read_bytes()
            proc = subprocess.run([sys.executable, "-m", "rocs_cli", "bootstrap", str(repo),
                "--class", "required"], cwd=ROOT, text=True, capture_output=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertEqual(outside.read_bytes(), before)
            self.assertTrue((repo / "scripts/ci/full.sh").is_symlink())

    def test_vendor_rolls_back_late_publication_failures(self) -> None:
        from rocs_cli.wave1 import vendor

        for point in ("prepublish", "publish", "after_publish"):
            with self.subTest(point=point), tempfile.TemporaryDirectory() as td:
                target = Path(td) / "artifact"
                target.mkdir()
                (target / "marker").write_bytes(b"vendor-preimage")
                before = tree_fingerprint(target)
                old = os.environ.get("ROCS_VENDOR_FAIL_AFTER")
                os.environ["ROCS_VENDOR_FAIL_AFTER"] = point
                try:
                    with self.assertRaises(RuntimeError):
                        vendor(ROOT, target)
                finally:
                    if old is None:
                        os.environ.pop("ROCS_VENDOR_FAIL_AFTER", None)
                    else:
                        os.environ["ROCS_VENDOR_FAIL_AFTER"] = old
                self.assertEqual(tree_fingerprint(target), before)

    def test_registry_is_closed_and_versioned(self) -> None:
        self.assertEqual(CAPABILITY_REGISTRY_VERSION, 1)
        self.assertEqual(tuple(CLASS_REQUIREMENTS["required"]), CAPABILITY_NAMES)
        with self.assertRaises(ValueError):
            class_policy("unknown")


if __name__ == "__main__":
    unittest.main()
