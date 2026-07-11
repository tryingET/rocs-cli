from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from rocs_cli.intelligence import (
    MembraneError, compile_plan, create_capsule, validate_capsule, validate_proposal, write_compiled_plan,
)


class TestIntelligenceMembrane(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "local.md").write_text("local\n", "utf-8")
        (self.root / "upstream.md").write_text("ref\n", "utf-8")
        self.cap = validate_capsule(create_capsule(self.root, [("local.md", "path"), ("upstream.md", "ref")]))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def proposal(self) -> dict:
        return {
            "schema_version": 1,
            "capsule_digest": self.cap["capsule_digest"],
            "registry_version": 1,
            "capabilities": ["ontology.propose.write", "ontology.read"],
            "read_paths": ["local.md", "upstream.md"],
            "write_paths": ["local.md"],
            "authority_requirement": {"kind": "human", "approval_required": True},
            "verifier": {"kind": "rocs-cli", "id": "ontology.validate.v1"},
            "rollback": {"kind": "restore", "paths": ["local.md"]},
            "operations": [{"op": "replace_text", "path": "local.md", "content": "proposed\n"}],
        }

    def test_valid_compile_is_deterministic_and_does_not_mutate_inputs(self) -> None:
        proposal, digest = validate_proposal(self.proposal(), self.cap)
        approval = {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "operator:test"}
        first = compile_plan(proposal, digest, self.cap, approval)
        second = compile_plan(proposal, digest, self.cap, approval)
        self.assertEqual(first, second)
        self.assertEqual((self.root / "local.md").read_text("utf-8"), "local\n")
        self.assertEqual(first["proposal_digest"], digest)
        self.assertRegex(first["plan_digest"], r"^sha256:[0-9a-f]{64}$")
        self.assertEqual(first["tool_version"], "rocs-intelligence-membrane/1")
        self.assertEqual(first["registry_version"], 1)

    def test_adversarial_proposals_fail_closed(self) -> None:
        mutations = []
        p = self.proposal(); p["surprise"] = True; mutations.append(p)
        p = self.proposal(); p["capabilities"] = ["shell.execute"]; mutations.append(p)
        p = self.proposal(); p["write_paths"] = ["../escape"]; mutations.append(p)
        p = self.proposal(); p["write_paths"] = ["upstream.md"]; p["rollback"]["paths"] = ["upstream.md"]; p["operations"][0]["path"] = "upstream.md"; mutations.append(p)
        p = self.proposal(); p["capsule_digest"] = "sha256:" + "0" * 64; mutations.append(p)
        p = self.proposal(); p["capabilities"] = ["ontology.propose.write"]; mutations.append(p)
        p = self.proposal(); p["capabilities"] = ["ontology.read"]; mutations.append(p)
        p = self.proposal(); p["capabilities"] = [["ontology.read"]]; mutations.append(p)
        p = self.proposal(); p["read_paths"] = ["missing.md"]; mutations.append(p)
        p = self.proposal(); p["operations"][0]["surprise"] = True; mutations.append(p)
        for proposal in mutations:
            with self.subTest(proposal=proposal), self.assertRaises(MembraneError):
                validate_proposal(proposal, self.cap)

    def test_canonical_order_and_exact_operation_consistency_fail_closed(self) -> None:
        mutations = []
        p = self.proposal(); p["capabilities"].reverse(); mutations.append(p)
        p = self.proposal(); p["read_paths"].reverse(); mutations.append(p)
        p = self.proposal(); p["write_paths"] = ["local.md", "local.md"]; mutations.append(p)
        p = self.proposal(); p["operations"] = []; mutations.append(p)
        p = self.proposal(); p["operations"].append(dict(p["operations"][0])); mutations.append(p)
        p = self.proposal(); p["rollback"]["paths"] = []; mutations.append(p)
        for proposal in mutations:
            with self.subTest(proposal=proposal), self.assertRaises(MembraneError):
                validate_proposal(proposal, self.cap)

    def test_compiled_artifact_sink_is_bounded_and_disjoint(self) -> None:
        proposal, digest = validate_proposal(self.proposal(), self.cap)
        approval = {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "operator:test"}
        plan = compile_plan(proposal, digest, self.cap, approval)
        artifact = self.root.parent / f"{self.root.name}-artifacts"
        artifact.mkdir()
        self.assertEqual(write_compiled_plan(artifact, "plans/plan.json", plan, ontology_root=self.root,
                                             capsule=self.cap, input_files=[]).parent, artifact / "plans")
        hostile = ("/tmp/absolute.json", "../escape.json", "local.md")
        for out in hostile:
            with self.subTest(out=out), self.assertRaises(MembraneError):
                write_compiled_plan(artifact, out, plan, ontology_root=self.root, capsule=self.cap, input_files=[])
        (artifact / "linked").symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(MembraneError):
            write_compiled_plan(artifact, "linked/plan.json", plan, ontology_root=self.root,
                                capsule=self.cap, input_files=[])
        with self.assertRaises(MembraneError):
            write_compiled_plan(self.root, "plan.json", plan, ontology_root=self.root,
                                capsule=self.cap, input_files=[])

    def test_missing_or_model_supplied_approval_cannot_compile(self) -> None:
        proposal, digest = validate_proposal(self.proposal(), self.cap)
        approvals = (
            {},
            {"schema_version": 1, "proposal_digest": digest, "approved": False, "approver": "operator:test"},
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "model"},
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "model:claude"},
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "self"},
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "openai"},
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "gpt-5"},
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "model-agent"},
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "assistant@example"},
            {"schema_version": 1, "proposal_digest": "sha256:" + "0" * 64, "approved": True, "approver": "operator:test"},
        )
        for approval in approvals:
            with self.subTest(approval=approval), self.assertRaises(MembraneError):
                compile_plan(proposal, digest, self.cap, approval)

    def test_compile_revalidates_all_digest_bound_inputs(self) -> None:
        proposal, digest = validate_proposal(self.proposal(), self.cap)
        approval = {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "operator:test"}
        proposal["operations"][0]["content"] = "drift\n"
        with self.assertRaises(MembraneError):
            compile_plan(proposal, digest, self.cap, approval)

    def test_capsule_content_and_digest_drift_fail(self) -> None:
        drifted = json.loads(json.dumps(self.cap)); drifted["inputs"][0]["content"] += "x"
        with self.assertRaises(MembraneError):
            validate_capsule(drifted)
        reordered = json.loads(json.dumps(self.cap))
        reordered["inputs"].reverse()
        body = {key: reordered[key] for key in ("schema_version", "tool_version", "inputs")}
        from rocs_cli.intelligence import _digest
        reordered["capsule_digest"] = _digest(body)
        with self.assertRaises(MembraneError):
            validate_capsule(reordered)


