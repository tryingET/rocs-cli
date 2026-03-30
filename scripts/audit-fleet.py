#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from rocs_cli.fcos_gate import (  # noqa: E402
    FCOS_CI_WRAPPER_CANDIDATES,
    FCOS_CI_WRAPPER_TEMPLATE_CANDIDATES,
    FCOS_GATE_HOOK_CANDIDATES,
    FCOS_GATE_HOOK_PATH,
    FCOS_GATE_HOOK_TEMPLATE_CANDIDATES,
    LEGACY_FCOS_GATE_CANDIDATES,
    hook_contract_evidence,
    wrapper_workspace_contract_evidence,
)
from rocs_cli.fleet_preflight import (  # noqa: E402
    FileProbe,
    FleetPreflightError,
    normalize_policy_repo_path,
    probe_managed_candidates,
    read_utf8_text,
)
from rocs_cli.managed_surface import strip_hash_comments, yaml_scalar_strings  # noqa: E402


EXIT_OK = 0
EXIT_ERROR = 1
EXIT_VIOLATIONS = 2

CAPABILITY_KEYS: tuple[str, ...] = (
    "rocs_cli_vendored",
    "ontology_manifest",
    "rocs_ci_gate",
)

MANIFEST_CANDIDATES: tuple[str, ...] = (
    "ontology/manifest.yaml",
    "ontology/manifest.yml",
    "ontology/manifest.yaml.j2",
    "ontology/manifest.yml.j2",
    "ontology/manifest.yaml.jinja",
    "ontology/manifest.yml.jinja",
    "manifest.yaml",
    "manifest.yml",
    "manifest.yaml.j2",
    "manifest.yml.j2",
    "manifest.yaml.jinja",
    "manifest.yml.jinja",
)

LOCATOR_RE = re.compile(r"<(?P<kind>repo|gitlab):[^>]+>")


class PolicyError(ValueError):
    pass


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit FCOS fleet policy capabilities and emit deterministic scorecards."
    )
    parser.add_argument("--workspace-root", required=True, help="Workspace root containing local repos")
    parser.add_argument("--policy", required=True, help="Path to fleet-state.yaml")
    parser.add_argument(
        "--json",
        nargs="?",
        const="-",
        default=None,
        metavar="PATH",
        help="Emit JSON scorecard (default stdout when PATH omitted)",
    )
    parser.add_argument(
        "--markdown",
        nargs="?",
        const="-",
        default=None,
        metavar="PATH",
        help="Emit Markdown scorecard (default stdout when PATH omitted)",
    )
    parser.add_argument(
        "--report-only",
        action="store_true",
        help="Always exit 0 even when capability violations are found",
    )
    return parser.parse_args()


