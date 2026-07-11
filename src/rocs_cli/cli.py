from __future__ import annotations

import argparse
import json
import os
import shutil
from pathlib import Path
from typing import cast

from rich.console import Console

from rocs_cli import __version__
from rocs_cli.authority import (
    authority_receipt_payload,
    can_write_authority_receipt,
    effective_workspace_ref_mode,
    write_authority_receipt,
)
from rocs_cli.cache import cache_dir, clear_cache, list_cache_entries, prune_cache
from rocs_cli.contracts import command_contract
from rocs_cli.constitution import (
    ConstitutionError,
    challenge_candidate,
    differential,
    generate_mutants,
    pareto_frontier,
    strict_json_load,
    validate_candidate,
)
from rocs_cli.graph import build_edges, collapse_nodes, compute_layout, write_graph
from rocs_cli.id_index import build_id_index
from rocs_cli.inverses import check_inverses
from rocs_cli.intelligence import (
    compile_plan,
    create_capsule,
    load_json as load_membrane_json,
    validate_capsule,
    validate_proposal,
    write_compiled_plan,
)
from rocs_cli.transactions import (
    apply_transaction,
    prepare_transaction,
    rollback_transaction,
    simulate_transaction,
    verify_receipt,
)
from rocs_cli.layers import (
    dist_dir,
    parse_ref_locator,
    repo_root as _repo_root,
    resolve_layers,
    resolve_ref_repo_root,
)
from rocs_cli.lint import lint_docs
from rocs_cli.normalize import normalize_tree
from rocs_cli.pack import build_pack, pack_config_from_profile
from rocs_cli.repo_view import RepoView, load_repo_view
from rocs_cli.rules import Finding, RULES
from rocs_cli.errors import RocsCliError
from rocs_cli.managed_surface import ensure_managed_output_dir, ensure_managed_output_file
from rocs_cli.rulesets import behavior_for_ruleset, effective_ruleset
from rocs_cli.validate import (
    enforce_budget,
    validate_layers_exist,
    validate_manifest_placeholders,
    validate_reference_schema,
    validate_repo_structure,
)
from rocs_cli.vendored import verify_vendored_hashes


console = Console()

_DEFAULT_ENV_REL = Path("holdingco/governance-kernel/.env")


def _discover_default_env_file(*, repo_root: Path | None) -> Path | None:
    env_from_var = os.environ.get("ROCS_ENV_FILE") or ""
    if env_from_var.strip():
        return Path(env_from_var).expanduser()
    if repo_root is None:
        return None

    repo_env = repo_root / ".env"
    if repo_env.exists():
        return repo_env

    for p in [repo_root, *repo_root.parents]:
        cand = p / _DEFAULT_ENV_REL
        if cand.exists():
            return cand

    return None


def _maybe_load_env_file(env_file: str | None, *, repo_root: Path | None) -> None:
    p = Path(env_file).expanduser() if env_file else _discover_default_env_file(repo_root=repo_root)
    if not p:
        return
    from rocs_cli.env import load_env_file

    load_env_file(p)


def _load_view(args: argparse.Namespace, *, load_docs: bool = True, repo: str | Path | None = None) -> RepoView:
    repo_root = _repo_root(str(repo if repo is not None else args.repo))
    _maybe_load_env_file(getattr(args, "env_file", None), repo_root=repo_root)
    return load_repo_view(
        repo_root,
        profile=getattr(args, "profile", None),
        resolve_refs=bool(getattr(args, "resolve_refs", False)),
        workspace_root=getattr(args, "workspace_root", None),
        workspace_ref_mode=getattr(args, "workspace_ref_mode", None),
        only=getattr(args, "only", None),
        layer=getattr(args, "layer", None),
        load_docs=load_docs,
    )


def _schema_validation_result(
    view: RepoView,
    *,
    strict_placeholders: bool,
    validate_deps: bool,
) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    findings.extend(validate_manifest_placeholders(view.repo, strict_placeholders=strict_placeholders))
    findings.extend(validate_layers_exist(view.layers))
    schema_findings, _meta2 = validate_reference_schema(
        view.layers,
        strict_placeholders=strict_placeholders,
        validate_deps=validate_deps,
        concepts=view.concepts,
        relations=view.relations,
    )
    findings.extend(schema_findings)

    budget = None
    profile_def = view.meta.get("profile_def") or {}
    if isinstance(profile_def, dict) and profile_def.get("budget") is not None:
        budget_raw = profile_def.get("budget")
        if isinstance(budget_raw, (int, str)):
            try:
                budget = int(budget_raw)
            except Exception:
                findings.append(
                    Finding(
                        rule_id="BUD001",
                        severity="error",
                        message=f"invalid profile budget (expected int): {budget_raw!r}",
                    )
                )
        else:
            findings.append(
                Finding(
                    rule_id="BUD001",
                    severity="error",
                    message=f"invalid profile budget (expected int): {budget_raw!r}",
                )
            )
    ok_budget, budget_payload = enforce_budget(view.concepts, view.relations, budget=budget)
    if not ok_budget:
        findings.append(
            Finding(
                rule_id="BUD010",
                severity="error",
                message=f"budget exceeded: units={budget_payload['units']} budget={budget_payload['budget']}",
            )
        )

    return findings, budget_payload


def _findings_to_json(findings: list[Finding]) -> list[dict]:
    return [f.to_dict() for f in findings]


def _print_findings(findings: list[Finding]) -> None:
    for f in findings:
        loc = f.path or ""
        if loc:
            console.print(f"- {f.rule_id} {f.severity} {loc}: {f.message}")
        else:
            console.print(f"- {f.rule_id} {f.severity}: {f.message}")


def _ensure_dist_dir(repo: Path, *, label: str) -> Path:
    return ensure_managed_output_dir(repo, dist_dir(repo), label=label)


def _write_resolve_artifact(repo: Path, *, layers, profile: str | None) -> Path:
    dist = _ensure_dist_dir(repo, label="resolve artifact dir")
    entries = []
    for layer_spec in layers:
        entries.append(
            {
                "name": layer_spec.name,
                "kind": layer_spec.kind,
                "origin": layer_spec.origin,
                "source": layer_spec.source,
                "src_root": str(layer_spec.src_root),
            }
        )
    entries.sort(key=lambda e: str(e.get("name") or ""))
    payload = {
        "schema_version": 2,
        "version": __version__,
        "repo": str(repo),
        "profile": profile,
        "layers": entries,
    }
    out = ensure_managed_output_file(repo, dist / "resolve.json", label="resolve artifact")
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")
    return out


def _clear_build_artifacts(repo: Path) -> None:
    dist = dist_dir(repo)
    for name in ("resolve.json", "summary.json", "id_index.json"):
        (dist / name).unlink(missing_ok=True)


