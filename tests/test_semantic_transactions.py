from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from rocs_cli.intelligence import _digest, compile_plan, create_capsule, validate_proposal
from rocs_cli.transactions import (
    TransactionError,
    apply_transaction,
    prepare_transaction,
    rollback_transaction,
    simulate_transaction,
    verify_receipt,
)


DOC_A = """---
ont:
  id: test.local
  type: concept
  labels: [Local]
  description: Local concept
  relations: []
---
old
"""
DOC_A_NEW = DOC_A.replace("old\n", "new\n")
DOC_B = """---
ont:
  id: test.second
  type: concept
  labels: [Second]
  description: Second concept
  relations: []
---
second-old
"""
DOC_B_NEW = DOC_B.replace("second-old\n", "second-new\n")


class TestSemanticTransactions(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "ontology"
        (self.root / "src/reference/concepts").mkdir(parents=True)
        (self.root / "manifest.yaml").write_text(
            "rocs:\n  layers:\n    - name: repo\n      path: src\n  profiles:\n    default: repo-dev\n    repo-dev:\n      include_layers: [repo]\n",
            "utf-8",
        )
        (self.root / "src/system4d.yaml").write_text("system4d: {}\n", "utf-8")
        (self.root / "src/reference/concepts/local.md").write_text(DOC_A, "utf-8")
        (self.root / "src/reference/concepts/second.md").write_text(DOC_B, "utf-8")
        (self.root / "src/context.txt").write_text("read-context\n", "utf-8")
        (self.root / "unchanged-link").symlink_to("src/context.txt")
        self.artifacts = base / "artifacts"
        self.artifacts.mkdir()
        self.cap = create_capsule(
            self.root,
            [("src/reference/concepts/local.md", "path"), ("src/context.txt", "path"),
             ("src/reference/concepts/second.md", "path")],
        )
        self.authority_body = {
            "schema_version": 1,
            "owner": "owner:ontology",
            "manifest": {"path": "manifest.yaml", "sha256": "sha256:" + hashlib.sha256(
                (self.root / "manifest.yaml").read_bytes()).hexdigest()},
            "inputs": [
                {"path": item["path"], "layer": item["layer"], "sha256": item["sha256"]}
                for item in self.cap["inputs"]
            ],
        }
        self.authority = {
            **self.authority_body,
            "authority_artifact_digest": _digest(self.authority_body),
        }
        self.effects = {
            "meaning_delta": "update two concept descriptions",
            "affected_concept_ids": ["test.local", "test.second"],
            "affected_relation_ids": [],
            "affected_edge_ids": [],
            "bridge_blast_radius": [],
            "code_blast_radius": [],
            "migration_obligations": [],
            "deprecation_obligations": [],
            "owner_effects": [
                {"owner": "owner:ontology", "paths": ["src/reference/concepts/local.md", "src/reference/concepts/second.md"]}
            ],
        }
        self.plan, self.tx = self._make_transaction(DOC_A_NEW, DOC_B_NEW)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _make_transaction(self, first: str, second: str):
        proposal = {
            "schema_version": 1,
            "capsule_digest": self.cap["capsule_digest"],
            "registry_version": 1,
            "capabilities": ["ontology.propose.write", "ontology.read"],
            "read_paths": ["src/context.txt", "src/reference/concepts/local.md", "src/reference/concepts/second.md"],
            "write_paths": ["src/reference/concepts/local.md", "src/reference/concepts/second.md"],
            "authority_requirement": {"kind": "human", "approval_required": True},
            "verifier": {"kind": "rocs-cli", "id": "ontology.validate.v1"},
            "rollback": {"kind": "restore", "paths": ["src/reference/concepts/local.md", "src/reference/concepts/second.md"]},
            "operations": [
                {"op": "replace_text", "path": "src/reference/concepts/local.md", "content": first},
                {"op": "replace_text", "path": "src/reference/concepts/second.md", "content": second},
            ],
        }
        proposal, digest = validate_proposal(proposal, self.cap)
        plan = compile_plan(
            proposal,
            digest,
            self.cap,
            {"schema_version": 1, "proposal_digest": digest, "approved": True, "approver": "operator:planner"},
        )
        tx = prepare_transaction(
            plan, self.cap, self.root, self.effects, "owner:ontology", self.authority
        )
        return plan, tx

    def _approval(self, tx=None):
        tx = tx or self.tx
        return {
            "schema_version": 1,
            "transaction_digest": tx["transaction_digest"],
            "approved": True,
            "approver": "operator:applier",
        }

    def _bytes(self):
        return {
            "a": (self.root / "src/reference/concepts/local.md").read_bytes(),
            "b": (self.root / "src/reference/concepts/second.md").read_bytes(),
            "context": (self.root / "src/context.txt").read_bytes(),
        }

    def test_full_two_write_lifecycle_is_generation_atomic(self) -> None:
        before = self._bytes()
        self.assertFalse(
            simulate_transaction(self.tx, self.plan, self.cap, self.root, self.authority)["mutated"]
        )
        receipt = apply_transaction(
            self.tx, self.plan, self.cap, self._approval(), self.root, self.artifacts, self.authority
        )
        self.assertEqual(self._bytes()["a"], DOC_A_NEW.encode())
        self.assertEqual(self._bytes()["b"], DOC_B_NEW.encode())
        self.assertEqual(self._bytes()["context"], before["context"])
        self.assertTrue((self.root / "unchanged-link").is_symlink())
        self.assertTrue(verify_receipt(receipt, self.tx, self.root)["ok"])
        with self.assertRaises(TransactionError):
            rollback_transaction(
                receipt, self.tx, self.root, inject_failure="rollback_after_exchange"
            )
        self.assertEqual(self._bytes()["a"], DOC_A_NEW.encode())
        self.assertEqual(rollback_transaction(receipt, self.tx, self.root)["status"], "rolled_back")
        self.assertEqual(self._bytes(), before)

    def test_apply_failures_restore_the_complete_generation(self) -> None:
        before = self._bytes()
        for failure in ("before_journal", "before_exchange", "after_exchange", "receipt_write"):
            with self.subTest(failure=failure), self.assertRaises(TransactionError):
                apply_transaction(
                    self.tx,
                    self.plan,
                    self.cap,
                    self._approval(),
                    self.root,
                    self.artifacts,
                    self.authority,
                    inject_failure=failure,
                )
            self.assertEqual(self._bytes(), before)
            self.assertFalse(list(self.root.parent.glob(".rocs-generation-*")))
            self.assertFalse(list(self.artifacts.glob(".rocs-pending-*")))

    def test_durable_receipt_recovery_finalizes_without_reapplying(self) -> None:
        with self.assertRaises(TransactionError):
            apply_transaction(
                self.tx, self.plan, self.cap, self._approval(), self.root, self.artifacts,
                self.authority, inject_failure="after_receipt",
            )
        self.assertEqual(self._bytes()["a"], DOC_A_NEW.encode())
        receipts = list(self.artifacts.glob("[0-9a-f]*.json"))
        self.assertEqual(len(receipts), 1)
        with self.assertRaises(TransactionError):
            apply_transaction(
                self.tx, self.plan, self.cap, self._approval(), self.root, self.artifacts,
                self.authority,
            )
        self.assertFalse(list(self.artifacts.glob(".rocs-pending-*")))
        self.assertFalse(list(self.root.parent.glob(".rocs-generation-*")))
        receipt = json.loads(receipts[0].read_text("utf-8"))
        self.assertTrue(verify_receipt(receipt, self.tx, self.root)["ok"])
        rollback_transaction(receipt, self.tx, self.root)
        self.assertEqual(self._bytes()["a"], DOC_A.encode())

    def test_rollback_crash_recovery_keeps_restored_generation(self) -> None:
        from rocs_cli.transactions import _exchange

        receipt = apply_transaction(
            self.tx, self.plan, self.cap, self._approval(), self.root, self.artifacts, self.authority
        )
        stage = Path(tempfile.mkdtemp(prefix=".rocs-rollback-", dir=self.root.parent))
        shutil.copytree(self.root, stage, dirs_exist_ok=True, symlinks=True)
        for item in receipt["preimages"]:
            (stage / item["path"]).write_bytes(bytes.fromhex(item["content_hex"]))
        journal = self.root.parent / ".rocs-rollback-pending.json"
        journal.write_text(json.dumps({"schema_version": 1,
            "transaction_digest": receipt["transaction_digest"], "root": str(self.root),
            "stage": str(stage)}), "utf-8")
        _exchange(self.root, stage)  # simulate process death after the atomic rollback exchange
        self.assertEqual(self._bytes()["a"], DOC_A.encode())
        result = rollback_transaction(receipt, self.tx, self.root)
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(self._bytes()["a"], DOC_A.encode())
        self.assertFalse(journal.exists())
        self.assertFalse(stage.exists())

    def test_forged_recovery_stage_cannot_delete_or_install_sibling_tree(self) -> None:
        from rocs_cli.transactions import _expected_receipt

        expected = _expected_receipt(self.tx, "operator:applier")
        stage = self.root.parent / ".rocs-generation-forged"
        stage.mkdir(); (stage / "sentinel").write_text("unrelated", "utf-8")
        journal = self.artifacts / (".rocs-pending-" + self.tx["transaction_digest"][7:] + ".json")
        journal.write_text(json.dumps({"schema_version": 1, "kind": "apply",
            "transaction_digest": self.tx["transaction_digest"], "root": str(self.root),
            "stage": str(stage), "receipt_digest": expected["receipt_digest"],
            "preimages": self.tx["write_preimages"], "postimages": expected["postimages"]}), "utf-8")
        with self.assertRaises(TransactionError):
            apply_transaction(self.tx, self.plan, self.cap, self._approval(), self.root,
                              self.artifacts, self.authority)
        self.assertTrue((stage / "sentinel").is_file())
        self.assertTrue(journal.is_file())
        journal.unlink(); shutil.rmtree(stage)

        receipt = apply_transaction(self.tx, self.plan, self.cap, self._approval(), self.root,
                                    self.artifacts, self.authority)
        forged = self.root.parent / ".rocs-rollback-forged"
        forged.mkdir(); (forged / "attacker").write_text("payload", "utf-8")
        rollback_journal = self.root.parent / ".rocs-rollback-pending.json"
        rollback_journal.write_text(json.dumps({"schema_version": 1,
            "transaction_digest": receipt["transaction_digest"], "root": str(self.root),
            "stage": str(forged)}), "utf-8")
        with self.assertRaises(TransactionError):
            rollback_transaction(receipt, self.tx, self.root)
        self.assertEqual(self._bytes()["a"], DOC_A_NEW.encode())
        self.assertTrue((forged / "attacker").is_file())
        rollback_journal.unlink(); shutil.rmtree(forged)
        rollback_transaction(receipt, self.tx, self.root)

    def test_rollback_recovery_rejects_write_mode_forgery(self) -> None:
        receipt = apply_transaction(
            self.tx, self.plan, self.cap, self._approval(), self.root, self.artifacts, self.authority
        )
        stage = Path(tempfile.mkdtemp(prefix=".rocs-rollback-", dir=self.root.parent))
        shutil.copytree(self.root, stage, dirs_exist_ok=True, symlinks=True)
        for item in receipt["preimages"]:
            target = stage / item["path"]
            target.write_bytes(bytes.fromhex(item["content_hex"]))
            target.chmod(item["mode"])
        (stage / receipt["preimages"][0]["path"]).chmod(0o777)
        journal = self.root.parent / ".rocs-rollback-pending.json"
        journal.write_text(json.dumps({"schema_version": 1,
            "transaction_digest": receipt["transaction_digest"], "root": str(self.root),
            "stage": str(stage)}), "utf-8")
        with self.assertRaises(TransactionError):
            rollback_transaction(receipt, self.tx, self.root)
        self.assertEqual(self._bytes()["a"], DOC_A_NEW.encode())
        self.assertTrue(stage.exists()); self.assertTrue(journal.exists())
        journal.unlink(); shutil.rmtree(stage)
        rollback_transaction(receipt, self.tx, self.root)

    def test_malformed_recovery_evidence_is_preserved_fail_closed(self) -> None:
        journal = self.artifacts / (".rocs-pending-" + self.tx["transaction_digest"][7:] + ".json")
        journal.write_text("{malformed", "utf-8")
        with self.assertRaises(TransactionError):
            apply_transaction(
                self.tx, self.plan, self.cap, self._approval(), self.root, self.artifacts,
                self.authority,
            )
        self.assertEqual(journal.read_text("utf-8"), "{malformed")
        self.assertEqual(self._bytes()["a"], DOC_A.encode())

    def test_stale_capsule_preimage_approval_and_authority_fail_closed(self) -> None:
        bad_approval = {**self._approval(), "approver": "model:self"}
        with self.assertRaises(TransactionError):
            apply_transaction(
                self.tx, self.plan, self.cap, bad_approval, self.root, self.artifacts, self.authority
            )
        (self.root / "src/context.txt").write_text("stale-context\n", "utf-8")
        with self.assertRaises(TransactionError):
            simulate_transaction(self.tx, self.plan, self.cap, self.root, self.authority)
        (self.root / "src/context.txt").write_text("read-context\n", "utf-8")
        manifest = self.root / "manifest.yaml"
        original_manifest = manifest.read_bytes()
        manifest.write_bytes(original_manifest + b"# drift\n")
        with self.assertRaises(TransactionError):
            simulate_transaction(self.tx, self.plan, self.cap, self.root, self.authority)
        manifest.write_bytes(original_manifest)

        tampered = copy.deepcopy(self.tx)
        tampered["write_preimages"][0]["content_hex"] = b"attacker".hex()
        tampered["transaction_digest"] = _digest(
            {key: value for key, value in tampered.items() if key != "transaction_digest"}
        )
        with self.assertRaises(TransactionError):
            simulate_transaction(tampered, self.plan, self.cap, self.root, self.authority)

        relabeled = copy.deepcopy(self.authority)
        relabeled["inputs"][0]["layer"] = "ref"
        relabeled["authority_artifact_digest"] = _digest(
            {key: value for key, value in relabeled.items() if key != "authority_artifact_digest"}
        )
        with self.assertRaises(TransactionError):
            prepare_transaction(
                self.plan, self.cap, self.root, self.effects, "owner:ontology", relabeled
            )

    def test_mandatory_full_verifier_rejects_semantically_invalid_stage(self) -> None:
        invalid = DOC_A_NEW.replace("id: test.local", "id: invalid")
        plan, tx = self._make_transaction(invalid, DOC_B_NEW)
        before = self._bytes()
        with self.assertRaises(TransactionError):
            apply_transaction(
                tx, plan, self.cap, self._approval(tx), self.root, self.artifacts, self.authority
            )
        self.assertEqual(self._bytes(), before)

    def test_mandatory_verifier_enforces_profile_budget(self) -> None:
        manifest = self.root / "manifest.yaml"
        manifest.write_text(manifest.read_text("utf-8").replace(
            "      include_layers: [repo]\n", "      include_layers: [repo]\n      budget: 1\n"), "utf-8")
        body = copy.deepcopy(self.authority_body)
        body["manifest"]["sha256"] = "sha256:" + hashlib.sha256(manifest.read_bytes()).hexdigest()
        authority = {**body, "authority_artifact_digest": _digest(body)}
        tx = prepare_transaction(
            self.plan, self.cap, self.root, self.effects, "owner:ontology", authority
        )
        before = self._bytes()
        with self.assertRaises(TransactionError):
            apply_transaction(
                tx, self.plan, self.cap, self._approval(tx), self.root, self.artifacts, authority
            )
        self.assertEqual(self._bytes(), before)

    def test_receipt_forgery_and_unsafe_roots_fail_closed(self) -> None:
        receipt = apply_transaction(
            self.tx, self.plan, self.cap, self._approval(), self.root, self.artifacts, self.authority
        )
        forged = copy.deepcopy(receipt)
        forged["postimages"][0]["path"] = "../victim"
        forged["receipt_digest"] = _digest(
            {key: value for key, value in forged.items() if key != "receipt_digest"}
        )
        with self.assertRaises(TransactionError):
            verify_receipt(forged, self.tx, self.root)
        with self.assertRaises(TransactionError):
            rollback_transaction(forged, self.tx, self.root)
        rollback_transaction(receipt, self.tx, self.root)

        with self.assertRaises(TransactionError):
            apply_transaction(
                self.tx, self.plan, self.cap, self._approval(), self.root, self.root, self.authority
            )

    def test_module_cli_dogfoods_prepare_through_rollback(self) -> None:
        base = self.root.parent
        paths = {
            "plan": base / "plan.json", "capsule": base / "capsule.json",
            "effects": base / "effects.json", "authority": base / "authority.json",
            "approval": base / "tx-approval.json",
        }
        for key in ("plan", "capsule", "effects", "authority"):
            paths[key].write_text(json.dumps({"plan": self.plan, "capsule": self.cap,
                "effects": self.effects, "authority": self.authority}[key]), "utf-8")
        run = lambda args: subprocess.run(
            [sys.executable, "-m", "rocs_cli", *args],
            cwd=Path(__file__).resolve().parents[1], text=True, capture_output=True,
        )
        prepare = run(["transaction", "prepare", "--plan", str(paths["plan"]),
            "--capsule", str(paths["capsule"]), "--effects", str(paths["effects"]),
            "--owner", "owner:ontology", "--authority-artifact", str(paths["authority"]),
            "--ontology-root", str(self.root), "--artifact-root", str(self.artifacts),
            "--out", "cli-transaction.json"])
        self.assertEqual(prepare.returncode, 0, prepare.stderr)
        tx_path = self.artifacts / "cli-transaction.json"
        tx = json.loads(tx_path.read_text("utf-8"))
        simulate = run(["transaction", "simulate", "--transaction", str(tx_path),
            "--plan", str(paths["plan"]), "--capsule", str(paths["capsule"]),
            "--authority-artifact", str(paths["authority"]), "--ontology-root", str(self.root)])
        self.assertEqual(simulate.returncode, 0, simulate.stderr)
        paths["approval"].write_text(json.dumps({"schema_version": 1,
            "transaction_digest": tx["transaction_digest"], "approved": True,
            "approver": "operator:cli-dogfood"}), "utf-8")
        applied = run(["transaction", "apply", "--transaction", str(tx_path),
            "--plan", str(paths["plan"]), "--capsule", str(paths["capsule"]),
            "--approval", str(paths["approval"]), "--authority-artifact", str(paths["authority"]),
            "--ontology-root", str(self.root), "--receipt-root", str(self.artifacts)])
        self.assertEqual(applied.returncode, 0, applied.stderr)
        receipt = json.loads(applied.stdout)
        receipt_path = self.artifacts / (receipt["receipt_digest"][7:] + ".json")
        for command in ("verify", "rollback"):
            result = run(["transaction", command, "--receipt", str(receipt_path),
                "--transaction", str(tx_path), "--ontology-root", str(self.root)])
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._bytes()["a"], DOC_A.encode())

    def test_owner_and_ref_crossing_rejected(self) -> None:
        bad = copy.deepcopy(self.effects)
        bad["owner_effects"] = [
            {"owner": "owner:other", "paths": ["src/reference/concepts/local.md", "src/reference/concepts/second.md"]}
        ]
        with self.assertRaises(TransactionError):
            prepare_transaction(
                self.plan, self.cap, self.root, bad, "owner:ontology", self.authority
            )


if __name__ == "__main__":
    unittest.main()
