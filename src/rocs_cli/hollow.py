"""Warn-only hollow-layer report (ADR-0008 §10; AK 6134).

A hollow layer resolves and validates, yet tells its reader nothing: its
system4d.yaml is still the project template, its YAML still carries template
placeholders, or a repo layer adds nothing to the view. system4d.yaml is context
harnessed LLMs read before they work in a repo, so a placeholder there misleads
rather than sitting harmlessly.

The report covers the repo's own path layers; a ref layer is reported by lint in
the repo that owns it. It only warns: `validate`, `build` and their authority
receipts do not read it.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import yaml
from yaml.nodes import MappingNode, Node, ScalarNode, SequenceNode

from rocs_cli.layers import LayerSpec
from rocs_cli.model import OntDoc
from rocs_cli.rules import Finding


# sha256 of ontology/src/system4d.yaml in core/tpl-template-repo's tpl-project-repo and
# tpl-monorepo templates (md5 36347f74decf..., unchanged since b680a8f, 2026-02-22).
TEMPLATE_SYSTEM4D_SHA256 = frozenset({"921200219fc90639f2b028b0198a453cd4ae88bb23487c29c2ab91dcdd6dfb5b"})

# A template placeholder is a whole YAML scalar ("<Repo Name>", "<http|kafka|file>").
# A token inside prose ("--repo <repo>", "contrib/<upstream>/<repo>") is usage notation.
_PLACEHOLDER_RE = re.compile(r"<[^<>\n]+>")
_REF_LOCATOR_RE = re.compile(r"<repo:[^@>]+@[^>]+>")
_BRIDGE_MAPPING = Path("bridge") / "mapping.yaml"
_MAX_LISTED = 5


def _yaml_files(src_root: Path) -> list[Path]:
    paths = [*src_root.rglob("*.yaml"), *src_root.rglob("*.yml")]
    return sorted(p for p in paths if p.is_file())


def _placeholder_scalars(root: Node) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    seen: set[int] = set()
    stack = [root]
    while stack:
        node = stack.pop()
        if id(node) in seen:  # aliases share nodes
            continue
        seen.add(id(node))
        if isinstance(node, ScalarNode):
            value = str(node.value).strip()
            if _PLACEHOLDER_RE.fullmatch(value) and not _REF_LOCATOR_RE.fullmatch(value):
                found.append((node.start_mark.line + 1, value))
        elif isinstance(node, SequenceNode):
            stack.extend(node.value)
        elif isinstance(node, MappingNode):
            for key, value in node.value:
                stack.extend((key, value))
    return found


def _parse_problem(exc: Exception) -> str:
    if isinstance(exc, UnicodeDecodeError):
        return "invalid UTF-8"
    if isinstance(exc, yaml.MarkedYAMLError) and exc.problem_mark is not None:
        return f"{exc.problem} (line {exc.problem_mark.line + 1})"
    return type(exc).__name__


def _yaml_findings(layer: LayerSpec) -> list[Finding]:
    findings: list[Finding] = []
    for path in _yaml_files(layer.src_root):
        try:
            raw = path.read_bytes()
        except OSError:
            continue
        if path == layer.src_root / "system4d.yaml" and hashlib.sha256(raw).hexdigest() in TEMPLATE_SYSTEM4D_SHA256:
            # One warning covers the template's own placeholders.
            findings.append(
                Finding(
                    rule_id="HOLLOW020",
                    severity="warn",
                    message="system4d.yaml is byte-identical to the project template; "
                    "describe this repo's scope, edges, invariants and risks",
                    path=str(path),
                    layer=layer.name,
                )
            )
            continue
        try:
            documents = list(yaml.compose_all(raw.decode("utf-8"), Loader=yaml.SafeLoader))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            findings.append(
                Finding(
                    rule_id="HOLLOW002",
                    severity="warn",
                    message=f"YAML does not parse, placeholder scan skipped: {_parse_problem(exc)}",
                    path=str(path),
                    layer=layer.name,
                )
            )
            continue
        tokens = sorted(hit for doc in documents if doc is not None for hit in _placeholder_scalars(doc))
        if not tokens:
            continue
        listed = ", ".join(f"line {line} {token}" for line, token in tokens[:_MAX_LISTED])
        more = f" (+{len(tokens) - _MAX_LISTED} more)" if len(tokens) > _MAX_LISTED else ""
        findings.append(
            Finding(
                rule_id="HOLLOW001",
                severity="warn",
                message=f"{len(tokens)} template placeholder(s) in YAML: {listed}{more}",
                path=str(path),
                layer=layer.name,
            )
        )
    return findings


def _bridge_mappings(src_root: Path) -> int:
    path = src_root / _BRIDGE_MAPPING
    if not path.is_file():
        return 0
    try:
        data = yaml.safe_load(path.read_text("utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return 0
    mappings = data.get("mappings") if isinstance(data, dict) else None
    return len(mappings) if isinstance(mappings, list) else 0


def hollow_layer_findings(
    layers: list[LayerSpec],
    concepts: dict[str, OntDoc],
    relations: dict[str, OntDoc],
) -> list[Finding]:
    contributed: dict[str, int] = {}
    for doc in (*concepts.values(), *relations.values()):
        contributed[doc.layer_name] = contributed.get(doc.layer_name, 0) + 1

    findings: list[Finding] = []
    for layer in layers:
        if layer.kind != "path" or not layer.src_root.is_dir():
            continue
        findings.extend(_yaml_findings(layer))
        # Borrowing upper-layer concepts through bridge mappings is content (ADR-0008 prefers it
        # to inventing repo words), so only a layer with neither documents nor mappings is hollow.
        if not contributed.get(layer.name) and not _bridge_mappings(layer.src_root):
            findings.append(
                Finding(
                    rule_id="HOLLOW010",
                    severity="warn",
                    message=f"repo layer {layer.name!r} contributes no documents "
                    "(0 concepts, 0 relations, 0 bridge mappings)",
                    path=str(layer.src_root),
                    layer=layer.name,
                )
            )
    return findings
