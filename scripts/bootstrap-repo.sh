#!/usr/bin/env bash
set -euo pipefail

usage() {
  echo "Usage: scripts/bootstrap-repo.sh <target> --class required|optional|ontology_repo [--company holdingco|softwareco|healthco] [--dry-run]"
  echo
  echo "Bootstraps FCOS baseline files into <target> using class policy."
  echo "- required: vendored rocs-cli + ontology scaffold + CI gate (advisory)"
  echo "- optional: inventory-only (no mandatory files)"
  echo "- ontology_repo: vendored rocs-cli + ontology overlay scaffold + CI gate (strict)"
}

ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"

TARGET=""
REPO_CLASS=""
COMPANY=""
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
    --company)
      if (($# < 2)); then
        echo "error: --company requires a value" >&2
        usage >&2
        exit 2
      fi
      COMPANY="$2"
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

python3 - "$ROOT" "$TARGET" "$REPO_CLASS" "$COMPANY" "$DRY_RUN" <<'PY'
from __future__ import annotations

import hashlib
import json
import re
import stat
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict

import yaml


sys.path.insert(0, str(Path(sys.argv[1]).resolve() / "src"))
from rocs_cli.managed_surface import KNOWN_COMPANIES, infer_company_from_parts, managed_path_blocker, workspace_company_inference_is_ambiguous


def norm(text: str) -> str:
    return textwrap.dedent(text).strip("\n") + "\n"


REPO_MANIFEST_TEMPLATE = """
rocs:
  layers:
    - name: core
      ref: "<repo:core/ontology-kernel@main>"
    - name: company
      ref: "{company_ref}"
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

ONTOLOGY_REPO_INDEX = norm(
    """
    # Ontology Index (company overlay)

    Start here when browsing manually.

    - `manifest.yaml` — company overlay metadata + dependency on core
    - `src/system4d.yaml` — company-level System4D boundaries/constraints
    - `src/reference/concepts/` — company concepts
    - `src/bridge/mapping.yaml` — concept-to-artifact mappings
    - `dist/` — generated artifacts

    Tip: Use `uvx --from ./tools/rocs-cli rocs pack <concept_id> --resolve-refs --workspace-ref-mode loose` instead of opening many files.
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

HOOKS_README = norm(
    """
    # ROCS local gate hooks

    Enable the checked-in hooks for this repo with:

    ```bash
    git config core.hooksPath .githooks
    ```

    The pre-push hook delegates to `scripts/ci/full.sh` so local gates and Pi-driven runs share one policy surface.
    """
)

HOOK_PRE_PUSH_ADVISORY = norm(
    """
    #!/usr/bin/env bash
    set -euo pipefail

    repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$repo_root"

    export ROCS_CMD="${ROCS_CMD:-uv run --project ./tools/rocs-cli python -m rocs_cli}"
    export ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-local-dev}"
    bash scripts/ci/full.sh
    """
)

HOOK_PRE_PUSH_STRICT = norm(
    """
    #!/usr/bin/env bash
    set -euo pipefail

    repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
    cd "$repo_root"

    export ROCS_CMD="${ROCS_CMD:-uv run --project ./tools/rocs-cli python -m rocs_cli}"
    export ROCS_CI_PROFILE="${ROCS_CI_PROFILE:-main-strict}"
    bash scripts/ci/full.sh
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
        try:
            mode = stat.S_IMODE(p.stat().st_mode)
            digest = sha256_file(p)
        except OSError as exc:
            detail = exc.strerror or exc.__class__.__name__
            out[rel.as_posix()] = f"error:{exc.__class__.__name__}:{detail}"
            continue
        out[rel.as_posix()] = f"mode={mode:o} sha256={digest}"
    return out


def ensure_trailing_newline(text: str) -> str:
    return text if text.endswith("\n") else text + "\n"


def read_utf8_text(path: Path, *, root: Path | None = None) -> tuple[str | None, str | None]:
    if root is not None:
        blocker = managed_path_blocker(root, path)
        if blocker is not None:
            return None, blocker
    try:
        return path.read_text("utf-8"), None
    except UnicodeDecodeError:
        return None, "file is not valid utf-8"
    except OSError as exc:
        detail = exc.strerror or exc.__class__.__name__
        return None, f"file is unreadable: {detail}"


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
        if isinstance(entry, str) and entry.strip().strip("\"'") == "gitlab/ci/rocs.yml":
            return True
    return False


def _is_rocs_include_scalar(value: str) -> bool:
    return value.strip().strip("\"'") == "gitlab/ci/rocs.yml"


def _render_inline_include(entries: list[object]) -> str:
    rendered = yaml.safe_dump(entries, sort_keys=False, default_flow_style=True).strip()
    return f"include: {rendered}"


def _filter_inline_include_value(value: str) -> tuple[str | None, bool]:
    stripped = value.strip()
    if not stripped:
        return None, False
    if _is_rocs_include_scalar(stripped):
        return None, True
    if not stripped.startswith(("[", "{")):
        return None, False
    try:
        loaded = yaml.safe_load(stripped)
    except yaml.YAMLError:
        return None, False
    if isinstance(loaded, dict):
        if _ci_include_has_rocs([loaded]):
            return None, True
        return None, False
    if not isinstance(loaded, list):
        return None, False
    filtered = [entry for entry in loaded if not _ci_include_has_rocs([entry])]
    if len(filtered) == len(loaded):
        return None, False
    if not filtered:
        return None, True
    return _render_inline_include(filtered), True


def _leading_spaces(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _remove_rocs_include_textually(text: str) -> str | None:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    i = 0
    changed = False

    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if _leading_spaces(line) == 0 and stripped.startswith("include:"):
            inline_value = stripped[len("include:") :].strip()
            if inline_value:
                rewritten, handled = _filter_inline_include_value(inline_value)
                if handled:
                    changed = True
                    if rewritten is not None:
                        newline = "\n" if line.endswith("\n") else ""
                        out.append(rewritten + newline)
                    i += 1
                    continue
                out.append(line)
                i += 1
                continue

            j = i + 1
            block: list[str] = []
            while j < len(lines):
                current = lines[j]
                if current.strip() and _leading_spaces(current) == 0:
                    break
                block.append(current)
                j += 1

            kept: list[str] = []
            k = 0
            while k < len(block):
                current = block[k]
                stripped_current = current.strip()
                if not stripped_current:
                    if kept:
                        kept.append(current)
                    k += 1
                    continue
                if stripped_current.startswith("#"):
                    kept.append(current)
                    k += 1
                    continue

                if stripped_current.startswith("-"):
                    entry_lines = [current]
                    entry_indent = _leading_spaces(current)
                    k += 1
                    while k < len(block):
                        nxt = block[k]
                        nxt_stripped = nxt.strip()
                        nxt_indent = _leading_spaces(nxt)
                        if nxt_stripped and nxt_indent == entry_indent and nxt_stripped.startswith("-"):
                            break
                        entry_lines.append(nxt)
                        k += 1

                    first = stripped_current[1:].strip()
                    remove_entry = _is_rocs_include_scalar(first)
                    if not remove_entry and first.startswith("local:"):
                        remove_entry = _is_rocs_include_scalar(first.split(":", 1)[1])
                    if not remove_entry:
                        for entry_line in entry_lines[1:]:
                            entry_line_stripped = entry_line.strip()
                            if entry_line_stripped.startswith("local:") and _is_rocs_include_scalar(entry_line_stripped.split(":", 1)[1]):
                                remove_entry = True
                                break
                    if remove_entry:
                        changed = True
                        continue
                    kept.extend(entry_lines)
                    continue

                if stripped_current.startswith("local:"):
                    if _is_rocs_include_scalar(stripped_current.split(":", 1)[1]):
                        changed = True
                        k += 1
                        continue

                kept.append(current)
                k += 1

            while kept and not kept[0].strip():
                kept.pop(0)
            while kept and not kept[-1].strip():
                kept.pop()

            if kept:
                out.append(line)
                out.extend(kept)
                if j < len(lines) and out and not out[-1].endswith("\n"):
                    out[-1] += "\n"
            else:
                changed = True
            i = j
            continue

        out.append(line)
        i += 1

    result = "".join(out)
    if not result.strip():
        return None
    return ensure_trailing_newline(result if changed else text)


def remove_rocs_include(text: str) -> str | None:
    if not text.strip():
        return None
    if "gitlab/ci/rocs.yml" not in text:
        return ensure_trailing_newline(text)

    try:
        loaded = yaml.safe_load(text) or {}
    except yaml.YAMLError as exc:
        updated = _remove_rocs_include_textually(text)
        if updated == ensure_trailing_newline(text):
            raise SystemExit(f"invalid .gitlab-ci.yml: {exc}") from exc
        return updated
    if not isinstance(loaded, dict):
        raise SystemExit("invalid .gitlab-ci.yml: root must be a mapping")

    include_entries = _normalize_ci_include(loaded.get("include"))
    filtered = [entry for entry in include_entries if not _ci_include_has_rocs([entry])]
    if len(filtered) == len(include_entries):
        return ensure_trailing_newline(text)

    if filtered:
        loaded["include"] = filtered
    else:
        loaded.pop("include", None)

    if not loaded:
        return None
    return ensure_trailing_newline(yaml.safe_dump(loaded, sort_keys=False, allow_unicode=True))


repo_root = Path(sys.argv[1]).resolve()
target_raw = Path(sys.argv[2]).expanduser()
repo_class = sys.argv[3].strip()
company_override = sys.argv[4].strip()
dry_run = sys.argv[5] == "1"

if repo_class not in CLASS_POLICY:
    raise SystemExit(f"unknown --class: {repo_class}")
if company_override and company_override not in KNOWN_COMPANIES:
    raise SystemExit(f"unknown --company: {company_override}")

if target_raw.is_absolute():
    target = target_raw.resolve()
else:
    target = (Path.cwd() / target_raw).resolve()

if target.exists() and not target.is_dir():
    raise SystemExit(f"target exists and is not a directory: {target}")

policy = CLASS_POLICY[repo_class]
CI_WRAPPER = ensure_trailing_newline((repo_root / "scripts" / "ci" / "full.sh").read_text("utf-8"))

planned_writes: dict[str, str] = {}
planned_deletes: set[str] = set()
planned_exec: set[str] = set()
planned_actions: list[dict[str, str]] = []
planned_blockers: list[dict[str, str]] = []


def plan_blocked(relpath: str, *, reason: str) -> None:
    planned_actions.append({"path": relpath, "action": "blocked", "reason": reason})
    planned_blockers.append({"path": relpath, "reason": reason})


def plan_file(relpath: str, content: str, *, allow_modify: bool = False, executable: bool = False) -> None:
    p = target / relpath
    blocker = managed_path_blocker(target, p)
    if blocker is not None:
        plan_blocked(relpath, reason=blocker)
        return
    if p.exists():
        current, read_error = read_utf8_text(p, root=target)
        if read_error is not None:
            plan_blocked(relpath, reason=read_error)
            return
        if current == content:
            if executable:
                planned_exec.add(relpath)
            planned_actions.append({"path": relpath, "action": "unchanged"})
            return
        if not allow_modify:
            planned_actions.append({"path": relpath, "action": "skip", "reason": "file exists"})
            return
        if executable:
            planned_exec.add(relpath)
        planned_writes[relpath] = content
        planned_actions.append({"path": relpath, "action": "modify"})
        return

    if executable:
        planned_exec.add(relpath)
    planned_writes[relpath] = content
    planned_actions.append({"path": relpath, "action": "create"})


def plan_delete(relpath: str, *, reason: str) -> None:
    p = target / relpath
    blocker = managed_path_blocker(target, p)
    if blocker is not None:
        plan_blocked(relpath, reason=blocker)
        return
    if not p.exists():
        planned_actions.append({"path": relpath, "action": "unchanged"})
        return
    planned_deletes.add(relpath)
    planned_actions.append({"path": relpath, "action": "delete", "reason": reason})


def infer_company_from_target(path: Path) -> str | None:
    if company_override:
        return company_override
    company = infer_company_from_parts(path)
    if company is not None:
        return company
    if workspace_company_inference_is_ambiguous(path):
        return None
    return "softwareco"


def company_ref_for_target(path: Path) -> str | None:
    company = infer_company_from_target(path)
    if company is None:
        return None
    return f"<repo:{company}/ontology@main>"


def repo_manifest_for_target(path: Path) -> str | None:
    company_ref = company_ref_for_target(path)
    if company_ref is None:
        return None
    return norm(REPO_MANIFEST_TEMPLATE.format(company_ref=company_ref))


LEGACY_CORE_LOCATOR_RE = re.compile(r"<gitlab:(?:ai-society/)?(?:core/ontology-kernel|org/ontology-kernel)@[^>]+>")
LEGACY_COMPANY_LOCATOR_RE = re.compile(r"<gitlab:(?:ai-society/)?(?:org/ontology|holdingco/ontology|softwareco/ontology|healthco/ontology)@[^>]+>")


def canonicalize_legacy_manifest(content: str) -> str:
    updated = LEGACY_CORE_LOCATOR_RE.sub("<repo:core/ontology-kernel@main>", content)
    if repo_class != "ontology_repo":
        company_ref = company_ref_for_target(target)
        if company_ref is not None:
            updated = LEGACY_COMPANY_LOCATOR_RE.sub(company_ref, updated)
    return updated


def plan_manifest_file(relpath: str, default_content: str) -> None:
    p = target / relpath
    blocker = managed_path_blocker(target, p)
    if blocker is not None:
        plan_blocked(relpath, reason=blocker)
        return
    if p.exists() and p.is_file():
        current, read_error = read_utf8_text(p, root=target)
        if read_error is not None:
            plan_blocked(relpath, reason=read_error)
            return
        canonicalized = canonicalize_legacy_manifest(current)
        if canonicalized != current:
            planned_writes[relpath] = canonicalized
            planned_actions.append({
                "path": relpath,
                "action": "modify",
                "reason": "canonicalize legacy ontology locators",
            })
            return
    plan_file(relpath, default_content)


def plan_remove_legacy_gitlab_ci() -> None:
    plan_delete("gitlab/ci/rocs.yml", reason="remove legacy generated GitLab ROCS gate")

    ci_root = target / ".gitlab-ci.yml"
    if not ci_root.exists():
        planned_actions.append({"path": ".gitlab-ci.yml", "action": "unchanged"})
        return
    if ci_root.is_dir():
        plan_blocked(".gitlab-ci.yml", reason="path is a directory")
        return

    current, read_error = read_utf8_text(ci_root, root=target)
    if read_error is not None:
        plan_blocked(".gitlab-ci.yml", reason=read_error)
        return
    updated = remove_rocs_include(current)
    if updated == current:
        planned_actions.append({"path": ".gitlab-ci.yml", "action": "unchanged"})
        return
    if updated is None:
        planned_deletes.add(".gitlab-ci.yml")
        planned_actions.append({"path": ".gitlab-ci.yml", "action": "delete", "reason": "remove generated ROCS GitLab include"})
        return
    planned_writes[".gitlab-ci.yml"] = updated
    planned_actions.append({"path": ".gitlab-ci.yml", "action": "modify", "reason": "remove generated ROCS GitLab include"})


if policy["ontology_manifest"]:
    scaffold = policy["ontology_scaffold"]
    if scaffold == "repo":
        manifest_content = repo_manifest_for_target(target)
        if manifest_content is None:
            plan_blocked(
                "ontology/manifest.yaml",
                reason=(
                    "could not infer company from target path inside ai-society workspace "
                    "(pass --company holdingco|softwareco|healthco)"
                ),
            )
        else:
            plan_manifest_file("ontology/manifest.yaml", manifest_content)
            plan_file("ontology/index.md", ONTOLOGY_INDEX)
            plan_file("ontology/src/system4d.yaml", REPO_SYSTEM4D)
            plan_file("ontology/src/bridge/mapping.yaml", BRIDGE_MAPPING)
            plan_file("ontology/src/bridge/README.md", BRIDGE_README)
            plan_file("ontology/src/reference/concepts/README.md", CONCEPTS_README)
    elif scaffold == "ontology_repo":
        plan_manifest_file("manifest.yaml", ONTOLOGY_REPO_MANIFEST)
        plan_file("index.md", ONTOLOGY_REPO_INDEX)
        plan_file("src/system4d.yaml", ONTOLOGY_REPO_SYSTEM4D)
        plan_file("src/bridge/mapping.yaml", BRIDGE_MAPPING)
        plan_file("src/bridge/README.md", BRIDGE_README)
        plan_file("src/reference/concepts/README.md", CONCEPTS_README)
else:
    planned_actions.append({"path": "ontology/*", "action": "skip", "reason": "class policy: not required"})

if policy["rocs_ci_gate"]:
    hook = HOOK_PRE_PUSH_STRICT if policy["gate_mode"] == "strict" else HOOK_PRE_PUSH_ADVISORY
    plan_file(".githooks/pre-push", hook, allow_modify=True, executable=True)
    plan_file(".githooks/README.md", HOOKS_README, allow_modify=True)
    plan_file("scripts/ci/full.sh", CI_WRAPPER, allow_modify=True)
    plan_remove_legacy_gitlab_ci()
else:
    planned_actions.append({"path": ".githooks/pre-push", "action": "skip", "reason": "class policy: not required"})
    planned_actions.append({"path": ".githooks/README.md", "action": "skip", "reason": "class policy: not required"})
    planned_actions.append({"path": "scripts/ci/full.sh", "action": "skip", "reason": "class policy: not required"})
    planned_actions.append({"path": "gitlab/ci/rocs.yml", "action": "skip", "reason": "class policy: not required"})
    planned_actions.append({"path": ".gitlab-ci.yml", "action": "skip", "reason": "class policy: not required"})

vendor_result: dict[str, object] = {
    "enabled": bool(policy["rocs_cli_vendored"]),
    "path": "tools/rocs-cli",
    "status": "skipped",
}

if planned_blockers:
    blocked_report: dict[str, object] = {
        "schema_version": 1,
        "target": str(target),
        "repo_class": repo_class,
        "dry_run": dry_run,
        "capabilities": policy,
        "planned_actions": sorted(planned_actions, key=lambda x: x["path"]),
        "vendor_sync": vendor_result,
        "blocked": True,
        "blocked_paths": sorted(planned_blockers, key=lambda x: x["path"]),
    }
    if dry_run:
        rollback_paths = set(planned_writes) | set(planned_deletes)
        if policy["rocs_cli_vendored"]:
            rollback_paths.add("tools/rocs-cli/**")
        blocked_report["rollback_paths"] = sorted(rollback_paths)
    else:
        blocked_report["created_files"] = []
        blocked_report["modified_files"] = []
        blocked_report["deleted_files"] = []
        blocked_report["rollback_paths"] = []
    print(json.dumps(blocked_report, indent=2, sort_keys=True))
    raise SystemExit(1)

before_snapshot = snapshot_tree(target)

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

if not dry_run and (planned_writes or planned_deletes or planned_exec):
    target.mkdir(parents=True, exist_ok=True)
    for relpath in sorted(set(planned_deletes) | set(planned_writes) | set(planned_exec)):
        blocker = managed_path_blocker(target, target / relpath)
        if blocker is not None:
            error_report = {
                "schema_version": 1,
                "target": str(target),
                "repo_class": repo_class,
                "dry_run": dry_run,
                "capabilities": policy,
                "planned_actions": sorted(planned_actions, key=lambda x: x["path"]),
                "vendor_sync": vendor_result,
                "blocked": True,
                "blocked_paths": [{"path": relpath, "reason": blocker}],
                "created_files": [],
                "modified_files": [],
                "deleted_files": [],
                "rollback_paths": [],
            }
            print(json.dumps(error_report, indent=2, sort_keys=True))
            raise SystemExit(1)
    for relpath in sorted(planned_deletes):
        p = target / relpath
        p.unlink(missing_ok=True)
    for relpath in sorted(planned_writes):
        p = target / relpath
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(planned_writes[relpath], "utf-8")
    for relpath in sorted(planned_exec):
        p = target / relpath
        if p.exists() and p.is_file():
            p.chmod(p.stat().st_mode | 0o111)

report: dict[str, object] = {
    "schema_version": 1,
    "target": str(target),
    "repo_class": repo_class,
    "dry_run": dry_run,
    "capabilities": policy,
    "planned_actions": sorted(planned_actions, key=lambda x: x["path"]),
    "vendor_sync": vendor_result,
    "blocked": bool(planned_blockers),
}
if planned_blockers:
    report["blocked_paths"] = sorted(planned_blockers, key=lambda x: x["path"])

if dry_run:
    rollback_paths = set(planned_writes) | set(planned_deletes)
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
    deleted_files = sorted(before_paths - after_paths)
    report["created_files"] = created_files
    report["modified_files"] = modified_files
    report["deleted_files"] = deleted_files
    report["rollback_paths"] = sorted(created_files + modified_files + deleted_files)

print(json.dumps(report, indent=2, sort_keys=True))
PY
