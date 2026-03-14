import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "bootstrap-repo.sh"


def _run_bootstrap(*args: str) -> subprocess.CompletedProcess[str]:
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
    if not path.exists():
        return out
    for p in sorted(path.rglob("*")):
        if p.is_file() and ".git" not in p.parts:
            out[str(p.relative_to(path))] = _sha256(p)
    return out


def _json_report(proc: subprocess.CompletedProcess[str]) -> dict:
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"stdout is not valid JSON:\n{proc.stdout}\n---\nstderr:\n{proc.stderr}") from exc


class TestBootstrapRepoScript(unittest.TestCase):
    def test_required_bootstrap_empty_repo_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"

            first = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)
            report1 = _json_report(first)
            self.assertIn("tools/rocs-cli/VENDORED_HASHES.json", report1.get("created_files", []))

            self.assertTrue((target / "tools" / "rocs-cli" / "VENDORED_HASHES.json").is_file())
            self.assertTrue((target / "ontology" / "manifest.yaml").is_file())
            self.assertTrue((target / "ontology" / "src" / "system4d.yaml").is_file())
            self.assertTrue((target / "gitlab" / "ci" / "rocs.yml").is_file())
            self.assertTrue((target / "scripts" / "ci" / "full.sh").is_file())
            self.assertTrue((target / ".gitlab-ci.yml").is_file())

            manifest = (target / "ontology" / "manifest.yaml").read_text("utf-8")
            self.assertIn('<repo:core/ontology-kernel@main>', manifest)
            self.assertIn('<repo:softwareco/ontology@main>', manifest)
            self.assertNotIn('<gitlab:org/', manifest)

            ci_snippet = (target / "gitlab" / "ci" / "rocs.yml").read_text("utf-8")
            self.assertIn("ROCS_CI_PROFILE=branch-ci", ci_snippet)
            self.assertIn("bash scripts/ci/full.sh", ci_snippet)
            self.assertNotIn("rocs build --repo . --resolve-refs", ci_snippet)
            self.assertNotIn("rocs validate --repo . --resolve-refs", ci_snippet)

            snap_a = _snapshot_tree(target)

            second = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            report2 = _json_report(second)

            snap_b = _snapshot_tree(target)
            self.assertEqual(snap_a, snap_b)
            self.assertEqual(report2.get("created_files"), [])
            self.assertEqual(report2.get("modified_files"), [])

    def test_required_bootstrap_dry_run_does_not_write(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            proc = _run_bootstrap(str(target), "--class", "required", "--dry-run")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertTrue(report.get("dry_run"))
            self.assertFalse(target.exists())
            self.assertIn("tools/rocs-cli/**", report.get("rollback_paths", []))

    def test_existing_repo_keeps_existing_ontology_and_wires_ci_include(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            (target / "ontology").mkdir(parents=True)
            (target / "ontology" / "manifest.yaml").write_text("rocs:\n  custom: true\n", "utf-8")
            (target / ".gitlab-ci.yml").write_text(
                "stages:\n  - test\nunit:test:\n  stage: test\n  script:\n    - echo ok\n",
                "utf-8",
            )

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            manifest = (target / "ontology" / "manifest.yaml").read_text("utf-8")
            self.assertEqual(manifest, "rocs:\n  custom: true\n")

            ci_root = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertIn("unit:test", ci_root)
            loaded = yaml.safe_load(ci_root)
            self.assertIn({"local": "gitlab/ci/rocs.yml"}, loaded.get("include", []))

            second = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            ci_root_second = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertEqual(ci_root_second.count("gitlab/ci/rocs.yml"), 1)

    def test_existing_repo_with_include_mapping_is_merged_structurally(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            (target / ".gitlab-ci.yml").write_text(
                "include:\n  local: 'gitlab/ci/existing.yml'\nstages:\n  - test\n",
                "utf-8",
            )

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            loaded = yaml.safe_load((target / ".gitlab-ci.yml").read_text("utf-8"))
            self.assertIsInstance(loaded, dict)
            self.assertEqual(
                loaded.get("include"),
                [{"local": "gitlab/ci/existing.yml"}, {"local": "gitlab/ci/rocs.yml"}],
            )
            self.assertEqual(loaded.get("stages"), ["test"])

    def test_existing_generated_ci_contract_is_converged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            (target / "gitlab" / "ci").mkdir(parents=True)
            (target / "scripts" / "ci").mkdir(parents=True)
            (target / "gitlab" / "ci" / "rocs.yml").write_text(
                "stages:\n  - validate\nrocs:validate:\n  stage: validate\n  script:\n    - uvx -n --from ./tools/rocs-cli rocs build --repo . --resolve-refs\n",
                "utf-8",
            )
            (target / "scripts" / "ci" / "full.sh").write_text("echo stale\n", "utf-8")

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertIn("gitlab/ci/rocs.yml", report.get("modified_files", []))
            self.assertIn("scripts/ci/full.sh", report.get("modified_files", []))

            ci_snippet = (target / "gitlab" / "ci" / "rocs.yml").read_text("utf-8")
            wrapper = (target / "scripts" / "ci" / "full.sh").read_text("utf-8")
            self.assertIn("ROCS_CI_PROFILE=branch-ci", ci_snippet)
            self.assertIn("bash scripts/ci/full.sh", ci_snippet)
            self.assertIn("ROCS_CI_PROFILE", wrapper)
            self.assertNotIn("echo stale", wrapper)

    def test_optional_class_is_inventory_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            (target / "README.md").write_text("hello\n", "utf-8")

            snap_before = _snapshot_tree(target)
            proc = _run_bootstrap(str(target), "--class", "optional")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = _json_report(proc)
            snap_after = _snapshot_tree(target)

            self.assertEqual(snap_before, snap_after)
            self.assertEqual(report.get("created_files"), [])
            self.assertEqual(report.get("modified_files"), [])
            self.assertFalse((target / "scripts" / "ci" / "full.sh").exists())

    def test_ontology_repo_class_uses_strict_overlay_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ontology"

            proc = _run_bootstrap(str(target), "--class", "ontology_repo")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            manifest = (target / "ontology" / "manifest.yaml").read_text("utf-8")
            self.assertIn("layer: company", manifest)
            self.assertIn('<repo:core/ontology-kernel@main>', manifest)

            ci_snippet = (target / "gitlab" / "ci" / "rocs.yml").read_text("utf-8")
            self.assertNotIn("allow_failure: true", ci_snippet)
            self.assertIn("ROCS_CI_PROFILE=main-strict", ci_snippet)
            self.assertIn("bash scripts/ci/full.sh", ci_snippet)
            self.assertTrue((target / "scripts" / "ci" / "full.sh").is_file())


if __name__ == "__main__":
    unittest.main()
