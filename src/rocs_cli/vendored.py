from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import unicodedata
from pathlib import Path, PurePosixPath
from typing import Any

from rocs_cli.semantic_protocol import jcs_bytes


CORE_VENDORED_FILES: tuple[Path, ...] = (Path("pyproject.toml"), Path("README.md"))
PINNED_VENDORED_FILES: tuple[Path, ...] = (Path("uv.lock"), Path("rocs.py"))
_RECEIPT = "VENDORED_HASHES.json"
_SCHEMA3_FIELDS = {
    "schema_version", "artifact", "upstream_project", "upstream_version",
    "source_commit", "uv_lock_sha256", "files", "bundle_manifest_digest",
}
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def _read_private_regular(path: Path, *, return_bytes: bool) -> bytes | str:
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
    fd = os.open(path, flags)
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"not a regular file: {path}")
        if before.st_nlink != 1:
            raise ValueError(f"multiply linked file: {path}")
        digest = hashlib.sha256()
        chunks: list[bytes] = []
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            if return_bytes:
                chunks.append(chunk)
        after = os.fstat(fd)
        identity_before = (
            before.st_dev, before.st_ino, before.st_mode, before.st_nlink,
            before.st_size, before.st_mtime_ns, before.st_ctime_ns,
        )
        identity_after = (
            after.st_dev, after.st_ino, after.st_mode, after.st_nlink,
            after.st_size, after.st_mtime_ns, after.st_ctime_ns,
        )
        if identity_before != identity_after:
            raise ValueError(f"file changed during read: {path}")
        if return_bytes:
            data = b"".join(chunks)
            if len(data) != before.st_size:
                raise ValueError(f"short read: {path}")
            return data
        return digest.hexdigest()
    finally:
        os.close(fd)


def sha256_file(path: Path) -> str:
    result = _read_private_regular(path, return_bytes=False)
    assert isinstance(result, str)
    return result


def _read_private_bytes(path: Path) -> bytes:
    result = _read_private_regular(path, return_bytes=True)
    assert isinstance(result, bytes)
    return result


def validate_vendor_source_layout(repo_root: Path) -> tuple[Path, Path, Path]:
    pyproject = repo_root / "pyproject.toml"
    readme = repo_root / "README.md"
    src_pkg = repo_root / "src" / "rocs_cli"
    if not pyproject.is_file():
        raise ValueError(f"missing source file: {pyproject}")
    if not readme.is_file():
        raise ValueError(f"missing source file: {readme}")
    if not src_pkg.is_dir():
        raise ValueError(f"missing source package dir: {src_pkg}")
    return pyproject, readme, src_pkg


def validate_vendor_target(*, repo_root: Path, target: Path) -> None:
    resolved_repo_root = repo_root.resolve()
    resolved_target = target.resolve()
    resolved_source_pkg = (resolved_repo_root / "src" / "rocs_cli").resolve()
    if resolved_target == resolved_repo_root:
        raise ValueError("refusing to vendor into source repo root")
    if resolved_target == resolved_source_pkg or resolved_target.is_relative_to(resolved_source_pkg):
        raise ValueError(f"refusing to vendor into source package tree: {resolved_target}")
    if resolved_target.is_relative_to(resolved_repo_root):
        raise ValueError(f"refusing to vendor into source repo tree: {resolved_target}")
    if resolved_target.exists() and not resolved_target.is_dir():
        raise ValueError(f"target exists and is not a directory: {resolved_target}")
    src_dir = resolved_target / "src"
    if src_dir.exists() and not src_dir.is_dir():
        raise ValueError(f"target src path is not a directory: {src_dir}")


def iter_vendored_relpaths(vendored_dir: Path) -> list[Path]:
    """Legacy schema-1/2 allowlisted inventory."""
    relpaths: list[Path] = list(CORE_VENDORED_FILES)
    relpaths.extend(path for path in PINNED_VENDORED_FILES if (vendored_dir / path).is_file())
    for src_root in (vendored_dir / "src" / "rocs_cli", vendored_dir / "runtime"):
        if src_root.exists():
            for path in sorted(src_root.rglob("*")):
                if "__pycache__" not in path.parts and path.is_file() and not path.is_symlink():
                    relpaths.append(path.relative_to(vendored_dir))
    return relpaths


def _safe_manifest_path(value: object, *, legacy: bool) -> Path | None:
    if type(value) is not str or not value or "\\" in value or unicodedata.normalize("NFC", value) != value:
        return None
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value or "//" in value or any(part in ("", ".", "..") for part in pure.parts):
        return None
    if value == _RECEIPT or any(ord(character) < 32 for character in value):
        return None
    path = Path(*pure.parts)
    if legacy and path not in CORE_VENDORED_FILES and path not in PINNED_VENDORED_FILES and not (
        (len(path.parts) >= 3 and path.parts[:2] == ("src", "rocs_cli"))
        or (len(path.parts) >= 2 and path.parts[0] == "runtime")
    ):
        return None
    return path


