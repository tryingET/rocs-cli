"""Generate the stdlib-only verifier/launcher used by managed consumer gates."""

from __future__ import annotations

import re

_LOCK_DIGEST_TOKEN = "__ROCS_VENDORED_LOCK_SHA256__"
_OWNER_REL_TOKEN = "__ROCS_OWNER_REL__"
_DISPATCH_TOKEN = "__ROCS_DISPATCH__"
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")

_WRAPPER = r'''#!/usr/bin/env bash
set -euo pipefail
export PATH="/usr/local/bin:/usr/bin:/bin"
unset PYTHONPATH PYTHONHOME LD_PRELOAD LD_LIBRARY_PATH
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
owner_repo="$(cd -- "$script_dir/__ROCS_OWNER_REL__" && pwd)"
repo="${ROCS_REPO:-$owner_repo}"
artifact="$owner_repo/tools/rocs-cli"
export ROCS_REPO="$repo"
export ROCS_WORKSPACE_ROOT="${ROCS_WORKSPACE_ROOT:-$repo}"
export PYTHONDONTWRITEBYTECODE=1
exec python3 -I -S -B -c 'import os; f=os.fdopen(3, "r", encoding="utf-8"); s=f.read(); f.close(); exec(compile(s, "<rocs-sealed-launcher>", "exec"))' "$repo" "$artifact" "$@" 3<<'PY'
from __future__ import annotations

import fcntl
import hashlib
import importlib.machinery
import importlib.util
import json
import os
import signal
import stat
import sys
import time
import traceback
import unicodedata
import zipfile
from pathlib import PurePosixPath

_RECEIPT = "VENDORED_HASHES.json"
_TRUSTED_RECEIPT_SHA256 = "__ROCS_VENDORED_LOCK_SHA256__"
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0)
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
_SEALS = fcntl.F_SEAL_SEAL | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_GROW | fcntl.F_SEAL_WRITE
_ACTIVE_CHILD = 0
_PENDING_SIGNAL = 0
_HANDLED_SIGNALS = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP)


def _fail(message: str) -> SystemExit:
    return SystemExit(f"ROCS bundled runtime invalid: {message}")


def _strict_json(raw: bytes) -> object:
    def pairs(items: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    return json.loads(raw.decode("utf-8", "strict"), object_pairs_hook=pairs)


def _safe_parts(value: object) -> tuple[str, ...]:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError(f"invalid receipt path: {value!r}")
    if unicodedata.normalize("NFC", value) != value or any(ord(character) < 32 for character in value):
        raise ValueError(f"invalid receipt path: {value!r}")
    pure = PurePosixPath(value)
    if pure.is_absolute() or pure.as_posix() != value or "//" in value:
        raise ValueError(f"invalid receipt path: {value!r}")
    if any(part in ("", ".", "..") for part in pure.parts) or value == _RECEIPT:
        raise ValueError(f"invalid receipt path: {value!r}")
    return pure.parts


def _open_dir_at(parent_fd: int, name: str) -> int:
    fd = os.open(name, _DIR_FLAGS, dir_fd=parent_fd)
    opened = os.fstat(fd)
    if not stat.S_ISDIR(opened.st_mode):
        os.close(fd)
        raise ValueError(f"not a directory: {name}")
    return fd


def _open_file_at(root_fd: int, parts: tuple[str, ...]) -> int:
    current = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            following = _open_dir_at(current, part)
            os.close(current)
            current = following
        return os.open(parts[-1], _FILE_FLAGS, dir_fd=current)
    finally:
        os.close(current)


def _read_private_file(fd: int, label: str) -> tuple[bytes, str]:
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode):
        raise ValueError(f"not a regular file: {label}")
    if before.st_nlink != 1:
        raise ValueError(f"multiply linked file: {label}")
    digest = hashlib.sha256()
    chunks: list[bytes] = []
    while True:
        chunk = os.read(fd, 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
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
        raise ValueError(f"file changed during capture: {label}")
    data = b"".join(chunks)
    if len(data) != before.st_size:
        raise ValueError(f"short read: {label}")
    return data, digest.hexdigest()


def _capture_at(root_fd: int, parts: tuple[str, ...], label: str) -> tuple[bytes, str]:
    fd = _open_file_at(root_fd, parts)
    try:
        return _read_private_file(fd, label)
    finally:
        os.close(fd)


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError("short memfd write")
        view = view[written:]


def _sealed_memfd(name: str, data: bytes) -> int:
    if not hasattr(os, "memfd_create") or not hasattr(os, "MFD_ALLOW_SEALING"):
        raise ValueError("sealed anonymous runtime is unsupported")
    fd = os.memfd_create(name, os.MFD_ALLOW_SEALING | getattr(os, "MFD_CLOEXEC", 0))
    try:
        _write_all(fd, data)
        os.fsync(fd)
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, _SEALS)
        if fcntl.fcntl(fd, fcntl.F_GET_SEALS) & _SEALS != _SEALS:
            raise ValueError(f"private runtime seal failed: {name}")
        os.lseek(fd, 0, os.SEEK_SET)
        digest = hashlib.sha256()
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
        if digest.hexdigest() != hashlib.sha256(data).hexdigest():
            raise ValueError(f"private runtime rehash failed: {name}")
        os.lseek(fd, 0, os.SEEK_SET)
        return fd
    except BaseException:
        os.close(fd)
        raise


def _private_archive(files: dict[tuple[str, ...], bytes]) -> int:
    if not hasattr(os, "memfd_create") or not hasattr(os, "MFD_ALLOW_SEALING"):
        raise ValueError("sealed anonymous runtime is unsupported")
    fd = os.memfd_create(
        "rocs-verified-archive", os.MFD_ALLOW_SEALING | getattr(os, "MFD_CLOEXEC", 0)
    )
    try:
        with os.fdopen(os.dup(fd), "w+b") as handle:
            with zipfile.ZipFile(handle, "w", compression=zipfile.ZIP_STORED) as archive:
                for parts in sorted(files, key=lambda value: os.fsencode("/".join(value))):
                    info = zipfile.ZipInfo("/".join(parts), date_time=(1980, 1, 1, 0, 0, 0))
                    info.external_attr = 0o100444 << 16
                    archive.writestr(info, files[parts])
            handle.flush()
            os.fsync(handle.fileno())
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, _SEALS)
        if fcntl.fcntl(fd, fcntl.F_GET_SEALS) & _SEALS != _SEALS:
            raise ValueError("private runtime archive seal failed")
        with os.fdopen(os.dup(fd), "rb") as handle:
            with zipfile.ZipFile(handle, "r") as archive:
                expected_names = {"/".join(parts) for parts in files}
                if set(archive.namelist()) != expected_names:
                    raise ValueError("private runtime archive inventory mismatch")
                for parts, data in files.items():
                    private = archive.read("/".join(parts))
                    if hashlib.sha256(private).digest() != hashlib.sha256(data).digest():
                        raise ValueError(f"private runtime rehash failed: {'/'.join(parts)}")
        return fd
    except BaseException:
        os.close(fd)
        raise


def _extension_name(parts: tuple[str, ...]) -> tuple[str, bool] | None:
    if not parts or parts[0] not in ("runtime", "src"):
        return None
    filename = parts[-1]
    for suffix in importlib.machinery.EXTENSION_SUFFIXES:
        if filename.endswith(suffix):
            stem = filename[:-len(suffix)]
            if stem == "__init__":
                return ".".join(parts[1:-1]), True
            return ".".join((*parts[1:-1], stem)), False
    return None


class _SealedExtensionFinder:
    def __init__(self, paths: dict[str, tuple[str, bool]]) -> None:
        self.paths = paths

    def find_spec(self, fullname: str, path: object = None, target: object = None) -> object:
        entry = self.paths.get(fullname)
        if entry is None:
            return None
        private_path, is_package = entry
        loader = importlib.machinery.ExtensionFileLoader(fullname, private_path)
        return importlib.util.spec_from_loader(fullname, loader, is_package=is_package)


def _exit_code(value: object) -> int:
    if value is None:
        return 0
    if isinstance(value, int):
        return value
    print(value, file=sys.stderr)
    return 1


def _run_captured_argv(arguments: list[str]) -> int:
    global _ACTIVE_CHILD, _PENDING_SIGNAL
    sys.stdout.flush()
    sys.stderr.flush()
    previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK, _HANDLED_SIGNALS)
    try:
        child = os.fork()
    except BaseException:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        raise
    if child == 0:
        signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
        status = 1
        try:
            sys.argv = ["rocs", *arguments]
            from rocs_cli.__main__ import main
            main()
            status = 0
        except SystemExit as exc:
            status = _exit_code(exc.code)
        except BaseException:
            traceback.print_exc()
            status = 1
        finally:
            sys.stdout.flush()
            sys.stderr.flush()
        os._exit(status)
    _ACTIVE_CHILD = child
    signal.pthread_sigmask(signal.SIG_SETMASK, previous_mask)
    deadline: float | None = None
    try:
        while True:
            try:
                waited, wait_status = os.waitpid(child, os.WNOHANG)
            except InterruptedError:
                continue
            if waited == child:
                break
            if _PENDING_SIGNAL:
                if deadline is None:
                    deadline = time.monotonic() + 5.0
                elif time.monotonic() >= deadline:
                    try:
                        os.kill(child, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    while True:
                        try:
                            _waited, wait_status = os.waitpid(child, 0)
                            break
                        except InterruptedError:
                            continue
                    break
            time.sleep(0.01)
    finally:
        _ACTIVE_CHILD = 0
    pending = _PENDING_SIGNAL
    _PENDING_SIGNAL = 0
    if pending:
        raise SystemExit(128 + pending)
    code = os.waitstatus_to_exitcode(wait_status)
    return 128 + (-code) if code < 0 else code


def _forward_signal(signum: int, _frame: object) -> None:
    global _PENDING_SIGNAL
    if not _ACTIVE_CHILD:
        raise SystemExit(128 + signum)
    forwarded = signum if not _PENDING_SIGNAL else signal.SIGKILL
    _PENDING_SIGNAL = _PENDING_SIGNAL or signum
    try:
        os.kill(_ACTIVE_CHILD, forwarded)
    except ProcessLookupError:
        pass


def _main() -> int:
    repo = os.path.abspath(sys.argv[1])
    artifact = os.path.abspath(sys.argv[2])
    root_fd = os.open(artifact, _DIR_FLAGS)
    try:
        receipt_bytes, receipt_digest = _capture_at(root_fd, (_RECEIPT,), _RECEIPT)
        if receipt_digest != _TRUSTED_RECEIPT_SHA256:
            raise ValueError("receipt digest does not match generated trust anchor")
        payload = _strict_json(receipt_bytes)
        if type(payload) is not dict or payload.get("schema_version") not in (2, 3):
            raise ValueError("receipt schema is not a supported self-contained bundle")
        if payload.get("artifact") != "rocs-cli-self-contained":
            raise ValueError("receipt artifact identity is invalid")
        expected = payload.get("files")
        if type(expected) is not dict or not expected:
            raise ValueError("receipt files must be a non-empty object")

        captured: dict[tuple[str, ...], bytes] = {}
        wanted: dict[tuple[str, ...], str] = {}
        for raw_path, raw_digest in expected.items():
            parts = _safe_parts(raw_path)
            if parts in wanted:
                raise ValueError(f"duplicate normalized receipt path: {raw_path}")
            if type(raw_digest) is not str or len(raw_digest) != 64 or any(
                character not in "0123456789abcdef" for character in raw_digest
            ):
                raise ValueError(f"invalid receipt digest: {raw_path}")
            wanted[parts] = raw_digest
        ordered = sorted(wanted, key=lambda parts: os.fsencode("/".join(parts)))
        for index, parts in enumerate(ordered):
            if any(parts[:len(earlier)] == earlier for earlier in ordered[:index]):
                raise ValueError(f"receipt path prefix collision: {'/'.join(parts)}")
            label = "/".join(parts)
            data, digest = _capture_at(root_fd, parts, label)
            if digest != wanted[parts]:
                raise ValueError(f"digest mismatch: {label}")
            captured[parts] = data
    finally:
        os.close(root_fd)

    all_bytes = {**captured, (_RECEIPT,): receipt_bytes}
    archive_fd = _private_archive(all_bytes)
    extension_fds: list[int] = []
    try:
        extension_paths: dict[str, tuple[str, bool]] = {}
        for parts, data in captured.items():
            extension = _extension_name(parts)
            if extension is None:
                continue
            name, is_package = extension
            if not name or name in extension_paths:
                raise ValueError(f"duplicate native extension module: {name!r}")
            fd = _sealed_memfd(f"rocs-extension-{name}", data)
            extension_fds.append(fd)
            extension_paths[name] = f"/proc/self/fd/{fd}", is_package
        sys.meta_path.insert(0, _SealedExtensionFinder(extension_paths))
        sys.path[:0] = [f"/proc/self/fd/{archive_fd}/runtime", f"/proc/self/fd/{archive_fd}/src"]

        if ("rocs.py",) not in captured:
            raise ValueError("receipt is missing rocs.py")
        __ROCS_DISPATCH__
    finally:
        for fd in extension_fds:
            os.close(fd)
        os.close(archive_fd)


for handled_signal in _HANDLED_SIGNALS:
    signal.signal(handled_signal, _forward_signal)
try:
    status = _main()
except (OSError, ValueError, UnicodeDecodeError, json.JSONDecodeError, zipfile.BadZipFile) as exc:
    raise _fail(str(exc)) from exc
raise SystemExit(status)
PY
'''


