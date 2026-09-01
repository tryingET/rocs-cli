from __future__ import annotations

import contextlib
import ctypes
import shutil
import json
import os
import secrets
import stat
from pathlib import Path
from typing import Any

import yaml

from rocs_cli.errors import RocsCliError


KNOWN_COMPANIES: tuple[str, ...] = ("holdingco", "softwareco", "healthco")

ROCS_OUTPUT_ROOT_ENV = "ROCS_OUTPUT_ROOT"
ROCS_OUTPUT_MARKER = ".rocs-output-root.json"
ROCS_OUTPUT_MARKER_SCHEMA = "rocs-managed-output-root/1"
MANAGED_OUTPUT_FILES = frozenset({
    "authority-receipt.json", "authority-receipt.validate.json",
    "authority-receipt.build.json", "resolve.json", "summary.json",
    "id_index.json", "graph.json", "graph.dot", "graph.excalidraw-cli.json",
    "graph.excalidraw.json", "diff.json",
})
MANAGED_OUTPUT_LOCK = ".authority-receipt.lock"


def _root_layout_source_surfaces(root: Path) -> tuple[Path, ...]:
    manifest = root / "manifest.yaml"
    if not manifest.exists():
        manifest = root / "manifest.yml"
    surfaces: list[Path] = [root / "manifest.yaml", root / "manifest.yml"]
    try:
        mode = os.lstat(manifest).st_mode
        if stat.S_ISLNK(mode) or not stat.S_ISREG(mode):
            raise RocsCliError(kind="config", message="root ontology manifest must be regular")
        payload = yaml.safe_load(manifest.read_text("utf-8")) or {}
    except FileNotFoundError:
        return (*surfaces, root / "src")
    except (OSError, UnicodeError, yaml.YAMLError) as exc:
        raise RocsCliError(kind="config", message="unable to inspect root ontology source paths") from exc
    rocs = payload.get("rocs") if isinstance(payload, dict) else None
    layers = rocs.get("layers") if isinstance(rocs, dict) else None
    found = False
    if isinstance(layers, list):
        for layer in layers:
            if isinstance(layer, dict) and "path" in layer:
                value = Path(str(layer["path"]))
                source = value if value.is_absolute() else root / value
                surfaces.append(source.resolve(strict=False))
                found = True
    if not found:
        surfaces.append(root / "src")
    return tuple(surfaces)


def configured_output_root(root: Path, ontology: Path) -> Path | None:
    """Resolve and preflight the explicit parent-owned managed output directory."""
    raw = (os.environ.get(ROCS_OUTPUT_ROOT_ENV) or "").strip()
    if not raw:
        return None
    lexical = Path(raw).expanduser()
    if ".." in lexical.parts:
        raise RocsCliError(kind="config", message="ROCS_OUTPUT_ROOT may not traverse with '..'")
    root = root.expanduser().resolve()
    ontology = ontology.expanduser().resolve()
    candidate = lexical if lexical.is_absolute() else root / lexical
    try:
        lexical_rel = candidate.absolute().relative_to(root)
    except ValueError as exc:
        raise RocsCliError(kind="config", message="ROCS_OUTPUT_ROOT must stay inside --repo") from exc
    current = root
    for part in lexical_rel.parts:
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise RocsCliError(kind="config", message=f"ROCS_OUTPUT_ROOT path is unreadable: {current}") from exc
        if stat.S_ISLNK(mode):
            raise RocsCliError(kind="config", message=f"ROCS_OUTPUT_ROOT path is a symlink: {current}")
        if not stat.S_ISDIR(mode):
            raise RocsCliError(kind="config", message=f"ROCS_OUTPUT_ROOT path is not a directory: {current}")
    resolved = candidate.resolve(strict=False)
    try:
        rel = resolved.relative_to(root)
    except ValueError as exc:
        raise RocsCliError(kind="config", message="ROCS_OUTPUT_ROOT must stay inside --repo") from exc
    if not rel.parts:
        raise RocsCliError(kind="config", message="ROCS_OUTPUT_ROOT may not be the repository root")
    if lexical_rel.parts[0] in {".git", "scripts"} or rel.parts[0] in {".git", "scripts"}:
        raise RocsCliError(kind="config", message=f"ROCS_OUTPUT_ROOT uses reserved path: {rel.parts[0]}")
    protected = _root_layout_source_surfaces(root) if ontology == root else (ontology,)
    if any(resolved == item or _is_within(resolved, item) or _is_within(item, resolved) for item in protected):
        raise RocsCliError(kind="config", message="ROCS_OUTPUT_ROOT must be disjoint from ontology source")
    return resolved


