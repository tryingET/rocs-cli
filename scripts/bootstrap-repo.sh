#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: scripts/bootstrap-repo.sh <target> --class required|optional|ontology_repo [--dry-run]"
  echo
  echo "Bootstraps FCOS baseline files into <target> using class policy."
  echo "- required: vendored rocs-cli + ontology scaffold + CI gate (advisory)"
  echo "- optional: inventory-only (no mandatory files)"
  echo "- ontology_repo: vendored rocs-cli + ontology overlay scaffold + CI gate (strict)"
}

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

TARGET=""
REPO_CLASS=""
DRY_RUN=0

while (($# > 0)); do
  case "$1" in
    --class)
      if (($# < 2)); then
        echo "error: --class requires a value" >&2
        usage >&2
        exit 2
      fi
      REPO_CLASS="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    -*)
      echo "error: unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$TARGET" ]]; then
        echo "error: unexpected positional argument: $1" >&2
        usage >&2
        exit 2
      fi
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "error: missing required <target>" >&2
  usage >&2
  exit 2
fi

if [[ -z "$REPO_CLASS" ]]; then
  echo "error: missing required --class" >&2
  usage >&2
  exit 2
fi

python3 - "$ROOT" "$TARGET" "$REPO_CLASS" "$DRY_RUN" <<'PY'
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict

import yaml


def norm(text: str) -> str:
    return textwrap.dedent(text).strip("\n") + "\n"


REPO_MANIFEST = norm(
    """
    rocs:
      layers:
        - name: core
          ref: "<repo:core/ontology-kernel@main>"
        - name: company
          ref: "<repo:softwareco/ontology@main>"
        - name: repo
          path: "ontology/src"
      profiles:
        default: "repo-dev"
        guiding-circle:
          include_layers: ["core", "company"]
          exclude_layers: ["repo"]
          budget: 1800
        repo-dev:
          include_layers: ["core", "company", "repo"]
          budget: 2800
    """
)

ONTOLOGY_REPO_MANIFEST = norm(
    """
    rocs:
      layer: company
      id: "<org.company>"
      version: "0.1.0"
      created: "<YYYY-MM-DD>"
      owners:
        - "@org-owners"
      depends_on:
        - layer: core
          ref: "<repo:core/ontology-kernel@main>"
    """
)

ONTOLOGY_INDEX = norm(
    """
    # Ontology Index (repo)

    Start here when browsing manually.

    - `ontology/manifest.yaml` — which layers apply
    - `ontology/src/system4d.yaml` — repo-local System4D (implementation)
    - `ontology/src/reference/concepts/` — repo-local concepts (only when needed)
    - `ontology/src/bridge/mapping.yaml` — map concepts to code symbols
    - `ontology/dist/` — generated artifacts (tool-first)

    Tip: Use `uvx --from ./tools/rocs-cli rocs pack <concept_id>` instead of opening many files.
    """
)

REPO_SYSTEM4D = norm(
    """
    ontology:
      system4d:
        name: "<Repo Name>"
        version: "0.1"
        container:
          boundary:
            in_scope:
              - "<what this repo implements>"
            out_of_scope:
              - "<explicitly not implemented here>"
          constraints:
            - "<runtime/tech constraints>"
          edges:
            - name: "<integration>"
              direction: "bi"
              protocol: "<http|kafka|file>"
              system: "<external system>"
              contract: "<link/spec>"
          dependencies:
            - name: "<dependency>"
              type: "<runtime|build|infra>"
              note: "<why>"
          anti_goals:
            - "<nice-to-have killed>"
        compass:
          drivers:
            - "<why now>"
          outcomes:
            - "<value>"
          tradeoffs:
            - decision: "<tradeoff>"
              chosen: "<choice>"
              because: "<why>"
        engine:
          triggers:
            - "<trigger>"
          states:
            - name: "<state>"
              meaning: "<meaning>"
          invariants:
            - id: "<REPO-INV-001>"
              statement: "<golden rule>"
              enforcement: "<test|db|policy>"
          lifecycle:
            - "<lifecycle>"
        fog:
          assumptions:
            - id: "<REPO-A-001>"
              statement: "<assumption>"
              how_to_validate: "<validation>"
          risks:
            - id: "<REPO-R-001>"
              statement: "<risk>"
              mitigation: "<mitigation>"
          exceptions:
            - id: "REPO-E-INCIDENT"
              statement: "Incident hotfix allowed"
              reason: "Record Exception immediately and Debt immediately"
          debt:
            - id: "<REPO-D-001>"
              statement: "<debt>"
              payoff_plan: "<plan>"
    """
)

ONTOLOGY_REPO_SYSTEM4D = norm(
    """
    ontology:
      system4d:
        name: "<Company Overlay>"
        version: "0.1"
        container:
          boundary:
            in_scope:
              - "<company semantics + invariants>"
            out_of_scope:
              - "<repo-specific implementation details>"
          constraints:
            - "Meaning changes require decision refs and deprecation metadata."
        compass:
          drivers:
            - "<why this overlay exists>"
          outcomes:
            - "<what consistency this creates>"
        engine:
          invariants: []
          lifecycle: []
        fog:
          assumptions: []
          risks: []
          exceptions: []
          debt: []
    """
)

BRIDGE_MAPPING = norm(
    """
    # Map concept IDs to repo artifacts (keep stable IDs; change mappings freely)

    mappings: []
    """
)

BRIDGE_README = norm(
    """
    # Bridge

    The bridge layer links ontology concepts to repo artifacts (code symbols, APIs, schemas).

    - `mapping.yaml` maps stable concept IDs → repo-local symbols/paths.
    """
)

CONCEPTS_README = norm(
    """
    # Repo Concepts

    Add repo-local concepts here only when needed.

    Guideline: if a concept is useful across many repos, propose it in the company overlay (or kernel), not here.
    """
)

CI_INCLUDE_ROOT = norm(
    """
    include:
      - local: 'gitlab/ci/rocs.yml'
    """
)

CI_SNIPPET_ADVISORY = norm(
    """
    stages:
      - validate

    rocs:vendored-check:
      stage: validate
      image: ghcr.io/astral-sh/uv:python3.11-bookworm-slim
      rules:
        - when: always
      allow_failure: true
      script:
        - uvx -n --from ./tools/rocs-cli rocs vendored-check --vendored-dir ./tools/rocs-cli

    rocs:validate:
      stage: validate
      image: ghcr.io/astral-sh/uv:python3.11-bookworm-slim
      rules:
        - when: always
      allow_failure: true
      script:
        - python --version
        - uv --version
        - uvx --version
        - uvx -n --from ./tools/rocs-cli rocs version
        - ROCS_CMD='uvx -n --from ./tools/rocs-cli rocs' ROCS_CI_PROFILE=branch-ci bash scripts/ci/full.sh
      artifacts:
        when: always
        paths:
          - ontology/dist/
    """
)

CI_SNIPPET_STRICT = norm(
    """
    stages:
      - validate

    rocs:vendored-check:
      stage: validate
      image: ghcr.io/astral-sh/uv:python3.11-bookworm-slim
      rules:
        - when: always
      script:
        - uvx -n --from ./tools/rocs-cli rocs vendored-check --vendored-dir ./tools/rocs-cli

    rocs:validate:
      stage: validate
      image: ghcr.io/astral-sh/uv:python3.11-bookworm-slim
      rules:
        - when: always
      script:
        - python --version
        - uv --version
        - uvx --version
        - uvx -n --from ./tools/rocs-cli rocs version
        - ROCS_CMD='uvx -n --from ./tools/rocs-cli rocs' ROCS_CI_PROFILE=main-strict bash scripts/ci/full.sh
      artifacts:
        when: always
        paths:
          - ontology/dist/
    """
)

CLASS_POLICY = {
    "required": {
        "rocs_cli_vendored": True,
        "ontology_manifest": True,
        "rocs_ci_gate": True,
        "ontology_scaffold": "repo",
        "gate_mode": "advisory",
    },
    "optional": {
        "rocs_cli_vendored": False,
        "ontology_manifest": False,
        "rocs_ci_gate": False,
        "ontology_scaffold": "none",
        "gate_mode": "inventory_only",
    },
    "ontology_repo": {
        "rocs_cli_vendored": True,
        "ontology_manifest": True,
        "rocs_ci_gate": True,
        "ontology_scaffold": "ontology_repo",
        "gate_mode": "strict",
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def snapshot_tree(path: Path) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not path.exists():
        return out
    for p in sorted(path.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(path)
        if ".git" in rel.parts:
            continue
        out[rel.as_posix()] = sha256_file(p)
    return out


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def _normalize_ci_include(value: object) -> list[object]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (dict, str)):
        return [value]
    raise SystemExit("invalid .gitlab-ci.yml: top-level include must be a string, mapping, or list")


def _ci_include_has_rocs(entries: list[object]) -> bool:
    for entry in entries:
        if isinstance(entry, dict) and str(entry.get("local") or "") == "gitlab/ci/rocs.yml":
            return True
        if isinstance(entry, str) and entry.strip() == "gitlab/ci/rocs.yml":
            return True
    return False


def add_rocs_include(text: str) -> str:
    if not text.strip():
        return CI_INCLUDE_ROOT

    try:
        loaded = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"invalid .gitlab-ci.yml: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit("invalid .gitlab-ci.yml: root must be a mapping")

    include_entries = _normalize_ci_include(loaded.get("include"))
    if _ci_include_has_rocs(include_entries):
        return ensure_trailing_newline(text)

    include_entries.append({"local": "gitlab/ci/rocs.yml"})
    if "include" in loaded:
        loaded["include"] = include_entries
        updated = loaded
    else:
        updated = {"include": include_entries, **loaded}

    return ensure_trailing_newline(yaml.safe_dump(updated, sort_keys=False, allow_unicode=True))


repo_root = Path(sys.argv[1]).resolve()
target_raw = Path(sys.argv[2]).expanduser()
repo_class = sys.argv[3].strip()
dry_run = sys.argv[4] == "1"

if repo_class not in CLASS_POLICY:
    raise SystemExit(f"unknown --class: {repo_class}")

if target_raw.is_absolute():
    target = target_raw.resolve()
else:
    target = (Path.cwd() / target_raw).resolve()

if target.exists() and not target.is_dir():
    raise SystemExit(f"target exists and is not a directory: {target}")

policy = CLASS_POLICY[repo_class]
CI_WRAPPER = ensure_trailing_newline((repo_root / "scripts" / "ci" / "full.sh").read_text("utf-8"))

planned_writes: dict[str, str] = {}
planned_actions: list[dict[str, str]] = []


def plan_file(relpath: str, content: str, *, allow_modify: bool = False) -> None:
    p = target / relpath
    if p.exists():
        if p.is_dir():
            planned_actions.append({"path": relpath, "action": "skip", "reason": "path is a directory"})
            return
        current = p.read_text("utf-8")
        if current == content:
            planned_actions.append({"path": relpath, "action": "unchanged"})
            return
        if not allow_modify:
            planned_actions.append({"path": relpath, "action": "skip", "reason": "file exists"})
            return
        planned_writes[relpath] = content
        planned_actions.append({"path": relpath, "action": "modify"})
        return

    planned_writes[relpath] = content
    planned_actions.append({"path": relpath, "action": "create"})


if policy["ontology_manifest"]:
    scaffold = policy["ontology_scaffold"]
    if scaffold == "repo":
        plan_file("ontology/manifest.yaml", REPO_MANIFEST)
        plan_file("ontology/index.md", ONTOLOGY_INDEX)
        plan_file("ontology/src/system4d.yaml", REPO_SYSTEM4D)
        plan_file("ontology/src/bridge/mapping.yaml", BRIDGE_MAPPING)
        plan_file("ontology/src/bridge/README.md", BRIDGE_README)
        plan_file("ontology/src/reference/concepts/README.md", CONCEPTS_README)
    elif scaffold == "ontology_repo":
        plan_file("ontology/manifest.yaml", ONTOLOGY_REPO_MANIFEST)
        plan_file("ontology/src/system4d.yaml", ONTOLOGY_REPO_SYSTEM4D)
else:
    planned_actions.append({"path": "ontology/*", "action": "skip", "reason": "class policy: not required"})

if policy["rocs_ci_gate"]:
    ci_snippet = CI_SNIPPET_STRICT if policy["gate_mode"] == "strict" else CI_SNIPPET_ADVISORY
    plan_file("gitlab/ci/rocs.yml", ci_snippet, allow_modify=True)
    plan_file("scripts/ci/full.sh", CI_WRAPPER, allow_modify=True)

    ci_root = target / ".gitlab-ci.yml"
    if ci_root.exists() and ci_root.is_dir():
        planned_actions.append({"path": ".gitlab-ci.yml", "action": "skip", "reason": "path is a directory"})
    elif ci_root.exists():
        current = ci_root.read_text("utf-8")
        updated = add_rocs_include(current)
        if updated == current:
            planned_actions.append({"path": ".gitlab-ci.yml", "action": "unchanged"})
        else:
            planned_writes[".gitlab-ci.yml"] = updated
            planned_actions.append({"path": ".gitlab-ci.yml", "action": "modify"})
    else:
        planned_writes[".gitlab-ci.yml"] = CI_INCLUDE_ROOT
        planned_actions.append({"path": ".gitlab-ci.yml", "action": "create"})
else:
    planned_actions.append({"path": "gitlab/ci/rocs.yml", "action": "skip", "reason": "class policy: not required"})
    planned_actions.append({"path": "scripts/ci/full.sh", "action": "skip", "reason": "class policy: not required"})
    planned_actions.append({"path": ".gitlab-ci.yml", "action": "skip", "reason": "class policy: not required"})

before_snapshot = snapshot_tree(target)

vendor_result: dict[str, object] = {
    "enabled": bool(policy["rocs_cli_vendored"]),
    "path": "tools/rocs-cli",
    "status": "skipped",
}

if policy["rocs_cli_vendored"]:
    vendor_cmd = [str(repo_root / "scripts" / "vendor-to.sh"), str(target / "tools" / "rocs-cli")]
    if dry_run:
        vendor_cmd.append("--dry-run")
    proc = subprocess.run(
        vendor_cmd,
        cwd=repo_root,
        check=False,
        capture_output=True,
        text=True,
    )
    vendor_result = {
        "enabled": True,
        "path": "tools/rocs-cli",
        "status": "ok" if proc.returncode == 0 else "error",
        "exit_code": proc.returncode,
    }
    if proc.stdout.strip():
        vendor_result["stdout"] = [line for line in proc.stdout.splitlines() if line.strip()]
    if proc.stderr.strip():
        vendor_result["stderr"] = [line for line in proc.stderr.splitlines() if line.strip()]
    if proc.returncode != 0:
        error_report = {
            "schema_version": 1,
            "target": str(target),
            "repo_class": repo_class,
            "dry_run": dry_run,
            "capabilities": policy,
            "planned_actions": planned_actions,
            "vendor_sync": vendor_result,
        }
        print(json.dumps(error_report, indent=2, sort_keys=True))
        raise SystemExit(proc.returncode)

if not dry_run and planned_writes:
    target.mkdir(parents=True, exist_ok=True)
    for relpath in sorted(planned_writes):
        p = target / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(planned_writes[relpath], "utf-8")

report: dict[str, object] = {
    "schema_version": 1,
    "target": str(target),
    "repo_class": repo_class,
    "dry_run": dry_run,
    "capabilities": policy,
    "planned_actions": sorted(planned_actions, key=lambda x: x["path"]),
    "vendor_sync": vendor_result,
}

if dry_run:
    rollback_paths = {
        relpath for relpath, content in planned_writes.items() if content
    }
    if policy["rocs_cli_vendored"]:
        rollback_paths.add("tools/rocs-cli/**")
    report["rollback_paths"] = sorted(rollback_paths)
else:
    after_snapshot = snapshot_tree(target)
    before_paths = set(before_snapshot)
    after_paths = set(after_snapshot)
    created_files = sorted(after_paths - before_paths)
    modified_files = sorted(
        rel for rel in (before_paths & after_paths) if before_snapshot[rel] != after_snapshot[rel]
    )
    report["created_files"] = created_files
    report["modified_files"] = modified_files
    report["rollback_paths"] = sorted(created_files + modified_files)

print(json.dumps(report, indent=2, sort_keys=True))
PY