def _complete_regular_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in sorted(root.rglob("*"), key=lambda item: os.fsencode(item.relative_to(root).as_posix())):
        rel = path.relative_to(root).as_posix()
        opened = os.lstat(path)
        mode = opened.st_mode
        if stat.S_ISDIR(mode):
            continue
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise ValueError(f"invalid bundle file type: {rel}")
        if opened.st_nlink != 1:
            raise ValueError(f"multiply linked bundle file: {rel}")
        if rel != _RECEIPT:
            if _safe_manifest_path(rel, legacy=False) is None:
                raise ValueError(f"unsafe bundle path: {rel!r}")
            files.append(path.relative_to(root))
    return files


def compute_expected_hashes(vendored_dir: Path) -> dict[str, str]:
    """Compatibility helper for legacy schema-1/2 fixtures."""
    return {str(rel): sha256_file(vendored_dir / rel) for rel in iter_vendored_relpaths(vendored_dir)}


def compute_complete_hashes(vendored_dir: Path) -> dict[str, str]:
    return {rel.as_posix(): sha256_file(vendored_dir / rel) for rel in _complete_regular_files(vendored_dir)}


def bundle_manifest_digest(receipt: dict[str, Any]) -> str:
    preimage = {key: value for key, value in receipt.items() if key != "bundle_manifest_digest"}
    return "sha256:" + hashlib.sha256(jcs_bytes(preimage)).hexdigest()


def create_materialization_receipt(
    vendored_dir: Path,
    *,
    upstream_version: str,
    source_commit: str,
) -> dict[str, Any]:
    """Build schema 3 for one exact local bundle; no cross-builder claim is made."""
    if _COMMIT_RE.fullmatch(source_commit) is None:
        raise ValueError("source_commit must be the current 40-hex Git SHA-1 commit id")
    if type(upstream_version) is not str or not upstream_version:
        raise ValueError("upstream_version must be non-empty")
    lock = vendored_dir / "uv.lock"
    if not lock.is_file() or lock.is_symlink():
        raise ValueError("schema-3 materialization requires a regular uv.lock")
    body: dict[str, Any] = {
        "schema_version": 3,
        "artifact": "rocs-cli-self-contained",
        "upstream_project": "ai-society/core/rocs-cli",
        "upstream_version": upstream_version,
        "source_commit": source_commit,
        "uv_lock_sha256": sha256_file(lock),
        "files": compute_complete_hashes(vendored_dir),
    }
    return {**body, "bundle_manifest_digest": bundle_manifest_digest(body)}


def write_materialization_receipt(
    vendored_dir: Path,
    *,
    upstream_version: str,
    source_commit: str,
) -> dict[str, Any]:
    receipt = create_materialization_receipt(
        vendored_dir, upstream_version=upstream_version, source_commit=source_commit
    )
    (vendored_dir / _RECEIPT).write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", "utf-8")
    return receipt


def _strict_json(raw: str) -> Any:
    def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(raw, object_pairs_hook=pairs)


def parse_vendored_hashes_bytes(raw: bytes) -> dict[str, Any]:
    value = _strict_json(raw.decode("utf-8", "strict"))
    if type(value) is not dict:
        raise ValueError("root must be an object")
    return value


def read_vendored_hashes(vendored_dir: Path) -> dict:
    path = vendored_dir / _RECEIPT
    if not path.exists():
        raise FileNotFoundError(str(path))
    return parse_vendored_hashes_bytes(_read_private_bytes(path))