def _is_within(path: Path, parent: Path) -> bool:
    return path.is_relative_to(parent)


def _is_managed_transient(name: str) -> bool:
    for base in MANAGED_OUTPUT_FILES:
        prefix = f".{base}.rocs-"
        if name.startswith(prefix):
            pid, separator, token = name[len(prefix):].partition("-")
            return bool(separator and pid.isascii() and pid.isdigit() and not pid.startswith("0")
                        and len(token) == 12 and all(ch in "0123456789abcdef" for ch in token))
    return False


def _cleanup_quarantine_identity(name: str) -> tuple[int, int] | None:
    prefix = ".rocs-cleanup-quarantine-"
    parts = name[len(prefix):].split("-") if name.startswith(prefix) else []
    if len(parts) != 4:
        return None
    device, inode, pid, token = parts
    if not (device and inode and all(ch in "0123456789abcdef" for ch in device + inode)
            and pid.isascii() and pid.isdigit() and not pid.startswith("0")
            and len(token) == 24 and all(ch in "0123456789abcdef" for ch in token)):
        return None
    return int(device, 16), int(inode, 16)


def _require_managed_output_file(path: Path, configured: Path) -> str:
    try:
        relative = path.expanduser().absolute().relative_to(configured)
    except ValueError as exc:
        raise RocsCliError(kind="config", message="managed output file escapes configured root") from exc
    if len(relative.parts) != 1 or relative.name not in MANAGED_OUTPUT_FILES | {MANAGED_OUTPUT_LOCK}:
        raise RocsCliError(kind="config", message=f"unknown managed output filename: {relative.as_posix()}")
    return relative.name


def _output_marker_payload(root: Path, output: Path) -> dict[str, object]:
    return {"schema": ROCS_OUTPUT_MARKER_SCHEMA, "purpose": "rocs-managed-output", "path": output.relative_to(root).as_posix()}


_DIRECTORY_FLAGS = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)


def _listdir_at(descriptor: int) -> list[str]:
    scan = os.open(".", _DIRECTORY_FLAGS, dir_fd=descriptor)
    try:
        return sorted(os.listdir(scan))
    finally:
        os.close(scan)


def _stat_identity(value: os.stat_result) -> tuple[int, ...]:
    return (value.st_dev, value.st_ino, value.st_mode, value.st_nlink,
            value.st_size, value.st_mtime_ns, value.st_ctime_ns)


@contextlib.contextmanager
def _external_output_fds(root: Path, output: Path, *, create: bool):
    root = root.expanduser().resolve()
    output = output.expanduser().absolute()
    parts = output.relative_to(root).parts
    descriptors = [os.open(root, _DIRECTORY_FLAGS)]
    try:
        for part in parts:
            try:
                descriptor = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptors[-1])
            except FileNotFoundError:
                if not create:
                    raise
                os.mkdir(part, 0o755, dir_fd=descriptors[-1])
                descriptor = os.open(part, _DIRECTORY_FLAGS, dir_fd=descriptors[-1])
            except OSError as exc:
                raise RocsCliError(
                    kind="config", message=f"external ROCS output path is unsafe: {output}"
                ) from exc
            descriptors.append(descriptor)
    except BaseException:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
        raise
    try:
        yield descriptors[-1], descriptors[-2], parts[-1]
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)


