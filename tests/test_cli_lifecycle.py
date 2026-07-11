from _cli_support import *  # noqa: F403
from _cli_support import _mk_repo, _parse_json, _run, _run_capture, _write

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

    def test_validate_ok_for_root_layout_ontology_repo(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td), layout="root")
                self.assertEqual(_run(["validate", "--repo", str(repo)]), 0)
                self.assertTrue((repo / "dist" / "authority-receipt.validate.json").exists())

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

    def test_build_writes_dist_at_repo_root_for_root_layout_ontology_repo(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td), layout="root")
                self.assertEqual(_run(["build", "--repo", str(repo)]), 0)
                self.assertTrue((repo / "dist" / "summary.json").exists())
                self.assertTrue((repo / "dist" / "id_index.json").exists())

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

    def test_validate_json_non_mapping_front_matter_returns_content_error(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td))
                _write(
                    repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
                    "---\n- 1\n---\n\n# Agent\n",
                )
                code, out = _run_capture(["validate", "--repo", str(repo), "--json"])
                self.assertEqual(code, 1)
                payload = _parse_json(out)
                self.assertEqual(payload.get("ok"), False)
                self.assertEqual(payload.get("error", {}).get("kind"), "content")
                self.assertIn("front matter must be a mapping", payload.get("error", {}).get("message", ""))

    def test_validate_json_non_mapping_ont_returns_content_error(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td))
                _write(
                    repo / "ontology" / "src" / "reference" / "concepts" / "core.Agent.md",
                    "---\nont: [1]\n---\n\n# Agent\n",
                )
                code, out = _run_capture(["validate", "--repo", str(repo), "--json"])
                self.assertEqual(code, 1)
                payload = _parse_json(out)
                self.assertEqual(payload.get("ok"), False)
                self.assertEqual(payload.get("error", {}).get("kind"), "content")
                self.assertIn("front matter ont must be a mapping", payload.get("error", {}).get("message", ""))

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

    def test_env_loader_strips_inline_comments(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                env_file = Path(td) / ".env"
                env_file.write_text("ROCS_WORKSPACE_ROOT=/tmp/example-workspace # inline comment\n", "utf-8")

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
