from __future__ import annotations

import contextlib
import hashlib
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

import rocs_cli.cli as cli_mod
from rocs_cli import __main__ as cli
from rocs_cli.discovery import DEFAULT_LIMITS
from rocs_cli.errors import RocsCliError
from rocs_cli.intelligence import (
    _digest,
    compile_plan,
    create_capsule,
    validate_capsule,
    validate_proposal,
)
from rocs_cli.layers import resolve_layers
from rocs_cli.repo_view import load_repo_view
from rocs_cli.semantic_snapshot import SnapshotError, capture_corpus
from rocs_cli.wave1 import _source_commit
from rocs_cli.source_contract import (
    SOURCE_CONTRACT_V1,
    SourceContractError,
    parse_ontology_markdown_v1,
    source_contract_conformance,
)
from rocs_cli.transactions import (
    TransactionError,
    _admit_interpreted_source,
    apply_transaction,
    prepare_transaction,
    rollback_transaction,
    simulate_transaction,
    verify_receipt,
)
from rocs_cli.vendored import (
    bundle_manifest_digest,
    verify_vendored_hashes,
    write_materialization_receipt,
)


def _concept(
    ont_id: str = "core.Actor",
    *,
    relations: str = "[]",
    extra_ont: str = "",
    top: str = "",
    body: str = "# Actor\n\n## Definition\nAn actor.\n",
) -> str:
    return f"""---
ont:
  id: {ont_id}
  type: concept
  labels: [Actor]
  description: An actor
  relations: {relations}
  examples: []
  anti_examples: []
{extra_ont}{top}---
{body}"""


def _relation(
    relation_id: str = "core.rel.is_a",
    *,
    label: str = "is_a",
    extra_ont: str = "",
) -> str:
    return f"""---
ont:
  id: {relation_id}
  type: relation
  labels: [{label}]
  description: Taxonomy relation
  examples: []
  anti_examples: []
  group: taxonomy
  characteristics:
    transitive: true
    symmetric: false
  axis_default: parents
{extra_ont}---
# {label}

## Definition
Taxonomy relation.
"""


def _make_repo(base: Path, name: str = "ontology", *, selector: bool = True) -> Path:
    root = base / name
    (root / "src/reference/concepts").mkdir(parents=True)
    (root / "src/reference/relations").mkdir(parents=True)
    selector_line = f"  source_contract: {SOURCE_CONTRACT_V1}\n" if selector else ""
    (root / "manifest.yaml").write_text(
        "rocs:\n"
        "  layer: core\n"
        + selector_line
        + "  profiles:\n"
        "    default: kernel-v1\n"
        "    kernel-v1:\n"
        "      include_layers: [core]\n",
        "utf-8",
    )
    (root / "src/system4d.yaml").write_text("system4d: {}\n", "utf-8")
    (root / "src/reference/concepts/core.Actor.md").write_text(_concept(), "utf-8")
    (root / "src/reference/relations/is_a.md").write_text(_relation(), "utf-8")
    return root


def _run(argv: list[str]) -> tuple[int, str]:
    output = io.StringIO()
    old_console = cli_mod.console
    cli_mod.console = Console(file=output, force_terminal=False, color_system=None, width=200)
    try:
        with contextlib.redirect_stdout(output):
            try:
                cli.main(argv)
            except SystemExit as exc:
                code = int(exc.code or 0)
            else:
                code = 0
    finally:
        cli_mod.console = old_console
    return code, output.getvalue()