def _read_marker_at(
    root: Path, output: Path, descriptor: int
) -> tuple[dict[str, object], tuple[int, ...]]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NONBLOCK", 0)
    try:
        marker_fd = os.open(ROCS_OUTPUT_MARKER, flags, dir_fd=descriptor)
    except FileNotFoundError as exc:
        raise RocsCliError(kind="config", message=f"external ROCS output root is unmarked: {output}") from exc
    except OSError as exc:
        raise RocsCliError(kind="config", message="external ROCS output marker path is unsafe") from exc
    try:
        marker_stat = os.fstat(marker_fd)
        if not stat.S_ISREG(marker_stat.st_mode) or marker_stat.st_nlink != 1:
            raise RocsCliError(kind="config", message="external ROCS output marker is not a private regular file")
        data = os.read(marker_fd, 16385)
        if len(data) > 16384:
            raise RocsCliError(kind="config", message="external ROCS output marker is too large")
        payload = json.loads(data.decode("utf-8"))
        marker_after = os.fstat(marker_fd)
        if _stat_identity(marker_stat) != _stat_identity(marker_after):
            raise RocsCliError(kind="config", message="external ROCS output marker changed during read")
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RocsCliError(kind="config", message="external ROCS output marker is invalid") from exc
    finally:
        os.close(marker_fd)
    expected = _output_marker_payload(root, output)
    if payload != expected:
        raise RocsCliError(kind="config", message="external ROCS output marker identity mismatch")
    return payload, _stat_identity(marker_after)


def _ensure_marker_at(root: Path, output: Path, descriptor: int) -> None:
    names = _listdir_at(descriptor)
    if ROCS_OUTPUT_MARKER in names:
        _read_marker_at(root, output, descriptor)
        return
    if names:
        raise RocsCliError(kind="config", message=f"external ROCS output root is nonempty and unmarked: {output}")
    payload = (json.dumps(_output_marker_payload(root, output), indent=2, sort_keys=True) + "\n").encode()
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        marker_fd = os.open(ROCS_OUTPUT_MARKER, flags, 0o644, dir_fd=descriptor)
    except FileExistsError:
        _read_marker_at(root, output, descriptor)
        return
    try:
        os.write(marker_fd, payload)
        os.fsync(marker_fd)
    finally:
        os.close(marker_fd)
    os.fsync(descriptor)


def _verify_external_binding(root: Path, output: Path, before: os.stat_result) -> None:
    with _external_output_fds(root, output, create=False) as (current, _parent, _name):
        after = os.fstat(current)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise RocsCliError(kind="config", message="external ROCS output root changed during operation")


def ensure_external_output_root(root: Path, output: Path) -> Path:
    root = root.expanduser().resolve()
    configured = _configured_root(root)
    if configured is None or output.expanduser().absolute() != configured:
        raise RocsCliError(kind="config", message="external ROCS output root is not configured")
    with _external_output_fds(root, configured, create=True) as (descriptor, _parent, _name):
        _ensure_marker_at(root, configured, descriptor)
        before = os.fstat(descriptor)
        os.fsync(descriptor)
        _verify_external_binding(root, configured, before)
    return output


def _cleanup_inventory(descriptor: int) -> tuple[dict[str, tuple[int, ...]], set[str]]:
    identities: dict[str, tuple[int, ...]] = {}
    deletable: set[str] = set()
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
    for entry in _listdir_at(descriptor):
        quarantine_identity = _cleanup_quarantine_identity(entry)
        delete = entry in MANAGED_OUTPUT_FILES or _is_managed_transient(entry) or quarantine_identity is not None
        if not delete and entry not in {ROCS_OUTPUT_MARKER, MANAGED_OUTPUT_LOCK}:
            raise RocsCliError(kind="config", message=f"external ROCS output contains unknown file: {entry}")
        try:
            file_fd = os.open(entry, flags, dir_fd=descriptor)
        except OSError as exc:
            raise RocsCliError(kind="config", message=f"external ROCS output entry is unsafe: {entry}") from exc
        try:
            opened = os.fstat(file_fd)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise RocsCliError(kind="config", message=f"external ROCS output entry is not private: {entry}")
            identities[entry] = _stat_identity(opened)
            if quarantine_identity is not None and (opened.st_dev, opened.st_ino) != quarantine_identity:
                raise RocsCliError(kind="config", message=f"cleanup quarantine identity mismatch: {entry}")
            if delete:
                deletable.add(entry)
        finally:
            os.close(file_fd)
    return identities, deletable