_FIXED_DISPATCH = '''profile = os.environ.get("ROCS_CI_PROFILE", "local-dev")
        if profile == "local-dev":
            resolve = ["--only", "path"]
        elif profile in ("main-strict", "branch-ci"):
            resolve = ["--resolve-refs", "--workspace-ref-mode", "strict"]
        else:
            print(f"unknown ROCS_CI_PROFILE: {profile}", file=sys.stderr)
            return 2
        if os.environ.get("ROCS_OUTPUT_ROOT"):
            os.environ["ROCS_AUTHORITY_AGGREGATE"] = "1"
        for arguments in (
            ["cleanup", "--repo", repo],
            ["validate", "--repo", repo, "--json", *resolve],
            ["build", "--repo", repo, "--json", *resolve],
        ):
            status = _run_captured_argv(arguments)
            if status:
                return status
        return 0'''
_GENERIC_DISPATCH = "return _run_captured_argv(sys.argv[3:])"


def _render_wrapper(receipt_sha256: str, *, owner_relative: str, dispatch: str) -> str:
    if _HEX64_RE.fullmatch(receipt_sha256) is None:
        raise ValueError("receipt_sha256 must be lowercase SHA-256 hex")
    return (_WRAPPER.replace(_LOCK_DIGEST_TOKEN, receipt_sha256)
            .replace(_OWNER_REL_TOKEN, owner_relative).replace(_DISPATCH_TOKEN, dispatch))


def render_ci_wrapper(receipt_sha256: str) -> str:
    """Bind one generated fixed gate to an exact vendored receipt."""
    return _render_wrapper(receipt_sha256, owner_relative="../..", dispatch=_FIXED_DISPATCH)


def render_cli_wrapper(receipt_sha256: str) -> str:
    """Bind one generic argv-preserving launcher to an exact vendored receipt."""
    return _render_wrapper(receipt_sha256, owner_relative="..", dispatch=_GENERIC_DISPATCH)
