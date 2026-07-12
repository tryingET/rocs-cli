from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tests.test_semantic_discovery import _document, _write

ROOT = Path(__file__).resolve().parents[1]
TOOL_MANIFEST = "sha256:" + "4" * 64


def _repo(tmp: Path) -> Path:
    root = tmp / "repo"
    ontology = root / "ontology"
    _write(
        ontology / "manifest.yaml",
        """rocs:
  layers:
    - name: core
      path: ontology/src
  profiles:
    default: review
    review:
      include_layers: [core]
""",
    )
    _write(ontology / "src/reference/concepts/core.Agent.md", _document("core.Agent", description="Agent authority.", examples=["agent"]))
    return root


def _request(query: str = "agent authority") -> dict:
    return {
        "schema": "semantic-discovery-request.v0",
        "query": query,
        "identity_selector": {"kind": "development_snapshot"},
        "profile": "review",
        "algorithm": "rocs-lexical-v0",
        "limits": {
            "query_bytes": 16384,
            "corpus_files": 5000,
            "corpus_bytes": 33554432,
            "file_bytes": 1048576,
            "parser_depth": 32,
            "collection_items": 10000,
            "candidates": 12,
            "result_bytes": 65536,
        },
    }


def _run(args: list[str], *, stdin: bytes = b"", env: dict[str, str] | None = None) -> subprocess.CompletedProcess[bytes]:
    clean = {
        "HOME": os.environ.get("HOME", "/tmp"),
        "PATH": "/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONNOUSERSITE": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
        "ROCS_INDEX_CACHE": "0",
    }
    if env:
        clean.update(env)
    return subprocess.run(
        [sys.executable, "-m", "rocs_cli", *args], cwd=ROOT, env=clean,
        input=stdin, capture_output=True, check=False,
    )


def _discover_args(repo: Path) -> list[str]:
    return [
        "discover", "--repo", str(repo), "--request-json", "-",
        "--tool-kind", "development_runtime", "--tool-manifest-digest", TOOL_MANIFEST,
        "--json", "--no-index-cache", "--no-env-file",
    ]


