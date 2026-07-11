"""Wave 1 operational capabilities.

This module is deliberately independent of the source checkout: every operation is
callable as Python and the CLI is only an adapter.
"""

from __future__ import annotations

import fcntl
import importlib.util
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from rocs_cli import __version__
from rocs_cli.capabilities import class_policy
from rocs_cli.vendored import (
    compute_expected_hashes,
    validate_vendor_source_layout,
    validate_vendor_target,
    verify_vendored_hashes,
)


def _emit(value: dict[str, Any], destination: str = "-") -> None:
    text = json.dumps(value, indent=2, sort_keys=True) + "\n"
    if destination == "-":
        print(text, end="")
    else:
        path = Path(destination).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, "utf-8")


def _remove_path(path: Path) -> None:
    if not path.exists() and not path.is_symlink():
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def _publish_sibling(stage: Path, target: Path, *, fail_point: str | None = None) -> None:
    """Publish a verified sibling stage atomically and restore its preimage on failure."""
    backup = target.parent / f".{target.name}.backup-{os.getpid()}"
    _remove_path(backup)
    had_target = target.exists() or target.is_symlink()
    moved_preimage = False
    published = False
    try:
        if fail_point == "prepublish":
            raise RuntimeError("injected failure before atomic publication")
        if had_target:
            os.replace(target, backup)
            moved_preimage = True
        if fail_point == "publish":
            raise RuntimeError("injected failure during atomic publication")
        os.replace(stage, target)
        published = True
        if fail_point == "after_publish":
            raise RuntimeError("injected failure after atomic publication")
    except BaseException:
        if published:
            _remove_path(target)
        if moved_preimage and backup.exists():
            os.replace(backup, target)
        raise
    else:
        _remove_path(backup)
    finally:
        _remove_path(stage)
        if not published and not moved_preimage:
            _remove_path(backup)


