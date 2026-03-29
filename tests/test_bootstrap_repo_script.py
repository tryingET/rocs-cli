import hashlib
import json
import os
import stat
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
            mode = stat.S_IMODE(p.stat().st_mode)
            out[str(p.relative_to(path))] = f"mode={mode:o} sha256={_sha256(p)}"
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
            self.assertIn('export ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-local-dev}"', hook)
            self.assertIn('export ROCS_CMD="${ROCS_CMD:-uv run --project ./tools/rocs-cli python -m rocs_cli}"', hook)
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
            self.assertIn('export ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-local-dev}"', hook)
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

    def test_required_bootstrap_infers_company_from_target_path(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ai-society" / "holdingco" / "owned" / "app-a"

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            manifest = (target / "ontology" / "manifest.yaml").read_text("utf-8")
            self.assertIn("<repo:holdingco/ontology@main>", manifest)
            self.assertNotIn("<repo:softwareco/ontology@main>", manifest)

    def test_required_bootstrap_blocks_ambiguous_workspace_company_inference(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ai-society" / "core" / "owned" / "app-a"

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertTrue(report.get("blocked"))
            blocked = [row for row in report.get("planned_actions", []) if row.get("path") == "ontology/manifest.yaml"][0]
            self.assertIn("could not infer company", blocked.get("reason", ""))
            self.assertFalse((target / "tools" / "rocs-cli").exists())

            explicit = _run_bootstrap(str(target), "--class", "required", "--company", "holdingco")
            self.assertEqual(explicit.returncode, 0, explicit.stdout + explicit.stderr)
            manifest = (target / "ontology" / "manifest.yaml").read_text("utf-8")
            self.assertIn("<repo:holdingco/ontology@main>", manifest)

    def test_existing_gitlab_ci_with_reference_tag_is_converged_without_yaml_roundtrip_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            (target / ".gitlab-ci.yml").write_text(
                "\n".join(
                    [
                        "include:",
                        "  - local: 'gitlab/ci/rocs.yml'",
                        "job:",
                        "  script:",
                        "    - echo ok",
                        "  rules: !reference [.shared, rules]",
                        ".shared:",
                        "  rules:",
                        "    - if: $CI_PIPELINE_SOURCE",
                        "",
                    ]
                ),
                "utf-8",
            )

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            gitlab_ci = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertNotIn("gitlab/ci/rocs.yml", gitlab_ci)
            self.assertIn("!reference [.shared, rules]", gitlab_ci)
            self.assertTrue((target / ".githooks" / "pre-push").is_file())

    def test_existing_gitlab_ci_with_reference_tag_and_no_rocs_include_is_left_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            original = "\n".join(
                [
                    "job:",
                    "  script:",
                    "    - echo ok",
                    "  rules: !reference [.shared, rules]",
                    ".shared:",
                    "  rules:",
                    "    - if: $CI_PIPELINE_SOURCE",
                    "",
                ]
            )
            (target / ".gitlab-ci.yml").write_text(original, "utf-8")

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            self.assertEqual((target / ".gitlab-ci.yml").read_text("utf-8"), original)

    def test_existing_gitlab_ci_flow_style_rocs_include_with_reference_tag_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            (target / ".gitlab-ci.yml").write_text(
                "\n".join(
                    [
                        "include: ['gitlab/ci/rocs.yml', 'gitlab/ci/keep.yml']",
                        "job:",
                        "  rules: !reference [.shared, rules]",
                        ".shared:",
                        "  rules:",
                        "    - if: $CI_PIPELINE_SOURCE",
                        "",
                    ]
                ),
                "utf-8",
            )

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            gitlab_ci = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertNotIn("gitlab/ci/rocs.yml", gitlab_ci)
            self.assertIn("gitlab/ci/keep.yml", gitlab_ci)
            self.assertIn("!reference [.shared, rules]", gitlab_ci)

    def test_existing_gitlab_ci_inline_mapping_rocs_include_with_reference_tag_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            (target / ".gitlab-ci.yml").write_text(
                "\n".join(
                    [
                        "include: {local: 'gitlab/ci/rocs.yml'}",
                        "job:",
                        "  rules: !reference [.shared, rules]",
                        ".shared:",
                        "  rules:",
                        "    - if: $CI_PIPELINE_SOURCE",
                        "",
                    ]
                ),
                "utf-8",
            )

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            gitlab_ci = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertNotIn("gitlab/ci/rocs.yml", gitlab_ci)
            self.assertIn("!reference [.shared, rules]", gitlab_ci)

    def test_existing_gitlab_ci_multiline_rocs_include_with_reference_tag_is_removed_atomically(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            target.mkdir(parents=True)
            (target / ".gitlab-ci.yml").write_text(
                "\n".join(
                    [
                        "include:",
                        "  - local: 'gitlab/ci/rocs.yml'",
                        "    rules:",
                        "      - if: $CI_PIPELINE_SOURCE",
                        "  - local: 'gitlab/ci/keep.yml'",
                        "job:",
                        "  rules: !reference [.shared, rules]",
                        ".shared:",
                        "  rules:",
                        "    - if: $CI_PIPELINE_SOURCE",
                        "",
                    ]
                ),
                "utf-8",
            )

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            gitlab_ci = (target / ".gitlab-ci.yml").read_text("utf-8")
            self.assertNotIn("gitlab/ci/rocs.yml", gitlab_ci)
            self.assertNotIn("    rules:\n      - if: $CI_PIPELINE_SOURCE\n  - local: 'gitlab/ci/keep.yml'", gitlab_ci)
            self.assertIn("gitlab/ci/keep.yml", gitlab_ci)
            self.assertIn("!reference [.shared, rules]", gitlab_ci)

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

    def test_existing_binary_managed_file_is_reported_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            (target / ".githooks").mkdir(parents=True)
            (target / ".githooks" / "pre-push").write_bytes(b"\xff\xfe\x00bin")

            proc = _run_bootstrap(str(target), "--class", "required", "--dry-run")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertTrue(report.get("blocked"))
            pre_push = [row for row in report.get("planned_actions", []) if row.get("path") == ".githooks/pre-push"][0]
            self.assertEqual(pre_push.get("action"), "blocked")
            self.assertIn("utf-8", pre_push.get("reason", ""))
            self.assertNotIn("Traceback", proc.stderr)

    def test_existing_unreadable_managed_file_is_reported_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            (target / ".githooks").mkdir(parents=True)
            pre_push = target / ".githooks" / "pre-push"
            pre_push.write_text("echo hi\n", "utf-8")
            pre_push.chmod(0)
            try:
                proc = _run_bootstrap(str(target), "--class", "required", "--dry-run")
            finally:
                pre_push.chmod(stat.S_IRUSR | stat.S_IWUSR)

            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertTrue(report.get("blocked"))
            blocked = [row for row in report.get("planned_actions", []) if row.get("path") == ".githooks/pre-push"][0]
            self.assertEqual(blocked.get("action"), "blocked")
            self.assertIn("unreadable", blocked.get("reason", ""))
            self.assertNotIn("Traceback", proc.stderr)

    def test_symlinked_managed_file_is_blocked_without_following_it(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            outside = Path(td) / "outside.txt"
            outside.write_text("ORIGINAL\n", "utf-8")
            (target / ".githooks").mkdir(parents=True)
            (target / ".githooks" / "pre-push").symlink_to(outside)

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertTrue(report.get("blocked"))
            blocked = [row for row in report.get("planned_actions", []) if row.get("path") == ".githooks/pre-push"][0]
            self.assertEqual(blocked.get("action"), "blocked")
            self.assertIn("symlink", blocked.get("reason", ""))
            self.assertEqual(outside.read_text("utf-8"), "ORIGINAL\n")
            self.assertFalse((target / "tools" / "rocs-cli").exists())

    def test_blocked_apply_mode_aborts_before_writes_or_chmod(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"
            (target / ".githooks").mkdir(parents=True)
            pre_push = target / ".githooks" / "pre-push"
            pre_push.write_bytes(b"\xff\xfe\x00bin")
            pre_push.chmod(0o644)

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 1, proc.stdout + proc.stderr)
            report = _json_report(proc)
            self.assertTrue(report.get("blocked"))
            self.assertEqual(report.get("created_files"), [])
            self.assertEqual(report.get("modified_files"), [])
            self.assertEqual(report.get("deleted_files"), [])
            self.assertFalse((target / "tools" / "rocs-cli").exists())
            self.assertFalse((target / "ontology").exists())
            self.assertFalse((target / "scripts" / "ci" / "full.sh").exists())
            self.assertEqual(stat.S_IMODE(pre_push.stat().st_mode), 0o644)

    def test_existing_pre_push_mode_change_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"

            first = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(first.returncode, 0, first.stdout + first.stderr)

            pre_push = target / ".githooks" / "pre-push"
            pre_push.chmod(0o644)

            second = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(second.returncode, 0, second.stdout + second.stderr)
            report = _json_report(second)
            self.assertIn(".githooks/pre-push", report.get("modified_files", []))
            self.assertEqual(stat.S_IMODE(pre_push.stat().st_mode), 0o755)

    def test_required_bootstrap_hook_runs_local_dev_path_only_without_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "repo"

            proc = _run_bootstrap(str(target), "--class", "required")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            env = os.environ.copy()
            env["HOME"] = td
            env["ROCS_CMD"] = f"uv run --directory {REPO_ROOT} python -m rocs_cli"
            env["ROCS_REPO"] = str(target)
            hook_proc = subprocess.run(
                ["bash", str(target / ".githooks" / "pre-push")],
                cwd=target,
                check=False,
                capture_output=True,
                text=True,
                env=env,
            )
            self.assertEqual(hook_proc.returncode, 0, hook_proc.stdout + hook_proc.stderr)
            self.assertTrue((target / "ontology" / "dist" / "summary.json").is_file())

    def test_ontology_repo_class_uses_strict_overlay_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            target = Path(td) / "ontology"

            proc = _run_bootstrap(str(target), "--class", "ontology_repo")
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)

            manifest = (target / "manifest.yaml").read_text("utf-8")
            self.assertIn("layer: company", manifest)
            self.assertIn('<repo:core/ontology-kernel@main>', manifest)
            self.assertTrue((target / "src" / "system4d.yaml").is_file())
            self.assertTrue((target / "index.md").is_file())

            hook = (target / ".githooks" / "pre-push").read_text("utf-8")
            self.assertIn('export ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-main-strict}"', hook)
            self.assertIn("bash scripts/ci/full.sh", hook)
            self.assertTrue((target / "scripts" / "ci" / "full.sh").is_file())


if __name__ == "__main__":
    unittest.main()