def _rename_noreplace(descriptor: int, source: str, target: str) -> None:
    renameat2 = getattr(ctypes.CDLL(None, use_errno=True), "renameat2", None)
    if renameat2 is None:
        raise RocsCliError(kind="config", message="atomic cleanup quarantine is unsupported")
    if renameat2(descriptor, os.fsencode(source), descriptor, os.fsencode(target), 1) != 0:
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error), target)


def _quarantine_unlink(
    descriptor: int, entry: str, file_fd: int, identity: tuple[int, ...]
) -> None:
    quarantine = (f".rocs-cleanup-quarantine-{identity[0]:x}-{identity[1]:x}-"
                  f"{os.getpid()}-{secrets.token_hex(12)}")
    _rename_noreplace(descriptor, entry, quarantine)
    moved = os.stat(quarantine, dir_fd=descriptor, follow_symlinks=False)
    pinned = os.fstat(file_fd)
    pinned_identity = (pinned.st_dev, pinned.st_ino, pinned.st_mode,
                       pinned.st_nlink, pinned.st_size, pinned.st_mtime_ns)
    if ((moved.st_dev, moved.st_ino) != (pinned.st_dev, pinned.st_ino)
            or pinned_identity != identity[:-1]):
        raise RocsCliError(kind="config", message=f"external ROCS output changed: {entry}")
    os.unlink(quarantine, dir_fd=descriptor)


def clear_managed_output_root(
    root: Path, output: Path, *, remove_root: bool, dry_run: bool = False
) -> None:
    root = root.expanduser().resolve()
    configured = _configured_root(root)
    if configured is None or output.expanduser().absolute() != configured:
        if not dry_run and output.exists():
            shutil.rmtree(output) if output.is_dir() else output.unlink()
        return
    _ = remove_root  # External marker directories and the stable lock persist.
    with _external_output_fds(root, configured, create=False) as (descriptor, _parent, _name):
        _marker, marker_identity = _read_marker_at(root, configured, descriptor)
        before = os.fstat(descriptor)
        first, first_deletable = _cleanup_inventory(descriptor)
        if first.get(ROCS_OUTPUT_MARKER) != marker_identity:
            raise RocsCliError(kind="config", message="external ROCS output marker changed after validation")
        second, deletable = _cleanup_inventory(descriptor)
        if first != second or first_deletable != deletable:
            raise RocsCliError(kind="config", message="external ROCS output changed during cleanup preflight")
        _verify_external_binding(root, configured, before)
        if dry_run:
            return
        opened: dict[str, int] = {}
        try:
            for entry in sorted(deletable):
                fd = os.open(entry, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0), dir_fd=descriptor)
                current = os.fstat(fd)
                current_identity = (current.st_dev, current.st_ino, current.st_mode,
                                    current.st_nlink, current.st_size,
                                    current.st_mtime_ns, current.st_ctime_ns)
                if current_identity != second[entry] or current.st_nlink != 1:
                    os.close(fd)
                    raise RocsCliError(kind="config", message=f"external ROCS output changed: {entry}")
                opened[entry] = fd
            current, current_deletable = _cleanup_inventory(descriptor)
            if current != second or current_deletable != deletable:
                raise RocsCliError(kind="config", message="external ROCS output changed before cleanup")
            for entry, fd in opened.items():
                _quarantine_unlink(descriptor, entry, fd, second[entry])
        finally:
            for fd in opened.values():
                os.close(fd)
        retained = {name: identity for name, identity in first.items() if name not in deletable}
        final, final_deletable = _cleanup_inventory(descriptor)
        if final != retained or final_deletable:
            raise RocsCliError(kind="config", message="external ROCS output changed during cleanup")
        os.fsync(descriptor)
        _verify_external_binding(root, configured, before)


