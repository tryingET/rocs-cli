"""Atomic persistence and crash recovery for semantic transactions."""
from __future__ import annotations

import ctypes
import json
import os
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any

from rocs_cli.intelligence import _canonical, _digest, _exact
from rocs_cli.transactions import (
    TransactionError,
    _approval,
    _contained_file,
    _receipt,
    _safe_root,
    _sha,
    simulate_transaction,
    validate_transaction,
    verify_receipt,
)

def _exchange(a: Path, b: Path) -> None:
    libc = ctypes.CDLL(None, use_errno=True); fn = getattr(libc, "renameat2", None)
    if fn is None: raise TransactionError("atomic generation exchange unsupported")
    if fn(-100, os.fsencode(a), -100, os.fsencode(b), 2) != 0:
        err = ctypes.get_errno(); raise TransactionError(f"atomic generation exchange failed: {os.strerror(err)}")


def _fsync_dir(path: Path) -> None:
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try: os.fsync(fd)
    finally: os.close(fd)


def _full_validate(stage: Path) -> None:
    try:
        from rocs_cli.cli import _schema_validation_result
        from rocs_cli.repo_view import load_repo_view
        from rocs_cli.validate import validate_repo_structure
        view = load_repo_view(stage, profile=None, resolve_refs=True)
        schema, _budget = _schema_validation_result(view, strict_placeholders=True, validate_deps=True)
        findings = list(validate_repo_structure(stage)) + schema
    except Exception as exc:
        raise TransactionError(f"ontology.validate.v1 failed: {exc}") from exc
    errors = [x for x in findings if getattr(x, "severity", "error") == "error"]
    if errors:
        detail = "; ".join(f"{getattr(x, 'rule_id', 'error')}: {getattr(x, 'message', x)}" for x in errors)
        raise TransactionError(f"ontology.validate.v1 failed: {detail}")


def _fsync_tree(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        if path.is_symlink():
            continue
        if path.is_file():
            fd = os.open(path, os.O_RDONLY)
            try: os.fsync(fd)
            finally: os.close(fd)
        elif path.is_dir():
            _fsync_dir(path)
    _fsync_dir(root)


def _receipt_root(root: Path, receipt_root: Path) -> Path:
    rr = _safe_root(receipt_root, "receipt root")
    if rr == root or rr.is_relative_to(root) or root.is_relative_to(rr): raise TransactionError("receipt root must be disjoint from ontology root")
    if rr.stat().st_dev != root.parent.stat().st_dev: raise TransactionError("receipt and generations must share a filesystem")
    return rr


def _expected_receipt(t: dict[str, Any], approver: str) -> dict[str, Any]:
    modes = {item["path"]: item["mode"] for item in t["write_preimages"]}
    post = [{"path": op["path"], "sha256": _sha(op["content"].encode("utf-8")), "mode": modes[op["path"]]}
            for op in t["operations"]]
    body = {"schema_version": 1, "transaction_digest": t["transaction_digest"], "approver": approver,
            "preimages": t["write_preimages"], "postimages": post, "status": "applied"}
    return {**body, "receipt_digest": _digest(body)}


def _write_exclusive(path: Path, value: dict[str, Any]) -> None:
    """Publish a complete file atomically without ever truncating the final path."""
    temp = path.parent / f".{path.name}.tmp-{os.getpid()}-{id(value)}"
    fd = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0), 0o600)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(_canonical(value)); f.flush(); os.fsync(f.fileno())
        os.link(temp, path, follow_symlinks=False)
        _fsync_dir(path.parent)
    finally:
        temp.unlink(missing_ok=True)
        _fsync_dir(path.parent)


def _matches_generation(root: Path, images: list[dict[str, Any]]) -> bool:
    try:
        return all(
            _sha(_contained_file(root, item["path"]).read_bytes()) == item["sha256"]
            and ("mode" not in item or stat.S_IMODE(os.lstat(root / item["path"]).st_mode) == item["mode"])
            for item in images
        )
    except TransactionError:
        return False


def _tree_snapshot(root: Path, excluded: set[str]) -> dict[str, tuple[Any, ...]]:
    snapshot: dict[str, tuple[Any, ...]] = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if rel in excluded:
            continue
        mode = os.lstat(path).st_mode
        if path.is_symlink():
            snapshot[rel] = ("symlink", os.readlink(path))
        elif path.is_file():
            snapshot[rel] = ("file", mode & 0o7777, _sha(path.read_bytes()))
        elif path.is_dir():
            snapshot[rel] = ("dir", mode & 0o7777)
        else:
            snapshot[rel] = ("special", mode)
    return snapshot


def _same_outside_writes(a: Path, b: Path, paths: list[str]) -> bool:
    excluded = set(paths)
    return _tree_snapshot(a, excluded) == _tree_snapshot(b, excluded)


