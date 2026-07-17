from __future__ import annotations

import fcntl
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from rocs_cli.semantic_release_protocol import jcs_bytes, validate_object
from rocs_cli.semantic_release_models import CheckedReleaseObject
import rocs_cli.semantic_release_transactions as transaction_module
from rocs_cli.semantic_release_transactions import (
    BlockedRecordError,
    CasMismatchError,
    EffectIndeterminateError,
    ReplayError,
    SANDBOX_PREFIX,
    SandboxTransaction,
    SandboxTransactionError,
    SemanticReleaseSandboxStore,
)

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs" / "project" / "semantic-release-v0"


class SemanticReleaseTransactionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        golden = json.loads((PACKET / "golden-fixtures.json").read_text(encoding="utf-8"))
        cls.instances = [record["instance"] for record in golden["records"]]

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.root = self.base / f"{SANDBOX_PREFIX}test"
        self.store = SemanticReleaseSandboxStore.create(self.root)
        self.first = validate_object(self.instances[0])
        self.second = validate_object(self.instances[1])

    def tearDown(self) -> None:
        self.temp.cleanup()

    def transaction(
        self,
        record=None,
        *,
        transaction_id: str = "tx-1",
        replay_key: str = "replay-1",
        revision: int | None = None,
        head_digest: str | None | object = ...,
    ) -> SandboxTransaction:
        head = self.store.current_head()
        expected_revision = (0 if head is None else head["revision"]) if revision is None else revision
        if head_digest is ...:
            expected_head = None if head is None else head["head_digest"]
        else:
            expected_head = head_digest
        return SandboxTransaction(
            transaction_id, replay_key, expected_revision, expected_head, record or self.first
        )

    def snapshot(self) -> dict[str, tuple[int, bytes | str]]:
        result: dict[str, tuple[int, bytes | str]] = {}
        for path in sorted(self.root.rglob("*")):
            relative = path.relative_to(self.root).as_posix()
            mode = os.lstat(path).st_mode
            if path.is_symlink():
                result[relative] = (mode, os.readlink(path))
            elif path.is_file():
                result[relative] = (mode, path.read_bytes())
            else:
                result[relative] = (mode, "directory")
        return result

    def assert_clean_pending(self, store: SemanticReleaseSandboxStore | None = None) -> None:
        store = store or self.store
        self.assertFalse(store.journal_path.exists())
        self.assertEqual(list(store.staging_root.iterdir()), [])

    def test_append_only_cas_lifecycle_and_disjoint_roots(self) -> None:
        topology = self.store.topology()
        self.assertEqual(len(set(topology.values())), 4)
        self.assertNotIn(topology["history"], topology["active"].parents)
        first_receipt = self.store.apply(self.transaction())
        first_head = self.store.current_head()
        self.assertEqual(first_head["revision"], 1)
        self.assertFalse(first_receipt["production_authorized"])
        history_before = {path.name: path.read_bytes() for path in self.store.history_root.iterdir()}
        second_receipt = self.store.apply(self.transaction(
            self.second, transaction_id="tx-2", replay_key="replay-2"
        ))
        self.assertEqual(self.store.current_head()["revision"], 2)
        self.assertEqual(second_receipt["prior_head_digest"], first_head["head_digest"])
        for name, raw in history_before.items():
            self.assertEqual((self.store.history_root / name).read_bytes(), raw)
        self.assertEqual(len(list(self.store.history_root.iterdir())), 2)
        self.assertEqual(len(list(self.store.receipt_root.iterdir())), 2)
        self.assert_clean_pending()

    def test_stale_head_and_replay_fail_without_effect(self) -> None:
        first_tx = self.transaction()
        self.store.apply(first_tx)
        before = self.snapshot()
        with self.assertRaises(ReplayError):
            self.store.apply(first_tx)
        stale = SandboxTransaction("tx-stale", "replay-stale", 0, None, self.second)
        with self.assertRaises(CasMismatchError):
            self.store.apply(stale)
        self.assertEqual(self.snapshot(), before)

    def test_revoked_and_superseded_pins_fail_before_mutation(self) -> None:
        for category in ("revoked", "superseded"):
            with self.subTest(category=category):
                root = self.base / f"{SANDBOX_PREFIX}{category}"
                kwargs = {f"{category}_record_digests": [self.first.computed_digest]}
                store = SemanticReleaseSandboxStore.create(root, **kwargs)
                tx = SandboxTransaction("tx", "replay", 0, None, self.first)
                before = self._snapshot_root(root)
                with self.assertRaises(BlockedRecordError):
                    store.apply(tx)
                self.assertEqual(self._snapshot_root(root), before)

    def test_caught_precommit_faults_restore_exact_preimage(self) -> None:
        for fault in ("before_journal", "after_journal", "after_head"):
            with self.subTest(fault=fault):
                root = self.base / f"{SANDBOX_PREFIX}{fault}"
                store = SemanticReleaseSandboxStore.create(root)
                before = self._snapshot_root(root)
                tx = SandboxTransaction("tx", "replay", 0, None, self.first)
                with self.assertRaises(SandboxTransactionError):
                    store.apply(tx, fault=fault)
                self.assertEqual(self._snapshot_root(root), before)
                self.assertIsNone(store.current_head())
                self.assert_clean_pending(store)

    def test_history_and_receipt_faults_recover_idempotently(self) -> None:
        for fault in ("after_history", "after_receipt"):
            with self.subTest(fault=fault):
                root = self.base / f"{SANDBOX_PREFIX}{fault}"
                store = SemanticReleaseSandboxStore.create(root)
                tx = SandboxTransaction("tx", "replay", 0, None, self.first)
                with self.assertRaises(EffectIndeterminateError):
                    store.apply(tx, fault=fault)
                recovered = store.recover()
                self.assertEqual(recovered.status, "completed_commit")
                self.assertEqual(store.recover().status, "no_pending_transaction")
                self.assertEqual(store.current_head()["revision"], 1)
                self.assertEqual(len(list(store.history_root.iterdir())), 1)
                self.assertEqual(len(list(store.receipt_root.iterdir())), 1)
                with self.assertRaises(ReplayError):
                    store.apply(tx)

    def test_process_death_after_head_is_recovered_before_next_append(self) -> None:
        record_path = self.base / "record.json"
        record_path.write_bytes(self.first.canonical_bytes)
        script = """from pathlib import Path
import sys
from rocs_cli.semantic_release_protocol import strict_json_loads,validate_object
from rocs_cli.semantic_release_transactions import SemanticReleaseSandboxStore,SandboxTransaction
record=validate_object(strict_json_loads(Path(sys.argv[2]).read_bytes()))
store=SemanticReleaseSandboxStore(Path(sys.argv[1]))
store.apply(SandboxTransaction('tx-crash','replay-crash',0,None,record),fault='process_exit_after_head')
"""
        child = subprocess.run(
            [sys.executable, "-c", script, str(self.root), str(record_path)],
            cwd=ROOT,
            env={"PATH": os.environ.get("PATH", ""), "HOME": str(self.base), "LANG": "C.UTF-8"},
            check=False,
        )
        self.assertEqual(child.returncode, 91)
        reopened = SemanticReleaseSandboxStore(self.root)
        recovered_head = reopened.current_head()  # reader lock completes recovery before exposure
        self.assertEqual(recovered_head["revision"], 1)
        self.assertEqual(len(list(reopened.receipt_root.iterdir())), 1)
        self.assertEqual(reopened.recover().status, "no_pending_transaction")
        next_tx = SandboxTransaction(
            "tx-next", "replay-next", 1, recovered_head["head_digest"], self.second
        )
        reopened.apply(next_tx)
        self.assertEqual(reopened.current_head()["revision"], 2)
        self.assert_clean_pending(reopened)

    def test_unknown_partial_state_fails_closed_and_retains_journal(self) -> None:
        tx = self.transaction()
        with self.assertRaises(EffectIndeterminateError):
            self.store.apply(tx, fault="after_history")
        self.store.head_path.write_bytes(b'{"tampered":true}')
        with self.assertRaises(SandboxTransactionError):
            self.store.recover()
        self.assertTrue(self.store.journal_path.exists())
        self.assertEqual(len(list(self.store.history_root.iterdir())), 1)

    def test_marker_head_and_symlink_tampering_fail_closed(self) -> None:
        self.store.marker_path.write_bytes(b'{"production_authorized":true}')
        with self.assertRaises(SandboxTransactionError):
            SemanticReleaseSandboxStore(self.root)
        root = self.base / f"{SANDBOX_PREFIX}head-tamper"
        store = SemanticReleaseSandboxStore.create(root)
        store.apply(SandboxTransaction("tx", "replay", 0, None, self.first))
        store.head_path.write_bytes(b'{"revision":1}')
        with self.assertRaises(SandboxTransactionError):
            store.current_head()
        other = self.base / f"{SANDBOX_PREFIX}symlink"
        other.mkdir()
        (other / "active").symlink_to(root / "active", target_is_directory=True)
        for name in ("history", "receipts", "staging"):
            (other / name).mkdir()
        (other / "SANDBOX.json").write_bytes((root / "SANDBOX.json").read_bytes())
        with self.assertRaises(SandboxTransactionError):
            SemanticReleaseSandboxStore(other)

    def test_forged_checked_object_is_independently_revalidated(self) -> None:
        forged = CheckedReleaseObject(
            self.first.schema,
            self.first.definition,
            self.first.canonical_bytes,
            "sha256:" + "0" * 64,
        )
        before = self.snapshot()
        with self.assertRaisesRegex(SandboxTransactionError, "identity mismatch"):
            self.store.apply(SandboxTransaction("tx", "replay", 0, None, forged))
        self.assertEqual(self.snapshot(), before)

    def test_directory_replacement_cannot_redirect_writes(self) -> None:
        original = self.root / "history-original"
        outside = self.base / "outside"
        outside.mkdir()
        self.store.history_root.rename(original)
        self.store.history_root.symlink_to(outside, target_is_directory=True)
        try:
            with self.assertRaisesRegex(SandboxTransactionError, "identity drift"):
                self.store.apply(self.transaction())
            self.assertEqual(list(outside.iterdir()), [])
        finally:
            self.store.history_root.unlink()
            original.rename(self.store.history_root)

    def test_mid_transaction_active_replacement_never_returns_committed(self) -> None:
        moved = self.root / "active-original"
        original_replace = transaction_module._replace
        swapped = False

        def replace_after_swap(path: Path, raw: bytes) -> None:
            nonlocal swapped
            if path.name == "head.json" and not swapped:
                self.store.active_root.rename(moved)
                self.store.active_root.mkdir()
                swapped = True
            original_replace(path, raw)

        try:
            with mock.patch.object(transaction_module, "_replace", replace_after_swap):
                with self.assertRaisesRegex(SandboxTransactionError, "identity drift"):
                    self.store.apply(self.transaction())
            self.assertFalse(self.store.head_path.exists())
            self.assertEqual(list(self.store.history_root.iterdir()), [])
            self.assertEqual(list(self.store.receipt_root.iterdir()), [])
        finally:
            if swapped:
                self.store.active_root.rmdir()
                moved.rename(self.store.active_root)

    def test_lock_acquisition_obeys_one_deadline(self) -> None:
        root = self.base / f"{SANDBOX_PREFIX}lock-deadline"
        store = SemanticReleaseSandboxStore.create(root, deadline_ms=10)
        fd = os.open(store.lock_path, os.O_RDWR)
        fcntl.flock(fd, fcntl.LOCK_EX)
        started = time.monotonic()
        try:
            with self.assertRaisesRegex(SandboxTransactionError, "lock acquisition"):
                store.apply(SandboxTransaction("tx", "replay", 0, None, self.first))
        finally:
            fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)
        self.assertLess(time.monotonic() - started, 0.5)

    def test_non_sandbox_and_unbounded_deadline_are_rejected(self) -> None:
        with self.assertRaises(SandboxTransactionError):
            SemanticReleaseSandboxStore.create(self.base / "production")
        root = self.base / f"{SANDBOX_PREFIX}deadline"
        store = SemanticReleaseSandboxStore.create(root, deadline_ms=0)
        with self.assertRaisesRegex(SandboxTransactionError, "deadline"):
            store.apply(SandboxTransaction("tx", "replay", 0, None, self.first))

    @staticmethod
    def _snapshot_root(root: Path) -> dict[str, tuple[int, bytes | str]]:
        result: dict[str, tuple[int, bytes | str]] = {}
        for path in sorted(root.rglob("*")):
            relative = path.relative_to(root).as_posix()
            mode = os.lstat(path).st_mode
            if path.is_symlink():
                result[relative] = (mode, os.readlink(path))
            elif path.is_file():
                result[relative] = (mode, path.read_bytes())
            else:
                result[relative] = (mode, "directory")
        return result


if __name__ == "__main__":
    unittest.main()
