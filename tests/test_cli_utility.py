from _cli_support import *  # noqa: F403
from _cli_support import _mk_repo, _parse_json, _run, _run_capture, _write

class TestRocsCli(unittest.TestCase):
    def test_graph_writes_default_excalidraw(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td))
                out = Path(td) / "g.excalidraw.json"
                self.assertEqual(_run(["graph", "--repo", str(repo), "--relation", "is_a", "--out", str(out)]), 0)
                self.assertTrue(out.exists())

    def test_graph_json_preserves_edges_to_missing_targets(self) -> None:
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
                            '      target: "core.Missing"',
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
                code, out = _run_capture(["graph", "--repo", str(repo), "--json"])
                self.assertEqual(code, 0)
                payload = _parse_json(out)
                graph_payload = json.loads(Path(payload["out"]).read_text("utf-8"))
                self.assertIn("core.Missing", graph_payload["nodes"])
                self.assertEqual(graph_payload["edges"], [{"src": "core.Agent", "rel": "is_a", "dst": "core.Missing"}])

    def test_graph_dot_escapes_labels(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(Path(td))
                _write(
                    repo / "ontology" / "src" / "reference" / "relations" / "quoted.md",
                    "\n".join(
                        [
                            "---",
                            "ont:",
                            '  id: "core.rel.quoted"',
                            "  type: relation",
                            "  labels:",
                            "    - 'owns\"now'",
                            '  description: "quoted relation"',
                            "  group: taxonomy",
                            "  characteristics:",
                            "    transitive: false",
                            "    symmetric: false",
                            "---",
                            "",
                            "# quoted",
                            "",
                            "## Definition",
                            "quoted relation",
                            "",
                            "## Domain / Range",
                            "- Domain: concept",
                            "- Range: concept",
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
                            "    - type: 'owns\"now'",
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
                out = Path(td) / "graph.dot"
                self.assertEqual(_run(["graph", "--repo", str(repo), "--format", "dot", "--out", str(out)]), 0)
                self.assertIn('[label="owns\\"now"]', out.read_text("utf-8"))

    def test_build_blocks_symlinked_dist(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                repo = _mk_repo(root)
                outside = root / "outside"
                outside.mkdir()
                dist = repo / "ontology" / "dist"
                dist.symlink_to(outside, target_is_directory=True)

                code, out = _run_capture(["build", "--repo", str(repo), "--json"])
                self.assertEqual(code, 1)
                payload = _parse_json(out)
                self.assertEqual(payload.get("ok"), False)
                self.assertEqual(payload.get("error", {}).get("kind"), "config")
                self.assertIn("build output dir is not writable", payload.get("error", {}).get("message", ""))
                self.assertEqual(list(outside.iterdir()), [])

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

    def test_pack_rejects_quoted_boolean_profile_flags(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                repo = _mk_repo(
                    Path(td),
                    manifest_extra="\n".join(
                        [
                            "  profiles:",
                            "    default: repo-dev",
                            "    repo-dev:",
                            "      pack:",
                            '        include_relation_defs: "false"',
                        ]
                    ),
                )
                code, out = _run_capture(["pack", "core.Agent", "--repo", str(repo), "--json"])
                self.assertEqual(code, 1)
                payload = _parse_json(out)
                self.assertEqual(payload.get("ok"), False)
                self.assertEqual(payload.get("error", {}).get("kind"), "config")
                self.assertIn("pack.include_relation_defs", payload.get("error", {}).get("message", ""))

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
                _write(vdir / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "upstream_project": "test", "upstream_version": "1", "files": files}, indent=2) + "\n")

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
                _write(vdir / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "upstream_project": "test", "upstream_version": "1", "files": files}, indent=2) + "\n")

                _write(vdir / "src" / "rocs_cli" / "extra-data.txt", "extra\n")
                code_extra, _out_extra = _run_capture(["vendored-check", "--vendored-dir", str(vdir)])
                self.assertNotEqual(code_extra, 0)

    def test_vendored_check_rejects_symlinks_and_incomplete_manifests(self) -> None:
            with tempfile.TemporaryDirectory() as td:
                root = Path(td)
                vdir = root / "vendored"
                _write(vdir / "pyproject.toml", '[project]\nname="rocs-cli"\nversion="0.0.0"\n')
                _write(vdir / "README.md", "vendored\n")
                _write(vdir / "src" / "rocs_cli" / "__init__.py", '__version__ = "0.0.0"\n')
                files = compute_expected_hashes(vdir)
                _write(vdir / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "upstream_project": "test", "upstream_version": "1", "files": files}, indent=2) + "\n")

                outside = root / "outside.py"
                outside.write_text("unsafe\n", "utf-8")
                (vdir / "src" / "rocs_cli" / "linked.py").symlink_to(outside)
                code_symlink, _ = _run_capture(["vendored-check", "--vendored-dir", str(vdir)])
                self.assertNotEqual(code_symlink, 0)

                (vdir / "src" / "rocs_cli" / "linked.py").unlink()
                (vdir / "README.md").unlink()
                incomplete = dict(files)
                incomplete.pop("README.md")
                _write(vdir / "VENDORED_HASHES.json", json.dumps({"schema_version": 1, "upstream_project": "test", "upstream_version": "1", "files": incomplete}, indent=2) + "\n")
                code_incomplete, _ = _run_capture(["vendored-check", "--vendored-dir", str(vdir)])
                self.assertNotEqual(code_incomplete, 0)