def verify_vendored_hashes(
    vendored_dir: Path, *, expected_receipt_bytes: bytes | None = None
) -> tuple[bool, list[str]]:
    receipt_path = vendored_dir / _RECEIPT
    try:
        current_receipt = _read_private_bytes(receipt_path)
        if expected_receipt_bytes is not None and current_receipt != expected_receipt_bytes:
            return False, [f"invalid {_RECEIPT}: receipt changed before verification"]
        verified_receipt = current_receipt if expected_receipt_bytes is None else expected_receipt_bytes
        data = parse_vendored_hashes_bytes(verified_receipt)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        return False, [f"invalid {_RECEIPT}: {exc}"]
    schema = data.get("schema_version")
    fields = {"schema_version", "upstream_project", "upstream_version", "files"}
    if schema == 2:
        fields.add("artifact")
    elif schema == 3:
        fields = _SCHEMA3_FIELDS
    if set(data) != fields:
        return False, [f"invalid {_RECEIPT}: unexpected or missing fields"]
    if schema not in (1, 2, 3):
        return False, [f"unsupported schema_version: {schema!r}"]
    if schema in (2, 3) and data.get("artifact") != "rocs-cli-self-contained":
        return False, [f"invalid {_RECEIPT}: unknown artifact identity"]
    if schema == 3 and data.get("upstream_project") != "ai-society/core/rocs-cli":
        return False, [f"invalid {_RECEIPT}: unknown upstream project"]
    if type(data.get("upstream_version")) is not str or not data["upstream_version"]:
        return False, [f"invalid {_RECEIPT}: invalid upstream version"]
    expected = data.get("files")
    if type(expected) is not dict or not expected:
        return False, [f"invalid {_RECEIPT}: 'files' must be a non-empty mapping"]

    lines: list[str] = []
    normalized: dict[str, str] = {}
    for raw_rel, wanted in expected.items():
        rel = _safe_manifest_path(raw_rel, legacy=schema in (1, 2))
        if rel is None:
            lines.append(f"invalid path: {raw_rel!r}")
            continue
        if type(wanted) is not str or _HEX64_RE.fullmatch(wanted) is None:
            lines.append(f"invalid sha256: {raw_rel}")
            continue
        normalized[rel.as_posix()] = wanted

    if schema == 3:
        source_commit = data.get("source_commit")
        lock_digest = data.get("uv_lock_sha256")
        manifest_digest = data.get("bundle_manifest_digest")
        if type(source_commit) is not str or _COMMIT_RE.fullmatch(source_commit) is None:
            lines.append("invalid source_commit: expected current Git SHA-1 object id")
        if type(lock_digest) is not str or _HEX64_RE.fullmatch(lock_digest) is None:
            lines.append("invalid uv_lock_sha256")
        if type(manifest_digest) is not str or re.fullmatch(r"sha256:[0-9a-f]{64}", manifest_digest) is None:
            lines.append("invalid bundle_manifest_digest")
        else:
            try:
                actual_manifest_digest = bundle_manifest_digest(data)
            except (TypeError, ValueError) as exc:
                lines.append(f"invalid bundle manifest preimage: {exc}")
            else:
                if manifest_digest != actual_manifest_digest:
                    lines.append(f"bundle manifest digest mismatch: expected={manifest_digest} got={actual_manifest_digest}")
        lock_path = vendored_dir / "uv.lock"
        if lock_path.is_file() and not lock_path.is_symlink() and type(lock_digest) is str:
            try:
                actual_lock = sha256_file(lock_path)
            except (OSError, ValueError) as exc:
                lines.append(f"unreadable: uv.lock ({exc})")
            else:
                if actual_lock != lock_digest:
                    lines.append(f"uv.lock digest mismatch: expected={lock_digest} got={actual_lock}")

    actual_paths: set[str] = set()
    for path in sorted(vendored_dir.rglob("*")):
        rel = path.relative_to(vendored_dir).as_posix()
        try:
            opened = os.lstat(path)
            mode = opened.st_mode
        except OSError as exc:
            lines.append(f"unreadable: {rel} ({exc})")
            continue
        if stat.S_ISDIR(mode):
            continue
        if rel == _RECEIPT and stat.S_ISREG(mode):
            continue
        if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            lines.append(f"invalid file type: {rel}")
            continue
        if opened.st_nlink != 1:
            lines.append(f"multiply linked file: {rel}")
            continue
        if schema in (1, 2) and _safe_manifest_path(rel, legacy=True) is None:
            lines.append(f"unexpected: {rel}")
            continue
        if _safe_manifest_path(rel, legacy=False) is None:
            lines.append(f"invalid path: {rel!r}")
            continue
        actual_paths.add(rel)

    required = CORE_VENDORED_FILES + (PINNED_VENDORED_FILES if schema in (2, 3) else ())
    for rel in sorted({path.as_posix() for path in required} - actual_paths):
        lines.append(f"missing required: {rel}")
    if not any(rel.startswith("src/rocs_cli/") for rel in actual_paths):
        lines.append("missing required: src/rocs_cli package files")
    for rel in sorted(actual_paths - set(normalized)):
        lines.append(f"unexpected: {rel}")
    for rel in sorted(set(normalized) - actual_paths):
        lines.append(f"missing: {rel}")
    for rel in sorted(actual_paths & set(normalized)):
        path = vendored_dir / rel
        try:
            got = sha256_file(path)
        except (OSError, ValueError) as exc:
            lines.append(f"unreadable: {rel} ({exc})")
            continue
        if got != normalized[rel]:
            lines.append(f"mismatch: {rel} expected={normalized[rel]} got={got}")
    if expected_receipt_bytes is not None:
        try:
            receipt_after = _read_private_bytes(receipt_path)
        except (OSError, ValueError) as exc:
            lines.append(f"unreadable: {_RECEIPT} ({exc})")
        else:
            if receipt_after != expected_receipt_bytes:
                lines.append(f"invalid {_RECEIPT}: receipt changed during verification")
    return not lines, lines or [f"ok: {rel} {normalized[rel]}" for rel in sorted(normalized)]