@contextlib.contextmanager
def open_managed_output(root: Path, path: Path, mode: str):
    root = root.expanduser().resolve()
    configured = _configured_root(root)
    if configured is None or not _is_within(path.expanduser().absolute(), configured):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open(mode, encoding="utf-8") as stream:
            yield stream
        return
    name = _require_managed_output_file(path, configured)
    flags_by_mode = {"r": os.O_RDONLY, "a+": os.O_RDWR | os.O_CREAT | os.O_APPEND}
    if mode not in flags_by_mode:
        raise ValueError(f"unsupported managed output mode: {mode}")
    with _external_output_fds(root, configured, create=True) as (descriptor, _parent, _name):
        _ensure_marker_at(root, configured, descriptor)
        before = os.fstat(descriptor)
        flags = (
            flags_by_mode[mode]
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        try:
            file_fd = os.open(name, flags, 0o644, dir_fd=descriptor)
        except FileNotFoundError:
            raise
        except OSError as exc:
            raise RocsCliError(kind="config", message=f"managed output path is unsafe: {name}") from exc
        file_stat = os.fstat(file_fd)
        if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_nlink != 1:
            os.close(file_fd)
            raise RocsCliError(kind="config", message=f"managed output is not a private regular file: {name}")
        with os.fdopen(file_fd, mode, encoding="utf-8") as stream:
            yield stream
            if mode != "r":
                stream.flush()
                os.fsync(stream.fileno())
        _verify_external_binding(root, configured, before)


def read_managed_output_text(root: Path, path: Path) -> str | None:
    try:
        with open_managed_output(root, path, "r") as stream:
            return stream.read()
    except FileNotFoundError:
        return None


def write_managed_output_text(root: Path, path: Path, text: str) -> None:
    root = root.expanduser().resolve()
    configured = _configured_root(root)
    if configured is None or not _is_within(path.expanduser().absolute(), configured):
        path.write_text(text, "utf-8")
        return
    name = _require_managed_output_file(path, configured)
    with _external_output_fds(root, configured, create=True) as (descriptor, _parent, _name):
        _ensure_marker_at(root, configured, descriptor)
        before = os.fstat(descriptor)
        temporary = f".{name}.rocs-{os.getpid()}-{secrets.token_hex(6)}"
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        file_fd = os.open(temporary, flags, 0o644, dir_fd=descriptor)
        try:
            with os.fdopen(file_fd, "w", encoding="utf-8") as stream:
                stream.write(text)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, name, src_dir_fd=descriptor, dst_dir_fd=descriptor)
        except BaseException:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary, dir_fd=descriptor)
            raise
        os.fsync(descriptor)
        _verify_external_binding(root, configured, before)


def unlink_managed_output(root: Path, path: Path) -> None:
    configured = _configured_root(root.expanduser().resolve())
    if configured is None or not _is_within(path.expanduser().absolute(), configured):
        path.unlink(missing_ok=True)
        return
    name = _require_managed_output_file(path, configured)
    with _external_output_fds(root.expanduser().resolve(), configured, create=True) as (descriptor, _p, _n):
        _ensure_marker_at(root.expanduser().resolve(), configured, descriptor)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            file_fd = os.open(name, flags, dir_fd=descriptor)
        except FileNotFoundError:
            return
        try:
            opened = os.fstat(file_fd)
            if not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1:
                raise RocsCliError(kind="config", message=f"managed output is not private regular: {name}")
            _quarantine_unlink(descriptor, name, file_fd, _stat_identity(opened))
        finally:
            os.close(file_fd)
        os.fsync(descriptor)


def list_managed_output_names(root: Path, output: Path) -> list[str]:
    configured = _configured_root(root.expanduser().resolve())
    if configured is None or output.expanduser().absolute() != configured:
        return sorted(path.name for path in output.iterdir()) if output.exists() else []
    with _external_output_fds(root.expanduser().resolve(), configured, create=True) as (descriptor, _p, _n):
        _ensure_marker_at(root.expanduser().resolve(), configured, descriptor)
        return _listdir_at(descriptor)


def _configured_root(root: Path) -> Path | None:
    # Lazy import avoids a module cycle: layers owns ontology layout selection.
    from rocs_cli.layers import ontology_root

    canonical = root.expanduser().resolve()
    return configured_output_root(canonical, ontology_root(canonical))


