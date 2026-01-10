from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path

import yaml
from rich.console import Console

from rocs_cli import __version__


console = Console()


FRONT_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)
PLACEHOLDER_RE = re.compile(r"<[^>]+>")


@dataclass(frozen=True)
class OntDoc:
    path: Path
    fm: dict
    body: str

    @property
    def ont(self) -> dict:
        return self.fm.get("ont") or {}

    @property
    def ont_id(self) -> str:
        return str(self.ont.get("id") or "")

    @property
    def ont_type(self) -> str:
        return str(self.ont.get("type") or "")


def _split_frontmatter(text: str) -> tuple[dict | None, str]:
    m = FRONT_RE.match(text)
    if not m:
        return None, text
    fm = yaml.safe_load(m.group(1)) or {}
    return fm, text[m.end() :]


def _load_doc(path: Path) -> OntDoc:
    text = path.read_text("utf-8")
    fm, body = _split_frontmatter(text)
    if fm is None:
        raise ValueError(f"missing front matter: {path}")
    return OntDoc(path=path, fm=fm, body=body)


def _repo_root(repo: str) -> Path:
    return Path(repo).resolve()


def _ontology_root(repo_root: Path) -> Path:
    return repo_root / "ontology"


def _manifest_path(repo_root: Path) -> Path:
    return _ontology_root(repo_root) / "manifest.yaml"


def _dist_dir(repo_root: Path) -> Path:
    return _ontology_root(repo_root) / "dist"


def _load_manifest(repo_root: Path) -> dict:
    p = _manifest_path(repo_root)
    if not p.exists():
        raise SystemExit(f"missing ontology manifest: {p}")
    return yaml.safe_load(p.read_text("utf-8")) or {}


def _iter_reference_md(repo_root: Path) -> list[Path]:
    ref = _ontology_root(repo_root) / "src" / "reference"
    out: list[Path] = []
    if not ref.exists():
        return out
    for p in sorted(ref.rglob("*.md")):
        if p.name == "README.md":
            continue
        out.append(p)
    return out


def _iter_ontology_md(repo_root: Path) -> list[Path]:
    src = _ontology_root(repo_root) / "src"
    out: list[Path] = []
    if not src.exists():
        return out
    for p in sorted(src.rglob("*.md")):
        out.append(p)
    return out


def _id_ok(ont_id: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z0-9_-]+(\.[A-Za-z0-9_-]+)+", ont_id))


def _collect_docs(repo_root: Path) -> tuple[dict[str, OntDoc], dict[str, OntDoc]]:
    concepts: dict[str, OntDoc] = {}
    relations: dict[str, OntDoc] = {}
    for p in _iter_reference_md(repo_root):
        d = _load_doc(p)
        if d.ont_type == "concept":
            concepts[d.ont_id] = d
        elif d.ont_type == "relation":
            relations[d.ont_id] = d
        else:
            raise SystemExit(f"unknown ont.type in {p}: {d.ont_type!r}")
    return concepts, relations


def _validate_repo_structure(repo_root: Path) -> list[str]:
    errs: list[str] = []
    if not _manifest_path(repo_root).exists():
        errs.append("missing ontology/manifest.yaml")
    if not (_ontology_root(repo_root) / "src" / "system4d.yaml").exists():
        errs.append("missing ontology/src/system4d.yaml")
    return errs


