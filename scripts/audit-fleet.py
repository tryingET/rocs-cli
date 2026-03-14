#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml


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
)

ROCS_CI_SNIPPET_CANDIDATES: tuple[str, ...] = (
    "gitlab/ci/rocs.yml",
    "gitlab/ci/rocs.yml.j2",
    "gitlab/ci/rocs.yml.jinja",
)

ROOT_CI_CANDIDATES: tuple[str, ...] = (
    ".gitlab-ci.yml",
    ".gitlab-ci.yml.j2",
    ".gitlab-ci.yml.jinja",
)


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
        raw = yaml.safe_load(path.read_text("utf-8"))
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


def _normalize_policy_repo_path(workspace_root: Path, policy_path: str) -> Path:
    p = Path(policy_path)
    if p.is_absolute():
        return p

    direct = workspace_root / p
    if direct.exists():
        return direct

    parts = p.parts
    if parts and parts[0] == workspace_root.name:
        trimmed = workspace_root.joinpath(*parts[1:])
        if trimmed.exists():
            return trimmed
        return trimmed

    return direct


def _find_existing(base: Path, candidates: tuple[str, ...]) -> list[str]:
    found: list[str] = []
    for rel in candidates:
        p = base / rel
        if p.is_file():
            found.append(rel)
    return found


def _ci_include_present(base: Path) -> tuple[bool, list[str]]:
    checked: list[str] = []
    for rel in ROOT_CI_CANDIDATES:
        p = base / rel
        if not p.is_file():
            continue
        checked.append(rel)
        try:
            text = p.read_text("utf-8")
        except UnicodeDecodeError:
            continue
        if "gitlab/ci/rocs.yml" in text:
            return True, checked
    return False, checked


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
    vendored_hash_path = resolved_path / "tools" / "rocs-cli" / "VENDORED_HASHES.json"
    rocs_cli_vendored = False
    vendored_reason = "missing"
    if vendored_hash_path.is_file():
        try:
            payload = json.loads(vendored_hash_path.read_text("utf-8"))
            if payload.get("schema_version") == 1 and isinstance(payload.get("files"), dict):
                rocs_cli_vendored = True
                vendored_reason = "ok"
            else:
                vendored_reason = "invalid_hash_schema"
        except json.JSONDecodeError:
            vendored_reason = "invalid_json"

    manifest_hits = _find_existing(resolved_path, MANIFEST_CANDIDATES)
    ci_snippet_hits = _find_existing(resolved_path, ROCS_CI_SNIPPET_CANDIDATES)
    ci_include_present, ci_roots_checked = _ci_include_present(resolved_path)

    observed = {
        "rocs_cli_vendored": rocs_cli_vendored,
        "ontology_manifest": bool(manifest_hits),
        "rocs_ci_gate": bool(ci_snippet_hits) and ci_include_present,
    }

    evidence = {
        "rocs_cli_vendored": {
            "hash_file": "tools/rocs-cli/VENDORED_HASHES.json",
            "status": vendored_reason,
        },
        "ontology_manifest": {
            "hits": manifest_hits,
        },
        "rocs_ci_gate": {
            "snippet_hits": ci_snippet_hits,
            "ci_roots_checked": ci_roots_checked,
            "include_present": ci_include_present,
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
        resolved = _normalize_policy_repo_path(workspace_root, policy_repo_path)
        exists = resolved.is_dir()

        repo_class = str(entry.get("class"))
        expected_caps = _sort_caps(repo_classes[repo_class]["required_capabilities"])
        declared_caps = _sort_caps(entry.get("capabilities", {}))

        if exists:
            observed_caps, evidence = _detect_capabilities(resolved)
        else:
            observed_caps = {k: False for k in CAPABILITY_KEYS}
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
    except PolicyError as exc:
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
