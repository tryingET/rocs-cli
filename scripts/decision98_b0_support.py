from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import stat
import subprocess
from typing import Any


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(65536):
            digest.update(chunk)
    return digest.hexdigest()


def tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        relative = path.relative_to(root).as_posix().encode()
        content = path.read_bytes()
        digest.update(len(relative).to_bytes(8, "big"))
        digest.update(relative)
        digest.update(len(content).to_bytes(8, "big"))
        digest.update(content)
    return digest.hexdigest()


def inventory(root: Path) -> list[tuple[Any, ...]]:
    """Inventory every working-tree entry except owner-managed .git metadata."""
    entries: list[tuple[Any, ...]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        details = path.lstat()
        mode = stat.S_IMODE(details.st_mode)
        common: tuple[Any, ...] = (relative.as_posix(), mode, details.st_mtime_ns)
        if stat.S_ISREG(details.st_mode):
            entries.append((*common, "file", details.st_size, sha256(path)))
        elif stat.S_ISDIR(details.st_mode):
            entries.append((*common, "directory"))
        elif stat.S_ISLNK(details.st_mode):
            entries.append((*common, "symlink", os.readlink(path)))
        else:
            entries.append((*common, "special", stat.S_IFMT(details.st_mode)))
    return entries


def inventory_digest(root: Path) -> str:
    payload = json.dumps(inventory(root), separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def percentile(values: list[float], quantile: float) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(quantile * len(ordered)) - 1)]


def git(root: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(root), *arguments],
        check=check,
        capture_output=True,
        text=True,
    )


def require_detached_clean_checkout(root: Path, commit: str, label: str) -> None:
    if git(root, "rev-parse", "HEAD").stdout.strip() != commit:
        raise RuntimeError(f"{label} commit mismatch")
    symbolic = git(root, "symbolic-ref", "-q", "HEAD", check=False)
    if symbolic.returncode == 0:
        raise RuntimeError(f"{label} checkout is not detached")
    if symbolic.returncode != 1:
        raise RuntimeError(f"unable to verify detached {label} checkout")
    if git(root, "status", "--porcelain=v1", "--untracked-files=all").stdout:
        raise RuntimeError(f"{label} checkout is dirty")


def require_no_ignored_content(root: Path) -> None:
    ignored = git(root, "status", "--porcelain=v1", "--ignored", "--untracked-files=all").stdout
    if ignored:
        raise RuntimeError("preregistration checkout contains ignored content")


