from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path


SEMVER_RE = re.compile(r"^(?P<maj>0|[1-9]\d*)\.(?P<min>0|[1-9]\d*)\.(?P<pat>0|[1-9]\d*)(?:-(?P<preid>[0-9A-Za-z-]+)\.(?P<pren>0|[1-9]\d*))?$")


@dataclass(frozen=True)
class SemVer:
    major: int
    minor: int
    patch: int
    preid: str | None = None
    pren: int | None = None

    @classmethod
    def parse(cls, s: str) -> "SemVer":
        m = SEMVER_RE.fullmatch(s.strip())
        if not m:
            raise ValueError(f"invalid semver: {s!r}")
        preid = m.group("preid")
        pren = m.group("pren")
        return cls(
            major=int(m.group("maj")),
            minor=int(m.group("min")),
            patch=int(m.group("pat")),
            preid=preid,
            pren=int(pren) if pren is not None else None,
        )

    def base(self) -> "SemVer":
        return SemVer(self.major, self.minor, self.patch, None, None)

    def with_prerelease(self, preid: str, pren: int) -> "SemVer":
        return SemVer(self.major, self.minor, self.patch, preid, pren)

    def __str__(self) -> str:
        v = f"{self.major}.{self.minor}.{self.patch}"
        if self.preid is not None and self.pren is not None:
            v += f"-{self.preid}.{self.pren}"
        return v


def read_pyproject_version(pyproject: Path) -> str:
    text = pyproject.read_text("utf-8")
    m = re.search(r'(?m)^\s*version\s*=\s*"([^"]+)"\s*$', text)
    if not m:
        raise RuntimeError(f"version not found in {pyproject}")
    return m.group(1).strip()


def write_pyproject_version(pyproject: Path, *, new_version: str) -> None:
    text = pyproject.read_text("utf-8")
    new_text, n = re.subn(r'(?m)^(\s*version\s*=\s*")([^"]+)(".*)$', rf"\g<1>{new_version}\g<3>", text, count=1)
    if n != 1:
        raise RuntimeError(f"failed to update version in {pyproject}")
    pyproject.write_text(new_text, "utf-8")


def read_init_version(init_py: Path) -> str:
    text = init_py.read_text("utf-8")
    m = re.search(r'(?m)^\s*__version__\s*=\s*"([^"]+)"\s*$', text)
    if not m:
        raise RuntimeError(f"__version__ not found in {init_py}")
    return m.group(1).strip()


def write_init_version(init_py: Path, *, new_version: str) -> None:
    text = init_py.read_text("utf-8")
    new_text, n = re.subn(r'(?m)^(\s*__version__\s*=\s*")([^"]+)(".*)$', rf"\g<1>{new_version}\g<3>", text, count=1)
    if n != 1:
        raise RuntimeError(f"failed to update __version__ in {init_py}")
    init_py.write_text(new_text, "utf-8")


def bump_base(v: SemVer, bump: str) -> SemVer:
    if bump == "major":
        return SemVer(v.major + 1, 0, 0)
    if bump == "minor":
        return SemVer(v.major, v.minor + 1, 0)
    if bump == "patch":
        return SemVer(v.major, v.minor, v.patch + 1)
    raise ValueError("bump must be major|minor|patch")


def compute_next(current: SemVer, *, bump: str, preid: str | None) -> SemVer:
    # Standard:
    # - without preid: bump base and drop prerelease
    # - with preid:
    #   - if already on same preid: bump prerelease only (keep base)
    #   - else: bump base and start preid.1
    if preid is None:
        return bump_base(current.base(), bump)

    if current.preid == preid and current.pren is not None:
        return current.base().with_prerelease(preid, current.pren + 1)

    return bump_base(current.base(), bump).with_prerelease(preid, 1)


