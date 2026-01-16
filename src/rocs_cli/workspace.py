from __future__ import annotations

import os
import subprocess
from pathlib import Path

from rocs_cli.errors import RocsCliError


def workspace_root_from_env() -> Path | None:
    raw = (os.environ.get("ROCS_WORKSPACE_ROOT") or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def workspace_ref_mode_from_env() -> str | None:
    raw = (os.environ.get("ROCS_WORKSPACE_REF_MODE") or "").strip().lower()
    if raw in ("strict", "loose"):
        return raw
    return None


def workspace_repo_candidates(workspace_root: Path, project_path: str) -> list[Path]:
    pp = project_path.strip().strip("/")
    if not pp:
        return []

    parts = [p for p in pp.split("/") if p]
    candidates: list[Path] = []

    candidates.append((workspace_root / Path(*parts)).resolve())
    if len(parts) >= 2:
        candidates.append((workspace_root / Path(*parts[1:])).resolve())

    out: list[Path] = []
    seen: set[Path] = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


def pick_workspace_repo_root(workspace_root: Path, project_path: str) -> Path | None:
    existing = [p for p in workspace_repo_candidates(workspace_root, project_path) if p.exists() and p.is_dir()]
    if not existing:
        return None
    if len(existing) == 1:
        repo = existing[0]
        if not (repo / ".git").exists():
            raise RocsCliError(
                kind="config",
                message=f"workspace repo path exists but is not a git repo: {repo}",
                details={"workspace_repo_root": str(repo), "project_path": project_path},
            )
        return repo
    raise RocsCliError(
        kind="config",
        message=f"workspace mapping is ambiguous for {project_path!r} under {workspace_root}",
        details={"workspace_root": str(workspace_root), "project_path": project_path, "candidates": [str(p) for p in existing]},
    )


def _git(repo_root: Path, args: list[str]) -> str | None:
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except FileNotFoundError as e:
        raise RocsCliError(kind="config", message="git is required for workspace ref checks but was not found") from e
    if r.returncode != 0:
        return None
    return (r.stdout or "").strip()


def git_head_sha(repo_root: Path) -> str | None:
    return _git(repo_root, ["rev-parse", "HEAD"])


def git_rev_sha(repo_root: Path, ref: str) -> str | None:
    ref = ref.strip()
    if not ref:
        return None
    return _git(repo_root, ["rev-parse", f"{ref}^{{commit}}"])