def require_hex_digest(value: str, label: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise RuntimeError(f"invalid {label}")


def require_git_commit(value: str, label: str) -> None:
    if len(value) != 40 or any(character not in "0123456789abcdef" for character in value):
        raise RuntimeError(f"invalid {label}")


def require_prefixed_digest(value: Any, label: str) -> None:
    if not isinstance(value, str) or not value.startswith("sha256:"):
        raise RuntimeError(f"invalid {label}")
    require_hex_digest(value.removeprefix("sha256:"), label)


def validate_dataset(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    expected_strata = {
        "exact_terminology": 10,
        "paraphrase_synonym": 10,
        "multi_concept": 10,
        "ambiguity_distractor": 10,
        "null_out_of_domain": 10,
    }
    if dataset.get("schema") != "decision98-b0-prompts-v1":
        raise RuntimeError("dataset schema mismatch")
    prompts = dataset.get("prompts")
    if not isinstance(prompts, list) or len(prompts) != 50:
        raise RuntimeError("preregistered prompt count mismatch")
    strata: dict[str, int] = {}
    identifiers: set[str] = set()
    applicable_count = 0
    for item in prompts:
        identifier = item["id"]
        if identifier in identifiers:
            raise RuntimeError("duplicate prompt identifier")
        identifiers.add(identifier)
        stratum = item["stratum"]
        strata[stratum] = strata.get(stratum, 0) + 1
        applicable = item["applicable"]
        gold = item["gold_ont_ids"]
        if not isinstance(item["query"], str) or not item["query"].strip():
            raise RuntimeError(f"empty query for {identifier}")
        if not isinstance(applicable, bool) or not isinstance(gold, list):
            raise RuntimeError(f"invalid label for {identifier}")
        if applicable != bool(gold) or len(gold) != len(set(gold)):
            raise RuntimeError(f"incomplete or duplicate gold label for {identifier}")
        annotations = item.get("annotations", {})
        if set(annotations) != {"annotator_a", "annotator_b"}:
            raise RuntimeError(f"annotation provenance missing for {identifier}")
        for annotation in annotations.values():
            if not annotation.get("dispatch") or not isinstance(annotation.get("gold_ont_ids"), list):
                raise RuntimeError(f"invalid annotation provenance for {identifier}")
        applicable_count += int(applicable)
    if strata != expected_strata or applicable_count != 40:
        raise RuntimeError("preregistered prompt balance mismatch")
    return prompts


def validate_discovery_result(
    result: Any,
    request: dict[str, Any],
    *,
    manifest_digest: str,
    allowed_ont_ids: set[str],
) -> None:
    from rocs_cli.semantic_protocol import object_digest, validate_protocol, verify_object_digest

    if not isinstance(result, dict) or validate_protocol(result):
        raise RuntimeError("ROCS discovery result violates the protocol schema")
    if result.get("schema") != "semantic-discovery-result.v0":
        raise RuntimeError("ROCS discovery result schema mismatch")
    if result.get("caller_request_digest") != object_digest("caller_request", request):
        raise RuntimeError("ROCS discovery request correlation mismatch")
    if result.get("algorithm") != {"id": "rocs-lexical-v0", "unicode_data": "15.0.0"}:
        raise RuntimeError("ROCS discovery algorithm identity mismatch")
    if result.get("effective_limits") != request["limits"]:
        raise RuntimeError("ROCS discovery effective limits mismatch")
    identity = result.get("tool_identity")
    expected_identity = {
        "kind": "development_runtime",
        "manifest_digest": manifest_digest,
        "python_version": "3.12.12",
        "unicode_data": "15.0.0",
    }
    if not isinstance(identity, dict) or any(identity.get(key) != value for key, value in expected_identity.items()):
        raise RuntimeError("ROCS discovery tool identity mismatch")
    if not verify_object_digest("tool_identity", identity):
        raise RuntimeError("ROCS discovery tool identity digest mismatch")
    require_prefixed_digest(result.get("corpus_snapshot_digest"), "corpus snapshot digest")
    require_prefixed_digest(result.get("effective_execution_digest"), "effective execution digest")
    if not verify_object_digest("result", result):
        raise RuntimeError("ROCS discovery result digest mismatch")
    candidates = result.get("candidates")
    if not isinstance(candidates, list):
        raise RuntimeError("ROCS discovery candidates are missing")
    observed_ids: set[str] = set()
    for rank, candidate in enumerate(candidates, 1):
        ont_id = candidate.get("ont_id")
        score = candidate.get("score")
        if ont_id not in allowed_ont_ids or ont_id in observed_ids:
            raise RuntimeError("ROCS discovery candidate identity is invalid")
        if candidate.get("rank") != rank or type(score) is not int or score < 100:
            raise RuntimeError("ROCS discovery candidate rank or score is invalid")
        observed_ids.add(ont_id)
    if result.get("retrieval") not in {
        "no_candidates",
        "low_confidence",
        "unique_candidate",
        "ambiguous_equivalence",
        "multiple_candidates",
    } or type(result.get("truncated")) is not bool:
        raise RuntimeError("ROCS discovery classification is invalid")


def write_report_exclusive(
    parent: Path, name: str, parent_identity: tuple[int, int], report: dict[str, Any]
) -> None:
    payload = (json.dumps(report, indent=2, sort_keys=True) + "\n").encode()
    directory = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    descriptor: int | None = None
    created = False
    try:
        details = os.fstat(directory)
        if (details.st_dev, details.st_ino) != parent_identity:
            raise RuntimeError("reserved report parent changed")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        descriptor = os.open(name, flags, 0o600, dir_fd=directory)
        created = True
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except FileExistsError as error:
        raise RuntimeError("reserved report path collision") from error
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        if created:
            os.unlink(name, dir_fd=directory)
        raise
    finally:
        os.close(directory)