def _validate_reference_schema(repo_root: Path, strict_placeholders: bool) -> list[str]:
    errs: list[str] = []
    concepts, relations = _collect_docs(repo_root)

    rel_label_to_ids: dict[str, set[str]] = {}
    for rid, rdoc in relations.items():
        labels = (rdoc.ont.get("labels") or [])
        for lbl in labels:
            rel_label_to_ids.setdefault(str(lbl), set()).add(rid)

    for cid, cdoc in concepts.items():
        if not _id_ok(cid):
            errs.append(f"{cdoc.path}: invalid ont.id: {cid!r}")
        rels = cdoc.ont.get("relations")
        if not isinstance(rels, list):
            errs.append(f"{cdoc.path}: ont.relations must be a list (use [])")
            continue
        for edge in rels:
            if not isinstance(edge, dict):
                errs.append(f"{cdoc.path}: relation edge must be mapping: {edge!r}")
                continue
            rtype = str(edge.get("type") or "")
            target = str(edge.get("target") or "")
            if rtype and rtype not in rel_label_to_ids:
                errs.append(f"{cdoc.path}: unknown relation type label: {rtype!r}")
            if target and target not in concepts:
                errs.append(f"{cdoc.path}: missing relation target concept: {target!r}")

        status = str(cdoc.ont.get("status") or "active")
        if status not in ("active", "deprecated"):
            errs.append(f"{cdoc.path}: ont.status must be active|deprecated")
        if status == "deprecated":
            dep = cdoc.ont.get("deprecated") or {}
            if not isinstance(dep, dict):
                errs.append(f"{cdoc.path}: ont.deprecated must be mapping")
            else:
                for k in ("since", "replaced_by", "decision"):
                    if not dep.get(k):
                        errs.append(f"{cdoc.path}: deprecated requires ont.deprecated.{k}")
                rb = str(dep.get("replaced_by") or "")
                if rb and rb not in concepts:
                    errs.append(f"{cdoc.path}: deprecated replaced_by missing: {rb!r}")

    for rid, rdoc in relations.items():
        if not _id_ok(rid):
            errs.append(f"{rdoc.path}: invalid ont.id: {rid!r}")
        inv = rdoc.ont.get("inverse")
        if inv is not None:
            inv = str(inv)
            labels = [str(x) for x in (rdoc.ont.get("labels") or [])]
            if inv in labels:
                continue
            if inv not in rel_label_to_ids:
                errs.append(f"{rdoc.path}: inverse label not defined in kernel: {inv!r}")

    if strict_placeholders:
        for p in _iter_ontology_md(repo_root):
            text = p.read_text("utf-8")
            if PLACEHOLDER_RE.search(text):
                errs.append(f"{p}: placeholder token found (e.g. <...>)")
        mp = _manifest_path(repo_root)
        if mp.exists() and PLACEHOLDER_RE.search(mp.read_text("utf-8")):
            errs.append(f"{mp}: placeholder token found (e.g. <...>)")

    # taxonomy cycles on is_a
    is_a_edges: list[tuple[str, str]] = []
    for cid, cdoc in concepts.items():
        for edge in cdoc.ont.get("relations") or []:
            if isinstance(edge, dict) and str(edge.get("type") or "") == "is_a":
                is_a_edges.append((cid, str(edge.get("target") or "")))

    graph: dict[str, list[str]] = {}
    for a, b in is_a_edges:
        if a and b:
            graph.setdefault(a, []).append(b)

    state: dict[str, int] = {}
    stack: list[str] = []

    def dfs(n: str) -> None:
        state[n] = 1
        stack.append(n)
        for nxt in graph.get(n, []):
            st = state.get(nxt, 0)
            if st == 0:
                dfs(nxt)
            elif st == 1 and nxt in stack:
                i = stack.index(nxt)
                cycle = " -> ".join(stack[i:] + [nxt])
                errs.append(f"taxonomy cycle: {cycle}")
        stack.pop()
        state[n] = 2

    for n in graph:
        if state.get(n, 0) == 0:
            dfs(n)

    return errs


def cmd_summary(args: argparse.Namespace) -> int:
    repo_root = _repo_root(args.repo)
    manifest = _load_manifest(repo_root)
    rocs = manifest.get("rocs") or {}
    layer = rocs.get("layer") or rocs.get("layers")
    concepts, relations = _collect_docs(repo_root)
    payload = {
        "repo": str(repo_root),
        "layer": layer,
        "counts": {"concepts": len(concepts), "relations": len(relations)},
    }
    console.print_json(json.dumps(payload))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    repo_root = _repo_root(args.repo)
    errs: list[str] = []
    errs.extend(_validate_repo_structure(repo_root))
    errs.extend(_validate_reference_schema(repo_root, strict_placeholders=args.strict_placeholders))
    if errs:
        console.print("[red]rocs validate: FAIL[/red]")
        for e in errs:
            console.print(f"- {e}")
        return 1
    console.print("[green]rocs validate: OK[/green]")
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    repo_root = _repo_root(args.repo)
    concepts, relations = _collect_docs(repo_root)
    cid = args.ont_id
    doc = concepts.get(cid) or relations.get(cid)
    if not doc:
        console.print(f"[red]unknown ont_id[/red]: {cid}")
        return 2
    console.print(str(doc.path))
    console.print(doc.path.read_text("utf-8"))
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    repo_root = _repo_root(args.repo)
    dist = _dist_dir(repo_root)
    dist.mkdir(parents=True, exist_ok=True)
    concepts, relations = _collect_docs(repo_root)
    summary = {
        "repo": str(repo_root),
        "counts": {"concepts": len(concepts), "relations": len(relations)},
        "concept_ids": sorted(concepts.keys()),
        "relation_ids": sorted(relations.keys()),
    }
    (dist / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", "utf-8")
    console.print(f"[green]wrote[/green] {dist/'summary.json'}")
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="rocs")
    parser.add_argument("--version", action="version", version=f"rocs-cli {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("summary")
    p.add_argument("--repo", default=".", help="repo root path")
    p.set_defaults(fn=cmd_summary)

    p = sub.add_parser("validate")
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--strict-placeholders", action="store_true", help="fail if any <...> placeholders exist")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("pack")
    p.add_argument("ont_id")
    p.add_argument("--repo", default=".", help="repo root path")
    p.set_defaults(fn=cmd_pack)

    p = sub.add_parser("build")
    p.add_argument("--repo", default=".", help="repo root path")
    p.set_defaults(fn=cmd_build)

    args = parser.parse_args(argv)
    raise SystemExit(int(args.fn(args)))


if __name__ == "__main__":
    main()