def sync_vendored(src_repo: Path, vendor_dir: Path) -> None:
    # Keep this intentionally “dumb”: copy source-of-truth into vendored.
    # Vendored layout matches the source repo layout.
    for cruft in ["build", "dist"]:
        p = vendor_dir / cruft
        if p.exists() and p.is_dir():
            shutil.rmtree(p)
    for egg in vendor_dir.glob("src/*.egg-info"):
        if egg.is_dir():
            shutil.rmtree(egg)

    (vendor_dir / "src").mkdir(parents=True, exist_ok=True)
    shutil.rmtree(vendor_dir / "src" / "rocs_cli", ignore_errors=True)
    shutil.copytree(src_repo / "src" / "rocs_cli", vendor_dir / "src" / "rocs_cli")
    shutil.copyfile(src_repo / "pyproject.toml", vendor_dir / "pyproject.toml")
    shutil.copyfile(src_repo / "README.md", vendor_dir / "README.md")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_vendor_hashes(src_repo: Path, vendor_dir: Path) -> tuple[bool, list[str]]:
    checks: list[Path] = [Path("pyproject.toml"), Path("README.md")]
    for p in sorted((src_repo / "src" / "rocs_cli").rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        checks.append(p.relative_to(src_repo))
    ok = True
    lines: list[str] = []
    for rel in checks:
        a = src_repo / rel
        b = vendor_dir / rel
        if not a.exists():
            ok = False
            lines.append(f"missing source: {a}")
            continue
        if not b.exists():
            ok = False
            lines.append(f"missing vendor: {b}")
            continue
        ha = sha256_file(a)
        hb = sha256_file(b)
        if ha != hb:
            ok = False
            lines.append(f"mismatch: {rel} src={ha} vendor={hb}")
        else:
            lines.append(f"ok: {rel} {ha}")
    return ok, lines


def write_vendored_hashes(vendor_dir: Path, *, upstream_project: str, upstream_version: str) -> None:
    files: dict[str, str] = {}
    checks: list[Path] = [Path("pyproject.toml"), Path("README.md")]
    for p in sorted((vendor_dir / "src" / "rocs_cli").rglob("*.py")):
        if "__pycache__" in p.parts:
            continue
        checks.append(p.relative_to(vendor_dir))
    for rel in checks:
        files[str(rel)] = sha256_file(vendor_dir / rel)
    payload = {
        "schema_version": 1,
        "upstream_project": upstream_project,
        "upstream_version": upstream_version,
        "files": files,
    }
    (vendor_dir / "VENDORED_HASHES.json").write_text(json.dumps(payload, indent=2) + "\n", "utf-8")


def main() -> int:
    p = argparse.ArgumentParser(prog="bump_version.py")
    p.add_argument("--repo", default=".", help="rocs-cli repo root (default: .)")
    p.add_argument("--bump", required=True, choices=["patch", "minor", "major"], help="SemVer part to bump")
    p.add_argument("--preid", help="optional prerelease id (e.g. rc); if current is rc.N, increments N without bumping base")
    p.add_argument("--sync-vendored", action="store_true", help="also sync vendored copies if their paths exist")
    p.add_argument("--dry-run", action="store_true", help="print planned changes; do not write files")
    args = p.parse_args()

    repo = Path(args.repo).resolve()
    pyproject = repo / "pyproject.toml"
    init_py = repo / "src" / "rocs_cli" / "__init__.py"

    a = read_pyproject_version(pyproject)
    b = read_init_version(init_py)
    if a != b:
        raise SystemExit(f"version mismatch: pyproject={a!r} init={b!r}")

    cur = SemVer.parse(a)
    nxt = compute_next(cur, bump=args.bump, preid=args.preid)
    new_version = str(nxt)

    print(f"{cur} -> {new_version}")
    if args.dry_run:
        return 0

    write_pyproject_version(pyproject, new_version=new_version)
    write_init_version(init_py, new_version=new_version)

    if args.sync_vendored:
        # Default ai-society workspace layout (if present). Safe to skip if missing.
        vendor_candidates = [
            repo.parent / "ontology-kernel" / "tools" / "rocs-cli",
            repo.parent.parent / "holdingco" / "holdingco-templates" / "copier" / "tpl-project-repo" / "tools" / "rocs-cli",
        ]
        any_mismatch = False
        for vdir in vendor_candidates:
            if vdir.is_dir():
                sync_vendored(repo, vdir)
                print(f"synced: {vdir}")
                write_vendored_hashes(vdir, upstream_project="ai-society/core/rocs-cli", upstream_version=new_version)
                ok, lines = verify_vendor_hashes(repo, vdir)
                for ln in lines:
                    print(f"hash: {vdir.name}: {ln}")
                if not ok:
                    any_mismatch = True
            else:
                print(f"skip (missing): {vdir}")
        if any_mismatch:
            raise SystemExit(3)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
