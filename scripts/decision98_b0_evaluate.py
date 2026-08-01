#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import shutil
import stat
import statistics
import subprocess
import sys
import time
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))

from decision98_b0_support import (  # noqa: E402
    inventory,
    inventory_digest,
    percentile,
    require_detached_clean_checkout,
    require_git_commit,
    require_hex_digest,
    require_no_ignored_content,
    sha256,
    tree_digest,
    validate_dataset,
    validate_discovery_result,
    write_report_exclusive,
)

LOCK_SCHEMA = "decision98-b0-lock-v1"
REPORT_SCHEMA = "decision98-b0-semantic-relevance-report-v1"
LOCK_PATH = Path("tests/fixtures/decision98-b0/preregistration-lock.json")
DATASET_PATH = Path("tests/fixtures/decision98-b0/prompts.json")
CORPUS_PATH = Path("tests/fixtures/decision98-b0/corpus")
PREREGISTRATION_PATH = Path("docs/project/decision98-b0-semantic-relevance-preregistration.md")
EVALUATOR_PATH = Path("scripts/decision98_b0_evaluate.py")
SUPPORT_PATH = Path("scripts/decision98_b0_support.py")
OUTPUT_PATH = Path("docs/project/decision98-b0-semantic-relevance-report.json")
PRIVATE_HOME_NAME = "decision98-b0-private-home"
RUNTIME_ROOT = Path("/data/agnt/tmp/rocs-cli-decision98-b0-runtime-c0cfb129")
RUNTIME_COMMIT = "c0cfb1297ba78f4ca1fe53f488bcb15ad79b7843"
PYTHON_IMPLEMENTATION = "CPython"
PYTHON_VERSION = "3.12.12"
UV_LOCK_SHA256 = "bdde23353d71df100b63fadcb9b35ddca54add02412276ee3395b11af33bda6b"
PYVENV_CFG_SHA256 = "b88c80de60f13be36bf53c717188e1dfa926730b9ef1102c3e169a3d1541c565"
INTERPRETER_SHA256 = "20341168c41f91f4328c68d1f1a8d563f5734d515e617ff80a8dcfce323218b7"
RUNTIME_INVENTORY_SHA256 = "21b12397aaaacf3d3a748242185d1f83b9728e960cee30f11940abf65ce04e9c"
PYTHON_ROOT = Path("/home/tryinget/.local/share/uv/python/cpython-3.12.12-linux-x86_64-gnu")
PYTHON_ROOT_INVENTORY_SHA256 = "6f1b98a4f02813c21be383ac910dbe6a3acbe9cdc585382f3835a8ca3868c96a"
NATIVE_LIBRARIES = {
    "/usr/lib/libpthread.so.0": "7e2b142dff3649e63e29d2a405a724eed227ae638f18235cfdafc749a7c20e66",
    "/usr/lib/libdl.so.2": "051078cafd9dc13ba9cc8533cf30ef58f92c18c9e3cbd0850ad2889775ad563a",
    "/usr/lib/libutil.so.1": "5373f5154659686e56d6e1e9ef97c23ed1d373aac951591139352c4c5bbf528c",
    "/usr/lib/librt.so.1": "d788f4f8bb7868bdbdec73452957e6e1050e9bc6f4df45760b920121df6ce52a",
    "/usr/lib/libm.so.6": "ef844d938ce86d2410a4b5a83a011c2daf667a80d4ec7f2bae08e52ce5ff3deb",
    "/usr/lib/libc.so.6": "27d2232b682d8372283d26a0999b9330f00ed742f9b717e025e06c293c15120d",
    "/usr/lib64/ld-linux-x86-64.so.2": "44da66fca8e68a885166bd95d743bfbf57cba6a98b35b42710d8260aadfe284b",
}
DEPENDENCIES = {
    "Pygments": "2.19.2",
    "PyYAML": "6.0.3",
    "markdown-it-py": "4.0.0",
    "mdurl": "0.1.2",
    "rich": "14.2.0",
}
TOOL_MANIFEST_DIGEST = f"sha256:{RUNTIME_INVENTORY_SHA256}"
TIMEOUT_SECONDS = 2.0
LIMITS = {
    "query_bytes": 16384,
    "corpus_files": 5000,
    "corpus_bytes": 33554432,
    "file_bytes": 1048576,
    "parser_depth": 32,
    "collection_items": 10000,
    "candidates": 5,
    "result_bytes": 65536,
}
FLOORS = {
    "recall_at_3": 0.90,
    "mrr": 0.85,
    "applicable_stratum_recall_at_3": 0.80,
    "null_rejection_rate": 0.90,
    "deterministic_repeat_rate": 1.0,
    "timeout_rate": 0.0,
    "cold_p95_ms": 750.0,
    "warm_p95_ms": 500.0,
}


