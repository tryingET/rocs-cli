import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path


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
            self.assertTrue((target / ".githooks" / "pre-push").is_file())
            self.assertTrue((target / ".githooks" / "README.md").is_file())
            self.assertTrue((target / "scripts" / "ci" / "full.sh").is_file())
            self.assertFalse((target / ".gitlab-ci.yml").exists())
            self.assertFalse((target / "gitlab" / "ci" / "rocs.yml").exists())

            manifest = (target / "ontology" / "manifest.yaml").read_text("utf-8")
            self.assertIn('<repo:core/ontology-kernel@main>', manifest)
            self.assertIn('<repo:softwareco/ontology@main>', manifest)
            self.assertNotIn('<gitlab:org/', manifest)

            hook = (target / ".githooks" / "pre-push").read_text("utf-8")
            self.assertIn("ROCS_CI_PROFILE=branch-ci", hook)
            self.assertIn("bash scripts/ci/full.sh", hook)
            self.assertNotIn("rocs build --repo . --resolve-refs", hook)
            self.assertNotIn("rocs validate --repo . --resolve-refs", hook)

            hooks_readme = (target / ".githooks" / "README.md").read_text("utf-8")
            self.assertIn("git config core.hooksPath .githooks", hooks_readme)

            ci_wrapper = (target / "scripts" / "ci" / "full.sh").read_text("utf-8")
            self.assertIn("ROCS_WORKSPACE_ROOT", ci_wrapper)
            self.assertIn("ROCS_WORKSPACE_REF_MODE", ci_wrapper)

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

    def test_existing_repo_keeps_existing_ontology_and_non_rocs_gitlab_file(self) -> None:
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

            gitlab_root = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertIn("unit:test", gitlab_root)
            self.assertTrue((target / ".githooks" / "pre-push").is_file())

            second = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            gitlab_root_second = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertEqual(gitlab_root_second, gitlab_root)

    def test_existing_repo_with_include_mapping_is_left_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            original = "include:\n  local: 'gitlab/ci/existing.yml'\nstages:\n  - test\n"
            (target / ".gitlab-ci.yml").write_text(original, "utf-8")

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            current = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertEqual(current, original)
            self.assertTrue((target / ".githooks" / "pre-push").is_file())

    def test_existing_generated_ci_contract_is_converged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            (target / "gitlab" / "ci").mkdir(parents=True)
            (target / "scripts" / "ci").mkdir(parents=True)
            (target / "gitlab" / "ci" / "rocs.yml").write_text(
                "stages:\n  - validate\nrocs:validate:\n  stage: validate\n  script:\n    - uvx -n --from ./tools/rocs-cli rocs build --repo . --resolve-refs\n",
                "utf-8",
            )
            (target / ".gitlab-ci.yml").write_text("include:\n  - local: 'gitlab/ci/rocs.yml'\n", "utf-8")
            (target / "scripts" / "ci" / "full.sh").write_text("echo stale\n", "utf-8")

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertIn("scripts/ci/full.sh", report.get("modified_files", []))
            self.assertIn("gitlab/ci/rocs.yml", report.get("deleted_files", []))
            self.assertIn(".gitlab-ci.yml", report.get("deleted_files", []))
            self.assertIn(".githooks/pre-push", report.get("created_files", []))

            hook = (target / ".githooks" / "pre-push").read_text("utf-8")
            wrapper = (target / "scripts" / "ci" / "full.sh").read_text("utf-8")
            self.assertIn("ROCS_CI_PROFILE=branch-ci", hook)
            self.assertIn("bash scripts/ci/full.sh", hook)
            self.assertIn("ROCS_WORKSPACE_ROOT", wrapper)
            self.assertIn("ROCS_WORKSPACE_REF_MODE", wrapper)
            self.assertNotIn("echo stale", wrapper)
            self.assertFalse((target / "gitlab" / "ci" / "rocs.yml").exists())
            self.assertFalse((target / ".gitlab-ci.yml").exists())

    def test_existing_legacy_manifest_is_canonicalized_to_repo_locators(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ai-society" / "softwareco" / "owned" / "app-a"
            (target / "ontology").mkdir(parents=True)
            (target / "ontology" / "manifest.yaml").write_text(
                "\n".join(
                    [
                        "rocs:",
                        "  layers:",
                        "    - name: core",
                        "      ref: '<gitlab:ai-society/core/ontology-kernel@v0.1.0>'",
                        "    - name: company",
                        "      ref: '<gitlab:org/ontology@v0.1.0>'",
                        "",
                    ]
                ),
                "utf-8",
            )

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            manifest = (target / "ontology" / "manifest.yaml").read_text("utf-8")
            self.assertIn("<repo:core/ontology-kernel@main>", manifest)
            self.assertIn("<repo:softwareco/ontology@main>", manifest)
            self.assertNotIn("<gitlab:", manifest)

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

            hook = (target / ".githooks" / "pre-push").read_text("utf-8")
            self.assertIn("ROCS_CI_PROFILE=main-strict", hook)
            self.assertIn("bash scripts/ci/full.sh", hook)
            self.assertTrue((target / "scripts" / "ci" / "full.sh").is_file())


if __name__ == "__main__":
    unittest.main()
