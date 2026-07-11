from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from pathlib import Path


CORE_VENDORED_FILES: tuple[Path, ...] = (
    Path("pyproject.toml"),
    Path("README.md"),
)
PINNED_VENDORED_FILES: tuple[Path, ...] = (Path("uv.lock"), Path("rocs.py"))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


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
    relpaths: list[Path] = list(CORE_VENDORED_FILES)
    relpaths.extend(path for path in PINNED_VENDORED_FILES if (vendored_dir / path).is_file())
    for src_root in (vendored_dir / "src" / "rocs_cli", vendored_dir / "runtime"):
        if src_root.exists():
            for p in sorted(src_root.rglob("*")):
                if "__pycache__" in p.parts:
                    continue
                if p.is_file() and not p.is_symlink():
                    relpaths.append(p.relative_to(vendored_dir))
    return relpaths


def _safe_manifest_relpath(value: object) -> Path | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = Path(value)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        return None
    if path not in CORE_VENDORED_FILES and path not in PINNED_VENDORED_FILES and not (
        (len(path.parts) >= 3 and path.parts[:2] == ("src", "rocs_cli"))
        or (len(path.parts) >= 2 and path.parts[0] == "runtime")
    ):
        return None
    return path


def compute_expected_hashes(vendored_dir: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    for rel in iter_vendored_relpaths(vendored_dir):
        out[str(rel)] = sha256_file(vendored_dir / rel)
    return out


def read_vendored_hashes(vendored_dir: Path) -> dict:
    p = vendored_dir / "VENDORED_HASHES.json"
    if not p.exists():
        raise FileNotFoundError(str(p))
    return json.loads(p.read_text("utf-8"))


def verify_vendored_hashes(vendored_dir: Path) -> tuple[bool, list[str]]:
    try:
        data = read_vendored_hashes(vendored_dir)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        return False, [f"invalid VENDORED_HASHES.json: {exc}"]
    if not isinstance(data, dict):
        return False, ["invalid VENDORED_HASHES.json: root must be an object"]
    schema = data.get("schema_version")
    fields = {"schema_version", "upstream_project", "upstream_version", "files"}
    if schema == 2:
        fields.add("artifact")
        if data.get("artifact") != "rocs-cli-self-contained":
            return False, ["invalid VENDORED_HASHES.json: unknown artifact identity"]
    if set(data) != fields:
        return False, ["invalid VENDORED_HASHES.json: unexpected or missing fields"]
    if schema not in (1, 2):
        return False, [f"unsupported schema_version: {schema!r}"]
    expected = data.get("files")
    if not isinstance(expected, dict) or not expected:
        return False, ["invalid VENDORED_HASHES.json: 'files' must be a non-empty mapping"]

    lines: list[str] = []
    normalized: dict[str, str] = {}
    for raw_rel, want in expected.items():
        rel = _safe_manifest_relpath(raw_rel)
        if rel is None:
            lines.append(f"invalid path: {raw_rel!r}")
            continue
        if not isinstance(want, str) or re.fullmatch(r"[0-9a-f]{64}", want) is None:
            lines.append(f"invalid sha256: {raw_rel}")
            continue
        normalized[str(rel)] = want

    actual_paths = {str(rel) for rel in iter_vendored_relpaths(vendored_dir)}
    expected_paths = set(normalized)
    required = CORE_VENDORED_FILES + (PINNED_VENDORED_FILES if schema == 2 else ())
    required_paths = {str(path) for path in required}
    for rel in sorted(required_paths - actual_paths):
        lines.append(f"missing required: {rel}")
    if not any(rel.startswith("src/rocs_cli/") for rel in actual_paths):
        lines.append("missing required: src/rocs_cli package files")
    for path in sorted(vendored_dir.rglob("*")):
        rel = str(path.relative_to(vendored_dir))
        try:
            mode = os.lstat(path).st_mode
        except OSError as exc:
            lines.append(f"unreadable: {rel} ({exc})")
            continue
        if stat.S_ISDIR(mode):
            continue
        if rel == "VENDORED_HASHES.json" and stat.S_ISREG(mode):
            continue
        if not stat.S_ISREG(mode):
            lines.append(f"invalid file type: {rel}")
        elif rel not in actual_paths:
            lines.append(f"unexpected: {rel}")
    for rel in sorted(actual_paths - expected_paths):
        lines.append(f"unexpected: {rel}")
    for rel in sorted(expected_paths - actual_paths):
        lines.append(f"missing: {rel}")

    for rel in sorted(actual_paths & expected_paths):
        p = vendored_dir / rel
        try:
            mode = os.lstat(p).st_mode
        except OSError as exc:
            lines.append(f"unreadable: {rel} ({exc})")
            continue
        if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
            lines.append(f"invalid file type: {rel}")
            continue
        got = sha256_file(p)
        if got != normalized[rel]:
            lines.append(f"mismatch: {rel} expected={normalized[rel]} got={got}")

    return not lines, lines or [f"ok: {rel} {normalized[rel]}" for rel in sorted(normalized)]
