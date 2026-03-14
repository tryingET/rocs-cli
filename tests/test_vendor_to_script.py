import hashlib
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from rocs_cli.vendored import compute_expected_hashes


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "vendor-to.sh"


def _run_vendor_to(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(SCRIPT), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _snapshot_tree(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for p in sorted(path.rglob("*")):
        if p.is_file():
            out[str(p.relative_to(path))] = _sha256(p)
    return out


def _repo_version() -> str:
    text = (REPO_ROOT / "pyproject.toml").read_text("utf-8")
    m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"\s*$', text)
    if not m:
        raise AssertionError("version not found in pyproject.toml")
    return m.group(1)


class TestVendorToScript(unittest.TestCase):
    def test_vendor_to_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "tools" / "rocs-cli"

            first = _run_vendor_to(str(target))
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            snap_a = _snapshot_tree(target)

            second = _run_vendor_to(str(target))
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            snap_b = _snapshot_tree(target)

            self.assertEqual(snap_a, snap_b)

    def test_vendor_to_writes_correct_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "tools" / "rocs-cli"

            proc = _run_vendor_to(str(target))
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            payload = json.loads((target / "VENDORED_HASHES.json").read_text("utf-8"))
            self.assertEqual(payload.get("schema_version"), 1)
            self.assertEqual(payload.get("upstream_project"), "ai-society/core/rocs-cli")
            self.assertEqual(payload.get("upstream_version"), _repo_version())

            expected_hashes = compute_expected_hashes(target)
            self.assertEqual(payload.get("files"), expected_hashes)

    def test_vendor_to_supports_version_override(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "tools" / "rocs-cli"
            proc = _run_vendor_to(str(target), "--version", "9.9.9")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            payload = json.loads((target / "VENDORED_HASHES.json").read_text("utf-8"))
            self.assertEqual(payload.get("upstream_version"), "9.9.9")

    def test_vendor_to_dry_run_does_not_write_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "tools" / "rocs-cli"
            proc = _run_vendor_to(str(target), "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertFalse(target.exists())

    def test_vendor_to_dry_run_validates_target_shape(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "not-a-directory"
            target.write_text("x", "utf-8")

            proc = _run_vendor_to(str(target), "--dry-run")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("target exists and is not a directory", proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