def _write_authority_receipt_if_possible(
    repo: Path,
    *,
    command: str,
    ok: bool,
    profile: str | None,
    resolve_refs_requested: bool,
    workspace_ref_mode: str,
    layers,
    result: dict | None = None,
    error: RocsCliError | None = None,
) -> dict[str, Path] | None:
    if not can_write_authority_receipt(repo):
        return None
    payload = authority_receipt_payload(
        repo,
        command=command,
        ok=ok,
        profile=profile,
        resolve_refs_requested=resolve_refs_requested,
        workspace_ref_mode=workspace_ref_mode,
        layers=list(layers),
        result=result,
        error=error,
    )
    return write_authority_receipt(repo, payload)


def _finding_summary(findings: list[Finding]) -> dict[str, int]:
    return {
        "finding_count": len(findings),
        "error_count": sum(1 for f in findings if f.severity == "error"),
        "warning_count": sum(1 for f in findings if f.severity == "warn"),
    }


def cmd_version(_args: argparse.Namespace) -> int:
    console.print(f"rocs-cli {__version__}")
    return 0


def cmd_contracts(_args: argparse.Namespace) -> int:
    payload = {**command_contract(), "tool": {"name": "rocs-cli", "version": __version__}}
    console.print_json(json.dumps(payload, sort_keys=True))
    return 0


def cmd_constitution(args: argparse.Namespace) -> int:
    def load(name: str):
        values = getattr(args, name)
        if type(values) is not list or len(values) != 1:
            raise ConstitutionError(f"--{name.replace('_', '-')} must be supplied exactly once")
        with Path(values[0]).open("r", encoding="utf-8") as handle:
            return strict_json_load(handle)

    if args.constitution_cmd == "validate":
        payload = validate_candidate(load("candidate"))
    elif args.constitution_cmd == "challenge":
        payload = challenge_candidate(load("candidate"))
    elif args.constitution_cmd == "differential":
        payload = differential(load("candidate_a"), load("candidate_b"), load("subjects"))
    else:
        payload = generate_mutants(load("contract"), load("acceptance"), load("corpus"))
    console.print_json(json.dumps(payload, sort_keys=True))
    return 0 if payload.get("fixtures_consistent", True) else 1


def cmd_repair_market(args: argparse.Namespace) -> int:
    if type(args.market) is not list or len(args.market) != 1:
        raise ConstitutionError("--market must be supplied exactly once")
    with Path(args.market[0]).open("r", encoding="utf-8") as handle:
        payload = pareto_frontier(strict_json_load(handle))
    console.print_json(json.dumps(payload, sort_keys=True))
    return 0


def cmd_wave1(args: argparse.Namespace) -> int:
    from rocs_cli import wave1

    op = args.operation
    if op in {"bootstrap", "converge"}:
        payload = wave1.bootstrap(Path(args.target), args.repo_class, dry_run=args.dry_run, converge=op == "converge")
        console.print_json(json.dumps(payload))
        return 0
    if op == "vendor":
        payload = wave1.vendor(_repo_root("."), Path(args.target), version=args.release_version, dry_run=args.dry_run)
        console.print_json(json.dumps(payload))
        return 0
    if op in {"release-plan", "release-apply"}:
        function = wave1.release_plan if op == "release-plan" else wave1.release_apply
        console.print_json(json.dumps(function(args.release_version, project=_repo_root("."))))
        return 0
    if op == "verify":
        payload, code = wave1.verify(Path(args.path))
    elif op == "cleanup":
        payload, code = wave1.cleanup(Path(args.repo), dry_run=args.dry_run), 0
    elif op == "doctor":
        payload, code = wave1.doctor(Path(args.repo))
    elif op == "generate":
        payload, code = wave1.generate(Path(args.out), args.count), 0
    elif op == "benchmark":
        payload, code = wave1.benchmark(args.command, args.count, args.runs), 0
    else:
        raise ValueError(f"unknown operation: {op}")
    console.print_json(json.dumps(payload))
    return code


def cmd_fleet(args: argparse.Namespace) -> int:
    from rocs_cli import fleet

    root, policy = Path(args.workspace_root), Path(args.policy)
    if args.fleet_cmd == "observe":
        payload, code = fleet.observe(root, policy, report_only=args.report_only)
    elif args.fleet_cmd == "plan":
        payload, code = fleet.plan(root, policy)
    elif args.fleet_cmd == "apply":
        payload, code = fleet.apply(root, policy, dry_run=args.dry_run)
    elif args.fleet_cmd == "run":
        payload, code = fleet.run(root, policy, mode=args.mode)
    else:
        raise ValueError(f"unknown fleet operation: {args.fleet_cmd}")
    text = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    destination = args.json
    if destination and destination != "-":
        out = Path(destination).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, "utf-8")
    else:
        print(text, end="")
    if getattr(args, "markdown", None):
        if args.fleet_cmd != "observe":
            raise ValueError("--markdown is supported only by fleet observe")
        md = fleet._render_markdown(payload)
        if args.markdown == "-":
            print(md, end="")
        else:
            Path(args.markdown).expanduser().resolve().write_text(md, "utf-8")
    return code


def cmd_rules(args: argparse.Namespace) -> int:
    rules = sorted(RULES.values(), key=lambda r: r.rule_id)
    payload = {
        "rules": [
            {
                "rule_id": r.rule_id,
                "default_severity": r.default_severity,
                "summary": r.summary,
            }
            for r in rules
        ]
    }
    if args.json:
        console.print_json(json.dumps(payload))
        return 0
    for r in rules:
        console.print(f"{r.rule_id} {r.default_severity} {r.summary}")
    return 0


def cmd_explain(args: argparse.Namespace) -> int:
    rule_id = str(args.rule_id)
    r = RULES.get(rule_id)
    if r is None:
        raise SystemExit(f"unknown rule id: {rule_id}")
    payload = {
        "rule": {
            "rule_id": r.rule_id,
            "default_severity": r.default_severity,
            "summary": r.summary,
            "suppress": {"field": "ont.lint_ignore", "value": r.rule_id},
        }
    }
    if args.json:
        console.print_json(json.dumps(payload))
        return 0
    console.print(f"{r.rule_id} ({r.default_severity})")
    console.print(r.summary)
    console.print("")
    console.print("suppress:")
    console.print(f"- add to `ont.lint_ignore`: {r.rule_id!r}")
    return 0


