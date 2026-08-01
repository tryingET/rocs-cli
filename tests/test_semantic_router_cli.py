from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from rocs_cli.cli import build_parser
from rocs_cli.semantic_router_protocol import jcs_bytes, object_digest, route_capabilities

ROOT = Path(__file__).resolve().parents[1]
GOLDEN = ROOT / "docs/project/semantic-router-v0/golden-fixtures.json"
TOOL_MANIFEST = "sha256:" + "4" * 64
GIT_ENV = {
    "PATH": "/usr/bin:/bin",
    "HOME": "/nonexistent",
    "LANG": "C",
    "LC_ALL": "C",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_CONFIG_GLOBAL": "/dev/null",
    "GIT_CONFIG_SYSTEM": "/dev/null",
    "GIT_AUTHOR_NAME": "Synthetic S3",
    "GIT_AUTHOR_EMAIL": "synthetic-s3@example.invalid",
    "GIT_COMMITTER_NAME": "Synthetic S3",
    "GIT_COMMITTER_EMAIL": "synthetic-s3@example.invalid",
    "GIT_AUTHOR_DATE": "2026-08-01T00:00:00Z",
    "GIT_COMMITTER_DATE": "2026-08-01T00:00:00Z",
}


def _digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _write(path: Path, raw: str | bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(raw, str):
        path.write_text(raw, "utf-8")
    else:
        path.write_bytes(raw)


def _document(ont_id: str, label: str) -> str:
    return f"""---
ont:
  id: {ont_id}
  type: concept
  labels: [{label}]
  description: Conspicuously synthetic {label.lower()} concept.
  relations: []
  examples: [{label.lower()}]
  anti_examples: [unrelated]
---

# {label}
"""


class _RouteFixture:
    def __init__(self, base: Path) -> None:
        self.base = base
        self.repo = base / "corpus"
        self.policy_root = base / "policy"
        self.owner_root = base / "owner"
        self.home = base / "home"
        self.cache = base / "must-not-exist-cache"
        self.env_file = base / "hostile.env"
        for path in (self.policy_root, self.owner_root, self.home):
            path.mkdir()
        _write(self.env_file, "ROCS_WORKSPACE_REF_MODE=loose\nROCS_INDEX_CACHE=1\n")
        self._write_corpus()
        self.request = self._write_policy()

    def _write_corpus(self) -> None:
        _write(
            self.repo / "ontology/manifest.yaml",
            """rocs:
  layers:
    - name: synthetic
      path: ontology/src
  profiles:
    default: review
    review:
      include_layers: [synthetic]
""",
        )
        _write(
            self.repo / "ontology/src/reference/concepts/synthetic.Alpha.md",
            _document("synthetic.Alpha", "Alpha"),
        )
        _write(
            self.repo / "ontology/src/reference/concepts/synthetic.Beta.md",
            _document("synthetic.Beta", "Beta"),
        )

    def _git(self, *args: str) -> bytes:
        return subprocess.run(
            ["/usr/bin/git", *args],
            cwd=self.owner_root,
            env=GIT_ENV,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
        ).stdout

    def _write_policy(self) -> dict:
        valid = json.loads(GOLDEN.read_text("utf-8"))["valid"]
        request = deepcopy(valid["request"])
        policy = deepcopy(valid["policy"])
        provenance = deepcopy(valid["provenance"])
        authority_raw = b"conspicuously synthetic S3 authority\n"
        record_raw = b"conspicuously synthetic S3 provenance record\n"
        self._git("init", "-q")
        _write(self.owner_root / "authority.txt", authority_raw)
        _write(self.owner_root / "record.txt", record_raw)
        self._git("add", "authority.txt", "record.txt")
        self._git("commit", "-q", "-m", "synthetic S3 sources")
        revision = self._git("rev-parse", "HEAD").decode().strip()
        policy["authority"].update(
            {
                "owner_repo": "synthetic-owner",
                "revision": revision,
                "path": "authority.txt",
                "source_content_digest": _digest(authority_raw),
                "review_ref": "synthetic-s3-review",
            }
        )
        provenance.update(
            {
                "policy_owner_repo": "synthetic-owner",
                "policy_revision": revision,
                "policy_path": "authority.txt",
                "policy_source_content_digest": _digest(authority_raw),
            }
        )
        for record in provenance["records"]:
            record.update(
                {
                    "source_owner_repo": "synthetic-owner",
                    "source_revision": revision,
                    "source_path": "record.txt",
                    "source_content_digest": _digest(record_raw),
                    "author": "synthetic-s3-author",
                    "review_ref": "synthetic-s3-review",
                    "b0_exposure": "confirmed",
                    "development_case_ids": ["SYNTHETIC_S3"],
                }
            )
        provenance["provenance_manifest_digest"] = object_digest("provenance_manifest", provenance)
        policy["provenance_manifest_digest"] = provenance["provenance_manifest_digest"]
        policy["routing_policy_digest"] = object_digest("routing_policy", policy)
        request["expected_provenance_manifest_digest"] = provenance["provenance_manifest_digest"]
        request["expected_routing_policy_digest"] = policy["routing_policy_digest"]
        _write(self.policy_root / "policy.json", jcs_bytes(policy))
        _write(self.policy_root / "provenance.json", jcs_bytes(provenance))
        return request

    def args(self) -> list[str]:
        return [
            "route",
            "--repo",
            str(self.repo),
            "--policy-owner-repo-id",
            "synthetic-owner",
            "--policy-owner-repo-root",
            str(self.owner_root),
            "--routing-policy-root",
            str(self.policy_root),
            "--routing-policy",
            "policy.json",
            "--routing-provenance",
            "provenance.json",
            "--request-json",
            "-",
            "--tool-kind",
            "development_runtime",
            "--tool-manifest-digest",
            TOOL_MANIFEST,
            "--json",
            "--no-index-cache",
            "--no-env-file",
        ]

    def env(self, **updates: str) -> dict[str, str]:
        value = {
            "HOME": str(self.home),
            "PATH": "/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONNOUSERSITE": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "ROCS_CACHE_DIR": str(self.cache),
            "ROCS_ENV_FILE": str(self.env_file),
            "ROCS_INDEX_CACHE": "1",
            "ROCS_WORKSPACE_REF_MODE": "loose",
            "ROCS_WORKSPACE_ROOT": str(self.owner_root),
            "ROCS_POLICY_OWNER_ROOT": str(self.base / "ambient-owner"),
        }
        value.update(updates)
        return value

    def run(
        self,
        args: list[str] | None = None,
        *,
        stdin: bytes | None = None,
        env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            [sys.executable, "-m", "rocs_cli", *(args or self.args())],
            cwd=ROOT,
            env=env or self.env(),
            input=jcs_bytes(self.request) if stdin is None else stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )


class SemanticRouterCliTests(unittest.TestCase):
    def test_route_success_is_stdin_only_deterministic_and_environment_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = _RouteFixture(Path(temporary))
            first = fixture.run()
            second = fixture.run(env=fixture.env(ROCS_WORKSPACE_REF_MODE="invalid"))
            debug = fixture.run(["--debug", *fixture.args()])
            self.assertEqual(first.returncode, 0, first.stderr.decode())
            self.assertEqual(first.stderr, second.stderr, b"")
            self.assertEqual((first.stdout, first.stderr), (second.stdout, second.stderr))
            self.assertEqual((first.stdout, first.stderr), (debug.stdout, debug.stderr))
            result = json.loads(first.stdout)
            self.assertEqual(result["schema"], "semantic-route-result.v0")
            self.assertEqual(result["routing"]["state"], "multi")
            self.assertEqual(
                result["routing"]["selected_ont_ids"],
                ["synthetic.Alpha", "synthetic.Beta"],
            )
            self.assertEqual(
                result["discovery_result"]["schema"],
                "semantic-discovery-result.v0",
            )
            self.assertFalse(fixture.cache.exists())
            self.assertFalse((fixture.repo / "ontology/dist").exists())

    def test_capabilities_and_contracts_are_separate_and_effect_free(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = _RouteFixture(Path(temporary))
            route_caps = fixture.run(["route-capabilities", "--json"], stdin=b"")
            discovery_caps = fixture.run(["discover-capabilities", "--json"], stdin=b"")
            self.assertEqual(route_caps.returncode, 0, route_caps.stderr.decode())
            self.assertEqual(json.loads(route_caps.stdout), route_capabilities())
            colored = fixture.run(["route-capabilities", "--json"], stdin=b"", env=fixture.env(FORCE_COLOR="1"))
            self.assertEqual(colored.stdout, route_caps.stdout)
            self.assertEqual(json.loads(colored.stdout), route_capabilities())
            self.assertEqual(
                json.loads(discovery_caps.stdout)["schema"],
                "semantic-discovery-capabilities.v0",
            )
            contracts = json.loads(fixture.run(["contracts"], stdin=b"").stdout)
            for operation in ("route-capabilities", "route"):
                declaration = contracts["commands"][operation]
                self.assertEqual(declaration["capability"], "semantic-routing")
                self.assertEqual(
                    declaration["effect_rules"],
                    [{"condition": "always", "effect": "none"}],
                )
                self.assertEqual(declaration["required_authority_artifacts"], [])

    def test_route_parser_has_only_the_exact_required_automatic_flags(self) -> None:
        parser = build_parser()
        sub = next(action for action in parser._actions if action.dest == "cmd")
        route_parser = sub.choices["route"]
        actions = {
            action.option_strings[0]: action
            for action in route_parser._actions
            if action.option_strings and action.option_strings[0] != "-h"
        }
        expected = {
            "--repo",
            "--policy-owner-repo-id",
            "--policy-owner-repo-root",
            "--routing-policy-root",
            "--routing-policy",
            "--routing-provenance",
            "--request-json",
            "--tool-kind",
            "--tool-manifest-digest",
            "--json",
            "--no-index-cache",
            "--no-env-file",
        }
        self.assertEqual(set(actions), expected)
        self.assertTrue(all(action.required for action in actions.values()))
        self.assertEqual(list(actions["--request-json"].choices), ["-"])
        self.assertEqual(list(actions["--tool-kind"].choices), ["development_runtime"])

    def test_forbidden_or_missing_flags_fail_with_closed_stdout_only_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = _RouteFixture(Path(temporary))
            variants = []
            variants.extend([
                ["--index-cache-debug", *fixture.args()],
                [*fixture.args(), "--repo", str(fixture.repo)],
                [*fixture.args(), "--json"],
            ])
            for forbidden in (
                ["--request-file", str(fixture.base / "request.json")],
                ["--resolve-refs"],
                ["--workspace-ref-mode", "loose"],
                ["--env-file", str(fixture.env_file)],
                ["--network"],
            ):
                variants.append([*fixture.args(), *forbidden])
            for required in (
                "--policy-owner-repo-root",
                "--json",
                "--no-index-cache",
                "--no-env-file",
            ):
                args = fixture.args()
                index = args.index(required)
                del args[index : index + (1 if required.startswith("--no-") or required == "--json" else 2)]
                variants.append(args)
            request_file = fixture.base / "request.json"
            _write(request_file, jcs_bytes(fixture.request))
            file_args = fixture.args()
            file_args[file_args.index("--request-json") + 1] = str(request_file)
            variants.append(file_args)
            for args in variants:
                with self.subTest(args=args):
                    completed = fixture.run(args)
                    self.assertEqual(completed.returncode, 1)
                    self.assertEqual(completed.stderr, b"")
                    error = json.loads(completed.stdout)["error"]
                    self.assertEqual(error["schema"], "semantic-route-error.v0")
                    self.assertEqual(error["kind"], "invalid_request")

    def test_malformed_and_operational_errors_stay_safe_under_debug(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = _RouteFixture(Path(temporary))
            malformed = fixture.run(stdin=b"{")
            malformed_debug = fixture.run(["--debug", *fixture.args()], stdin=b"{")
            self.assertEqual(malformed.returncode, 1)
            self.assertEqual(
                (malformed.stdout, malformed.stderr),
                (malformed_debug.stdout, malformed_debug.stderr),
            )
            self.assertEqual(malformed.stderr, b"")
            self.assertEqual(json.loads(malformed.stdout)["error"]["kind"], "invalid_request")

            secret = "SECRET_OWNER_PATH_MUST_NOT_LEAK"
            args = fixture.args()
            args[args.index("--policy-owner-repo-root") + 1] = str(fixture.base / secret)
            failed = fixture.run(args)
            failed_debug = fixture.run(["--debug", *args])
            self.assertEqual((failed.stdout, failed.stderr), (failed_debug.stdout, failed_debug.stderr))
            self.assertEqual(failed.stderr, b"")
            self.assertEqual(json.loads(failed.stdout)["error"]["kind"], "invalid_policy")
            self.assertNotIn(secret.encode(), failed.stdout + failed.stderr)

    def test_ref_corpus_cannot_enable_loose_resolution_from_ambient_environment(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = _RouteFixture(Path(temporary))
            source = fixture.repo / "ontology/src"
            target = fixture.repo / "ontology/synthetic-external"
            os.rename(source, target); source.symlink_to(target, target_is_directory=True)
            failed = fixture.run()
            self.assertEqual(failed.returncode, 1)
            self.assertEqual(json.loads(failed.stdout)["error"]["kind"], "invalid_ontology")

        with tempfile.TemporaryDirectory() as temporary:
            fixture = _RouteFixture(Path(temporary))
            _write(
                fixture.repo / "ontology/manifest.yaml",
                """rocs:
  layers:
    - name: synthetic
      ref: <repo:synthetic/owner@main>
  profiles:
    default: review
    review:
      include_layers: [synthetic]
""",
            )
            failed = fixture.run(
                env=fixture.env(
                    ROCS_WORKSPACE_ROOT=str(fixture.base),
                    ROCS_WORKSPACE_REF_MODE="loose",
                )
            )
            self.assertEqual(failed.returncode, 1)
            self.assertEqual(failed.stderr, b"")
            self.assertEqual(json.loads(failed.stdout)["error"]["kind"], "invalid_ontology")


if __name__ == "__main__":
    unittest.main()