class TestExactJsonTypes(unittest.TestCase):
    def test_boolean_versions_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "x.md").write_text("x\n", "utf-8")
            cap = create_capsule(root, [("x.md", "path")])
            cap["schema_version"] = True
            with self.assertRaises(MembraneError):
                validate_capsule(cap)

        # Proposal and registry versions are independently exact integers.
        for field in ("schema_version", "registry_version"):
            with tempfile.TemporaryDirectory() as td:
                root = Path(td); (root / "x.md").write_text("x\n", "utf-8")
                cap = create_capsule(root, [("x.md", "path")])
                proposal = {
                    "schema_version": 1, "capsule_digest": cap["capsule_digest"], "registry_version": 1,
                    "capabilities": [], "read_paths": [], "write_paths": [],
                    "authority_requirement": {"kind": "human", "approval_required": True},
                    "verifier": {"kind": "rocs-cli", "id": "ontology.validate.v1"},
                    "rollback": {"kind": "restore", "paths": []}, "operations": [],
                }
                proposal[field] = True
                with self.assertRaises(MembraneError):
                    validate_proposal(proposal, cap)

    def test_approval_required_rejects_integer(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            root = Path(td); (root / "x.md").write_text("x\n", "utf-8")
            cap = create_capsule(root, [("x.md", "path")])
            proposal = {
                "schema_version": 1, "capsule_digest": cap["capsule_digest"], "registry_version": 1,
                "capabilities": [], "read_paths": [], "write_paths": [],
                "authority_requirement": {"kind": "human", "approval_required": 1},
                "verifier": {"kind": "rocs-cli", "id": "ontology.validate.v1"},
                "rollback": {"kind": "restore", "paths": []}, "operations": [],
            }
            with self.assertRaises(MembraneError):
                validate_proposal(proposal, cap)
