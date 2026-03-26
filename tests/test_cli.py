import tempfile
import unittest
import io
import json
import os
from pathlib import Path

from rich.console import Console

from rocs_cli import __main__ as cli
import rocs_cli.cli as cli_mod
from rocs_cli.vendored import compute_expected_hashes


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, "utf-8")


def _mk_repo(tmp: Path, *, manifest_extra: str = "") -> Path:
    repo = tmp / "repo"
    _write(
        repo / "ontology" / "manifest.yaml",
        "\n".join(
            [
                "rocs:",
                "  layer: core",
                '  id: "test.core"',
                '  version: "0.0.0"',
                '  created: "2026-01-10"',
                f"{manifest_extra}".rstrip(),
                "",
            ]
        ),
    )
    _write(repo / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")
    _write(
        repo / "ontology" / "src" / "reference" / "relations" / "is_a.md",
        "\n".join(
            [
                "---",
                "ont:",
                '  id: "core.rel.is_a"',
                "  type: relation",
                '  labels: ["is_a"]',
                '  description: "taxonomy"',
                "  group: taxonomy",
                "  characteristics:",
                "    transitive: true",
                "    symmetric: false",
                "---",
                "",
                "examples:",
                '  - "core.Agent is_a core.Actor"',
                "",
                "# is_a",
                "",
                "## Definition",
                "taxonomy",
                "",
                "## Domain / Range",
                "- Domain: subtype concept",
                "- Range: supertype concept",
                "",
            ]
        ),
    )
    _write(
        repo / "ontology" / "src" / "reference" / "concepts" / "core.Actor.md",
        "\n".join(
            [
                "---",
                "ont:",
                '  id: "core.Actor"',
                "  type: concept",
                '  labels: ["Actor"]',
                '  description: "an actor"',
                "  relations: []",
                "  examples:",
                '    - "an example"',
                "  anti_examples:",
                '    - "an anti-example"',
                "---",
                "",
                "# Actor",
                "",
                "## Definition",
                "an actor",
                "",
            ]
        ),
    )
    _write(
        repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
        "\n".join(
            [
                "---",
                "ont:",
                '  id: "core.Agent"',
                "  type: concept",
                '  labels: ["Agent"]',
                '  description: "an agent"',
                "  relations:",
                "    - type: is_a",
                '      target: "core.Actor"',
                "  examples:",
                '    - "an example"',
                "  anti_examples:",
                '    - "an anti-example"',
                "---",
                "",
                "# Agent",
                "",
                "## Definition",
                "an agent",
                "",
            ]
        ),
    )
    return repo


def _run(argv: list[str]) -> int:
    buf = io.StringIO()
    prev_console = cli_mod.console
    cli_mod.console = Console(file=buf, force_terminal=False, color_system=None, width=200)
    try:
        cli.main(argv)
    except SystemExit as e:
        return int(e.code or 0)
    finally:
        cli_mod.console = prev_console
    return 0


def _run_capture(argv: list[str]) -> tuple[int, str]:
    buf = io.StringIO()
    prev_console = cli_mod.console
    cli_mod.console = Console(file=buf, force_terminal=False, color_system=None, width=200)
    try:
        try:
            cli.main(argv)
        except SystemExit as e:
            code = int(e.code or 0)
        else:
            code = 0
    finally:
        cli_mod.console = prev_console
    return code, buf.getvalue()


def _parse_json(out: str) -> dict:
    return json.loads(out.strip())


class TestRocsCli(unittest.TestCase):
    def test_version_subcommand(self) -> None:
        self.assertEqual(_run(["version"]), 0)

    def test_rules_json_schema(self) -> None:
        code, out = _run_capture(["rules", "--json"])
        self.assertEqual(code, 0)
        payload = _parse_json(out)
        self.assertIsInstance(payload.get("rules"), list)
        self.assertIn("STRUCT001", {r.get("rule_id") for r in payload["rules"]})

    def test_explain_unknown_rule_json_error_envelope(self) -> None:
        code, out = _run_capture(["explain", "NOPE999", "--json"])
        self.assertEqual(code, 1)
        payload = _parse_json(out)
        self.assertEqual(payload.get("ok"), False)
        self.assertIn("unknown rule id", payload.get("error", {}).get("message", ""))

    def test_validate_ok(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)

    def test_validate_json_ok_schema(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["validate", "--repo", str(repo), "--json"])
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), True)
            self.assertEqual(payload.get("findings"), [])
            self.assertIn("budget", payload)

    def test_validate_writes_authority_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
            aggregate = repo / "ontology" / "dist" / "authority-receipt.json"
            command_receipt = repo / "ontology" / "dist" / "authority-receipt.validate.json"
            self.assertTrue(aggregate.exists())
            self.assertTrue(command_receipt.exists())
            payload = json.loads(command_receipt.read_text("utf-8"))
            self.assertEqual(payload.get("schema_version"), 3)
            self.assertEqual(payload.get("command"), "validate")
            self.assertEqual(payload.get("ok"), True)
            self.assertEqual(payload.get("authority_mode"), "local_only")
            self.assertEqual(payload.get("authoritative"), False)
            self.assertEqual(payload.get("resolve_refs_requested"), False)
            self.assertEqual(payload.get("ref_layers_present"), False)
            self.assertEqual(payload.get("locator_kinds_present"), ["path"])
            self.assertEqual(payload.get("layer_sources", [{}])[0].get("source"), "path")
            self.assertEqual(payload.get("result", {}).get("finding_count"), 0)

            aggregate_payload = json.loads(aggregate.read_text("utf-8"))
            self.assertEqual(aggregate_payload.get("schema_version"), 3)
            self.assertEqual(aggregate_payload.get("last_command"), "validate")
            self.assertIn("validate", aggregate_payload.get("commands", {}))
            self.assertEqual(aggregate_payload.get("command_files", {}).get("validate"), "authority-receipt.validate.json")

    def test_validate_json_failure_has_exit_code_1(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            _write(
                repo / "ontology" / "src" / "reference" / "relations" / "also_is_a.md",
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.rel.is_a_2"',
                        "  type: relation",
                        '  labels: ["is_a"]',
                        '  description: "duplicate label"',
                        "  group: taxonomy",
                        "---",
                        "",
                        "# also_is_a",
                        "",
                    ]
                ),
            )
            code, out = _run_capture(["validate", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertIsInstance(payload.get("findings"), list)
            receipt = json.loads((repo / "ontology" / "dist" / "authority-receipt.validate.json").read_text("utf-8"))
            self.assertEqual(receipt.get("command"), "validate")
            self.assertEqual(receipt.get("ok"), False)
            self.assertEqual(receipt.get("authority_mode"), "local_only")
            self.assertGreaterEqual(receipt.get("result", {}).get("finding_count", 0), 1)

    def test_validate_ruleset_strict_implies_strict_placeholders(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            p = repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md"
            p.write_text(p.read_text("utf-8") + "\n\n<todo>\n", "utf-8")

            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
            code, out = _run_capture(["validate", "--repo", str(repo), "--ruleset", "strict", "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertIn("PLACE010", {f.get("rule_id") for f in payload.get("findings") or []})

    def test_validate_lint_ignore_suppresses_schema_findings(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            _write(
                repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.Agent"',
                        "  type: concept",
                        '  labels: ["Agent"]',
                        '  description: ""',
                        '  lint_ignore: ["ONT004"]',
                        "  relations:",
                        "    - type: is_a",
                        '      target: "core.Actor"',
                        "---",
                        "",
                        "# Agent",
                        "",
                        "## Definition",
                        "an agent",
                        "",
                    ]
                ),
            )
            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)

    def test_validate_unknown_layer_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["validate", "--repo", str(repo), "--layer", "nope", "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "usage")
            self.assertIn("unknown layer", payload.get("error", {}).get("message", ""))

    def test_summary_unknown_layer_returns_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["summary", "--repo", str(repo), "--layer", "nope", "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "usage")

    def test_summary_only_ref_fails_when_selection_is_empty(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["summary", "--repo", str(repo), "--only", "ref", "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "not_found")
            self.assertIn("matched no layers", payload.get("error", {}).get("message", ""))

    def test_validate_json_missing_front_matter_returns_content_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            _write(repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md", "# missing front matter\n")
            code, out = _run_capture(["validate", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "content")
            self.assertIn("missing front matter", payload.get("error", {}).get("message", ""))

    def test_lint_ruleset_strict_fails_on_warn(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            _write(
                repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.Agent"',
                        "  type: concept",
                        '  labels: ["Agent"]',
                        '  description: "an agent"',
                        "  relations:",
                        "    - type: is_a",
                        '      target: "core.Actor"',
                        "---",
                        "",
                        "# Agent",
                        "",
                        "## Definition",
                        "an agent",
                        "",
                    ]
                ),
            )
            self.assertEqual(_run(["lint", "--repo", str(repo), "--ruleset", "dev"]), 0)
            self.assertEqual(_run(["lint", "--repo", str(repo), "--ruleset", "strict"]), 1)

    def test_rocs_env_file_default_is_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            env_file = Path(td) / ".env"
            env_file.write_text("ROCS_WORKSPACE_ROOT=/tmp/example-workspace\n", "utf-8")

            prev_env_file = os.environ.get("ROCS_ENV_FILE")
            prev_workspace_root = os.environ.get("ROCS_WORKSPACE_ROOT")
            try:
                os.environ["ROCS_ENV_FILE"] = str(env_file)
                os.environ.pop("ROCS_WORKSPACE_ROOT", None)

                repo = _mk_repo(Path(td))
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                self.assertEqual(os.environ.get("ROCS_WORKSPACE_ROOT"), "/tmp/example-workspace")
            finally:
                if prev_env_file is None:
                    os.environ.pop("ROCS_ENV_FILE", None)
                else:
                    os.environ["ROCS_ENV_FILE"] = prev_env_file
                if prev_workspace_root is None:
                    os.environ.pop("ROCS_WORKSPACE_ROOT", None)
                else:
                    os.environ["ROCS_WORKSPACE_ROOT"] = prev_workspace_root

    def test_workspace_default_env_is_loaded(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td) / "ai-society"
            env_file = ws / "holdingco" / "governance-kernel" / ".env"
            env_file.parent.mkdir(parents=True, exist_ok=True)
            env_file.write_text("ROCS_WORKSPACE_ROOT=/tmp/workspace-from-default-env\n", "utf-8")

            repo_root = ws / "holdingco" / "projects" / "xrepo"
            _write(
                repo_root / "ontology" / "manifest.yaml",
                "\n".join(
                    [
                        "rocs:",
                        "  layer: core",
                        '  id: \"test.core\"',
                        '  version: \"0.0.0\"',
                        '  created: \"2026-01-10\"',
                        "",
                    ]
                ),
            )
            _write(repo_root / "ontology" / "src" / "system4d.yaml", "system4d: {}\n")

            prev_env_file = os.environ.get("ROCS_ENV_FILE")
            prev_workspace_root = os.environ.get("ROCS_WORKSPACE_ROOT")
            try:
                os.environ.pop("ROCS_ENV_FILE", None)
                os.environ.pop("ROCS_WORKSPACE_ROOT", None)
                self.assertEqual(_run(["validate", "--repo", str(repo_root)]), 0)
                self.assertEqual(os.environ.get("ROCS_WORKSPACE_ROOT"), "/tmp/workspace-from-default-env")
            finally:
                if prev_env_file is None:
                    os.environ.pop("ROCS_ENV_FILE", None)
                else:
                    os.environ["ROCS_ENV_FILE"] = prev_env_file
                if prev_workspace_root is None:
                    os.environ.pop("ROCS_WORKSPACE_ROOT", None)
                else:
                    os.environ["ROCS_WORKSPACE_ROOT"] = prev_workspace_root

    def test_strict_placeholders_rejects_gitlab_locator_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), manifest_extra='  note: "<gitlab:ai-society/core/ontology-kernel@v0.1.0>"')
            self.assertNotEqual(_run(["validate", "--repo", str(repo), "--strict-placeholders"]), 0)

    def test_strict_placeholders_allows_repo_locator_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), manifest_extra='  note: "<repo:core/ontology-kernel@main>"')
            self.assertEqual(_run(["validate", "--repo", str(repo), "--strict-placeholders"]), 0)

    def test_only_path_skips_ref_layers_without_resolve_refs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(
                Path(td),
                manifest_extra="\n".join(
                    [
                        "  depends_on:",
                        "    - layer: dep",
                        '      ref: "<repo:core/dep@main>"',
                    ]
                ),
            )
            self.assertEqual(_run(["validate", "--repo", str(repo), "--only", "path"]), 0)

    def test_diff_requires_resolve_refs_offline_first(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            code, out = _run_capture(["diff", "--repo", str(repo), "--baseline", "<repo:x/y@main>"])
            self.assertEqual(code, 1)
            self.assertIn("requires --resolve-refs", out)

    def test_invalid_manifest_does_not_print_traceback_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            (repo / "ontology" / "manifest.yaml").write_text("rocs: [\n", "utf-8")
            code, out = _run_capture(["validate", "--repo", str(repo)])
            self.assertEqual(code, 1)
            self.assertNotIn("Traceback", out)
            self.assertIn("error:", out)

    def test_validate_json_invalid_manifest_returns_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            (repo / "ontology" / "manifest.yaml").write_text("rocs: [\n", "utf-8")
            code, out = _run_capture(["validate", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertIn("error", payload)
            self.assertIn("kind", payload["error"])
            self.assertIn("message", payload["error"])

    def test_resolve_json_invalid_manifest_shape_returns_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            (repo / "ontology" / "manifest.yaml").write_text("rocs: 1\n", "utf-8")
            code, out = _run_capture(["resolve", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "config")
            self.assertIn("manifest.rocs must be a mapping", payload.get("error", {}).get("message", ""))

    def test_resolve_json_invalid_profiles_shape_returns_config_error(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), manifest_extra="  profiles: 1")
            code, out = _run_capture(["resolve", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "config")
            self.assertIn("manifest.rocs.profiles must be a mapping", payload.get("error", {}).get("message", ""))

    def test_resolve_json_profile_with_empty_selection_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(
                Path(td),
                manifest_extra="\n".join(
                    [
                        "  profiles:",
                        "    default: ref-only",
                        "    ref-only:",
                        "      include_layers: [dep]",
                    ]
                ),
            )
            code, out = _run_capture(["resolve", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "not_found")
            self.assertIn("matched no layers", payload.get("error", {}).get("message", ""))

    def test_resolve_rejects_layer_with_both_path_and_ref(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(
                Path(td),
                manifest_extra="\n".join(
                    [
                        "  layers:",
                        "    - name: mixed",
                        "      path: ontology/src",
                        "      ref: \"<repo:core/dep@main>\"",
                    ]
                ),
            )
            code, out = _run_capture(["resolve", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "config")
            self.assertIn("exactly one of path or ref", payload.get("error", {}).get("message", ""))

    def test_resolve_json_missing_manifest_returns_error_envelope(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = Path(td) / "repo"
            repo.mkdir(parents=True, exist_ok=True)
            code, out = _run_capture(["resolve", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertIn("error", payload)
            self.assertEqual(payload["error"].get("kind"), "config")

    def test_strict_placeholders_rejects_other_placeholders_in_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td), manifest_extra='  note: "<placeholder>"')
            self.assertNotEqual(_run(["validate", "--repo", str(repo), "--strict-placeholders"]), 0)

    def test_relation_label_collision_fails(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            _write(
                repo / "ontology" / "src" / "reference" / "relations" / "also_is_a.md",
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.rel.is_a_2"',
                        "  type: relation",
                        '  labels: ["is_a"]',
                        '  description: "duplicate label"',
                        "  group: taxonomy",
                        "---",
                        "",
                        "# also_is_a",
                        "",
                    ]
                ),
            )
            self.assertNotEqual(_run(["validate", "--repo", str(repo)]), 0)

    def test_graph_writes_default_excalidraw(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            out = Path(td) / "g.excalidraw.json"
            self.assertEqual(_run(["graph", "--repo", str(repo), "--relation", "is_a", "--out", str(out)]), 0)
            self.assertTrue(out.exists())

    def test_lint_flags_empty_markdown_heading(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            p = repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md"
            p.write_text(p.read_text("utf-8") + "#\n", "utf-8")
            code, out = _run_capture(["lint", "--repo", str(repo), "--json"])
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            self.assertIn("LINT011", {f.get("rule_id") for f in payload.get("findings") or []})

    def test_normalize_check_then_apply(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            bad = repo / "ontology" / "src" / "reference" / "concepts" / "bad.md"
            _write(
                bad,
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.Bad"',
                        "  type: concept",
                        '  labels: ["Bad"]',
                        '  description: "bad"',
                        "  relations:",
                        "---",
                        "",
                        "# Bad",
                        "",
                        "## Definition",
                        "bad",
                        "",
                    ]
                ),
            )
            self.assertEqual(_run(["normalize", "--repo", str(repo)]), 2)
            self.assertEqual(_run(["normalize", "--repo", str(repo), "--apply"]), 0)
            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)

    def test_pack_default_is_single_doc(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo)])
            self.assertEqual(code, 0)
            self.assertIn("core.Agent.md", out)
            self.assertNotIn("core.Actor.md", out)

    def test_pack_unknown_id_json_error_has_exit_code_2(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["pack", "NOPE", "--repo", str(repo), "--json"])
            self.assertEqual(code, 2)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "not_found")

    def test_pack_profile_depth_expands(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(
                Path(td),
                manifest_extra="\n".join(
                    [
                        "  profiles:",
                        "    default: repo-dev",
                        "    repo-dev:",
                        "      pack:",
                        "        max_depth: 1",
                        "        include_relation_defs: true",
                        "        rel_types: [is_a]",
                    ]
                ),
            )
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo)])
            self.assertEqual(code, 0)
            self.assertIn("core.Agent.md", out)
            self.assertIn("core.Actor.md", out)
            self.assertIn("is_a.md", out)

    def test_pack_relation_root_returns_relation_doc(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["pack", "core.rel.is_a", "--repo", str(repo), "--json"])
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            self.assertEqual(payload.get("pack", {}).get("counts", {}).get("docs"), 1)
            self.assertEqual(payload.get("docs", [{}])[0].get("ont_id"), "core.rel.is_a")
            self.assertEqual(payload.get("docs", [{}])[0].get("kind"), "relation")

    def test_pack_max_docs_is_global_cap(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(
                Path(td),
                manifest_extra="\n".join(
                    [
                        "  profiles:",
                        "    default: repo-dev",
                        "    repo-dev:",
                        "      pack:",
                        "        max_depth: 1",
                        "        include_relation_defs: true",
                        "        rel_types: [is_a]",
                    ]
                ),
            )
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo), "--max-docs", "1", "--json"])
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            self.assertEqual(payload.get("pack", {}).get("counts", {}).get("docs"), 1)
            self.assertEqual(payload.get("docs", [{}])[0].get("ont_id"), "core.Agent")

    def test_pack_rejects_root_doc_excluded_by_max_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo), "--max-bytes", "10", "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "usage")
            self.assertIn("requested root doc", payload.get("error", {}).get("message", ""))

    def test_pack_rejects_non_positive_max_docs(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo), "--max-docs", "0", "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "usage")
            self.assertIn("--max-docs", payload.get("error", {}).get("message", ""))

    def test_pack_rejects_negative_depth(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo), "--depth", "-1", "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "usage")
            self.assertIn("--depth", payload.get("error", {}).get("message", ""))

    def test_pack_rejects_invalid_profile_pack_limits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(
                Path(td),
                manifest_extra="\n".join(
                    [
                        "  profiles:",
                        "    default: repo-dev",
                        "    repo-dev:",
                        "      pack:",
                        "        max_docs: 0",
                    ]
                ),
            )
            code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertEqual(payload.get("error", {}).get("kind"), "config")
            self.assertIn("pack.max_docs", payload.get("error", {}).get("message", ""))

    def test_build_writes_id_index(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
            idx = repo / "ontology" / "dist" / "id_index.json"
            self.assertTrue(idx.exists())
            text = idx.read_text("utf-8")
            self.assertIn('"schema_version": 1', text)
            self.assertIn('"id": "core.Agent"', text)
            self.assertIn('"id": "core.rel.is_a"', text)

    def test_build_json_output_schema(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            code, out = _run_capture(["build", "--repo", str(repo), "--json"])
            self.assertEqual(code, 0)
            payload = _parse_json(out)
            self.assertIn("dist", payload)
            self.assertIn("files", payload.get("dist") or {})
            self.assertIn("authority_receipt", payload.get("dist", {}).get("files", {}))
            self.assertIn("authority_receipt_command", payload.get("dist", {}).get("files", {}))

    def test_build_writes_authority_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
            aggregate = json.loads((repo / "ontology" / "dist" / "authority-receipt.json").read_text("utf-8"))
            receipt = json.loads((repo / "ontology" / "dist" / "authority-receipt.build.json").read_text("utf-8"))
            self.assertEqual(aggregate.get("last_command"), "build")
            self.assertEqual(receipt.get("command"), "build")
            self.assertEqual(receipt.get("ok"), True)
            self.assertEqual(receipt.get("authority_mode"), "local_only")
            self.assertEqual(receipt.get("locator_kinds_present"), ["path"])

    def test_build_fails_closed_on_invalid_schema(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            _write(
                repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.Agent"',
                        "  type: concept",
                        '  labels: ["Agent"]',
                        "  relations: []",
                        "  examples:",
                        '    - "an example"',
                        "---",
                        "",
                        "# Agent",
                        "",
                        "## Definition",
                        "an agent",
                        "",
                    ]
                ),
            )
            code, out = _run_capture(["build", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertIn("ONT004", {f.get("rule_id") for f in payload.get("findings") or []})
            self.assertFalse((repo / "ontology" / "dist" / "summary.json").exists())
            receipt = json.loads((repo / "ontology" / "dist" / "authority-receipt.build.json").read_text("utf-8"))
            self.assertEqual(receipt.get("ok"), False)
            self.assertGreaterEqual(receipt.get("result", {}).get("finding_count", 0), 1)

    def test_build_clears_stale_summary_after_prior_success_then_failure(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
            self.assertTrue((repo / "ontology" / "dist" / "summary.json").exists())

            _write(
                repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
                "\n".join(
                    [
                        "---",
                        "ont:",
                        '  id: "core.Agent"',
                        "  type: concept",
                        '  labels: ["Agent"]',
                        "  relations: []",
                        "  examples:",
                        '    - "an example"',
                        "---",
                        "",
                        "# Agent",
                        "",
                        "## Definition",
                        "an agent",
                        "",
                    ]
                ),
            )

            code, out = _run_capture(["build", "--repo", str(repo), "--json"])
            self.assertEqual(code, 1)
            payload = _parse_json(out)
            self.assertEqual(payload.get("ok"), False)
            self.assertFalse((repo / "ontology" / "dist" / "summary.json").exists())
            self.assertFalse((repo / "ontology" / "dist" / "id_index.json").exists())
            self.assertFalse((repo / "ontology" / "dist" / "resolve.json").exists())
            self.assertTrue((repo / "ontology" / "dist" / "authority-receipt.build.json").exists())

    def test_build_resolve_refs_with_no_ref_layers_is_not_authoritative(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["build", "--repo", str(repo), "--resolve-refs"]), 0)
            receipt = json.loads((repo / "ontology" / "dist" / "authority-receipt.build.json").read_text("utf-8"))
            self.assertEqual(receipt.get("resolve_refs_requested"), True)
            self.assertEqual(receipt.get("ref_layers_present"), False)
            self.assertEqual(receipt.get("authority_mode"), "no_ref_layers")
            self.assertEqual(receipt.get("authoritative"), False)

    def test_standalone_build_rewrites_aggregate_to_current_command_only(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
            self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
            aggregate = json.loads((repo / "ontology" / "dist" / "authority-receipt.json").read_text("utf-8"))
            self.assertEqual(aggregate.get("last_command"), "build")
            self.assertEqual(sorted(aggregate.get("commands", {}).keys()), ["build"])
            self.assertFalse((repo / "ontology" / "dist" / "authority-receipt.validate.json").exists())
            self.assertTrue((repo / "ontology" / "dist" / "authority-receipt.build.json").exists())

    def test_build_artifacts_are_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
            dist = repo / "ontology" / "dist"
            paths = [
                dist / "resolve.json",
                dist / "summary.json",
                dist / "id_index.json",
                dist / "authority-receipt.json",
                dist / "authority-receipt.build.json",
            ]
            first = {p.name: p.read_bytes() for p in paths}

            self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
            second = {p.name: p.read_bytes() for p in paths}
            self.assertEqual(first, second)

    def test_build_artifacts_are_deterministic_with_index_cache_disabled(self) -> None:
        prev = os.environ.get("ROCS_INDEX_CACHE")
        os.environ["ROCS_INDEX_CACHE"] = "0"
        try:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td))
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                dist = repo / "ontology" / "dist"
                paths = [
                    dist / "resolve.json",
                    dist / "summary.json",
                    dist / "id_index.json",
                    dist / "authority-receipt.json",
                    dist / "authority-receipt.build.json",
                ]
                first = {p.name: p.read_bytes() for p in paths}

                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                second = {p.name: p.read_bytes() for p in paths}
                self.assertEqual(first, second)
        finally:
            if prev is None:
                os.environ.pop("ROCS_INDEX_CACHE", None)
            else:
                os.environ["ROCS_INDEX_CACHE"] = prev

    def test_index_cache_does_not_hide_content_changes_with_same_mtime(self) -> None:
        prev = os.environ.get("ROCS_INDEX_CACHE")
        os.environ["ROCS_INDEX_CACHE"] = "1"
        try:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td))
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                dist = repo / "ontology" / "dist"
                first_idx = (dist / "id_index.json").read_bytes()

                p = repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md"
                st = p.stat()
                mtime = st.st_mtime
                atime = st.st_atime
                text = p.read_text("utf-8")
                self.assertIn('labels: ["Agent"]', text)
                # same-length edit (Agent -> Ag3nt) and restore mtime to simulate timestamp-preserving edits.
                p.write_text(text.replace('labels: ["Agent"]', 'labels: ["Ag3nt"]'), "utf-8")
                os.utime(p, (atime, mtime))

                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                second_idx = (dist / "id_index.json").read_bytes()
                self.assertNotEqual(first_idx, second_idx)
        finally:
            if prev is None:
                os.environ.pop("ROCS_INDEX_CACHE", None)
            else:
                os.environ["ROCS_INDEX_CACHE"] = prev

    def test_vendored_check_ok_then_fail(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vdir = Path(td) / "vendored"
            _write(vdir / "pyproject.toml", '[project]\nname="rocs-cli"\nversion="0.0.0"\n')
            _write(vdir / "README.md", "vendored\n")
            _write(vdir / "src" / "rocs_cli" / "__init__.py", '__version__ = "0.0.0"\n')

            files = compute_expected_hashes(vdir)
            _write(vdir / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": files}, indent=2) + "\n")

            code_ok, _out_ok = _run_capture(["vendored-check", "--vendored-dir", str(vdir)])
            self.assertEqual(code_ok, 0)

            # mutate a file -> should fail
            _write(vdir / "README.md", "changed\n")
            code_bad, _out_bad = _run_capture(["vendored-check", "--vendored-dir", str(vdir)])
            self.assertNotEqual(code_bad, 0)

    def test_vendored_check_fails_on_unexpected_files(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            vdir = Path(td) / "vendored"
            _write(vdir / "pyproject.toml", '[project]\nname="rocs-cli"\nversion="0.0.0"\n')
            _write(vdir / "README.md", "vendored\n")
            _write(vdir / "src" / "rocs_cli" / "__init__.py", '__version__ = "0.0.0"\n')

            files = compute_expected_hashes(vdir)
            _write(vdir / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "files": files}, indent=2) + "\n")

            _write(vdir / "src" / "rocs_cli" / "extra-data.txt", "extra\n")
            code_extra, _out_extra = _run_capture(["vendored-check", "--vendored-dir", str(vdir)])
            self.assertNotEqual(code_extra, 0)


if __name__ == "__main__":
    unittest.main()