def _apply_journal_path(rr: Path, transaction_digest: str) -> Path:
    return rr / (".rocs-pending-" + transaction_digest[7:] + ".json")


def _recover_pending(root: Path, rr: Path, t: dict[str, Any], receipt: dict[str, Any]) -> None:
    journal = _apply_journal_path(rr, t["transaction_digest"])
    if not journal.exists():
        return
    if journal.is_symlink() or not journal.is_file():
        raise TransactionError("unsafe pending recovery journal")
    try:
        j = json.loads(journal.read_bytes())
    except (OSError, json.JSONDecodeError) as exc:
        raise TransactionError("malformed pending recovery journal") from exc
    keys = {"schema_version", "kind", "transaction_digest", "root", "stage", "receipt_digest", "preimages", "postimages"}
    j = _exact(j, keys, "recovery journal")
    if (type(j["schema_version"]) is not int or j["schema_version"] != 1 or j["kind"] != "apply"
            or j["transaction_digest"] != t["transaction_digest"] or j["receipt_digest"] != receipt["receipt_digest"]
            or j["preimages"] != t["write_preimages"] or j["postimages"] != receipt["postimages"]):
        raise TransactionError("recovery journal binding drift")
    stage = Path(j["stage"])
    if (j["root"] != str(root) or stage.parent != root.parent or not stage.name.startswith(".rocs-generation-")
            or stage.is_symlink() or not stage.is_dir()):
        raise TransactionError("unsafe recovery journal paths")
    receipt_path = rr / (receipt["receipt_digest"][7:] + ".json")
    paths = [item["path"] for item in t["write_preimages"]]
    current_is_pre = _matches_generation(root, t["write_preimages"])
    current_is_post = _matches_generation(root, receipt["postimages"])
    stage_is_pre = _matches_generation(stage, t["write_preimages"])
    stage_is_post = _matches_generation(stage, receipt["postimages"])
    if not _same_outside_writes(root, stage, paths):
        raise TransactionError("recovery stage differs outside transaction writes")
    if receipt_path.exists():
        if (receipt_path.is_symlink() or receipt_path.read_bytes() != _canonical(receipt)
                or not current_is_post or not stage_is_pre):
            raise TransactionError("committed recovery state is inconsistent")
        shutil.rmtree(stage)
    elif current_is_pre and stage_is_post:
        shutil.rmtree(stage)
    elif current_is_post and stage_is_pre:
        _exchange(root, stage)
        _fsync_dir(root.parent)
        shutil.rmtree(stage)
    else:
        raise TransactionError("recovery journal found unknown generation")
    journal.unlink()
    _fsync_dir(rr)


def apply_transaction(tx: Any, plan: Any, capsule: Any, approval: Any, root: Path, receipt_root: Path, authority_artifact: Any, inject_failure: str | None = None) -> dict[str, Any]:
    t = validate_transaction(tx); approver = _approval(approval, t["transaction_digest"])
    root = _safe_root(root, "ontology root"); rr = _receipt_root(root, receipt_root)
    receipt = _expected_receipt(t, approver)
    import fcntl
    lock_fd = os.open(root.parent / ".rocs-transaction.lock", os.O_RDWR | os.O_CREAT, 0o600); fcntl.flock(lock_fd, fcntl.LOCK_EX)
    stage: Path | None = None; exchanged = False; recovery_complete = False
    journal = _apply_journal_path(rr, t["transaction_digest"])
    out = rr / (receipt["receipt_digest"][7:] + ".json")
    try:
        _recover_pending(root, rr, t, receipt)
        recovery_complete = True
        if out.exists() or out.is_symlink():
            raise TransactionError("content-addressed receipt already exists")
        simulate_transaction(t, plan, capsule, root, authority_artifact)
        stage = Path(tempfile.mkdtemp(prefix=".rocs-generation-", dir=root.parent)); shutil.copytree(root, stage, dirs_exist_ok=True, symlinks=True)
        for op in t["operations"]: (stage / op["path"]).write_text(op["content"], "utf-8")
        _full_validate(stage)
        _fsync_tree(stage)
        if inject_failure == "before_journal": raise TransactionError("injected failure before journal")
        j = {"schema_version": 1, "kind": "apply", "transaction_digest": t["transaction_digest"],
             "root": str(root), "stage": str(stage), "receipt_digest": receipt["receipt_digest"],
             "preimages": t["write_preimages"], "postimages": receipt["postimages"]}
        _write_exclusive(journal, j)
        if inject_failure == "before_exchange": raise TransactionError("injected failure before exchange")
        _exchange(root, stage); exchanged = True; _fsync_dir(root.parent)
        if inject_failure == "after_exchange": raise TransactionError("injected failure after exchange")
        if inject_failure == "receipt_write": raise TransactionError("injected receipt write failure")
        _write_exclusive(out, receipt)
        if inject_failure == "after_receipt": raise TransactionError("injected failure after durable receipt")
        journal.unlink(); _fsync_dir(rr); shutil.rmtree(stage); return receipt
    except BaseException:
        if not recovery_complete:
            raise
        committed = out.is_file() and not out.is_symlink() and out.read_bytes() == _canonical(receipt)
        if committed:
            # Receipt is the commit marker. Preserve journal + old generation for deterministic recovery.
            raise
        if exchanged and stage is not None:
            try: _exchange(root, stage); exchanged = False; _fsync_dir(root.parent)
            except Exception as exc: raise TransactionError(f"compensation failed; recovery journal retained: {exc}") from exc
        journal.unlink(missing_ok=True)
        if stage is not None: shutil.rmtree(stage, ignore_errors=True)
        raise
    finally: os.close(lock_fd)