class OntologyMarkdownV1ParserTests(unittest.TestCase):
    def test_valid_concept_relation_and_non_normative_system4d(self) -> None:
        concept = _concept(
            top="system4d:\n  fog:\n    risks: []\n    assumptions: []\n    exceptions: []\n    debt: []\n"
        ).encode()
        parsed = parse_ontology_markdown_v1(concept, "reference/concepts/core.Actor.md")
        self.assertEqual((parsed.ont_id, parsed.kind), ("core.Actor", "concept"))
        relation = parse_ontology_markdown_v1(
            _relation().encode(), "reference/relations/is_a.md"
        )
        self.assertEqual(relation.ont["axis_default"], "parents")
        self.assertIn("system4d", parsed.frontmatter)

    def test_envelope_and_resource_limits_fail_closed(self) -> None:
        valid = _concept().encode()
        cases = {
            "bom": b"\xef\xbb\xbf" + valid,
            "utf8": valid + b"\xff",
            "crlf-open": valid.replace(b"---\n", b"---\r\n", 1),
            "missing-close": valid.replace(b"\n---\n", b"\n----\n", 1),
            "oversize": valid + b"x" * (1_048_577 - len(valid)),
        }
        for name, raw in cases.items():
            with self.subTest(name=name), self.assertRaises(SourceContractError) as raised:
                parse_ontology_markdown_v1(raw, "reference/concepts/core.Actor.md")
            self.assertIn(raised.exception.phase, {"resource", "envelope"})
        with self.assertRaises(SourceContractError) as depth:
            parse_ontology_markdown_v1(
                valid, "reference/concepts/core.Actor.md", operation_max_depth=1
            )
        self.assertEqual((depth.exception.kind, depth.exception.phase), ("resource_exhausted", "resource"))
        with self.assertRaises(SourceContractError) as items:
            parse_ontology_markdown_v1(
                valid, "reference/concepts/core.Actor.md", operation_max_items=2
            )
        self.assertEqual(items.exception.kind, "resource_exhausted")

    def test_forbidden_yaml_constructs_and_duplicate_keys(self) -> None:
        valid = _concept()
        cases = {
            "duplicate": valid.replace("  type: concept", "  id: core.Other\n  type: concept"),
            "anchor": valid.replace("  labels: [Actor]", "  labels: &labels [Actor]"),
            "alias": valid.replace(
                "  labels: [Actor]\n  description: An actor",
                "  labels: &labels [Actor]\n  description: *labels",
            ),
            "merge": valid.replace("ont:\n", "ont:\n  <<: {unknown: value}\n"),
            "tag": valid.replace("  description: An actor", "  description: !!str An actor"),
            "non-string-key": valid.replace("  description: An actor", "  true: value\n  description: An actor"),
            "document-marker": valid.replace("  description: An actor", "  description: An actor\n..."),
        }
        for name, text in cases.items():
            with self.subTest(name=name), self.assertRaises(SourceContractError) as raised:
                parse_ontology_markdown_v1(text.encode(), "reference/concepts/core.Actor.md")
            self.assertEqual(raised.exception.phase, "yaml")

    def test_closed_field_types_paths_and_implicit_coercion(self) -> None:
        cases = [
            (_concept().replace("description: An actor", "description: 1"), "reference/concepts/core.Actor.md", "schema"),
            (_concept(extra_ont="  lint_ignore: [LINT001]\n"), "reference/concepts/core.Actor.md", "schema"),
            (_concept(), "reference/concepts/not-the-id.md", "identity"),
            (_relation().replace("transitive: true", "transitive: yes"), "reference/relations/is_a.md", "schema"),
            (_relation().replace("symmetric: false", 'symmetric: "false"'), "reference/relations/is_a.md", "schema"),
            (_relation(label="not/path"), "reference/relations/not-path.md", "identity"),
        ]
        for text, path, phase in cases:
            with self.subTest(path=path, phase=phase), self.assertRaises(SourceContractError) as raised:
                parse_ontology_markdown_v1(text.encode(), path)
            self.assertEqual(raised.exception.phase, phase)

    def test_placeholder_has_last_error_precedence(self) -> None:
        malformed = _concept(body="<placeholder>\n").replace("description: An actor", "description: 7")
        with self.assertRaises(SourceContractError) as raised:
            parse_ontology_markdown_v1(malformed.encode(), "reference/concepts/core.Actor.md")
        self.assertEqual(raised.exception.phase, "schema")
        with self.assertRaises(SourceContractError) as placeholder:
            parse_ontology_markdown_v1(
                _concept(body="<placeholder>\n").encode(), "reference/concepts/core.Actor.md"
            )
        self.assertEqual(placeholder.exception.phase, "placeholder")