def vendor(source: Path, target: Path, *, version: str | None = None, dry_run: bool = False) -> dict[str, Any]:
    """Publish a pinned, hash-complete consumer tree through a verified sibling stage."""
    source, target = source.resolve(), target.expanduser().resolve()
    pyproject, readme, package = validate_vendor_source_layout(source)
    validate_vendor_target(repo_root=source, target=target)
    effective = version or __version__
    result = {"schema_version": 2, "tool": "rocs-cli", "version": effective, "target": str(target), "dry_run": dry_run}
    if dry_run:
        return result
    target.parent.mkdir(parents=True, exist_ok=True)
    lock_path = target.parent / f".{target.name}.vendor.lock"
    with lock_path.open("a+b") as lock_file:
        fcntl.flock(lock_file, fcntl.LOCK_EX)
        stage = Path(tempfile.mkdtemp(prefix=f".{target.name}.stage-", dir=target.parent))
        try:
            shutil.copytree(package, stage / "src/rocs_cli", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            shutil.copy2(pyproject, stage / "pyproject.toml")
            shutil.copy2(readme, stage / "README.md")
            uv_lock = source / "uv.lock"
            if not uv_lock.is_file():
                raise RuntimeError("self-contained artifact requires uv.lock")
            shutil.copy2(uv_lock, stage / "uv.lock")
            runtime = stage / "runtime"
            runtime.mkdir()
            for module_name in ("yaml", "rich", "markdown_it", "mdurl", "pygments"):
                spec = importlib.util.find_spec(module_name)
                if spec is None or spec.origin is None:
                    raise RuntimeError(f"runtime dependency is unavailable: {module_name}")
                origin = Path(spec.origin)
                if spec.submodule_search_locations:
                    shutil.copytree(origin.parent, runtime / module_name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
                else:
                    shutil.copy2(origin, runtime / origin.name)
            (stage / "rocs.py").write_text(
                "from pathlib import Path\nimport sys\nroot = Path(__file__).resolve().parent\nsys.path[:0] = [str(root / 'runtime'), str(root / 'src')]\nfrom rocs_cli.__main__ import main\nmain()\n",
                "utf-8",
            )
            manifest = {
                "schema_version": 2,
                "artifact": "rocs-cli-self-contained",
                "upstream_project": "ai-society/core/rocs-cli",
                "upstream_version": effective,
                "files": compute_expected_hashes(stage),
            }
            (stage / "VENDORED_HASHES.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", "utf-8")
            ok, errors = verify_vendored_hashes(stage)
            if not ok:
                raise RuntimeError("staged vendor verification failed: " + "; ".join(errors))
            _publish_sibling(stage, target, fail_point=os.environ.get("ROCS_VENDOR_FAIL_AFTER"))
        finally:
            _remove_path(stage)
    return result


def verify(path: Path) -> tuple[dict[str, Any], int]:
    ok, errors = verify_vendored_hashes(path.resolve())
    return {"schema_version": 1, "ok": ok, "path": str(path.resolve()), "errors": errors}, 0 if ok else 1


def _distribution_root() -> Path:
    """Return the self-contained project root containing this package."""
    root = Path(__file__).resolve().parents[2]
    validate_vendor_source_layout(root)
    return root


def _preflight_managed_path(root: Path, rel: str, *, directory: bool = False) -> None:
    current = root
    parts = Path(rel).parts
    for index, part in enumerate(parts):
        current /= part
        try:
            mode = os.lstat(current).st_mode
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(mode):
            raise ValueError(f"managed path is a symlink: {rel}")
        if index < len(parts) - 1 and not stat.S_ISDIR(mode):
            raise ValueError(f"managed parent is not a directory: {rel}")
        if index == len(parts) - 1:
            expected = stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)
            if not expected:
                kind = "directory" if directory else "regular file"
                raise ValueError(f"managed path is not a {kind}: {rel}")


_CI_WRAPPER = """#!/usr/bin/env bash
set -euo pipefail
repo="${ROCS_REPO:-$(pwd)}"
rocs=(uv run --offline --frozen --project "$repo/tools/rocs-cli" python -m rocs_cli)
"${rocs[@]}" cleanup --repo "$repo"
"${rocs[@]}" validate --repo "$repo" --json
"${rocs[@]}" build --repo "$repo" --json
"""


def bootstrap(target: Path, repo_class: str, *, dry_run: bool = False, converge: bool = False) -> dict[str, Any]:
    """Converge a repository transactionally, publishing one verified sibling stage."""
    final_target = target.expanduser().resolve()
    policy = class_policy(repo_class)
    if not final_target.is_dir():
        raise ValueError(f"target repository not found: {final_target}")
    source = _distribution_root()
    managed = [
        "tools/rocs-cli", "ontology/manifest.yaml", "ontology/src/system4d.yaml",
        "scripts/ci/full.sh", ".githooks/pre-push", ".githooks/README.md",
    ]
    legacy = [
        "scripts/audit-fleet.py", "scripts/bootstrap-repo.sh", "scripts/vendor-to.sh",
        "scripts/open-remediation-batch.sh", "scripts/run-fleet-audit-nightly.py",
        "scripts/run-fleet-audit-nightly.sh", "scripts/bump_version.py",
    ]
    changes = list(managed if policy["rocs_cli_vendored"] else []) + [p for p in legacy if (final_target / p).exists()]
    result = {
        "schema_version": 2, "operation": "converge" if converge else "bootstrap",
        "class": repo_class, "target": str(final_target), "dry_run": dry_run,
        "changes": changes, "rollback_paths": changes,
    }
    managed_directories = {"tools", "tools/rocs-cli"}
    for rel in managed_directories:
        _preflight_managed_path(final_target, rel, directory=True)
    for rel in managed:
        if rel not in managed_directories and rel != "tools/rocs-cli":
            _preflight_managed_path(final_target, rel)
    if dry_run:
        return result

    stage = Path(tempfile.mkdtemp(prefix=f".{final_target.name}.bootstrap-stage-", dir=final_target.parent))
    try:
        shutil.copytree(final_target, stage, dirs_exist_ok=True, symlinks=True, copy_function=shutil.copy2)
        if policy["rocs_cli_vendored"]:
            vendor(source, stage / "tools/rocs-cli")
            if os.environ.get("ROCS_BOOTSTRAP_FAIL_AFTER") == "vendor":
                raise RuntimeError("injected failure after vendor")
            manifest = stage / "ontology/manifest.yaml"
            manifest.parent.mkdir(parents=True, exist_ok=True)
            if not manifest.exists():
                manifest.write_text(
                    "rocs:\n  layers:\n    - name: repo\n      path: ontology/src\n  profiles:\n    default: repo-dev\n    repo-dev:\n      include_layers: [repo]\n",
                    "utf-8",
                )
            system4d = stage / "ontology/src/system4d.yaml"
            system4d.parent.mkdir(parents=True, exist_ok=True)
            if not system4d.exists():
                system4d.write_text("system4d: {}\n", "utf-8")
            ci = stage / "scripts/ci/full.sh"
            ci.parent.mkdir(parents=True, exist_ok=True)
            ci.write_text(_CI_WRAPPER, "utf-8")
            ci.chmod(0o755)
            hook = stage / ".githooks/pre-push"
            hook.parent.mkdir(parents=True, exist_ok=True)
            profile = "main-strict" if policy["gate_mode"] == "strict" else "local-dev"
            hook.write_text(
                f'#!/bin/sh\nROCS_CI_PROFILE={profile} exec scripts/ci/full.sh\n', "utf-8"
            )
            hook.chmod(0o755)
            (hook.parent / "README.md").write_text(
                "Managed ROCS local gate. Run `git config core.hooksPath .githooks`.\n", "utf-8"
            )
        for rel in legacy:
            _remove_path(stage / rel)
        if os.environ.get("ROCS_BOOTSTRAP_FAIL_AFTER") == "managed":
            raise RuntimeError("injected failure after managed writes")
        if policy["rocs_cli_vendored"]:
            ok, errors = verify_vendored_hashes(stage / "tools/rocs-cli")
            if not ok:
                raise RuntimeError("staged bootstrap verification failed: " + "; ".join(errors))
        _publish_sibling(stage, final_target, fail_point=os.environ.get("ROCS_BOOTSTRAP_FAIL_AFTER"))
    finally:
        _remove_path(stage)
    return result


def release_plan(version: str, *, project: Path | None = None) -> dict[str, Any]:
    import re

    if re.fullmatch(r"\d+\.\d+\.\d+(?:[-+][0-9A-Za-z.-]+)?", version) is None:
        raise ValueError(f"invalid release version: {version}")
    return {
        "schema_version": 1,
        "operation": "plan",
        "current_version": __version__,
        "target_version": version,
        "project": str((project or _distribution_root()).resolve()),
    }


def release_apply(version: str, *, project: Path | None = None) -> dict[str, Any]:
    import re

    root = (project or _distribution_root()).resolve()
    payload = release_plan(version, project=root)
    pyproject = root / "pyproject.toml"
    init_py = root / "src/rocs_cli/__init__.py"
    originals = {pyproject: pyproject.read_bytes(), init_py: init_py.read_bytes()}
    py_text, py_count = re.subn(
        r'(?m)^version = "[^"]+"$', f'version = "{version}"', originals[pyproject].decode(), count=1
    )
    init_text, init_count = re.subn(
        r'(?m)^__version__ = "[^"]+"$', f'__version__ = "{version}"', originals[init_py].decode(), count=1
    )
    if py_count != 1 or init_count != 1:
        raise ValueError("project version declarations are missing or inconsistent")
    try:
        for path, text in ((pyproject, py_text), (init_py, init_text)):
            temp = path.with_name(f".{path.name}.release-{os.getpid()}")
            temp.write_text(text, "utf-8")
            os.replace(temp, path)
    except BaseException:
        for path, data in originals.items():
            path.write_bytes(data)
        raise
    payload["operation"] = "apply"
    return payload


def cleanup(repo: Path, *, dry_run: bool = False) -> dict[str, Any]:
    root = repo.expanduser().resolve(strict=True)
    if root == Path(root.anchor) or not root.is_dir():
        raise ValueError("unsafe repository root")
    manifests = tuple(root / path for path in ("ontology/manifest.yaml", "ontology/manifest.yml", "manifest.yaml", "manifest.yml"))
    pyproject = root / "pyproject.toml"
    is_source = pyproject.is_file() and not pyproject.is_symlink() and 'name = "rocs-cli"' in pyproject.read_text("utf-8")
    if not any(path.is_file() and not path.is_symlink() for path in manifests) and not is_source:
        raise ValueError("repository identity is not verifiable")
    targets = [root / "ontology/dist", root / "dist"]
    removed: list[str] = []
    for target in targets:
        resolved = target.resolve(strict=False)
        resolved.relative_to(root)
        if target.is_symlink():
            raise ValueError(f"refusing symlink cleanup target: {target}")
    for target in targets:
        if target.exists():
            removed.append(str(target.relative_to(root)))
            if not dry_run:
                shutil.rmtree(target) if target.is_dir() else target.unlink()
    return {"schema_version": 1, "repo": str(root), "dry_run": dry_run, "removed": removed}


def doctor(repo: Path) -> tuple[dict[str, Any], int]:
    root = repo.expanduser().resolve()
    identity = {"name": "rocs-cli", "version": __version__, "executable": sys.executable}
    checks = {
        "repo": root.is_dir(),
        "manifest": any(
            (root / p).is_file()
            for p in ("ontology/manifest.yaml", "ontology/manifest.yml", "manifest.yaml", "manifest.yml")
        ),
    }
    ok = all(checks.values())
    return {"schema_version": 1, "ok": ok, "tool": identity, "checks": checks}, 0 if ok else 1


def generate(out: Path, count: int) -> dict[str, Any]:
    from rocs_cli.generator import generate_repo

    repo = generate_repo(out, count=count)
    return {"schema_version": 1, "repo": str(repo), "concepts": count}


def benchmark(command: str, count: int, runs: int) -> dict[str, Any]:
    from rocs_cli.generator import generate_repo

    with tempfile.TemporaryDirectory() as td:
        repo = generate_repo(Path(td) / "repo", count=count)
        samples = []
        env = {**os.environ, "ROCS_CACHE_DIR": str(Path(td) / "cache")}
        for _ in range(runs + 1):
            start = time.perf_counter()
            subprocess.run(
                [sys.executable, "-m", "rocs_cli", command, "--repo", str(repo), "--json"],
                env=env,
                check=True,
                stdout=subprocess.DEVNULL,
            )
            samples.append((time.perf_counter() - start) * 1000)
    warm = sorted(samples[1:])
    return {
        "schema_version": 1,
        "command": command,
        "concepts": count,
        "cold_ms": samples[0],
        "warm_ms": samples[1:],
        "warm_median_ms": warm[len(warm) // 2] if warm else 0,
    }
