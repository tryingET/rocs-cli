from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from rocs_cli.errors import RocsCliError


# Git exports repository-local variables while running hooks. Those variables
# override `git -C <foreign-repo>` unless they are removed from the child
# environment. Keep this aligned with `git rev-parse --local-env-vars`.
_GIT_REPOSITORY_LOCAL_ENV_VARS = frozenset(
    {
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_COMMON_DIR",
        "GIT_CONFIG",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_PARAMETERS",
        "GIT_DIR",
        "GIT_GRAFT_FILE",
        "GIT_IMPLICIT_WORK_TREE",
        "GIT_INDEX_FILE",
        "GIT_NO_REPLACE_OBJECTS",
        "GIT_OBJECT_DIRECTORY",
        "GIT_PREFIX",
        "GIT_REPLACE_REF_BASE",
        "GIT_SHALLOW_FILE",
        "GIT_WORK_TREE",
    }
)


def workspace_root_from_env() -> Path | None:
    raw = (os.environ.get("ROCS_WORKSPACE_ROOT") or "").strip()
    if not raw:
        return None
    return Path(raw).expanduser().resolve()


def resolve_refs_default_from_env() -> bool:
    """`ROCS_RESOLVE_REFS=1` makes `--resolve-refs` the default; explicit selectors still win."""
    return (os.environ.get("ROCS_RESOLVE_REFS") or "").strip() == "1"


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

    # Support the explicit workspace namespace prefix when a locator uses
    # `<repo:ai-society/...>` or `<repo:<workspace-root-name>/...>` while the
    # local checkout root already points at that namespace directory.
    if len(parts) >= 2 and parts[0] in {"ai-society", workspace_root.name}:
        candidates.append((workspace_root / Path(*parts[1:])).resolve())

    out: list[Path] = []
    seen: set[Path] = set()
    for c in candidates:
        if c in seen:
            continue
        seen.add(c)
        out.append(c)
    return out


_SCP_LIKE_RE = re.compile(r"^(?P<user>[^@]+)@(?P<host>[^:]+):(?P<path>.+)$")


def _project_path_from_remote_url(remote_url: str) -> str | None:
    """
    Extract a workspace-style `<group>/<subgroup>/<repo>` path from common Git remote URL forms:
    - https://host/group/subgroup/repo(.git)
    - http://host/group/subgroup/repo(.git)
    - ssh://git@host/group/subgroup/repo(.git)
    - git@host:group/subgroup/repo(.git)
    """
    raw = (remote_url or "").strip()
    if not raw:
        return None

    try:
        u = urlparse(raw)
    except Exception:
        return None

    if u.scheme in ("http", "https", "ssh"):
        path = (u.path or "").lstrip("/")
        if path.endswith(".git"):
            path = path[: -len(".git")]
        return path or None

    # SCP-like form, e.g. git@host:group/subgroup/repo.git
    # Only attempt this when no URL scheme is present.
    if "://" not in raw:
        m = _SCP_LIKE_RE.match(raw)
        if m:
            path = m.group("path").lstrip("/")
            if path.endswith(".git"):
                path = path[: -len(".git")]
            return path or None

    return None


def _origin_project_path(repo_root: Path) -> str | None:
    url = _git(repo_root, ["config", "--get", "remote.origin.url"])
    return _project_path_from_remote_url(url or "")


def pick_workspace_repo_root(
    workspace_root: Path,
    project_path: str,
    *,
    require_origin_match: bool = True,
) -> Path | None:
    existing = [p for p in workspace_repo_candidates(workspace_root, project_path) if p.exists() and p.is_dir()]
    if not existing:
        return None

    git_repos: list[Path] = []
    for repo in existing:
        if not (repo / ".git").exists():
            continue
        git_repos.append(repo)

    if not git_repos:
        return None

    if not require_origin_match:
        for candidate in workspace_repo_candidates(workspace_root, project_path):
            if candidate in git_repos:
                return candidate
        return None

    matching: list[Path] = []
    for repo in git_repos:
        origin_pp = _origin_project_path(repo)
        if origin_pp == project_path:
            matching.append(repo)

    if not matching:
        return None
    if len(matching) == 1:
        return matching[0]

    raise RocsCliError(
        kind="config",
        message=f"workspace mapping is ambiguous for {project_path!r} under {workspace_root}",
        details={"workspace_root": str(workspace_root), "project_path": project_path, "candidates": [str(p) for p in matching]},
    )


def origin_matches_project_path(repo_root: Path, project_path: str) -> bool:
    """Test helper: true if `remote.origin.url` parses to `project_path`."""
    return _origin_project_path(repo_root) == project_path


def workspace_repo_exists(workspace_root: Path, project_path: str) -> bool:
    """Test helper: true if a workspace repo directory exists (git or not)."""
    return any(p.exists() and p.is_dir() for p in workspace_repo_candidates(workspace_root, project_path))



def _git(repo_root: Path, args: list[str]) -> str | None:
    env = os.environ.copy()
    for name in _GIT_REPOSITORY_LOCAL_ENV_VARS:
        env.pop(name, None)

    try:
        r = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            env=env,
        )
    except FileNotFoundError as e:
        raise RocsCliError(kind="config", message="git is required for workspace ref checks but was not found") from e
    if r.returncode != 0:
        return None
    return (r.stdout or "").strip()


_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_SNAPSHOT_MARKER = ".rocs-workspace-ref-snapshot"


def _tree_spec(rev: str, subpath: str) -> str:
    return f"{rev}:{subpath}" if subpath else f"{rev}^{{tree}}"