def _load_policy(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise PolicyError(f"policy not found: {path}")
    try:
        raw = yaml.safe_load(read_utf8_text(path, label="policy"))
    except FleetPreflightError as exc:
        raise PolicyError(str(exc)) from exc
    except yaml.YAMLError as exc:
        raise PolicyError(f"invalid YAML: {exc}") from exc
    if not isinstance(raw, dict):
        raise PolicyError("policy root must be a mapping")
    return raw


def _require_mapping(parent: dict[str, Any], key: str, *, where: str) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        raise PolicyError(f"{where}.{key} must be a mapping")
    return value


def _require_list(parent: dict[str, Any], key: str, *, where: str) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        raise PolicyError(f"{where}.{key} must be a list")
    return value


def _validate_policy(policy: dict[str, Any]) -> None:
    schema = _require_mapping(policy, "schema", where="policy")
    required_repo_fields = schema.get("repo_entry_required_fields")
    if not isinstance(required_repo_fields, list) or not all(isinstance(x, str) for x in required_repo_fields):
        raise PolicyError("policy.schema.repo_entry_required_fields must be a list[str]")

    repo_classes = _require_mapping(policy, "repo_classes", where="policy")
    if not repo_classes:
        raise PolicyError("policy.repo_classes must not be empty")

    for class_name, class_spec in repo_classes.items():
        if not isinstance(class_spec, dict):
            raise PolicyError(f"policy.repo_classes.{class_name} must be a mapping")
        required_caps = class_spec.get("required_capabilities")
        if not isinstance(required_caps, dict):
            raise PolicyError(f"policy.repo_classes.{class_name}.required_capabilities must be a mapping")
        for key in CAPABILITY_KEYS:
            if key not in required_caps:
                raise PolicyError(
                    f"policy.repo_classes.{class_name}.required_capabilities missing key {key!r}"
                )

    fleet = _require_mapping(policy, "fleet", where="policy")
    repos = _require_list(fleet, "repos", where="policy.fleet")

    for idx, entry_any in enumerate(repos):
        if not isinstance(entry_any, dict):
            raise PolicyError(f"policy.fleet.repos[{idx}] must be a mapping")
        entry = entry_any
        missing = [field for field in required_repo_fields if field not in entry]
        if missing:
            raise PolicyError(f"policy.fleet.repos[{idx}] missing required fields: {', '.join(missing)}")
        cls = entry.get("class")
        if cls not in repo_classes:
            raise PolicyError(f"policy.fleet.repos[{idx}] class {cls!r} not declared in policy.repo_classes")
        caps = entry.get("capabilities")
        if not isinstance(caps, dict):
            raise PolicyError(f"policy.fleet.repos[{idx}].capabilities must be a mapping")


def _probe_paths(base: Path, candidates: tuple[str, ...], *, label: str, load_text: bool = False) -> list[FileProbe]:
    return probe_managed_candidates(base, candidates, label=label, load_text=load_text)


def _valid_hits(probes: list[FileProbe]) -> list[str]:
    return [probe.relpath for probe in probes if probe.valid]


def _blocked_hits(probes: list[FileProbe]) -> list[dict[str, str]]:
    return [
        {"path": probe.relpath, "reason": str(probe.blocker or "unknown")}
        for probe in probes
        if probe.present and not probe.valid
    ]


def _manifest_contract_status(manifest_probes: list[FileProbe]) -> tuple[bool, dict[str, Any], bool]:
    valid_probes = [probe for probe in manifest_probes if probe.valid]
    blocked_hits = _blocked_hits(manifest_probes)
    if not valid_probes:
        evidence: dict[str, Any] = {"primary_hit": None, "locator_kind": "missing", "locators": []}
        if blocked_hits:
            evidence.update(
                {
                    "primary_hit": blocked_hits[0]["path"],
                    "locator_kind": "invalid",
                    "parse_error": blocked_hits[0]["reason"],
                    "blocked_hits": blocked_hits,
                }
            )
        return False, evidence, False

    primary_probe = valid_probes[0]
    text = primary_probe.text or ""
    scalar_strings = yaml_scalar_strings(text)
    if scalar_strings is not None:
        locator_source = "yaml_scalars"
        locator_chunks = scalar_strings
    else:
        locator_source = "comment_stripped_text"
        locator_chunks = [strip_hash_comments(text)]

    locators = [
        {"kind": match.group("kind"), "value": match.group(0)}
        for chunk in locator_chunks
        for match in LOCATOR_RE.finditer(chunk)
    ]
    repo_locators = [entry["value"] for entry in locators if entry["kind"] == "repo"]
    gitlab_locators = [entry["value"] for entry in locators if entry["kind"] == "gitlab"]

    if gitlab_locators and repo_locators:
        locator_kind = "mixed"
    elif gitlab_locators:
        locator_kind = "gitlab"
    elif repo_locators:
        locator_kind = "repo"
    else:
        locator_kind = "none"

    contract_ok = not gitlab_locators
    evidence = {
        "primary_hit": primary_probe.relpath,
        "locator_kind": locator_kind,
        "locator_source": locator_source,
        "locators": locators,
        "requires_workspace_contract": bool(repo_locators),
    }
    if blocked_hits:
        evidence["blocked_hits"] = blocked_hits
    if gitlab_locators:
        evidence["contract_reason"] = "legacy_gitlab_locators"

    return contract_ok, evidence, bool(repo_locators)


def _wrapper_workspace_contract(wrapper_probes: list[FileProbe]) -> tuple[bool, dict[str, Any]]:
    valid_probes = [probe for probe in wrapper_probes if probe.valid]
    checked: list[str] = [probe.relpath for probe in valid_probes]
    workspace_root_present = False
    workspace_ref_mode_present = False
    wrapper_contract_lines: list[dict[str, Any]] = []

    for probe in valid_probes:
        contract = wrapper_workspace_contract_evidence(probe.text or "")
        wrapper_contract_lines.append({"path": probe.relpath, "lines": contract["lines"]})
        workspace_root_present = workspace_root_present or bool(contract["workspace_root_present"])
        workspace_ref_mode_present = workspace_ref_mode_present or bool(contract["workspace_ref_mode_present"])

    ok = workspace_root_present and workspace_ref_mode_present
    evidence: dict[str, Any] = {
        "wrapper_workspace_checked": checked,
        "wrapper_contract_lines": wrapper_contract_lines,
        "workspace_root_present": workspace_root_present,
        "workspace_ref_mode_present": workspace_ref_mode_present,
    }
    blocked_hits = _blocked_hits(wrapper_probes)
    if blocked_hits:
        evidence["wrapper_workspace_blocked_hits"] = blocked_hits
    return ok, evidence


def _hook_contract_status(base: Path, *, requires_workspace_contract: bool) -> tuple[bool, dict[str, Any]]:
    hook_probes = _probe_paths(base, FCOS_GATE_HOOK_CANDIDATES, label="ROCS gate hook", load_text=True)
    hook_template_probes = _probe_paths(base, FCOS_GATE_HOOK_TEMPLATE_CANDIDATES, label="ROCS gate hook template")
    wrapper_probes = _probe_paths(base, FCOS_CI_WRAPPER_CANDIDATES, label="ROCS CI wrapper", load_text=True)
    wrapper_template_probes = _probe_paths(base, FCOS_CI_WRAPPER_TEMPLATE_CANDIDATES, label="ROCS CI wrapper template")
    legacy_gate_probes = _probe_paths(base, LEGACY_FCOS_GATE_CANDIDATES, label="legacy ROCS gate")
    wrapper_call_present = False
    profile_contract_present = False
    hook_contract_checked: list[str] = []
    hook_contexts_checked: list[dict[str, Any]] = []
    hook_exec_checked: dict[str, bool] = {}
    hook_exec_required = False
    hook_exec_present = False

    valid_hook_probes = [probe for probe in hook_probes if probe.valid]
    for probe in valid_hook_probes:
        hook_contract_checked.append(probe.relpath)

        exec_required = probe.relpath == FCOS_GATE_HOOK_PATH
        is_executable = True
        if exec_required:
            hook_exec_required = True
            try:
                is_executable = bool(probe.path.stat().st_mode & 0o111)
            except OSError:
                is_executable = False
            hook_exec_checked[probe.relpath] = is_executable
            if is_executable:
                hook_exec_present = True

        contract = hook_contract_evidence(probe.text or "")
        hook_contexts_checked.append({"path": probe.relpath, "lines": contract["lines"]})
        if contract["wrapper_call_present"]:
            wrapper_call_present = True
        if contract["profile_contract_present"]:
            profile_contract_present = True

    workspace_contract_ok, workspace_contract_evidence = _wrapper_workspace_contract(wrapper_probes)

    hook_hits = _valid_hits(hook_probes)
    wrapper_hits = _valid_hits(wrapper_probes)
    ok = bool(hook_hits) and bool(wrapper_hits) and wrapper_call_present and profile_contract_present
    if hook_exec_required:
        ok = ok and hook_exec_present
    if requires_workspace_contract:
        ok = ok and workspace_contract_ok

    evidence = {
        "hook_hits": hook_hits,
        "hook_template_hits": _valid_hits(hook_template_probes),
        "hook_blocked_hits": _blocked_hits(hook_probes),
        "hook_template_blocked_hits": _blocked_hits(hook_template_probes),
        "wrapper_hits": wrapper_hits,
        "wrapper_template_hits": _valid_hits(wrapper_template_probes),
        "wrapper_template_blocked_hits": _blocked_hits(wrapper_template_probes),
        "legacy_gate_hits": _valid_hits(legacy_gate_probes),
        "legacy_gate_blocked_hits": _blocked_hits(legacy_gate_probes),
        "hook_contract_checked": hook_contract_checked,
        "hook_exec_required": hook_exec_required,
        "hook_exec_present": hook_exec_present,
        "hook_exec_checked": hook_exec_checked,
        "wrapper_call_present": wrapper_call_present,
        "profile_contract_present": profile_contract_present,
        "workspace_contract_required": requires_workspace_contract,
        **workspace_contract_evidence,
        "hook_contexts_checked": hook_contexts_checked,
    }
    return ok, evidence


def _safe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    return None


def _detect_capabilities(resolved_path: Path) -> tuple[dict[str, bool], dict[str, Any]]:
    vendored_probes = _probe_paths(
        resolved_path,
        ("tools/rocs-cli/VENDORED_HASHES.json",),
        label="vendored hash file",
        load_text=True,
    )
    vendored_probe = vendored_probes[0] if vendored_probes else None
    rocs_cli_vendored = False
    vendored_reason = "missing"
    if vendored_probe is not None:
        if not vendored_probe.valid:
            vendored_reason = str(vendored_probe.blocker or "invalid")
        else:
            try:
                payload = json.loads(vendored_probe.text or "")
                if payload.get("schema_version") == 1 and isinstance(payload.get("files"), dict):
                    rocs_cli_vendored = True
                    vendored_reason = "ok"
                else:
                    vendored_reason = "invalid_hash_schema"
            except json.JSONDecodeError:
                vendored_reason = "invalid_json"

    manifest_probes = _probe_paths(resolved_path, MANIFEST_CANDIDATES, label="ontology manifest", load_text=True)
    manifest_hits = _valid_hits(manifest_probes)
    manifest_contract_ok, manifest_contract_evidence, requires_workspace_contract = _manifest_contract_status(manifest_probes)
    hook_contract_ok, hook_contract_evidence = _hook_contract_status(
        resolved_path,
        requires_workspace_contract=requires_workspace_contract,
    )

    observed = {
        "rocs_cli_vendored": rocs_cli_vendored,
        "ontology_manifest": bool(manifest_hits) and manifest_contract_ok,
        "rocs_ci_gate": bool(hook_contract_evidence.get("hook_hits")) and hook_contract_ok,
    }

    evidence = {
        "rocs_cli_vendored": {
            "hash_file": "tools/rocs-cli/VENDORED_HASHES.json",
            "status": vendored_reason,
            "blocked_hits": _blocked_hits(vendored_probes),
        },
        "ontology_manifest": {
            "hits": manifest_hits,
            **manifest_contract_evidence,
        },
        "rocs_ci_gate": {
            **hook_contract_evidence,
        },
    }
    return observed, evidence


def _sort_caps(caps: dict[str, Any]) -> dict[str, Any]:
    return {k: caps.get(k) for k in CAPABILITY_KEYS}


def _build_scorecard(policy: dict[str, Any], *, workspace_root: Path, policy_path: Path, report_only: bool) -> dict[str, Any]:
    repo_classes = policy["repo_classes"]
    fleet_entries = policy["fleet"]["repos"]
    kill_switch_mode = (
        policy.get("kill_switch", {})
        .get("fcos_enforcement", {})
        .get("mode", "unknown")
    )

    repo_rows: list[dict[str, Any]] = []
    total_require_violations = 0
    total_decl_drifts = 0

    for entry_any in sorted(fleet_entries, key=lambda x: str(x.get("path", ""))):
        entry = dict(entry_any)
        policy_repo_path = str(entry.get("path", ""))
        resolved, path_issue = normalize_policy_repo_path(workspace_root, policy_repo_path)
        exists = path_issue is None and resolved.is_dir()

        repo_class = str(entry.get("class"))
        expected_caps = _sort_caps(repo_classes[repo_class]["required_capabilities"])
        declared_caps = _sort_caps(entry.get("capabilities", {}))

        if exists:
            observed_caps, evidence = _detect_capabilities(resolved)
        else:
            observed_caps = {k: False for k in CAPABILITY_KEYS}
            if path_issue is not None:
                evidence = {
                    "path_boundary": {
                        "resolved": str(resolved),
                        "reason": path_issue,
                    }
                }
            else:
                evidence = {
                    "missing_path": {
                        "resolved": str(resolved),
                    }
                }

        requirement_violations: list[str] = []
        for key in CAPABILITY_KEYS:
            if expected_caps.get(key) is True and observed_caps.get(key) is not True:
                requirement_violations.append(key)

        declaration_drifts: list[str] = []
        for key in CAPABILITY_KEYS:
            declared_bool = _safe_bool(declared_caps.get(key))
            if declared_bool is None:
                continue
            if declared_bool != observed_caps.get(key):
                declaration_drifts.append(key)

        total_require_violations += len(requirement_violations)
        total_decl_drifts += len(declaration_drifts)

        row = {
            "path": policy_repo_path,
            "resolved_path": str(resolved),
            "scope": entry.get("scope"),
            "class": repo_class,
            "state": entry.get("state"),
            "owner": entry.get("owner"),
            "exists": exists,
            "expected_capabilities": expected_caps,
            "declared_capabilities": declared_caps,
            "observed_capabilities": observed_caps,
            "requirement_violations": requirement_violations,
            "declaration_drifts": declaration_drifts,
            "evidence": evidence,
        }
        repo_rows.append(row)

    requirement_violation_entries = [r for r in repo_rows if r["requirement_violations"]]
    declaration_drift_entries = [r for r in repo_rows if r["declaration_drifts"]]

    exit_code = EXIT_OK if total_require_violations == 0 else EXIT_VIOLATIONS
    if report_only:
        exit_code = EXIT_OK

    summary = {
        "total_entries": len(repo_rows),
        "existing_entries": sum(1 for r in repo_rows if r["exists"]),
        "missing_entries": sum(1 for r in repo_rows if not r["exists"]),
        "requirement_violation_entries": len(requirement_violation_entries),
        "requirement_violations": total_require_violations,
        "declaration_drift_entries": len(declaration_drift_entries),
        "declaration_drifts": total_decl_drifts,
        "status": "pass" if total_require_violations == 0 else "fail",
    }

    return {
        "schema_version": 1,
        "workspace_root": str(workspace_root),
        "policy": str(policy_path),
        "kill_switch_mode": kill_switch_mode,
        "report_only": report_only,
        "summary": summary,
        "repos": repo_rows,
        "violations": {
            "required_capabilities": [
                {
                    "path": r["path"],
                    "class": r["class"],
                    "missing": r["requirement_violations"],
                }
                for r in requirement_violation_entries
            ],
            "declaration_drifts": [
                {
                    "path": r["path"],
                    "class": r["class"],
                    "drifts": r["declaration_drifts"],
                }
                for r in declaration_drift_entries
            ],
        },
        "exit_code": exit_code,
        "exit_codes": {
            "ok": EXIT_OK,
            "error": EXIT_ERROR,
            "violations": EXIT_VIOLATIONS,
        },
    }


def _yn(value: bool) -> str:
    return "yes" if value else "no"


def _render_markdown(scorecard: dict[str, Any]) -> str:
    s = scorecard["summary"]
    lines: list[str] = []
    lines.append("# FCOS Fleet Audit Scorecard")
    lines.append("")
    lines.append(f"- workspace_root: `{scorecard['workspace_root']}`")
    lines.append(f"- policy: `{scorecard['policy']}`")
    lines.append(f"- kill_switch_mode: `{scorecard['kill_switch_mode']}`")
    lines.append(f"- report_only: `{str(scorecard['report_only']).lower()}`")
    lines.append(f"- status: `{s['status']}`")
    lines.append(f"- suggested_exit_code: `{scorecard['exit_code']}`")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| metric | value |")
    lines.append("|---|---:|")
    lines.append(f"| total_entries | {s['total_entries']} |")
    lines.append(f"| existing_entries | {s['existing_entries']} |")
    lines.append(f"| missing_entries | {s['missing_entries']} |")
    lines.append(f"| requirement_violation_entries | {s['requirement_violation_entries']} |")
    lines.append(f"| requirement_violations | {s['requirement_violations']} |")
    lines.append(f"| declaration_drift_entries | {s['declaration_drift_entries']} |")
    lines.append(f"| declaration_drifts | {s['declaration_drifts']} |")
    lines.append("")

    req_viol = scorecard["violations"]["required_capabilities"]
    lines.append("## Required Capability Violations")
    lines.append("")
    if not req_viol:
        lines.append("none")
        lines.append("")
    else:
        lines.append("| path | class | missing_required_capabilities |")
        lines.append("|---|---|---|")
        for row in req_viol:
            lines.append(f"| `{row['path']}` | `{row['class']}` | `{', '.join(row['missing'])}` |")
        lines.append("")

    lines.append("## Repo Results")
    lines.append("")
    lines.append(
        "| path | class | exists | rocs_cli_vendored | ontology_manifest | rocs_ci_gate | required_missing | declaration_drifts |"
    )
    lines.append("|---|---|---|---|---|---|---|---|")
    for row in scorecard["repos"]:
        obs = row["observed_capabilities"]
        missing = ", ".join(row["requirement_violations"]) or "-"
        drifts = ", ".join(row["declaration_drifts"]) or "-"
        lines.append(
            "| `{path}` | `{cls}` | {exists} | {vendored} | {manifest} | {ci} | `{missing}` | `{drifts}` |".format(
                path=row["path"],
                cls=row["class"],
                exists=_yn(bool(row["exists"])),
                vendored=_yn(bool(obs.get("rocs_cli_vendored"))),
                manifest=_yn(bool(obs.get("ontology_manifest"))),
                ci=_yn(bool(obs.get("rocs_ci_gate"))),
                missing=missing,
                drifts=drifts,
            )
        )

    return "\n".join(lines).rstrip() + "\n"


def _write_output(dest: str, payload: str) -> None:
    if dest == "-":
        sys.stdout.write(payload)
        return
    out = Path(dest).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(payload, "utf-8")


def main() -> int:
    args = _parse_args()

    workspace_root = Path(args.workspace_root).expanduser().resolve()
    policy_path = Path(args.policy).expanduser().resolve()

    if not workspace_root.is_dir():
        print(f"error: workspace root not found: {workspace_root}", file=sys.stderr)
        return EXIT_ERROR

    try:
        policy = _load_policy(policy_path)
        _validate_policy(policy)
        scorecard = _build_scorecard(
            policy,
            workspace_root=workspace_root,
            policy_path=policy_path,
            report_only=bool(args.report_only),
        )
    except (PolicyError, FleetPreflightError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    json_payload = json.dumps(scorecard, indent=2, sort_keys=True) + "\n"
    md_payload = _render_markdown(scorecard)

    json_dest = args.json
    md_dest = args.markdown

    if json_dest is None and md_dest is None:
        json_dest = "-"

    if json_dest == "-" and md_dest == "-":
        sys.stdout.write(json_payload)
        sys.stdout.write("\n---\n\n")
        sys.stdout.write(md_payload)
    else:
        if json_dest is not None:
            _write_output(json_dest, json_payload)
        if md_dest is not None:
            _write_output(md_dest, md_payload)

    return int(scorecard["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