class SemanticDiscoveryCliTests(unittest.TestCase):
    def test_capabilities_and_contracts_are_parser_closed_and_effect_free(self) -> None:
        capabilities = _run(["discover-capabilities", "--json"])
        self.assertEqual(capabilities.returncode, 0, capabilities.stderr.decode())
        payload = json.loads(capabilities.stdout)
        self.assertEqual(payload["schema"], "semantic-discovery-capabilities.v0")
        contracts = json.loads(_run(["contracts"]).stdout)
        for operation in ("discover-capabilities", "discover"):
            self.assertEqual(contracts["commands"][operation]["effect_rules"], [{"effect": "none", "condition": "always"}])

    def test_discover_success_is_deterministic_and_non_mutating(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo(Path(td))
            before = {path.relative_to(repo): (path.read_bytes(), path.stat().st_mtime_ns) for path in repo.rglob("*") if path.is_file()}
            raw = json.dumps(_request(), separators=(",", ":")).encode()
            first = _run(_discover_args(repo), stdin=raw)
            second = _run(_discover_args(repo), stdin=raw, env={"ROCS_ENV_FILE": "/hostile/.env", "PYTHONPATH": "/hostile"})
            self.assertEqual(first.returncode, 0, first.stderr.decode())
            self.assertEqual(second.returncode, 0, second.stderr.decode())
            self.assertEqual(json.loads(first.stdout), json.loads(second.stdout))
            result = json.loads(first.stdout)
            self.assertEqual(result["schema"], "semantic-discovery-result.v0")
            self.assertEqual(result["candidates"][0]["score"], 1150)
            self.assertEqual(result["tool_identity"]["manifest_digest"], TOOL_MANIFEST)
            after = {path.relative_to(repo): (path.read_bytes(), path.stat().st_mtime_ns) for path in repo.rglob("*") if path.is_file()}
            self.assertEqual(after, before)
            self.assertFalse((repo / "ontology/dist").exists())

    def test_request_error_boundary_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo(Path(td))
            malformed = _run(_discover_args(repo), stdin=b"{")
            self.assertEqual(malformed.returncode, 1)
            error = json.loads(malformed.stdout)["error"]
            self.assertEqual((error["kind"], error["caller_request_digest"]), ("invalid_request", None))

            unknown = _request()
            unknown["extra"] = True
            rejected = _run(_discover_args(repo), stdin=json.dumps(unknown).encode())
            self.assertEqual(rejected.returncode, 1)
            error = json.loads(rejected.stdout)["error"]
            self.assertEqual(error["kind"], "invalid_request")
            self.assertRegex(error["caller_request_digest"], r"^sha256:[0-9a-f]{64}$")

            oversized = _request("a" * 16385)
            exhausted = _run(_discover_args(repo), stdin=json.dumps(oversized).encode())
            self.assertEqual(json.loads(exhausted.stdout)["error"]["kind"], "resource_exhausted")

    def test_explicit_request_file_rejects_symlink_and_automatic_flags_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            repo = _repo(base)
            request_file = base / "request.json"
            request_file.write_text(json.dumps(_request()), "utf-8")
            link = base / "request-link.json"
            link.symlink_to(request_file)
            args = _discover_args(repo)
            args[args.index("--request-json"):args.index("--request-json") + 2] = ["--request-file", str(link)]
            rejected = _run(args)
            self.assertEqual(json.loads(rejected.stdout)["error"]["kind"], "invalid_request")
            for args_variant in (
                [item for item in _discover_args(repo) if item != "--no-env-file"],
                [*_discover_args(repo), "--bogus"],
                [*_discover_args(repo), "--json=bad"],
                [*_discover_args(repo), "--resolve-refs=bad"],
            ):
                rejected_flags = _run(args_variant, stdin=json.dumps(_request()).encode())
                self.assertEqual(rejected_flags.returncode, 1)
                self.assertEqual(json.loads(rejected_flags.stdout)["error"]["kind"], "invalid_request")
                self.assertEqual(rejected_flags.stderr, b"")

            malformed_digest = _discover_args(repo)
            malformed_digest[malformed_digest.index("--tool-manifest-digest") + 1] = "bad"
            rejected_digest = _run(malformed_digest, stdin=json.dumps(_request()).encode())
            self.assertEqual(json.loads(rejected_digest.stdout)["error"]["kind"], "invalid_request")

    def test_bound_pack_replays_snapshot_and_document_identity(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo(Path(td))
            discovery = json.loads(_run(_discover_args(repo), stdin=json.dumps(_request()).encode()).stdout)
            candidate = discovery["candidates"][0]
            args = [
                "pack", candidate["ont_id"], "--repo", str(repo), "--profile", "review",
                "--expected-snapshot-digest", discovery["corpus_snapshot_digest"],
                "--expected-document-digest", candidate["document_digest"],
                "--json", "--no-index-cache", "--no-env-file",
            ]
            packed = _run(args)
            self.assertEqual(packed.returncode, 0, packed.stderr.decode())
            payload = json.loads(packed.stdout)
            self.assertEqual(payload["schema"], "semantic-pack-result.v0")
            self.assertEqual(payload["root_id"], "core.Agent")
            self.assertEqual(payload["documents"][0]["document_digest"], candidate["document_digest"])
            self.assertIn("agent authority", payload["documents"][0]["text"].lower())

            wrong = list(args)
            wrong[wrong.index("--expected-document-digest") + 1] = "sha256:" + "0" * 64
            rejected = _run(wrong)
            self.assertEqual(rejected.returncode, 1)
            self.assertEqual(json.loads(rejected.stdout)["error"]["kind"], "snapshot_changed")

    def test_bound_pack_requires_both_preconditions_and_preserves_unbound_parser(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            repo = _repo(Path(td))
            partial = _run([
                "pack", "core.Agent", "--repo", str(repo), "--profile", "review",
                "--expected-snapshot-digest", "sha256:" + "0" * 64,
                "--json", "--no-index-cache", "--no-env-file",
            ])
            self.assertEqual(json.loads(partial.stdout)["error"]["kind"], "invalid_request")
            unbound = _run(["pack", "core.Agent", "--repo", str(repo), "--profile", "review", "--json"])
            self.assertEqual(unbound.returncode, 0, unbound.stderr.decode())
            self.assertIn("pack", json.loads(unbound.stdout))


if __name__ == "__main__":
    unittest.main()