def cmd_resolve(args: argparse.Namespace) -> int:
    view = _load_view(args, load_docs=False)
    repo = view.repo
    profile_name = (
        view.meta.get("profile") if isinstance(view.meta, dict) and isinstance(view.meta.get("profile"), str) else None
    )
    resolution_notes = view.meta.get("resolution_notes") if isinstance(view.meta, dict) else None
    layer_entries: list[dict[str, object]] = []
    for layer_spec in view.layers:
        entry: dict[str, object] = {
            "name": layer_spec.name,
            "origin": layer_spec.origin,
            "src_root": str(layer_spec.src_root),
            "kind": layer_spec.kind,
            "source": layer_spec.source,
        }
        if args.show_resolve_details:
            entry["details"] = (resolution_notes or {}).get(layer_spec.name)
        layer_entries.append(entry)
    for layer_entry in layer_entries:
        if layer_entry.get("details") is None:
            layer_entry.pop("details", None)

    payload: dict[str, object] = {"repo": str(repo), "profile": profile_name, "layers": layer_entries}
    if args.write_dist:
        _write_resolve_artifact(repo, layers=view.layers, profile=profile_name)
    if args.json:
        console.print_json(json.dumps(payload))
    else:
        console.print(f"repo: {repo}")
        console.print(f"profile: {profile_name}")
        for layer_entry in layer_entries:
            name = str(layer_entry.get("name") or "")
            origin = str(layer_entry.get("origin") or "")
            if args.show_resolve_sources or args.show_resolve_details:
                source = str(layer_entry.get("source") or "")
                extra = f"source={source}"
                details = layer_entry.get("details")
                if args.show_resolve_details and isinstance(details, dict):
                    details_map = cast(dict[str, object], details)
                    ws_obj = details_map.get("workspace")
                    if isinstance(ws_obj, dict):
                        ws = cast(dict[str, object], ws_obj)
                        if ws.get("present"):
                            if not ws.get("used") and ws.get("reason"):
                                extra += f"; workspace={ws.get('reason')}"
                console.print(f"- layer {name}: {origin} ({extra})")
            else:
                console.print(f"- layer {name}: {origin}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    view = _load_view(args)
    repo = view.repo
    profile_name = (
        view.meta.get("profile") if isinstance(view.meta, dict) and isinstance(view.meta.get("profile"), str) else None
    )
    resolution_notes = view.meta.get("resolution_notes") if isinstance(view.meta, dict) else None
    layer_entries: list[dict[str, object]] = []
    for layer_spec in view.layers:
        entry: dict[str, object] = {
            "name": layer_spec.name,
            "origin": layer_spec.origin,
            "src_root": str(layer_spec.src_root),
            "kind": layer_spec.kind,
            "source": layer_spec.source,
        }
        if args.show_resolve_details:
            entry["details"] = (resolution_notes or {}).get(layer_spec.name)
        layer_entries.append(entry)
    for layer_entry in layer_entries:
        if layer_entry.get("details") is None:
            layer_entry.pop("details", None)
    payload: dict[str, object] = {
        "repo": str(repo),
        "profile": profile_name,
        "layers": layer_entries,
        "counts": {"concepts": len(view.concepts), "relations": len(view.relations)},
    }
    if not args.json:
        console.print(f"repo: {repo}")
        console.print(f"profile: {profile_name}")
        console.print(f"counts: concepts={len(view.concepts)} relations={len(view.relations)}")
        for layer_entry in layer_entries:
            name = str(layer_entry.get("name") or "")
            origin = str(layer_entry.get("origin") or "")
            if args.show_resolve_sources or args.show_resolve_details:
                source = str(layer_entry.get("source") or "")
                extra = f"source={source}"
                details = layer_entry.get("details")
                if args.show_resolve_details and isinstance(details, dict):
                    details_map = cast(dict[str, object], details)
                    ws_obj = details_map.get("workspace")
                    if isinstance(ws_obj, dict):
                        ws = cast(dict[str, object], ws_obj)
                        if ws.get("present"):
                            if not ws.get("used") and ws.get("reason"):
                                extra += f"; workspace={ws.get('reason')}"
                console.print(f"- layer {name}: {origin} ({extra})")
            else:
                console.print(f"- layer {name}: {origin}")
    else:
        console.print_json(json.dumps(payload))
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    repo = _repo_root(args.repo)
    ws_mode = effective_workspace_ref_mode(getattr(args, "workspace_ref_mode", None))
    findings: list[Finding] = []
    findings.extend(validate_repo_structure(repo))
    if findings:
        _write_authority_receipt_if_possible(
            repo,
            command="validate",
            ok=False,
            profile=getattr(args, "profile", None),
            resolve_refs_requested=bool(args.resolve_refs),
            workspace_ref_mode=ws_mode,
            layers=[],
            result=_finding_summary(findings),
        )
        if args.json:
            console.print_json(
                json.dumps(
                    {"ok": False, "findings": _findings_to_json(findings), "budget": {"budget": None, "units": None}}
                )
            )
        else:
            console.print("[red]rocs validate: FAIL[/red]")
            _print_findings(findings)
        return 1
    try:
        view = _load_view(args)
    except RocsCliError as e:
        _write_authority_receipt_if_possible(
            repo,
            command="validate",
            ok=False,
            profile=getattr(args, "profile", None),
            resolve_refs_requested=bool(args.resolve_refs),
            workspace_ref_mode=ws_mode,
            layers=[],
            error=e,
        )
        raise
    profile_name = (
        view.meta.get("profile") if isinstance(view.meta, dict) and isinstance(view.meta.get("profile"), str) else None
    )
    profile_def = view.meta.get("profile_def") if isinstance(view.meta, dict) else None
    ruleset_name = effective_ruleset(cli_ruleset=getattr(args, "ruleset", None), profile_def=profile_def)
    ruleset_behavior = behavior_for_ruleset(ruleset_name)
    strict_placeholders = bool(args.strict_placeholders or ruleset_behavior.strict_placeholders)

    findings, budget_payload = _schema_validation_result(
        view,
        strict_placeholders=strict_placeholders,
        validate_deps=bool(args.validate_deps),
    )

    ok = not findings
    _write_authority_receipt_if_possible(
        repo,
        command="validate",
        ok=ok,
        profile=profile_name,
        resolve_refs_requested=bool(args.resolve_refs),
        workspace_ref_mode=ws_mode,
        layers=view.layers,
        result=_finding_summary(findings),
    )
    if findings:
        if args.json:
            console.print_json(
                json.dumps({"ok": False, "findings": _findings_to_json(findings), "budget": budget_payload})
            )
        else:
            console.print("[red]rocs validate: FAIL[/red]")
            _print_findings(findings)
        return 1

    if args.json:
        console.print_json(json.dumps({"ok": True, "findings": [], "budget": budget_payload}))
    else:
        console.print("[green]rocs validate: OK[/green]")
    return 0


def cmd_build(args: argparse.Namespace) -> int:
    repo = _repo_root(args.repo)
    ws_mode = effective_workspace_ref_mode(getattr(args, "workspace_ref_mode", None))
    dist = dist_dir(repo)
    _ensure_dist_dir(repo, label="build output dir")
    if args.clean and dist.exists():
        shutil.rmtree(dist)
    _ensure_dist_dir(repo, label="build output dir")
    _clear_build_artifacts(repo)
    try:
        view = _load_view(args)
    except RocsCliError as e:
        _write_authority_receipt_if_possible(
            repo,
            command="build",
            ok=False,
            profile=getattr(args, "profile", None),
            resolve_refs_requested=bool(args.resolve_refs),
            workspace_ref_mode=ws_mode,
            layers=[],
            error=e,
        )
        raise
    profile_name = (
        view.meta.get("profile") if isinstance(view.meta, dict) and isinstance(view.meta.get("profile"), str) else None
    )
    profile_def = view.meta.get("profile_def") if isinstance(view.meta, dict) else None
    ruleset_name = effective_ruleset(cli_ruleset=None, profile_def=profile_def)
    strict_placeholders = behavior_for_ruleset(ruleset_name).strict_placeholders
    findings, _budget_payload = _schema_validation_result(
        view,
        strict_placeholders=strict_placeholders,
        validate_deps=True,
    )
    if findings:
        _write_authority_receipt_if_possible(
            repo,
            command="build",
            ok=False,
            profile=profile_name,
            resolve_refs_requested=bool(args.resolve_refs),
            workspace_ref_mode=ws_mode,
            layers=view.layers,
            result=_finding_summary(findings),
        )
        if args.json:
            console.print_json(json.dumps({"ok": False, "findings": _findings_to_json(findings)}))
        else:
            console.print("[red]rocs build: FAIL[/red]")
            _print_findings(findings)
        return 1

    resolve_out = _write_resolve_artifact(repo, layers=view.layers, profile=profile_name)
    payload = {
        "schema_version": 1,
        "version": __version__,
        "repo": str(repo),
        "profile": profile_name,
        "layers": [{"name": layer_spec.name, "origin": layer_spec.origin} for layer_spec in view.layers],
        "counts": {"concepts": len(view.concepts), "relations": len(view.relations)},
        "concept_ids": sorted(view.concepts.keys()),
        "relation_ids": sorted(view.relations.keys()),
    }
    summary_out = ensure_managed_output_file(repo, dist / "summary.json", label="build summary artifact")
    summary_out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")
    id_index_out = ensure_managed_output_file(repo, dist / "id_index.json", label="build id-index artifact")
    id_index_out.write_text(
        json.dumps(build_id_index(concepts=view.concepts, relations=view.relations), indent=2, sort_keys=True) + "\n",
        "utf-8",
    )
    authority_receipt_out = _write_authority_receipt_if_possible(
        repo,
        command="build",
        ok=True,
        profile=profile_name,
        resolve_refs_requested=bool(args.resolve_refs),
        workspace_ref_mode=ws_mode,
        layers=view.layers,
    )
    if args.json:
        files = {
            "resolve": str(resolve_out),
            "summary": str(summary_out),
            "id_index": str(id_index_out),
        }
        if authority_receipt_out is not None:
            files["authority_receipt"] = str(authority_receipt_out["aggregate"])
            files["authority_receipt_command"] = str(authority_receipt_out["command"])
        console.print_json(
            json.dumps(
                {
                    "repo": str(repo),
                    "profile": profile_name,
                    "dist": {
                        "dir": str(dist),
                        "files": files,
                    },
                    "counts": payload.get("counts"),
                }
            )
        )
    else:
        console.print(f"[green]wrote[/green] {summary_out}")
        console.print(f"[green]wrote[/green] {id_index_out}")
        if authority_receipt_out is not None:
            console.print(f"[green]wrote[/green] {authority_receipt_out['aggregate']}")
            console.print(f"[green]wrote[/green] {authority_receipt_out['command']}")
    return 0


def cmd_pack(args: argparse.Namespace) -> int:
    view = _load_view(args)
    cid = args.ont_id
    doc = view.concepts.get(cid) or view.relations.get(cid)
    if not doc:
        raise RocsCliError(kind="not_found", message=f"unknown ont_id: {cid}", exit_code=2, details={"ont_id": cid})

    rel_types: set[str] | None = None
    if args.rel_types:
        rel_types = {x.strip() for x in args.rel_types.split(",") if x.strip()}

    cfg = pack_config_from_profile(
        profile_def=view.meta.get("profile_def") if isinstance(view.meta, dict) else None,
        overrides={
            "max_depth": args.depth,
            "rel_types": rel_types,
            "include_relation_defs": True if args.include_relation_defs else None,
            "max_docs": args.max_docs,
            "max_bytes": args.max_bytes,
        },
    )

    packed, pack_meta = build_pack(concepts=view.concepts, relations=view.relations, root_id=cid, config=cfg)
    if args.json:
        console.print_json(
            json.dumps(
                {
                    "repo": str(view.repo),
                    "profile": view.meta.get("profile"),
                    "pack": pack_meta,
                    "docs": [{"ont_id": d.ont_id, "kind": d.kind, "path": d.path} for d in packed],
                }
            )
        )
        return 0

    first = True
    for d in packed:
        if not first:
            console.print("\n---\n")
        first = False
        console.print(d.path)
        console.print(d.text)
    return 0


def cmd_lint(args: argparse.Namespace) -> int:
    view = _load_view(args)
    profile_def = view.meta.get("profile_def") if isinstance(view.meta, dict) else None
    ruleset_name = effective_ruleset(cli_ruleset=getattr(args, "ruleset", None), profile_def=profile_def)
    ruleset_behavior = behavior_for_ruleset(ruleset_name)
    strict_placeholders = bool(args.strict_placeholders or ruleset_behavior.strict_placeholders)
    fail_on_warn = bool(args.fail_on_warn or ruleset_behavior.fail_on_warn)

    findings = lint_docs(view.concepts, view.relations, strict_placeholders=strict_placeholders)
    rule_filter: set[str] | None = None
    if args.rules and args.rules != "all":
        rule_filter = {x.strip() for x in args.rules.split(",") if x.strip()}
        unknown = sorted([r for r in rule_filter if r not in RULES])
        if unknown:
            raise SystemExit(f"unknown lint rule ids: {unknown}")
    if rule_filter is not None:
        findings = [f for f in findings if f.rule_id in rule_filter]
    if args.json:
        console.print_json(json.dumps({"findings": _findings_to_json(findings)}))
    else:
        if findings:
            console.print("[yellow]rocs lint[/yellow]")
            _print_findings(findings)
        else:
            console.print("[green]rocs lint: OK[/green]")
    if findings and fail_on_warn:
        return 1
    return 0


def cmd_check_inverses(args: argparse.Namespace) -> int:
    view = _load_view(args)
    findings = check_inverses(view.relations, fix=args.fix)
    if args.json:
        console.print_json(json.dumps({"findings": _findings_to_json(findings)}))
    else:
        if not findings:
            console.print("[green]rocs check-inverses: OK[/green]")
        else:
            console.print("[yellow]rocs check-inverses[/yellow]")
            _print_findings(findings)
    if any(f.severity == "error" for f in findings):
        return 1
    return 0


def cmd_graph(args: argparse.Namespace) -> int:
    view = _load_view(args)
    rel_filter: set[str] | None = None
    if args.scope == "taxonomy":
        rel_filter = {"is_a"}
    if args.relation:
        rel_filter = {args.relation}
    edges = build_edges(view.concepts, rel_filter=rel_filter)
    nodes = sorted(set(view.concepts.keys()) | {edge.src for edge in edges} | {edge.dst for edge in edges})
    if args.collapse_prefix:
        nodes, edges = collapse_nodes(nodes, edges, prefixes=args.collapse_prefix.split(","))
    layout = compute_layout(nodes, edges, layout=args.layout)
    if args.out:
        out = Path(args.out)
    else:
        dist = _ensure_dist_dir(view.repo, label="graph output dir")
        if args.json:
            out = ensure_managed_output_file(view.repo, dist / "graph.json", label="graph artifact")
        elif args.format == "dot":
            out = ensure_managed_output_file(view.repo, dist / "graph.dot", label="graph artifact")
        elif args.format == "excalidraw-cli-json":
            out = ensure_managed_output_file(view.repo, dist / "graph.excalidraw-cli.json", label="graph artifact")
        else:
            out = ensure_managed_output_file(view.repo, dist / "graph.excalidraw.json", label="graph artifact")
    direction = "LR" if args.layout == "dag" else "TB"
    fmt = "json" if args.json else args.format
    write_graph(out, fmt=fmt, nodes=nodes, edges=edges, layout=layout, direction=direction)
    if args.json:
        console.print_json(json.dumps({"ok": True, "out": str(out), "format": fmt}))
    else:
        console.print(f"[green]wrote[/green] {out}")
    return 0


def cmd_cache(args: argparse.Namespace) -> int:
    if args.subcmd == "dir":
        console.print(str(cache_dir()))
        return 0
    if args.subcmd == "ls":
        entries = list_cache_entries()
        for e in entries:
            console.print(f"{e.bytes:>12}  {e.path}")
        return 0
    if args.subcmd == "clear":
        clear_cache()
        console.print("[green]cache cleared[/green]")
        return 0
    if args.subcmd == "prune":
        removed = prune_cache(max_age_days=int(args.max_age_days))
        console.print(f"[green]pruned[/green] {removed}")
        return 0
    raise SystemExit(f"unknown cache subcmd: {args.subcmd}")


def cmd_vendored_check(args: argparse.Namespace) -> int:
    vendored_dir = Path(args.vendored_dir).resolve()
    ok, lines = verify_vendored_hashes(vendored_dir)
    if ok:
        console.print("[green]vendored-check: OK[/green]")
        return 0
    console.print("[red]vendored-check: FAIL[/red]")
    for ln in lines[:200]:
        console.print(f"- {ln}")
    if len(lines) > 200:
        console.print(f"... ({len(lines) - 200} more)")
    return 1


def cmd_normalize(args: argparse.Namespace) -> int:
    repo = _repo_root(args.repo)
    _maybe_load_env_file(getattr(args, "env_file", None), repo_root=repo)
    layers, _meta = resolve_layers(
        repo,
        profile=args.profile,
        resolve_refs=args.resolve_refs,
        workspace_root=args.workspace_root,
        workspace_ref_mode=args.workspace_ref_mode,
        only="path",
        layer=args.layer,
    )
    changed_paths: list[str] = []
    for layer_spec in layers:
        for c in normalize_tree(layer_spec.src_root, apply=args.apply):
            if c.changed:
                changed_paths.append(str(c.path))

    if changed_paths and not args.apply:
        console.print("[yellow]rocs normalize: changes needed (rerun with --apply)[/yellow]")
        for p in changed_paths[:50]:
            console.print(f"- {p}")
        if len(changed_paths) > 50:
            console.print(f"... ({len(changed_paths) - 50} more)")
        return 2

    if changed_paths and args.apply:
        console.print(f"[green]rocs normalize: applied[/green] ({len(changed_paths)} files)")
    else:
        console.print("[green]rocs normalize: OK[/green]")
    return 0


def _diff_sets(a: set[str], b: set[str]) -> tuple[list[str], list[str]]:
    removed = sorted(a - b)
    added = sorted(b - a)
    return removed, added


def cmd_diff(args: argparse.Namespace) -> int:
    repo = _repo_root(args.repo)
    _maybe_load_env_file(getattr(args, "env_file", None), repo_root=repo)
    baseline = args.baseline.strip()
    if not args.resolve_refs:
        raise SystemExit("rocs diff requires --resolve-refs to resolve a <repo:...@...> baseline")
    parsed = parse_ref_locator(baseline)
    if parsed is None:
        raise SystemExit("--baseline must be a <repo:...@...> locator")

    base_repo, _base_source, _base_notes = resolve_ref_repo_root(
        baseline,
        resolve_refs=args.resolve_refs,
        workspace_root=args.workspace_root,
        workspace_ref_mode=args.workspace_ref_mode,
    )

    cur_view = _load_view(args)
    base_view = _load_view(args, repo=base_repo)

    cur_edges = {f"{e.src}|{e.rel}|{e.dst}" for e in build_edges(cur_view.concepts, rel_filter=None)}
    base_edges = {f"{e.src}|{e.rel}|{e.dst}" for e in build_edges(base_view.concepts, rel_filter=None)}

    removed_concepts, added_concepts = _diff_sets(set(base_view.concepts.keys()), set(cur_view.concepts.keys()))
    removed_relations, added_relations = _diff_sets(set(base_view.relations.keys()), set(cur_view.relations.keys()))
    removed_edges, added_edges = _diff_sets(base_edges, cur_edges)

    breaking = {
        "removed_concepts": removed_concepts,
        "removed_relations": removed_relations,
        "removed_edges": removed_edges,
    }

    payload = {
        "schema_version": 1,
        "version": __version__,
        "repo": str(repo),
        "profile": cur_view.meta.get("profile")
        if isinstance(cur_view.meta, dict) and isinstance(cur_view.meta.get("profile"), str)
        else None,
        "baseline": baseline,
        "baseline_repo": str(base_repo),
        "diff": {
            "concepts": {"removed": removed_concepts, "added": added_concepts},
            "relations": {"removed": removed_relations, "added": added_relations},
            "edges": {"removed": removed_edges, "added": added_edges},
        },
        "breaking": breaking,
    }

    dist = _ensure_dist_dir(repo, label="diff output dir")
    out = ensure_managed_output_file(repo, dist / "diff.json", label="diff artifact")
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", "utf-8")

    if args.json:
        console.print_json(json.dumps(payload))
        return 0 if not (removed_concepts or removed_relations or removed_edges) else 2

    console.print(f"baseline: {baseline}")
    console.print(f"profile: {payload['profile']}")
    console.print(f"wrote: {out}")
    console.print(f"concepts: -{len(removed_concepts)} +{len(added_concepts)}")
    console.print(f"relations: -{len(removed_relations)} +{len(added_relations)}")
    console.print(f"edges: -{len(removed_edges)} +{len(added_edges)}")
    if removed_concepts or removed_relations or removed_edges:
        console.print("[yellow]breaking removals detected[/yellow]")
        return 2
    return 0


def cmd_context(args: argparse.Namespace) -> int:
    root = Path(args.root)
    inputs = []
    for spec in args.input:
        if ":" not in spec:
            raise SystemExit("--input must be LAYER:PATH where LAYER is path or ref")
        layer, path = spec.split(":", 1)
        inputs.append((path, layer))
    capsule = create_capsule(root, inputs)
    write_compiled_plan(
        Path(args.artifact_root),
        args.out,
        capsule,
        ontology_root=root,
        capsule=capsule,
        input_files=[root / path for path, _layer in inputs],
    )
    return 0


def cmd_proposal(args: argparse.Namespace) -> int:
    capsule = validate_capsule(load_membrane_json(Path(args.capsule)))
    proposal, digest = validate_proposal(load_membrane_json(Path(args.proposal)), capsule)
    if args.proposal_cmd == "validate":
        console.print_json(json.dumps({"ok": True, "proposal_digest": digest}, sort_keys=True))
        return 0
    plan = compile_plan(proposal, digest, capsule, load_membrane_json(Path(args.approval)))
    write_compiled_plan(
        Path(args.artifact_root),
        args.out,
        plan,
        ontology_root=Path(args.ontology_root),
        capsule=capsule,
        input_files=[Path(args.capsule), Path(args.proposal), Path(args.approval)],
    )
    return 0


def cmd_transaction(args: argparse.Namespace) -> int:
    load = lambda name: load_membrane_json(Path(getattr(args, name)))
    root = Path(args.ontology_root)
    if args.transaction_cmd == "prepare":
        value = prepare_transaction(
            load("plan"), load("capsule"), root, load("effects"), args.owner, load("authority_artifact")
        )
        write_compiled_plan(
            Path(args.artifact_root),
            args.out,
            value,
            ontology_root=root,
            capsule=validate_capsule(load("capsule")),
            input_files=[Path(args.plan), Path(args.capsule), Path(args.effects)],
        )
        return 0
    if args.transaction_cmd == "simulate":
        value = simulate_transaction(
            load("transaction"), load("plan"), load("capsule"), root, load("authority_artifact")
        )
    elif args.transaction_cmd == "apply":
        value = apply_transaction(
            load("transaction"),
            load("plan"),
            load("capsule"),
            load("approval"),
            root,
            Path(args.receipt_root),
            load("authority_artifact"),
            inject_failure=args.inject_failure,
        )
    elif args.transaction_cmd == "verify":
        value = verify_receipt(load("receipt"), load("transaction"), root)
    else:
        value = rollback_transaction(load("receipt"), load("transaction"), root)
    console.print_json(json.dumps(value, sort_keys=True))
    return 0


class _StrictArgumentParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)