def require_lock_shape(lock: dict[str, Any]) -> None:
    if lock.get("schema") != LOCK_SCHEMA:
        raise RuntimeError("preregistration lock schema mismatch")
    expected_paths = {
        "evaluator": EVALUATOR_PATH.as_posix(),
        "support": SUPPORT_PATH.as_posix(),
        "preregistration": PREREGISTRATION_PATH.as_posix(),
        "dataset": DATASET_PATH.as_posix(),
        "corpus": CORPUS_PATH.as_posix(),
    }
    for name, expected_path in expected_paths.items():
        if lock["source"][name]["path"] != expected_path:
            raise RuntimeError(f"locked {name} path mismatch")
    if lock["output_path"] != OUTPUT_PATH.as_posix():
        raise RuntimeError("locked output path mismatch")
    if lock["timeout_seconds"] != TIMEOUT_SECONDS:
        raise RuntimeError("locked timeout mismatch")
    if lock["limits"] != LIMITS or lock["floors"] != FLOORS:
        raise RuntimeError("locked limits or floors mismatch")
    runtime = lock["runtime"]
    expected_runtime = {
        "root": str(RUNTIME_ROOT),
        "commit": RUNTIME_COMMIT,
        "uv_lock_sha256": UV_LOCK_SHA256,
        "tool_manifest_digest": TOOL_MANIFEST_DIGEST,
        "algorithm": "rocs-lexical-v0",
        "profile": "review",
    }
    for name, expected in expected_runtime.items():
        if runtime[name] != expected:
            raise RuntimeError(f"locked runtime {name} mismatch")
    expected_python = {
        "implementation": PYTHON_IMPLEMENTATION,
        "version": PYTHON_VERSION,
        "pyvenv_cfg_sha256": PYVENV_CFG_SHA256,
        "interpreter_sha256": INTERPRETER_SHA256,
        "dependencies": DEPENDENCIES,
        "root": str(PYTHON_ROOT),
        "root_inventory_sha256": PYTHON_ROOT_INVENTORY_SHA256,
        "native_libraries": NATIVE_LIBRARIES,
    }
    for name, expected in expected_python.items():
        if runtime["python"][name] != expected:
            raise RuntimeError(f"locked Python {name} mismatch")
    if runtime["working_tree_inventory_sha256"] != RUNTIME_INVENTORY_SHA256:
        raise RuntimeError("locked runtime inventory digest mismatch")


def require_locked_sources(repo: Path, lock: dict[str, Any]) -> None:
    sources = lock["source"]
    for name, relative in (
        ("evaluator", EVALUATOR_PATH),
        ("support", SUPPORT_PATH),
        ("preregistration", PREREGISTRATION_PATH),
        ("dataset", DATASET_PATH),
    ):
        expected = sources[name]["sha256"]
        require_hex_digest(expected, f"{name} digest")
        if sha256(repo / relative) != expected:
            raise RuntimeError(f"{name} digest mismatch")
    expected_corpus = sources["corpus"]["tree_sha256"]
    require_hex_digest(expected_corpus, "corpus tree digest")
    if tree_digest(repo / CORPUS_PATH) != expected_corpus:
        raise RuntimeError("corpus tree digest mismatch")