class SourceContractDispatchTests(unittest.TestCase):
    def test_selector_on_parser_and_semantic_snapshot_agree(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(Path(td))
            view = load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertEqual((len(view.concepts), len(view.relations)), (1, 1))
            self.assertTrue(all(doc.source_contract == SOURCE_CONTRACT_V1 for doc in [*view.concepts.values(), *view.relations.values()]))
            layers, _meta = resolve_layers(repo, profile="kernel-v1", resolve_refs=False)
            corpus = capture_corpus(layers, profile="kernel-v1", limits=dict(DEFAULT_LIMITS))
            self.assertEqual({doc.ont_id for doc in corpus.documents}, {"core.Actor", "core.rel.is_a"})
            self.assertTrue(all(doc.source_contract == SOURCE_CONTRACT_V1 for doc in corpus.documents))

    def test_file_backed_loader_prechecks_and_bounds_document_reads(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(Path(td))
            path = repo / "src/reference/concepts/core.Actor.md"
            path.write_bytes(b"x" * 1_048_577)
            with patch("rocs_cli.model.os.read") as read, self.assertRaises(RocsCliError) as oversized:
                load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            read.assert_not_called()
            self.assertEqual(oversized.exception.details.get("phase"), "resource")

            path.write_text(_concept(), "utf-8")
            total = 0
            requested: list[int] = []

            def growing_read(_fd: int, size: int) -> bytes:
                nonlocal total
                requested.append(size)
                if total >= 1_048_577:
                    return b""
                chunk = b"x" * min(size, 1_048_577 - total)
                total += len(chunk)
                return chunk

            with patch("rocs_cli.model.os.read", side_effect=growing_read), self.assertRaises(RocsCliError) as grew:
                load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertEqual(grew.exception.details.get("phase"), "resource")
            self.assertEqual(total, 1_048_577)
            self.assertLessEqual(max(requested), 65_536)

    def test_selector_off_preserves_legacy_path_and_shape_behavior(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(Path(td), selector=False)
            concept = repo / "src/reference/concepts/core.Actor.md"
            concept.rename(repo / "src/reference/concepts/legacy-name.md")
            relation = repo / "src/reference/relations/is_a.md"
            relation.write_text(
                _relation().replace("  axis_default: parents\n", "").replace(
                    "ont:\n", "legacy_guidance: retained\nont:\n"
                ),
                "utf-8",
            )
            view = load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertIn("core.Actor", view.concepts)
            self.assertIsNone(view.layers[0].source_contract)
            manifest = repo / "manifest.yaml"
            manifest.write_text(
                manifest.read_text("utf-8").replace("  layer: core\n", f"  layer: core\n  source_contract: {SOURCE_CONTRACT_V1}\n"),
                "utf-8",
            )
            with self.assertRaises(RocsCliError):
                load_repo_view(repo, profile="kernel-v1", resolve_refs=False)

    def test_complete_membership_references_lifecycle_and_inverse(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = _make_repo(base)
            concept = repo / "src/reference/concepts/core.Actor.md"
            concept.write_text(
                _concept(relations="[{type: missing, target: core.Missing}]") , "utf-8"
            )
            with self.assertRaises(RocsCliError) as unresolved:
                load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertEqual(unresolved.exception.details.get("phase"), "reference")

            concept.write_text(_concept(), "utf-8")
            nested = repo / "src/reference/concepts/nested"
            nested.mkdir()
            (nested / "hidden.md").write_text(_concept("core.Hidden"), "utf-8")
            with self.assertRaises(RocsCliError) as membership:
                load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertEqual(membership.exception.details.get("phase"), "identity")

    def test_deprecation_uniqueness_and_reciprocal_inverse_are_corpus_checks(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(Path(td))
            concepts = repo / "src/reference/concepts"
            concepts.joinpath("core.Old.md").write_text(
                _concept(
                    "core.Old",
                    extra_ont=(
                        "  status: deprecated\n"
                        "  deprecated:\n"
                        '    since: "2026-08-03"\n'
                        "    replaced_by: core.Actor\n"
                        "    decision: docs/adr/replacement.md\n"
                    ),
                ),
                "utf-8",
            )
            relations = repo / "src/reference/relations"
            relations.joinpath("parent_of.md").write_text(
                _relation("core.rel.parent_of", label="parent_of", extra_ont="  inverse: child_of\n"),
                "utf-8",
            )
            relations.joinpath("child_of.md").write_text(
                _relation("core.rel.child_of", label="child_of", extra_ont="  inverse: parent_of\n"),
                "utf-8",
            )
            view = load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertIn("core.Old", view.concepts)
            relations.joinpath("child_of.md").write_text(
                _relation("core.rel.child_of", label="child_of"), "utf-8"
            )
            with self.assertRaises(RocsCliError) as inverse:
                load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertEqual(inverse.exception.details.get("phase"), "reference")
            relations.joinpath("child_of.md").write_text(
                _relation("core.rel.child_of", label="child_of", extra_ont="  inverse: parent_of\n"),
                "utf-8",
            )
            concepts.joinpath("core.Old.md").write_text(
                _concept(
                    "core.Old",
                    extra_ont=(
                        "  status: deprecated\n"
                        "  deprecated:\n"
                        '    since: "2026-02-30"\n'
                        "    replaced_by: core.Old\n"
                        "    decision: ../escape\n"
                    ),
                ),
                "utf-8",
            )
            with self.assertRaises(RocsCliError) as lifecycle:
                load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            self.assertEqual(lifecycle.exception.details.get("phase"), "reference")

    def test_mixed_layers_dispatch_their_adjacent_manifest_selectors(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "resolved"
            for name in ("strict", "legacy"):
                (root / name / "src/reference/concepts").mkdir(parents=True)
                (root / name / "src/reference/relations").mkdir(parents=True)
            (root / "manifest.yaml").write_text(
                "rocs:\n  layers:\n    - name: strict\n      path: strict/src\n"
                "    - name: legacy\n      path: legacy/src\n",
                "utf-8",
            )
            (root / "strict/manifest.yaml").write_text(
                f"rocs:\n  source_contract: {SOURCE_CONTRACT_V1}\n", "utf-8"
            )
            (root / "legacy/manifest.yaml").write_text("rocs: {}\n", "utf-8")
            (root / "strict/src/reference/concepts/strict.Actor.md").write_text(
                _concept("strict.Actor"), "utf-8"
            )
            (root / "legacy/src/reference/concepts/legacy-name.md").write_text(
                _concept("legacy.Actor").replace("ont:\n", "legacy_guidance: retained\nont:\n"),
                "utf-8",
            )
            view = load_repo_view(root, profile=None, resolve_refs=False)
            self.assertEqual(
                {layer.name: layer.source_contract for layer in view.layers},
                {"strict": SOURCE_CONTRACT_V1, "legacy": None},
            )
            self.assertEqual(set(view.concepts), {"strict.Actor", "legacy.Actor"})

    def test_all_interpreting_cli_paths_reject_one_v1_schema_violation(self) -> None:
        commands = [
            ["summary", "--json"], ["validate", "--json"], ["build", "--json"],
            ["lint", "--json"], ["graph", "--json"], ["check-inverses", "--json"],
            ["normalize"], ["pack", "core.Actor", "--json"],
        ]
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            for index, command in enumerate(commands):
                repo = _make_repo(base, f"repo-{index}")
                path = repo / "src/reference/concepts/core.Actor.md"
                path.write_text(_concept(extra_ont="  unknown: rejected\n"), "utf-8")
                code, output = _run([command[0], *command[1:2], "--repo", str(repo), *command[2:]])
                self.assertNotEqual(code, 0, (command, output))
            repo = _make_repo(base, "snapshot")
            (repo / "src/reference/concepts/core.Actor.md").write_text(
                _concept(extra_ont="  unknown: rejected\n"), "utf-8"
            )
            layers, _ = resolve_layers(repo, profile="kernel-v1", resolve_refs=False)
            with self.assertRaises(SnapshotError):
                capture_corpus(layers, profile="kernel-v1", limits=dict(DEFAULT_LIMITS))

    def test_operation_qualified_claims_exist_only_on_complete_success(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _make_repo(Path(td))
            for operation in ("summary", "validate"):
                code, output = _run([operation, "--repo", str(repo), "--json"])
                self.assertEqual(code, 0, output)
                claim = json.loads(output)["source_contract_conformance"]
                self.assertEqual(claim["operation"], operation)
                self.assertEqual(claim["scope"], "source-contract/schema/reference")
                self.assertTrue(claim["complete"])
            view = load_repo_view(repo, profile="kernel-v1", resolve_refs=False)
            docs = [*view.concepts.values(), *view.relations.values()]
            self.assertIsNone(source_contract_conformance(docs, view.layers, operation="summary", complete_success=False))
            self.assertIsNone(source_contract_conformance(
                docs, view.layers, operation="summary", complete_success=True, resource_exhausted=True
            ))
            self.assertIsNone(source_contract_conformance(
                docs, view.layers, operation="context.create", complete_success=True
            ))
            path = repo / "src/reference/concepts/core.Actor.md"
            path.write_text(_concept(body="<not-admitted>\n"), "utf-8")
            code, output = _run(["summary", "--repo", str(repo), "--json"])
            self.assertNotEqual(code, 0)
            self.assertNotIn("source_contract_conformance", json.loads(output))

    def test_context_create_is_raw_custody_and_transaction_interpretation_readmits(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = _make_repo(base)
            malformed = repo / "src/reference/concepts/core.Actor.md"
            malformed.write_text(_concept(body="<raw-custody-placeholder>\n"), "utf-8")
            capsule = create_capsule(
                repo, [("src/reference/concepts/core.Actor.md", "path")]
            )
            self.assertEqual(validate_capsule(capsule), capsule)
            self.assertNotIn("conformance", json.dumps(capsule))
            with self.assertRaises(TransactionError):
                _admit_interpreted_source(repo, "transaction.prepare")

    def test_all_transaction_source_reading_paths_readmit_v1(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = _make_repo(base)
            rel = "src/reference/concepts/core.Actor.md"
            old = (repo / rel).read_text("utf-8")
            new = old.replace("An actor.\n", "An actor after the transaction.\n")
            capsule = create_capsule(repo, [(rel, "path")])
            proposal = {
                "schema_version": 1,
                "capsule_digest": capsule["capsule_digest"],
                "registry_version": 1,
                "capabilities": ["ontology.propose.write", "ontology.read"],
                "read_paths": [rel],
                "write_paths": [rel],
                "authority_requirement": {"kind": "human", "approval_required": True},
                "verifier": {"kind": "rocs-cli", "id": "ontology.validate.v1"},
                "rollback": {"kind": "restore", "paths": [rel]},
                "operations": [{"op": "replace_text", "path": rel, "content": new}],
            }
            proposal, proposal_digest = validate_proposal(proposal, capsule)
            plan = compile_plan(
                proposal,
                proposal_digest,
                capsule,
                {
                    "schema_version": 1,
                    "proposal_digest": proposal_digest,
                    "approved": True,
                    "approver": "operator:planner",
                },
            )
            authority_body = {
                "schema_version": 1,
                "owner": "owner:ontology",
                "manifest": {
                    "path": "manifest.yaml",
                    "sha256": "sha256:" + hashlib.sha256((repo / "manifest.yaml").read_bytes()).hexdigest(),
                },
                "inputs": [{"path": rel, "layer": "path", "sha256": capsule["inputs"][0]["sha256"]}],
            }
            authority = {**authority_body, "authority_artifact_digest": _digest(authority_body)}
            effects = {
                "meaning_delta": "update explanatory body",
                "affected_concept_ids": ["core.Actor"],
                "affected_relation_ids": [],
                "affected_edge_ids": [],
                "bridge_blast_radius": [],
                "code_blast_radius": [],
                "migration_obligations": [],
                "deprecation_obligations": [],
                "owner_effects": [{"owner": "owner:ontology", "paths": [rel]}],
            }
            transaction = prepare_transaction(
                plan, capsule, repo, effects, "owner:ontology", authority
            )
            self.assertNotIn("source_contract_conformance", transaction)
            simulated = simulate_transaction(transaction, plan, capsule, repo, authority)
            self.assertEqual(
                simulated["source_contract_conformance"]["operation"],
                "transaction.simulate",
            )
            receipt_root = base / "receipts"
            receipt_root.mkdir()
            receipt = apply_transaction(
                transaction,
                plan,
                capsule,
                {
                    "schema_version": 1,
                    "transaction_digest": transaction["transaction_digest"],
                    "approved": True,
                    "approver": "operator:applier",
                },
                repo,
                receipt_root,
                authority,
            )
            verified = verify_receipt(receipt, transaction, repo)
            self.assertEqual(
                verified["source_contract_conformance"]["operation"],
                "transaction.verify",
            )
            rolled_back = rollback_transaction(receipt, transaction, repo)
            self.assertEqual(
                rolled_back["source_contract_conformance"]["operation"],
                "transaction.rollback",
            )
            self.assertEqual((repo / rel).read_text("utf-8"), old)


class SchemaThreeMaterializationTests(unittest.TestCase):
    def _bundle(self, root: Path) -> Path:
        bundle = root / "bundle"
        (bundle / "src/rocs_cli").mkdir(parents=True)
        (bundle / "pyproject.toml").write_text("[project]\nname='rocs-cli'\n", "utf-8")
        (bundle / "README.md").write_text("bundle\n", "utf-8")
        (bundle / "uv.lock").write_text("version = 1\n", "utf-8")
        (bundle / "rocs.py").write_text("pass\n", "utf-8")
        (bundle / "src/rocs_cli/__init__.py").write_text("__version__='x'\n", "utf-8")
        (bundle / "extra.bin").write_bytes(b"\x00exact\xff")
        write_materialization_receipt(
            bundle, upstream_version="0.3.0", source_commit="a" * 40
        )
        return bundle

    def test_schema_three_binds_git_lock_complete_files_and_jcs_digest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            bundle = self._bundle(Path(td))
            receipt = json.loads((bundle / "VENDORED_HASHES.json").read_text("utf-8"))
            self.assertEqual(receipt["schema_version"], 3)
            self.assertEqual(receipt["source_commit"], "a" * 40)
            self.assertIn("extra.bin", receipt["files"])
            self.assertEqual(receipt["bundle_manifest_digest"], bundle_manifest_digest(receipt))
            self.assertTrue(verify_vendored_hashes(bundle)[0])

    def test_source_commit_inheritance_requires_verified_schema_three(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            original = self._bundle(root)
            self.assertEqual(_source_commit(original, required=False), "a" * 40)

            tampered_file = root / "tampered-file"
            shutil.copytree(original, tampered_file)
            (tampered_file / "extra.bin").write_bytes(b"changed")
            self.assertIsNone(_source_commit(tampered_file, required=False))

            tampered_digest = root / "tampered-digest"
            shutil.copytree(original, tampered_digest)
            receipt_path = tampered_digest / "VENDORED_HASHES.json"
            receipt = json.loads(receipt_path.read_text("utf-8"))
            receipt["bundle_manifest_digest"] = "sha256:" + "0" * 64
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
            self.assertIsNone(_source_commit(tampered_digest, required=False))

            fake_schema_two = root / "fake-schema-two"
            shutil.copytree(original, fake_schema_two)
            receipt_path = fake_schema_two / "VENDORED_HASHES.json"
            receipt = json.loads(receipt_path.read_text("utf-8"))
            receipt["schema_version"] = 2
            receipt.pop("uv_lock_sha256")
            receipt.pop("bundle_manifest_digest")
            receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
            self.assertIsNone(_source_commit(fake_schema_two, required=False))
            with self.assertRaises(RuntimeError):
                _source_commit(fake_schema_two)

    def test_schema_three_rejects_mutations_missing_extra_symlink_lock_and_digest(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            original = self._bundle(Path(td))
            for name in ("source", "missing", "extra", "symlink", "lock", "digest"):
                with self.subTest(name=name):
                    candidate = Path(td) / name
                    shutil.copytree(original, candidate)
                    receipt_path = candidate / "VENDORED_HASHES.json"
                    receipt = json.loads(receipt_path.read_text("utf-8"))
                    if name == "source":
                        receipt["source_commit"] = "A" * 40
                        receipt["bundle_manifest_digest"] = bundle_manifest_digest(receipt)
                        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
                    elif name == "missing":
                        (candidate / "extra.bin").unlink()
                    elif name == "extra":
                        (candidate / "undeclared").write_text("extra\n", "utf-8")
                    elif name == "symlink":
                        (candidate / "linked").symlink_to("README.md")
                    elif name == "lock":
                        (candidate / "uv.lock").write_text("changed\n", "utf-8")
                        receipt["files"]["uv.lock"] = hashlib.sha256(
                            (candidate / "uv.lock").read_bytes()
                        ).hexdigest()
                        receipt["bundle_manifest_digest"] = bundle_manifest_digest(receipt)
                        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
                    else:
                        receipt["bundle_manifest_digest"] = "sha256:" + "0" * 64
                        receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
                    ok, errors = verify_vendored_hashes(candidate)
                    self.assertFalse(ok, errors)


if __name__ == "__main__":
    unittest.main()
