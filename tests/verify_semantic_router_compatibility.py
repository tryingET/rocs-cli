#!/usr/bin/env python3
"""Independent packet, byte, parser, and direct-discovery compatibility gate."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

PACKET_COMMIT = "52454f5dd86582290db642b73acc6c5cab8e9e1d"
PACKET_MANIFEST_SHA256 = "0fad833e48d6d2c198ee4f5f8c39d6fea67d59a20a758969b623dbe44fd09d68"
BASE_COMMIT = "0a9d9eed00c4c2875d6a7dd870b8978032c95875"
BASE_TREE = "a55c5dc00dce05a9ee4a5d12179f4daa2b2c1c8f"
TOOL_MANIFEST = "sha256:" + "4" * 64


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text("utf-8"))


def run(
    args: list[str], *, cwd: Path, env: dict[str, str], stdin: bytes | None = None,
    expected: int = 0,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(args, cwd=cwd, env=env, input=stdin, capture_output=True, check=False)
    if completed.returncode != expected:
        raise AssertionError(
            f"command exit mismatch: {args!r}; expected={expected} actual={completed.returncode}; "
            f"stdout_sha256={sha(completed.stdout)} stderr_sha256={sha(completed.stderr)}"
        )
    return completed


def clean_env(home: Path, root: Path | None = None) -> dict[str, str]:
    env = {
        "HOME": str(home), "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8",
        "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1", "PYTHONHASHSEED": "0",
        "ROCS_INDEX_CACHE": "0",
    }
    if root is not None:
        env["PYTHONPATH"] = str(root / "src")
    return env


def git(candidate: Path, *args: str) -> bytes:
    return subprocess.run(
        ["git", "-C", str(candidate), *args], env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
        capture_output=True, check=True,
    ).stdout


def verify_packet(candidate: Path, expected_aggregate: str) -> None:
    manifest_path = candidate / "docs/project/semantic-router-v0/packet-manifest.json"
    raw_manifest = manifest_path.read_bytes()
    assert sha(raw_manifest) == PACKET_MANIFEST_SHA256, "packet manifest digest drift"
    manifest = json.loads(raw_manifest)
    rows: list[bytes] = []
    for item in manifest["files"]:
        raw = (candidate / item["path"]).read_bytes()
        assert len(raw) == item["bytes"], f"packet byte length drift: {item['path']}"
        assert sha(raw) == item["sha256"], f"packet hash drift: {item['path']}"
        rows.append(f"{item['path']}\t{len(raw)}\t{sha(raw)}\n".encode())
    aggregate = sha(b"".join(sorted(rows)))
    assert aggregate == expected_aggregate == manifest["packet_aggregate_sha256"], "packet aggregate drift"
    ancestor = subprocess.run(["git", "-C", str(candidate), "merge-base", "--is-ancestor", PACKET_COMMIT, "HEAD"])
    assert ancestor.returncode == 0, "accepted packet commit is not an ancestor"


def protected_state(candidate: Path) -> dict[str, str]:
    baseline = read_json(candidate / "docs/project/semantic-router-v0/discovery-compatibility-baseline.json")
    assert baseline["base_commit"] == BASE_COMMIT and baseline["base_tree"] == BASE_TREE
    state = {}
    for item in baseline["protected_files"]:
        actual = sha((candidate / item["path"]).read_bytes())
        assert actual == item["sha256"], f"protected hash drift: {item['path']}"
        state[item["path"]] = actual
    return state


def verify_behavior_vectors(candidate: Path, python: str, home: Path) -> None:
    baseline = read_json(candidate / "docs/project/semantic-router-v0/discovery-compatibility-baseline.json")
    for vector in baseline["behavior_vectors"]:
        command = vector["command"].replace("<candidate>", str(candidate)).replace("<python>", python)
        assert "<" not in command and ">" not in command, f"unknown placeholder: {vector['id']}"
        command_args = shlex.split(command)
        # The baseline's semantic-oracle vector names `python` generically; bind it
        # to the same explicit 3.12 interpreter used for every other comparison.
        if command_args[0] == "python":
            command_args[0] = python
        completed = run(command_args, cwd=candidate, env=clean_env(home), expected=vector["expected_exit"])
        if "stdout_sha256" in vector:
            assert sha(completed.stdout) == vector["stdout_sha256"], f"stdout drift: {vector['id']}"
        if "stderr_sha256" in vector:
            assert sha(completed.stderr) == vector["stderr_sha256"], f"stderr drift: {vector['id']}"


def extract_base(candidate: Path, destination: Path) -> None:
    destination.mkdir()
    archive = subprocess.Popen(
        ["git", "-C", str(candidate), "archive", "--format=tar", BASE_COMMIT],
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}, stdout=subprocess.PIPE,
    )
    assert archive.stdout is not None
    unpack = subprocess.run(
        ["tar", "-xf", "-", "-C", str(destination)], stdin=archive.stdout,
        env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}, capture_output=True,
    )
    archive.stdout.close()
    assert archive.wait() == 0 and unpack.returncode == 0, "base archive extraction failed"


def write_synthetic_repo(root: Path) -> Path:
    repo = root / "synthetic-repo"
    ontology = repo / "ontology"
    (ontology / "src/reference/concepts").mkdir(parents=True)
    (ontology / "manifest.yaml").write_text(
        "rocs:\n  layers:\n    - name: core\n      path: ontology/src\n  profiles:\n    default: review\n    review:\n      include_layers: [core]\n",
        "utf-8",
    )
    (ontology / "src/reference/concepts/synthetic.Agent.md").write_text(
        "---\nont:\n  id: synthetic.Agent\n  type: concept\n  labels: [Agent]\n  description: Synthetic agent authority.\n  examples: [agent]\n  anti_examples: [tool]\n---\n",
        "utf-8",
    )
    return repo


def discovery_request() -> bytes:
    value = {
        "schema": "semantic-discovery-request.v0", "query": "synthetic agent authority",
        "identity_selector": {"kind": "development_snapshot"}, "profile": "review", "algorithm": "rocs-lexical-v0",
        "limits": {
            "query_bytes": 16384, "corpus_files": 5000, "corpus_bytes": 33554432,
            "file_bytes": 1048576, "parser_depth": 32, "collection_items": 10000,
            "candidates": 12, "result_bytes": 65536,
        },
    }
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def discover(root: Path, python: str, home: Path, repo: Path, raw: bytes, *, debug: bool = False) -> subprocess.CompletedProcess[bytes]:
    args = [python, "-m", "rocs_cli"]
    if debug:
        args.append("--debug")
    args.extend([
        "discover", "--repo", str(repo), "--request-json", "-",
        "--tool-kind", "development_runtime", "--tool-manifest-digest", TOOL_MANIFEST,
        "--json", "--no-index-cache", "--no-env-file",
    ])
    expected = 1 if raw == b"{" else 0
    return run(args, cwd=root, env=clean_env(home, root), stdin=raw, expected=expected)


PARSER_SCRIPT = r'''
import argparse, json
from rocs_cli.cli import build_parser

def atom(value):
    if callable(value): return f"{value.__module__}.{value.__qualname__}"
    try: json.dumps(value); return value
    except TypeError: return repr(value)

def parser_value(parser):
    actions=[]; children={}; subparser=None
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            subparser={"dest":action.dest,"required":action.required,"nargs":action.nargs}
            children={name: parser_value(child) for name,child in sorted(action.choices.items())}
            continue
        actions.append({
            "class": type(action).__name__, "options": list(action.option_strings), "dest": action.dest,
            "nargs": action.nargs, "required": action.required, "const": atom(action.const),
            "default": atom(action.default), "choices": sorted(action.choices) if action.choices is not None else None,
            "type": atom(action.type), "metavar": atom(action.metavar), "help": atom(action.help),
        })
    mutex=[{"required":group.required,"actions":[action.dest for action in group._group_actions]} for group in parser._mutually_exclusive_groups]
    settings={"allow_abbrev":parser.allow_abbrev,"prefix_chars":parser.prefix_chars,"fromfile_prefix_chars":parser.fromfile_prefix_chars,"conflict_handler":parser.conflict_handler,"exit_on_error":parser.exit_on_error,"description":atom(parser.description),"epilog":atom(parser.epilog),"usage":atom(parser.usage),"defaults":{key:atom(value) for key,value in sorted(parser._defaults.items())}}
    return {"actions":actions,"children":children,"subparser":subparser,"mutex":mutex,"settings":settings}
print(json.dumps(parser_value(build_parser()),sort_keys=True,separators=(",",":")))
'''


def parser_signature(root: Path, python: str, home: Path) -> dict[str, Any]:
    completed = run([python, "-c", PARSER_SCRIPT], cwd=root, env=clean_env(home, root))
    return json.loads(completed.stdout)


def assert_base_signature_preserved(base: dict[str, Any], candidate: dict[str, Any], path: str = "") -> None:
    for key in ("actions", "subparser", "mutex", "settings"):
        assert base[key] == candidate[key], f"parser {key} drift at {path or '/'}"
    for name, child in base["children"].items():
        assert name in candidate["children"], f"parser command missing: {path}/{name}"
        assert_base_signature_preserved(child, candidate["children"][name], f"{path}/{name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default=BASE_COMMIT)
    parser.add_argument("--packet-aggregate", required=True)
    parser.add_argument("--candidate-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    candidate = args.candidate_root.resolve()
    assert args.base == BASE_COMMIT, "unexpected compatibility base"
    assert sys.version_info[:2] == (3, 12), "compatibility verifier requires CPython 3.12"
    assert sys.implementation.name == "cpython", "compatibility verifier requires CPython"
    verify_packet(candidate, args.packet_aggregate)
    before = protected_state(candidate)
    with tempfile.TemporaryDirectory(prefix="rocs-router-compat-") as temporary:
        temp = Path(temporary)
        home = temp / "home"; home.mkdir()
        verify_behavior_vectors(candidate, sys.executable, home)
        base = temp / "base"; extract_base(candidate, base)
        assert git(candidate, "rev-parse", f"{BASE_COMMIT}^{{tree}}").decode().strip() == BASE_TREE
        repo = write_synthetic_repo(temp)
        for raw in (discovery_request(), b"{"):
            for debug in (False, True):
                candidate_result = discover(candidate, sys.executable, home, repo, raw, debug=debug)
                base_result = discover(base, sys.executable, home, repo, raw, debug=debug)
                assert candidate_result.returncode == base_result.returncode, "direct discovery exit drift"
                assert candidate_result.stdout == base_result.stdout, "direct discovery stdout drift"
                assert candidate_result.stderr == base_result.stderr, "direct discovery stderr drift"
        assert_base_signature_preserved(parser_signature(base, sys.executable, home), parser_signature(candidate, sys.executable, home))
    assert protected_state(candidate) == before, "protected discovery changed during verification"
    print("semantic-router-v0 compatibility verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