def require_runtime(runtime: Path, lock: dict[str, Any]) -> None:
    specification = lock["runtime"]
    if runtime != RUNTIME_ROOT or str(runtime) != specification["root"]:
        raise RuntimeError("runtime root mismatch")
    require_detached_clean_checkout(runtime, RUNTIME_COMMIT, "runtime")
    if sha256(runtime / "uv.lock") != UV_LOCK_SHA256:
        raise RuntimeError("runtime uv.lock digest mismatch")
    venv = runtime / ".venv"
    if not venv.is_dir() or Path(sys.base_prefix).resolve() != PYTHON_ROOT:
        raise RuntimeError("frozen base Python root mismatch")
    interpreter = venv / "bin/python"
    if not interpreter.exists() or not os.path.samefile(sys.executable, interpreter):
        raise RuntimeError("runtime interpreter mismatch")
    if sha256(interpreter) != INTERPRETER_SHA256:
        raise RuntimeError("runtime interpreter digest mismatch")
    if platform.python_implementation() != PYTHON_IMPLEMENTATION:
        raise RuntimeError("Python implementation mismatch")
    if platform.python_version() != PYTHON_VERSION:
        raise RuntimeError("Python version mismatch")
    if sha256(venv / "pyvenv.cfg") != PYVENV_CFG_SHA256:
        raise RuntimeError("pyvenv.cfg digest mismatch")
    if inventory_digest(PYTHON_ROOT) != PYTHON_ROOT_INVENTORY_SHA256:
        raise RuntimeError("base Python inventory mismatch")
    for path, expected in NATIVE_LIBRARIES.items():
        if sha256(Path(path)) != expected:
            raise RuntimeError(f"native library digest mismatch: {path}")
    for path in (runtime / "src", venv / "lib/python3.12/site-packages"):
        if str(path) not in sys.path:
            sys.path.append(str(path))
    observed_dependencies = {name: metadata.version(name) for name in DEPENDENCIES}
    if observed_dependencies != DEPENDENCIES:
        raise RuntimeError("frozen dependency version mismatch")
    if inventory_digest(runtime) != RUNTIME_INVENTORY_SHA256:
        raise RuntimeError("frozen runtime inventory mismatch")