def _tree_id(repo_root: Path, spec: str) -> str | None:
    """The object id `spec` names when it is a tree in this clone (a gitlink names a commit)."""
    oid = _git(repo_root, ["rev-parse", "--verify", "-q", spec])
    if not oid or not _HEX40.fullmatch(oid):
        return None
    return oid if _git(repo_root, ["cat-file", "-t", oid]) == "tree" else None


def _layer_read_paths(subpath: str) -> list[str]:
    """What rocs reads for a layer: its manifest (source contract selector) and its src tree."""
    prefix = f"{subpath}/" if subpath else ""
    return [f"{prefix}manifest.yaml", f"{prefix}manifest.yml", f"{prefix}src"]


def _holds_nested_repo(repo_root: Path, subpath: str) -> bool:
    """A nested clone or submodule owns its own files, which the outer tree does not contain."""
    base = repo_root / subpath if subpath else repo_root
    if subpath and (base / ".git").exists():
        return True
    for _dirpath, dirnames, filenames in os.walk(base / "src"):
        if ".git" in dirnames or ".git" in filenames:
            return True
    return False


def _reads_committed_bytes(repo_root: Path, subpath: str) -> bool:
    """True when the working files rocs reads for the layer are exactly the checkout's committed ones.

    `git status` cannot see ignored paths or into a nested repository, so a clean status alone
    does not prove that the files read are the committed tree (AK 6329).
    """
    if _holds_nested_repo(repo_root, subpath):
        return False
    status = _git(repo_root, ["status", "--porcelain", "--untracked-files=all", "--", subpath or "."])
    ignored = _git(
        repo_root,
        ["status", "--porcelain", "--untracked-files=all", "--ignored=matching", "--", *_layer_read_paths(subpath)],
    )
    return status == "" and ignored == ""


def workspace_gitlink(repo_root: Path, commit: str, subpath: str) -> str | None:
    """The submodule commit that `commit` pins at `subpath`, when that path is a gitlink."""
    if not subpath:
        return None
    parts = (_git(repo_root, ["ls-tree", commit, "--", subpath]) or "").split()
    if len(parts) >= 3 and parts[0] == "160000" and _HEX40.fullmatch(parts[2]):
        return parts[2]
    return None


def workspace_ref_binding(repo_root: Path, commit: str, subpath: str) -> dict | None:
    """Where the exact ontology tree of `commit` can be read, or None if `commit` has no layer to read.

    None means the clone has no committed tree for the ontology or for its `src`, so strict mode has
    no bytes to bind. `in_place` is true when the checkout's committed ontology tree equals it and
    the files read for the layer are exactly those bytes; otherwise the tree is read from a snapshot.
    """
    tree = _tree_id(repo_root, _tree_spec(commit, subpath))
    src = f"{subpath}/src" if subpath else "src"
    if tree is None or _tree_id(repo_root, _tree_spec(commit, src)) is None:
        return None
    head_tree = _tree_id(repo_root, _tree_spec("HEAD", subpath))
    in_place = head_tree == tree and _reads_committed_bytes(repo_root, subpath)
    return {"tree": tree, "head_tree": head_tree, "in_place": in_place}


def workspace_ref_snapshot(repo_root: Path, commit: str, subpath: str, tree: str) -> Path:
    """Export the ontology tree of `commit` from a workspace clone into an immutable snapshot.

    Keyed by the tree hash, written once into rocs's local cache, never touching the clone.
    The snapshot keeps the repo layout (`ontology/...` or root) so layer paths resolve as usual.
    """
    import io
    import shutil
    import tarfile
    import tempfile

    from rocs_cli.cache import cache_dir

    if not _HEX40.fullmatch(commit) or not _HEX40.fullmatch(tree):
        raise RocsCliError(kind="config", message="workspace ref snapshot needs full commit and tree ids")
    root = cache_dir() / "workspace-ref-snapshots"
    dest = root / tree
    marker = dest / _SNAPSHOT_MARKER
    if marker.is_file() and marker.read_text("utf-8").strip() == tree:
        return dest
    env = os.environ.copy()
    for name in _GIT_REPOSITORY_LOCAL_ENV_VARS:
        env.pop(name, None)
    args = ["git", "-C", str(repo_root), "archive", "--format=tar", commit]
    if subpath:
        args += ["--", subpath]
    try:
        archive = subprocess.run(args, check=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    except FileNotFoundError as e:
        raise RocsCliError(kind="config", message="git is required for workspace ref snapshots but was not found") from e
    if archive.returncode != 0:
        raise RocsCliError(
            kind="not_found",
            message=f"cannot export workspace ref {commit} from {repo_root}",
            details={"stderr": archive.stderr.decode("utf-8", "replace").strip()},
        )
    root.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{tree}.", dir=root))
    try:
        with tarfile.open(fileobj=io.BytesIO(archive.stdout), mode="r:") as tar:
            tar.extractall(stage, filter="data")
        (stage / _SNAPSHOT_MARKER).write_text(tree + "\n", "utf-8")
        try:
            os.rename(stage, dest)
        except OSError:
            # A concurrent run published the same immutable snapshot first.
            if not (marker.is_file() and marker.read_text("utf-8").strip() == tree):
                raise
            shutil.rmtree(stage, ignore_errors=True)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return dest


def git_head_sha(repo_root: Path) -> str | None:
    return _git(repo_root, ["rev-parse", "--verify", "HEAD^{commit}"])


def git_rev_sha(repo_root: Path, ref: str) -> str | None:
    ref = ref.strip()
    if not ref:
        return None
    # Harden: never treat dash-prefixed strings as revisions.
    if ref.startswith("-"):
        return None
    return _git(repo_root, ["rev-parse", "--verify", f"{ref}^{{commit}}"])