def build_parser() -> argparse.ArgumentParser:
    parser = _StrictArgumentParser(prog="rocs")
    parser.add_argument("--version", action="version", version=f"rocs-cli {__version__}")
    parser.add_argument("--debug", action="store_true", help="show full tracebacks on error")
    parser.add_argument("--no-index-cache", action="store_true", help="disable incremental doc/index cache (debugging)")
    parser.add_argument("--index-cache-debug", action="store_true", help="emit index-cache hit/miss stats to stderr")

    p_resolve_common = argparse.ArgumentParser(add_help=False)
    p_resolve_common.add_argument(
        "--workspace-root",
        help="workspace root used to satisfy <repo:...@ref> refs locally (or ROCS_WORKSPACE_ROOT)",
    )
    p_resolve_common.add_argument(
        "--workspace-ref-mode",
        choices=["strict", "loose"],
        help="workspace ref mode for local clones: strict requires HEAD matches requested ref (or ROCS_WORKSPACE_REF_MODE)",
    )
    p_resolve_common.add_argument(
        "--show-resolve-sources",
        action="store_true",
        help="show path/workspace source per layer in text output",
    )
    p_resolve_common.add_argument(
        "--show-resolve-details",
        action="store_true",
        help="show workspace skip reasons (and include per-layer details in JSON output)",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("version")
    p.set_defaults(fn=cmd_version)

    p = sub.add_parser("contracts", help="emit the closed machine-readable command contract")
    p.set_defaults(fn=cmd_contracts)

    p = sub.add_parser("constitution", help="validate and challenge proposal-only constitutional rules")
    constitution_sub = p.add_subparsers(dest="constitution_cmd", required=True)
    for name in ("validate", "challenge"):
        p2 = constitution_sub.add_parser(name)
        p2.add_argument("--candidate", action="append", required=True)
        p2.set_defaults(fn=cmd_constitution, machine_json=True)
    p2 = constitution_sub.add_parser("differential")
    p2.add_argument("--candidate-a", action="append", required=True)
    p2.add_argument("--candidate-b", action="append", required=True)
    p2.add_argument("--subjects", action="append", required=True)
    p2.set_defaults(fn=cmd_constitution, machine_json=True)
    p2 = constitution_sub.add_parser("mutate")
    p2.add_argument("--contract", action="append", required=True)
    p2.add_argument("--acceptance", action="append", required=True)
    p2.add_argument("--corpus", action="append", required=True)
    p2.set_defaults(fn=cmd_constitution, machine_json=True)

    p = sub.add_parser("repair-market", help="compute a proposal-only stable Pareto frontier")
    p.add_argument("--market", action="append", required=True)
    p.set_defaults(fn=cmd_repair_market, machine_json=True)

    p = sub.add_parser("context", help="create a deterministic content-addressed context capsule")
    context_sub = p.add_subparsers(dest="context_cmd", required=True)
    p2 = context_sub.add_parser("create")
    p2.add_argument("--root", required=True)
    p2.add_argument("--input", action="append", required=True, metavar="LAYER:PATH")
    p2.add_argument("--artifact-root", required=True, help="existing disjoint root bounding capsule artifacts")
    p2.add_argument("--out", required=True, help="artifact-root-relative output path")
    p2.set_defaults(fn=cmd_context)

    p = sub.add_parser("proposal", help="validate or compile an untrusted proposal without mutation")
    proposal_sub = p.add_subparsers(dest="proposal_cmd", required=True)
    p2 = proposal_sub.add_parser("validate")
    p2.add_argument("--capsule", required=True)
    p2.add_argument("--proposal", required=True)
    p2.set_defaults(fn=cmd_proposal)
    p2 = proposal_sub.add_parser("compile")
    p2.add_argument("--capsule", required=True)
    p2.add_argument("--proposal", required=True)
    p2.add_argument("--approval", required=True)
    p2.add_argument("--ontology-root", required=True, help="source/input root forbidden to compiled artifacts")
    p2.add_argument("--artifact-root", required=True, help="existing disjoint root bounding compiled artifacts")
    p2.add_argument("--out", required=True, help="artifact-root-relative output path")
    p2.set_defaults(fn=cmd_proposal)

    p = sub.add_parser("transaction", help="prepare, simulate, apply, verify, or rollback a semantic transaction")
    transaction_sub = p.add_subparsers(dest="transaction_cmd", required=True)
    p2 = transaction_sub.add_parser("prepare")
    p2.add_argument("--plan", required=True)
    p2.add_argument("--capsule", required=True)
    p2.add_argument("--effects", required=True)
    p2.add_argument("--owner", required=True)
    p2.add_argument("--authority-artifact", required=True)
    p2.add_argument("--ontology-root", required=True)
    p2.add_argument("--artifact-root", required=True)
    p2.add_argument("--out", required=True)
    p2.set_defaults(fn=cmd_transaction)
    p2 = transaction_sub.add_parser("simulate")
    p2.add_argument("--transaction", required=True)
    p2.add_argument("--plan", required=True)
    p2.add_argument("--capsule", required=True)
    p2.add_argument("--authority-artifact", required=True)
    p2.add_argument("--ontology-root", required=True)
    p2.set_defaults(fn=cmd_transaction)
    p2 = transaction_sub.add_parser("apply")
    p2.add_argument("--transaction", required=True)
    p2.add_argument("--plan", required=True)
    p2.add_argument("--capsule", required=True)
    p2.add_argument("--approval", required=True)
    p2.add_argument("--authority-artifact", required=True)
    p2.add_argument("--ontology-root", required=True)
    p2.add_argument("--receipt-root", required=True)
    p2.add_argument("--inject-failure", help=argparse.SUPPRESS)
    p2.set_defaults(fn=cmd_transaction)
    for name in ("verify", "rollback"):
        p2 = transaction_sub.add_parser(name)
        p2.add_argument("--receipt", required=True)
        p2.add_argument("--transaction", required=True)
        p2.add_argument("--ontology-root", required=True)
        p2.set_defaults(fn=cmd_transaction)

    p = sub.add_parser("fleet", help="fleet observation and convergence")
    fleet_sub = p.add_subparsers(dest="fleet_cmd", required=True)
    p2 = fleet_sub.add_parser("observe", help="audit fleet capabilities deterministically")
    p2.add_argument("--workspace-root", required=True)
    p2.add_argument("--policy", required=True)
    p2.add_argument("--json", nargs="?", const="-", default=None, metavar="PATH")
    p2.add_argument("--markdown", nargs="?", const="-", default=None, metavar="PATH")
    p2.add_argument("--report-only", action="store_true")
    p2.set_defaults(fn=cmd_fleet)
    for name in ("plan", "apply", "run"):
        p2 = fleet_sub.add_parser(name, help=f"{name} deterministic fleet convergence")
        p2.add_argument("--workspace-root", required=True)
        p2.add_argument("--policy", required=True)
        p2.add_argument("--json", nargs="?", const="-", default=None)
        if name == "apply":
            p2.add_argument("--dry-run", action="store_true")
        if name == "run":
            p2.add_argument("--mode", choices=["audit-only", "patch", "apply"], default="apply")
        p2.set_defaults(fn=cmd_fleet)

    for name in ("bootstrap", "converge"):
        p = sub.add_parser(name, help=f"repository {name}")
        p.add_argument("target")
        p.add_argument("--class", dest="repo_class", required=True, choices=["required", "optional", "ontology_repo"])
        p.add_argument("--dry-run", action="store_true")
        p.set_defaults(fn=cmd_wave1, operation=name)
    p = sub.add_parser("vendor", help="publish a pinned self-contained consumer artifact")
    p.add_argument("target")
    p.add_argument("--release-version")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_wave1, operation="vendor")
    p = sub.add_parser("release", help="plan or apply an explicit release")
    release_sub = p.add_subparsers(dest="release_cmd", required=True)
    for name in ("plan", "apply"):
        p2 = release_sub.add_parser(name)
        p2.add_argument("--version", dest="release_version", required=True)
        p2.set_defaults(fn=cmd_wave1, operation=f"release-{name}")
    p = sub.add_parser("verify", help="verify pinned consumer identity and hashes")
    p.add_argument("path")
    p.set_defaults(fn=cmd_wave1, operation="verify")
    p = sub.add_parser("cleanup", help="safely remove managed build outputs")
    p.add_argument("--repo", default=".")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_wave1, operation="cleanup")
    p = sub.add_parser("doctor", help="check standalone consumer and tool identity")
    p.add_argument("--repo", default=".")
    p.set_defaults(fn=cmd_wave1, operation="doctor")
    p = sub.add_parser("generate", help="generate a deterministic benchmark repository")
    p.add_argument("--out", required=True)
    p.add_argument("--count", type=int, default=200)
    p.set_defaults(fn=cmd_wave1, operation="generate")
    p = sub.add_parser("benchmark", help="benchmark an importable ROCS capability")
    p.add_argument("--command", choices=["build", "validate", "lint"], default="build")
    p.add_argument("--count", type=int, default=500)
    p.add_argument("--runs", type=int, default=7)
    p.set_defaults(fn=cmd_wave1, operation="benchmark")

    p = sub.add_parser("rules")
    p.add_argument("--json", action="store_true", help="emit JSON output")
    p.set_defaults(fn=cmd_rules)

    p = sub.add_parser("explain")
    p.add_argument("rule_id")
    p.add_argument("--json", action="store_true", help="emit JSON output")
    p.set_defaults(fn=cmd_explain)

    p = sub.add_parser("resolve", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--json", action="store_true", help="emit JSON output")
    p.add_argument("--write-dist", action="store_true", help="write managed dist/resolve.json artifact")
    p.set_defaults(fn=cmd_resolve)

    p = sub.add_parser("summary", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--json", action="store_true", help="emit JSON output")
    p.set_defaults(fn=cmd_summary)

    p = sub.add_parser("validate", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--strict-placeholders", action="store_true", help="fail if any <...> placeholders exist")
    p.add_argument("--ruleset", choices=["dev", "strict"], help="ruleset defaults (or rocs.profiles.<name>.ruleset)")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument(
        "--validate-deps",
        action="store_true",
        help="also enforce strict schema rules on dependency layers (ref layers); default: validate path layers only",
    )
    p.add_argument("--json", action="store_true", help="emit JSON result")
    p.set_defaults(fn=cmd_validate)

    p = sub.add_parser("diff", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--baseline", required=True, help="baseline <repo:...@ref> to diff against")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--json", action="store_true", help="emit JSON diff")
    p.set_defaults(fn=cmd_diff)

    p = sub.add_parser("lint", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--strict-placeholders", action="store_true", help="treat placeholders in bodies as lint warnings")
    p.add_argument("--rules", default="all", help="comma-separated rule ids (or 'all')")
    p.add_argument("--json", action="store_true", help="emit JSON result")
    p.add_argument("--fail-on-warn", action="store_true", help="exit non-zero if warnings exist")
    p.add_argument("--ruleset", choices=["dev", "strict"], help="ruleset defaults (or rocs.profiles.<name>.ruleset)")
    p.set_defaults(fn=cmd_lint)

    p = sub.add_parser("check-inverses", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--fix", action="store_true", help="apply safe fixes to local/path layer relation docs")
    p.add_argument("--json", action="store_true", help="emit JSON result")
    p.set_defaults(fn=cmd_check_inverses)

    p = sub.add_parser("graph", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--scope", choices=["all", "taxonomy"], default="all")
    p.add_argument("--relation", help="only include this relation label (e.g. is_a)")
    p.add_argument("--collapse-prefix", help="comma-separated prefixes to collapse (e.g. co.software)")
    p.add_argument("--layout", choices=["grid", "dag"], default="grid")
    p.add_argument("--format", choices=["excalidraw", "excalidraw-cli-json", "dot"], default="excalidraw")
    p.add_argument("--json", action="store_true", help="emit JSON output (writes graph.json by default)")
    p.add_argument("--out", help="output path (default: managed dist/graph.<fmt>.*)")
    p.set_defaults(fn=cmd_graph)

    p = sub.add_parser("build", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--clean", action="store_true", help="remove the managed dist directory before building")
    p.add_argument("--json", action="store_true", help="emit JSON output")
    p.set_defaults(fn=cmd_build)

    p = sub.add_parser("pack", parents=[p_resolve_common])
    p.add_argument("ont_id")
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--only", help="filter layers: path|ref")
    p.add_argument("--layer", help="filter a specific layer name")
    p.add_argument("--depth", type=int, help="relation expansion depth (default: profile pack.max_depth or 0)")
    p.add_argument(
        "--rel-types", help="comma-separated relation labels to follow (default: profile pack.rel_types or all)"
    )
    p.add_argument("--include-relation-defs", action="store_true", help="include relation definition docs used")
    p.add_argument("--max-docs", type=int, help="max docs in pack (default: profile pack.max_docs)")
    p.add_argument("--max-bytes", type=int, help="max UTF-8 bytes in pack (default: profile pack.max_bytes)")
    p.add_argument("--json", action="store_true", help="emit JSON output")
    p.set_defaults(fn=cmd_pack)

    p = sub.add_parser("vendored-check")
    p.add_argument(
        "--vendored-dir", required=True, help="path to vendored rocs-cli dir (contains VENDORED_HASHES.json)"
    )
    p.set_defaults(fn=cmd_vendored_check)

    p = sub.add_parser("cache")
    sub2 = p.add_subparsers(dest="subcmd", required=True)
    p2 = sub2.add_parser("dir")
    p2.set_defaults(fn=cmd_cache)
    p2 = sub2.add_parser("ls")
    p2.set_defaults(fn=cmd_cache)
    p2 = sub2.add_parser("clear")
    p2.set_defaults(fn=cmd_cache)
    p2 = sub2.add_parser("prune")
    p2.add_argument("--max-age-days", default="30")
    p2.set_defaults(fn=cmd_cache)

    p = sub.add_parser("normalize", parents=[p_resolve_common])
    p.add_argument("--repo", default=".", help="repo root path")
    p.add_argument("--profile", help="manifest profile name (defaults to rocs.profiles.default)")
    p.add_argument(
        "--resolve-refs",
        action="store_true",
        help="resolve <repo:...@...> refs from the local workspace",
    )
    p.add_argument("--env-file", help="dotenv file to load into environment (for local config)")
    p.add_argument("--layer", help="only normalize a specific layer name (path layers only)")
    p.add_argument("--apply", action="store_true", help="apply changes (default: check only)")
    p.set_defaults(fn=cmd_normalize)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    debug = bool(getattr(args, "debug", False))
    if bool(getattr(args, "no_index_cache", False)):
        os.environ["ROCS_INDEX_CACHE"] = "0"
    if bool(getattr(args, "index_cache_debug", False)):
        os.environ["ROCS_INDEX_CACHE_DEBUG"] = "1"

    def _wants_json() -> bool:
        return bool(getattr(args, "json", False) or getattr(args, "machine_json", False))

    def _emit_error(kind: str, message: str, *, details: dict | None = None) -> None:
        if _wants_json():
            payload: dict = {"ok": False, "error": {"kind": kind, "message": message}}
            if details:
                payload["error"]["details"] = details
            console.print_json(json.dumps(payload))
        else:
            console.print(f"[red]error[/red]: {message}")

    try:
        code = int(args.fn(args))
    except RocsCliError as e:
        if debug:
            raise
        _emit_error(e.kind, e.message, details=e.details)
        raise SystemExit(int(e.exit_code)) from None
    except SystemExit as e:
        if debug:
            raise
        # Normalize our "raise SystemExit('message')" cases into clean CLI output.
        if isinstance(e.code, str) and e.code.strip():
            _emit_error("error", e.code)
            raise SystemExit(1) from None
        raise
    except Exception as e:  # noqa: BLE001
        if debug:
            raise
        _emit_error("internal", str(e))
        raise SystemExit(1) from None
    raise SystemExit(code)