def request(query: str, lock: dict[str, Any]) -> bytes:
    value = {
        "schema": "semantic-discovery-request.v0",
        "query": query,
        "identity_selector": {"kind": "development_snapshot"},
        "profile": lock["runtime"]["profile"],
        "algorithm": lock["runtime"]["algorithm"],
        "limits": LIMITS,
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def invoke(
    runtime: Path,
    corpus: Path,
    home: Path,
    query: str,
    lock: dict[str, Any],
    allowed_ont_ids: set[str],
) -> dict[str, Any]:
    environment = {
        "HOME": str(home),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONPATH": str(runtime / "src"),
        "ROCS_INDEX_CACHE": "0",
    }
    command = [
        sys.executable,
        "-m",
        "rocs_cli",
        "discover",
        "--repo",
        str(corpus),
        "--request-json",
        "-",
        "--tool-kind",
        "development_runtime",
        "--tool-manifest-digest",
        lock["runtime"]["tool_manifest_digest"],
        "--json",
        "--no-index-cache",
        "--no-env-file",
    ]
    started = time.perf_counter_ns()
    request_payload = request(query, lock)
    try:
        completed = subprocess.run(
            command,
            cwd=runtime,
            env=environment,
            input=request_payload,
            capture_output=True,
            timeout=TIMEOUT_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return {"timeout": True, "elapsed_ms": TIMEOUT_SECONDS * 1000}
    elapsed_ms = (time.perf_counter_ns() - started) / 1_000_000
    if completed.returncode != 0:
        raise RuntimeError(
            f"ROCS discovery failed ({completed.returncode}): "
            f"{completed.stderr.decode('utf-8', 'replace')[:1000]}"
        )
    try:
        result = json.loads(completed.stdout)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise RuntimeError("ROCS discovery returned malformed JSON") from error
    validate_discovery_result(
        result,
        json.loads(request_payload),
        manifest_digest=TOOL_MANIFEST_DIGEST,
        allowed_ont_ids=allowed_ont_ids,
    )
    return {
        "timeout": False,
        "elapsed_ms": elapsed_ms,
        "raw_sha256": hashlib.sha256(completed.stdout).hexdigest(),
        "raw": completed.stdout,
        "result": result,
    }


def evaluate(prompts: list[dict[str, Any]], runtime: Path, corpus: Path, home: Path, lock: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    allowed_ont_ids = {ont_id for item in prompts for ont_id in item["gold_ont_ids"]}
    for item in prompts:
        cold = invoke(runtime, corpus, home, item["query"], lock, allowed_ont_ids)
        warm = invoke(runtime, corpus, home, item["query"], lock, allowed_ont_ids)
        candidates = [] if cold["timeout"] else cold["result"]["candidates"]
        returned = [candidate["ont_id"] for candidate in candidates]
        gold = item["gold_ont_ids"]
        relevant_ranks = [index + 1 for index, ont_id in enumerate(returned) if ont_id in gold]
        rows.append(
            {
                "id": item["id"],
                "stratum": item["stratum"],
                "applicable": item["applicable"],
                "gold_ont_ids": gold,
                "returned": [
                    {"ont_id": candidate["ont_id"], "score": candidate["score"]}
                    for candidate in candidates
                ],
                "recall_at_3": 1.0 if not gold else len(set(gold) & set(returned[:3])) / len(gold),
                "reciprocal_rank": 0.0 if not relevant_ranks else 1.0 / min(relevant_ranks),
                "null_rejected": not returned if not item["applicable"] else None,
                "cold_ms": cold["elapsed_ms"],
                "warm_ms": warm["elapsed_ms"],
                "cold_timeout": cold["timeout"],
                "warm_timeout": warm["timeout"],
                "repeat_equal": not cold["timeout"] and not warm["timeout"] and cold["raw"] == warm["raw"],
                "cold_result_sha256": cold.get("raw_sha256"),
                "warm_result_sha256": warm.get("raw_sha256"),
            }
        )
    return rows


def build_metrics(rows: list[dict[str, Any]]) -> tuple[dict[str, Any], dict[str, bool]]:
    applicable = [row for row in rows if row["applicable"]]
    nulls = [row for row in rows if not row["applicable"]]
    strata = sorted({row["stratum"] for row in applicable})
    stratum_recall = {
        stratum: statistics.fmean(
            row["recall_at_3"] for row in applicable if row["stratum"] == stratum
        )
        for stratum in strata
    }
    metrics = {
        "recall_at_3": statistics.fmean(row["recall_at_3"] for row in applicable),
        "mrr": statistics.fmean(row["reciprocal_rank"] for row in applicable),
        "applicable_stratum_recall_at_3": stratum_recall,
        "null_rejection_rate": statistics.fmean(bool(row["null_rejected"]) for row in nulls),
        "deterministic_repeat_rate": statistics.fmean(row["repeat_equal"] for row in rows),
        "timeout_rate": statistics.fmean(row["cold_timeout"] or row["warm_timeout"] for row in rows),
        "cold_p95_ms": percentile([row["cold_ms"] for row in rows], 0.95),
        "warm_p95_ms": percentile([row["warm_ms"] for row in rows], 0.95),
    }
    gates = {
        "recall_at_3": metrics["recall_at_3"] >= FLOORS["recall_at_3"],
        "mrr": metrics["mrr"] >= FLOORS["mrr"],
        "applicable_stratum_recall_at_3": all(
            value >= FLOORS["applicable_stratum_recall_at_3"] for value in stratum_recall.values()
        ),
        "null_rejection_rate": metrics["null_rejection_rate"] >= FLOORS["null_rejection_rate"],
        "deterministic_repeat_rate": metrics["deterministic_repeat_rate"] >= FLOORS["deterministic_repeat_rate"],
        "timeout_rate": metrics["timeout_rate"] <= FLOORS["timeout_rate"],
        "cold_p95_ms": metrics["cold_p95_ms"] <= FLOORS["cold_p95_ms"],
        "warm_p95_ms": metrics["warm_p95_ms"] <= FLOORS["warm_p95_ms"],
    }
    return metrics, gates


def main() -> int:
    if not (
        sys.flags.isolated
        and sys.flags.no_site
        and sys.flags.ignore_environment
        and sys.flags.dont_write_bytecode
    ):
        raise RuntimeError("evaluator requires Python -I -S -B isolated startup")
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-root", type=Path, required=True)
    parser.add_argument("--prereg-commit", required=True)
    parser.add_argument("--lock-sha256", required=True)
    arguments = parser.parse_args()
    require_git_commit(arguments.prereg_commit, "preregistration commit")
    require_hex_digest(arguments.lock_sha256, "lock digest")

    repo = Path(__file__).resolve().parents[1]
    runtime = arguments.runtime_root.resolve(strict=True)
    output = (repo / OUTPUT_PATH).resolve(strict=False)
    if output != repo / OUTPUT_PATH or not output.parent.is_dir():
        raise RuntimeError("reserved report path resolution mismatch")
    if output.exists() or output.is_symlink():
        raise RuntimeError("reserved report path already exists")
    output_parent_stat = output.parent.stat()
    output_parent_identity = (output_parent_stat.st_dev, output_parent_stat.st_ino)
    if runtime == repo or runtime in repo.parents or repo in runtime.parents:
        raise RuntimeError("runtime and preregistration checkouts must be isolated")

    tmpdir_value = os.environ.get("TMPDIR")
    if not tmpdir_value:
        raise RuntimeError("TMPDIR is required for the private home")
    tmpdir = Path(tmpdir_value).resolve(strict=True)
    if not tmpdir.is_dir() or stat.S_IMODE(tmpdir.stat().st_mode) & 0o077:
        raise RuntimeError("TMPDIR must be a private directory")
    if (
        tmpdir in {repo, runtime}
        or tmpdir in repo.parents
        or tmpdir in runtime.parents
        or repo in tmpdir.parents
        or runtime in tmpdir.parents
    ):
        raise RuntimeError("TMPDIR must be isolated from source and runtime checkouts")
    home = tmpdir / PRIVATE_HOME_NAME
    if home.exists() or home.is_symlink():
        raise RuntimeError("private home collision")

    lock_path = repo / LOCK_PATH
    if sha256(lock_path) != arguments.lock_sha256:
        raise RuntimeError("preregistration lock digest mismatch")
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    require_lock_shape(lock)
    require_detached_clean_checkout(repo, arguments.prereg_commit, "preregistration")
    require_no_ignored_content(repo)
    require_locked_sources(repo, lock)
    require_runtime(runtime, lock)
    dataset = json.loads((repo / DATASET_PATH).read_text(encoding="utf-8"))
    prompts = validate_dataset(dataset)

    source_before = inventory(repo)
    runtime_before = inventory(runtime)
    corpus_before = inventory(repo / CORPUS_PATH)
    home.mkdir(mode=0o700, parents=False, exist_ok=False)
    rows: list[dict[str, Any]] = []
    try:
        rows = evaluate(prompts, runtime, repo / CORPUS_PATH, home, lock)
    finally:
        if home.exists() or home.is_symlink():
            shutil.rmtree(home)
    if home.exists() or home.is_symlink():
        raise RuntimeError("private home cleanup failed")

    if inventory(repo / CORPUS_PATH) != corpus_before:
        raise RuntimeError("corpus mutated during evaluation")
    if inventory(runtime) != runtime_before:
        raise RuntimeError("runtime filesystem mutated during evaluation")
    if inventory(repo) != source_before:
        raise RuntimeError("preregistration filesystem mutated during evaluation")
    require_detached_clean_checkout(repo, arguments.prereg_commit, "preregistration")
    require_no_ignored_content(repo)
    require_locked_sources(repo, lock)
    require_runtime(runtime, lock)

    metrics, gates = build_metrics(rows)
    report = {
        "schema": REPORT_SCHEMA,
        "preregistration": {
            "commit": arguments.prereg_commit,
            "lock_sha256": arguments.lock_sha256,
            "evaluator_sha256": lock["source"]["evaluator"]["sha256"],
            "document_sha256": lock["source"]["preregistration"]["sha256"],
        },
        "runtime": {
            "commit": lock["runtime"]["commit"],
            "python": platform.python_version(),
            "implementation": platform.python_implementation(),
            "uv_lock_sha256": lock["runtime"]["uv_lock_sha256"],
            "pyvenv_cfg_sha256": lock["runtime"]["python"]["pyvenv_cfg_sha256"],
            "dependencies": lock["runtime"]["python"]["dependencies"],
            "tool_manifest_digest": lock["runtime"]["tool_manifest_digest"],
            "algorithm": lock["runtime"]["algorithm"],
            "profile": lock["runtime"]["profile"],
            "index_cache": False,
        },
        "dataset_sha256": lock["source"]["dataset"]["sha256"],
        "corpus_sha256": lock["source"]["corpus"]["tree_sha256"],
        "prompt_counts": {
            "total": len(rows),
            "applicable": sum(row["applicable"] for row in rows),
            "null": sum(not row["applicable"] for row in rows),
        },
        "floors": FLOORS,
        "metrics": metrics,
        "gates": gates,
        "passed": all(gates.values()),
        "rows": rows,
    }
    write_report_exclusive(output.parent, output.name, output_parent_identity, report)
    print(json.dumps({"output": str(output), "passed": report["passed"], "metrics": metrics}, sort_keys=True))
    return 0 if report["passed"] else 1

if __name__ == "__main__":
    raise SystemExit(main())