def _recover_rollback(root: Path, r: dict[str, Any]) -> bool:
    journal = root.parent / ".rocs-rollback-pending.json"
    if not journal.exists(): return False
    if journal.is_symlink() or not journal.is_file(): raise TransactionError("unsafe rollback journal")
    try: j = json.loads(journal.read_bytes())
    except (OSError, json.JSONDecodeError) as exc: raise TransactionError("malformed rollback journal") from exc
    j = _exact(j, {"schema_version", "transaction_digest", "root", "stage"}, "rollback journal")
    stage = Path(j["stage"])
    if (type(j["schema_version"]) is not int or j["schema_version"] != 1
            or j["transaction_digest"] != r["transaction_digest"] or j["root"] != str(root)
            or stage.parent != root.parent or not stage.name.startswith(".rocs-rollback-")
            or stage.is_symlink() or not stage.is_dir()):
        raise TransactionError("rollback journal binding mismatch")
    paths = [item["path"] for item in r["preimages"]]
    post = _matches_generation(root, r["postimages"])
    pre = _matches_generation(root, r["preimages"])
    stage_post = _matches_generation(stage, r["postimages"])
    stage_pre = _matches_generation(stage, r["preimages"])
    if not _same_outside_writes(root, stage, paths):
        raise TransactionError("rollback stage differs outside transaction writes")
    if post:
        if not stage_pre:
            raise TransactionError("rollback recovery stage is not the prepared preimage generation")
        _exchange(root, stage)
        _fsync_dir(root.parent)
    elif pre:
        if not stage_post:
            raise TransactionError("rollback recovery stage is not the prior postimage generation")
    else:
        raise TransactionError("rollback recovery found unknown generation")
    shutil.rmtree(stage); journal.unlink(); _fsync_dir(root.parent)
    return True


def rollback_transaction(receipt: Any, tx: Any, root: Path, inject_failure: str | None = None) -> dict[str, Any]:
    r = _receipt(receipt, tx); root = _safe_root(root, "ontology root")
    import fcntl
    lock_fd = os.open(root.parent / ".rocs-transaction.lock", os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(lock_fd, fcntl.LOCK_EX)
    try:
        if _recover_rollback(root, r):
            return {"ok": True, "receipt_digest": r["receipt_digest"], "status": "rolled_back"}
        verify_receipt(r, tx, root)
        stage = Path(tempfile.mkdtemp(prefix=".rocs-rollback-", dir=root.parent)); exchanged = False
        journal = root.parent / ".rocs-rollback-pending.json"
        try:
            shutil.copytree(root, stage, dirs_exist_ok=True, symlinks=True)
            for item in r["preimages"]:
                (stage / item["path"]).write_bytes(bytes.fromhex(item["content_hex"]))
            _fsync_tree(stage)
            j = {"schema_version": 1, "transaction_digest": r["transaction_digest"], "root": str(root), "stage": str(stage)}
            _write_exclusive(journal, j)
            if inject_failure == "rollback_exchange": raise TransactionError("injected rollback failure")
            _exchange(root, stage); exchanged = True; _fsync_dir(root.parent)
            if inject_failure == "rollback_after_exchange": raise TransactionError("injected rollback failure after exchange")
            shutil.rmtree(stage); journal.unlink(); _fsync_dir(root.parent)
        except BaseException:
            if exchanged:
                try: _exchange(root, stage); _fsync_dir(root.parent)
                except Exception as exc: raise TransactionError(f"rollback compensation failed; journal retained: {exc}") from exc
            journal.unlink(missing_ok=True); shutil.rmtree(stage, ignore_errors=True); raise
        return {"ok": True, "receipt_digest": r["receipt_digest"], "status": "rolled_back"}
    finally:
        os.close(lock_fd)
