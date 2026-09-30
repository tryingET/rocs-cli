import hashlib
import tempfile
import unittest
from pathlib import Path

from _cli_support import _mk_repo, _parse_json, _run, _run_capture, _write

from rocs_cli.hollow import TEMPLATE_SYSTEM4D_SHA256, hollow_layer_findings
from rocs_cli.layers import LayerSpec

TEMPLATE_SYSTEM4D = Path(__file__).parent / "fixtures" / "hollow" / "tpl-project-repo-system4d.yaml"
HOLLOW_RULES = "HOLLOW001,HOLLOW002,HOLLOW010,HOLLOW020"


def _mk_empty_repo(tmp: Path, *, system4d: bytes) -> Path:
    """A repo layer shaped like a fresh project-template copy: no concept or relation documents."""
    repo = tmp / "repo"
    _write(repo / "ontology" / "manifest.yaml", 'rocs:\n  layer: core\n  id: "test.core"\n  version: "0.0.0"\n')
    src = repo / "ontology" / "src"
    src.mkdir(parents=True)
    (src / "system4d.yaml").write_bytes(system4d)
    _write(src / "reference" / "concepts" / "README.md", "# Concepts\n")
    _write(src / "bridge" / "mapping.yaml", "mappings: []\n")
    return repo


def _lint(repo: Path, *extra: str) -> tuple[int, list[dict]]:
    code, out = _run_capture(["lint", "--repo", str(repo), "--rules", HOLLOW_RULES, "--json", *extra])
    return code, _parse_json(out).get("findings") or []


class TestHollowLayerReport(unittest.TestCase):
    def test_fixture_is_the_template_the_digest_names(self) -> None:
        self.assertIn(hashlib.sha256(TEMPLATE_SYSTEM4D.read_bytes()).hexdigest(), TEMPLATE_SYSTEM4D_SHA256)

    def test_template_copy_warns_in_dev_and_fails_only_under_strict(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_empty_repo(Path(td), system4d=TEMPLATE_SYSTEM4D.read_bytes())
            code, findings = _lint(repo)
            self.assertEqual(code, 0)
            self.assertEqual([f["rule_id"] for f in findings], ["HOLLOW020", "HOLLOW010"])
            self.assertTrue(all(f["severity"] == "warn" for f in findings))
            self.assertTrue(findings[0]["path"].endswith("system4d.yaml"))
            self.assertIn("0 concepts, 0 relations, 0 bridge mappings", findings[1]["message"])
            self.assertEqual(_lint(repo, "--ruleset", "strict")[0], 1)
            self.assertEqual(_lint(repo, "--fail-on-warn")[0], 1)

    def test_validate_and_its_receipt_ignore_the_report(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_empty_repo(Path(td), system4d=TEMPLATE_SYSTEM4D.read_bytes())
            code, out = _run_capture(["validate", "--repo", str(repo), "--json"])
            self.assertEqual(code, 0)
            self.assertEqual(_parse_json(out)["findings"], [])
            receipt = _parse_json((repo / "ontology" / "dist" / "authority-receipt.validate.json").read_text("utf-8"))
            self.assertTrue(receipt["ok"])
            self.assertEqual(receipt["result"]["finding_count"], 0)

    def test_whole_scalar_placeholders_are_listed_with_lines(self) -> None:
        system4d = "\n".join(
            [
                "ontology:",
                "  system4d:",
                '    name: "Real Repo"',
                "    container:",
                "      boundary:",
                "        in_scope:",
                '          - "<what this repo implements>"',
                "      edges:",
                '        - protocol: "<http|kafka|file>"',
                '          contract: "<repo:core/ontology-kernel@main>"',
                "      constraints:",
                '        - "Run ./scripts/install-hooks.sh --repo <repo> in each observed repo"',
                '        - "contrib/<upstream>/<repo> holds forks"',
                "",
            ]
        )
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_empty_repo(Path(td), system4d=system4d.encode())
            _write(repo / "ontology" / "src" / "bridge" / "mapping.yaml", 'mappings:\n  - concept_id: "<id>"\n')
            code, findings = _lint(repo)
            self.assertEqual(code, 0)
            by_file = {Path(f["path"]).name: f["message"] for f in findings if f["rule_id"] == "HOLLOW001"}
            self.assertEqual(
                by_file["system4d.yaml"],
                "2 template placeholder(s) in YAML: line 7 <what this repo implements>, line 9 <http|kafka|file>",
            )
            self.assertEqual(by_file["mapping.yaml"], "1 template placeholder(s) in YAML: line 2 <id>")
            # A bridge mapping, even a placeholder one, is content the layer adds.
            self.assertNotIn("HOLLOW010", {f["rule_id"] for f in findings})

    def test_long_placeholder_lists_are_capped(self) -> None:
        lines = ["items:", *[f'  - "<item {i}>"' for i in range(7)], ""]
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_empty_repo(Path(td), system4d="\n".join(lines).encode())
            _, findings = _lint(repo)
            message = next(f["message"] for f in findings if f["rule_id"] == "HOLLOW001")
            self.assertTrue(message.startswith("7 template placeholder(s) in YAML: line 2 <item 0>, "))
            self.assertTrue(message.endswith("line 6 <item 4> (+2 more)"))

    def test_unparseable_yaml_is_reported_not_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_empty_repo(Path(td), system4d=b'name: "<Repo Name>"\n  bad: [\n')
            _, findings = _lint(repo)
            parse = [f for f in findings if f["rule_id"] == "HOLLOW002"]
            self.assertEqual(len(parse), 1)
            self.assertTrue(parse[0]["path"].endswith("system4d.yaml"))
            self.assertIn("placeholder scan skipped", parse[0]["message"])

    def test_filled_layer_that_borrows_through_bridge_mappings_is_not_hollow(self) -> None:
        system4d = 'ontology:\n  system4d:\n    name: "Replay Fabric"\n    debt:\n      - "rerun install-hooks.sh --repo <repo>"\n'
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_empty_repo(Path(td), system4d=system4d.encode())
            _write(
                repo / "ontology" / "src" / "bridge" / "mapping.yaml",
                'mappings:\n  - concept_id: "core.AuditEvent"\n    relation: "core.rel.instance_of"\n',
            )
            self.assertEqual(_lint(repo), (0, []))

    def test_layer_with_documents_is_not_hollow(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _mk_repo(Path(td))
            self.assertEqual(_lint(repo), (0, []))
            self.assertEqual(_run(["lint", "--repo", str(repo), "--ruleset", "dev"]), 0)

    def test_ref_layers_are_left_to_their_owner_repo(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "src"
            src.mkdir()
            (src / "system4d.yaml").write_bytes(TEMPLATE_SYSTEM4D.read_bytes())
            layer = LayerSpec(name="company", src_root=src, origin="<repo:x/y@main>", kind="ref", source="workspace")
            self.assertEqual(hollow_layer_findings([layer], {}, {}), [])
            path_layer = LayerSpec(name="repo", src_root=src, origin="ontology/src", kind="path", source="path")
            rules = [f.rule_id for f in hollow_layer_findings([path_layer], {}, {})]
            self.assertEqual(rules, ["HOLLOW020", "HOLLOW010"])


if __name__ == "__main__":
    unittest.main()
