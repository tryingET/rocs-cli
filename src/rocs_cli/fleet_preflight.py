from __future__ import annotations

import shutil
from pathlib import Path


class FleetPreflightError(ValueError):
    pass


def normalize_policy_repo_path(workspace_root: Path, policy_path: str) -> tuple[Path, str | None]:
    workspace_root = workspace_root.expanduser().resolve()
    raw = (policy_path or "").strip()
    p = Path(raw) if raw else Path()

    if p.is_absolute():
        resolved = p.expanduser().resolve()
    else:
        direct = (workspace_root / p).resolve()
        if direct.exists():
            resolved = direct
        else:
            parts = p.parts
            if parts and parts[0] == workspace_root.name:
                resolved = workspace_root.joinpath(*parts[1:]).resolve()
            else:
                resolved = direct

    if not raw or resolved == workspace_root:
        return resolved, "repo path is empty or resolves to workspace root"

    try:
        resolved.relative_to(workspace_root)
    except ValueError:
        return resolved, "resolved path escapes workspace root"

    return resolved, None


def read_utf8_text(path: Path, *, label: str) -> str:
    try:
        return path.read_text("utf-8")
    except UnicodeDecodeError as exc:
        raise FleetPreflightError(f"{label} is not valid utf-8: {path}") from exc
    except OSError as exc:
        detail = exc.strerror or exc.__class__.__name__
        raise FleetPreflightError(f"could not read {label}: {path} ({detail})") from exc


def remove_stale_artifact(path: Path) -> None:
    try:
        if not path.exists() and not path.is_symlink():
            return
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
            return
        path.unlink()
    except OSError as exc:
        detail = exc.strerror or exc.__class__.__name__
        raise FleetPreflightError(f"could not clear stale artifact: {path} ({detail})") from exc


def validate_bootstrap_script(mode: str, bootstrap_script: Path) -> None:
    if mode != "apply":
        return
    if not bootstrap_script.is_file():
        raise FleetPreflightError(f"bootstrap script not found: {bootstrap_script}")