def _hash_comment_index(line: str) -> int | None:
    in_single = False
    in_double = False
    escaped = False
    prev = ""

    for idx, ch in enumerate(line):
        if escaped:
            escaped = False
            prev = ch
            continue
        if ch == "\\" and in_double:
            escaped = True
            prev = ch
            continue
        if ch == "'" and not in_double:
            in_single = not in_single
            prev = ch
            continue
        if ch == '"' and not in_single:
            in_double = not in_double
            prev = ch
            continue
        if ch == "#" and not in_single and not in_double and (idx == 0 or prev.isspace()):
            return idx
        prev = ch

    return None


def strip_inline_hash_comment(line: str) -> str:
    idx = _hash_comment_index(line)
    if idx is None:
        return line
    return line[:idx].rstrip()


def strip_hash_comments(text: str) -> str:
    out: list[str] = []
    for raw in text.splitlines():
        out.append(strip_inline_hash_comment(raw))
    return "\n".join(out)


def normalize_shell_lines(text: str) -> list[str]:
    lines: list[str] = []
    for raw in strip_hash_comments(text).splitlines():
        line = raw.strip()
        if line:
            lines.append(line)
    return lines


def _iter_scalar_strings(value: Any):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for key, nested in value.items():
            yield from _iter_scalar_strings(key)
            yield from _iter_scalar_strings(nested)
        return
    if isinstance(value, list):
        for nested in value:
            yield from _iter_scalar_strings(nested)


def yaml_scalar_strings(text: str) -> list[str] | None:
    try:
        loaded = yaml.safe_load(text)
    except yaml.YAMLError:
        return None
    if loaded is None:
        return []
    return list(_iter_scalar_strings(loaded))


def ensure_managed_output_dir(root: Path, path: Path, *, label: str) -> Path:
    root = root.expanduser().resolve()
    path = path.expanduser()
    configured = _configured_root(root)
    if configured is not None and path.absolute() == configured:
        return ensure_external_output_root(root, configured)
    blocker = managed_path_blocker(root, path / ".rocs-write-probe")
    if blocker is not None:
        raise RocsCliError(
            kind="config",
            message=f"{label} is not writable: {path} ({blocker})",
            details={"path": str(path), "blocker": blocker},
        )
    path.mkdir(parents=True, exist_ok=True)
    return path


def ensure_managed_output_file(root: Path, path: Path, *, label: str) -> Path:
    root = root.expanduser().resolve()
    path = path.expanduser()
    configured = _configured_root(root)
    if configured is not None and _is_within(path.absolute(), configured):
        _require_managed_output_file(path, configured)
        ensure_external_output_root(root, configured)
    blocker = managed_path_blocker(root, path)
    if blocker is not None:
        raise RocsCliError(
            kind="config",
            message=f"{label} is not writable: {path} ({blocker})",
            details={"path": str(path), "blocker": blocker},
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def managed_path_blocker(root: Path, path: Path) -> str | None:
    try:
        path.relative_to(root)
    except ValueError:
        return "path escapes target root"

    current = root
    try:
        rel = path.relative_to(root)
    except ValueError:
        return "path escapes target root"

    for part in rel.parts[:-1]:
        current = current / part
        try:
            st = os.lstat(current)
        except FileNotFoundError:
            continue
        except OSError as exc:
            detail = exc.strerror or exc.__class__.__name__
            return f"parent path is unreadable: {detail}"
        if stat.S_ISLNK(st.st_mode):
            return f"parent path is a symlink: {current.relative_to(root)}"
        if not stat.S_ISDIR(st.st_mode):
            return f"parent path is not a directory: {current.relative_to(root)}"

    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    except OSError as exc:
        detail = exc.strerror or exc.__class__.__name__
        return f"path is unreadable: {detail}"

    if stat.S_ISLNK(st.st_mode):
        return "path is a symlink"
    if stat.S_ISDIR(st.st_mode):
        return "path is a directory"
    if not stat.S_ISREG(st.st_mode):
        return "path is not a regular file"
    return None


def infer_company_from_parts(path: Path) -> str | None:
    for company in KNOWN_COMPANIES:
        if company in path.parts:
            return company
    return None


def workspace_company_inference_is_ambiguous(path: Path) -> bool:
    return "ai-society" in path.parts and infer_company_from_parts(path) is None
