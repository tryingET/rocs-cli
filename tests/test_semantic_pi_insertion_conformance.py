from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "docs" / "project" / "semantic-pi-insertion-evidence-v1"
VECTORS = ROOT / "docs" / "project" / "semantic-pi-insertion-evidence-v1-vectors.json"
VECTOR_SHA256 = "e23437e075f49c36e7487deeec2ab8126cd8fb14c0dbf07bf48d17e466525ed4"
FROZEN_AGGREGATE = "272c892af593ff10ddb056b1914f20372308fe8a47ca28b3ca04ca8e27882991"
ACCEPTED_AGGREGATE = "e1a715cd868bdd9807eecb798b29ac02342697cc2afd9ac8eb7d9b6296b97a7e"
SCHEMA_NAMES = (
    "semantic-pi-insertion-request.v1",
    "pi.prompt-chain-application-witness.v1",
    "semantic-pi-insertion-acknowledgement.v1",
    "pi.prompt-chain-insertion-record.v1",
    "semantic-pi-insertion-error.v1",
    "semantic-pi-insertion-vector-set.v1",
)
DOMAINS = (
    "semantic-pi-insertion.request.v1",
    "pi.prompt-chain-application-witness.v1",
    "semantic-pi-insertion.acknowledgement.v1",
    "pi.prompt-chain-insertion-record.v1",
    "semantic-pi-insertion.error.v1",
    "semantic-pi-insertion.input-prompt-bytes.v1",
    "semantic-pi-insertion.contribution-bytes.v1",
    "pi.prompt-chain-bytes.v1",
)
FROZEN_PATHS = (
    "docs/project/semantic-pi-insertion-evidence-v1-problem-brief.md",
    "docs/project/semantic-pi-insertion-evidence-v1-evidence-note.md",
    "docs/project/semantic-pi-insertion-evidence-v1-rfc.md",
    "docs/project/semantic-pi-insertion-evidence-v1-review-set-plan.md",
    "docs/project/semantic-pi-insertion-evidence-v1-vectors.json",
)


def frozen_aggregate(root: Path) -> str:
    rows = bytearray()
    for name in sorted(FROZEN_PATHS, key=lambda value: value.encode("utf-8")):
        raw = (root / name).read_bytes()
        rows.extend(f"{name}\t{len(raw)}\t{hashlib.sha256(raw).hexdigest()}\n".encode("utf-8"))
    return hashlib.sha256(rows).hexdigest()


def resolve_pointer(root: object, ref: str) -> object:
    value = root
    for raw in ref.removeprefix("#/").split("/"):
        key = raw.replace("~1", "/").replace("~0", "~")
        value = value[key]  # type: ignore[index]
    return value


def run_validator(root: Path, language: str) -> subprocess.CompletedProcess[str]:
    relative = Path("docs/project/semantic-pi-insertion-evidence-v1")
    command = (
        [sys.executable, str(relative / "validate_vectors.py")]
        if language == "python"
        else ["node", str(relative / "validate_vectors.mjs")]
    )
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    return subprocess.run(command, cwd=root, env=environment, text=True, capture_output=True, check=False)


class SemanticPiInsertionConformanceTests(unittest.TestCase):
    def test_frozen_sources_and_unconditional_node_pin(self) -> None:
        self.assertEqual(hashlib.sha256(VECTORS.read_bytes()).hexdigest(), VECTOR_SHA256)
        self.assertEqual(frozen_aggregate(ROOT), FROZEN_AGGREGATE)
        vectors = json.loads(VECTORS.read_text("utf-8"))
        self.assertEqual(len(vectors["cases"]), 16)
        self.assertEqual(len(vectors["host_fixtures"]), 13)
        self.assertEqual(sum(case["expected"]["accepted"] for case in vectors["cases"]), 3)
        self.assertEqual(vectors["accepted_object_aggregate_sha256"], ACCEPTED_AGGREGATE)
        tools = json.loads((ROOT / "scripts" / "tool_versions.json").read_text("utf-8"))
        self.assertEqual(tools["node"], "26.1.0")
        runtime = subprocess.run(["node", "--version"], text=True, capture_output=True, check=True).stdout.strip()
        self.assertEqual(runtime, "v26.1.0")

    def test_bundle_has_exactly_six_closed_local_ref_schemas_and_eight_domains(self) -> None:
        schema = json.loads((PACKET / "protocol.schema.json").read_text("utf-8"))
        self.assertEqual(schema["$schema"], "https://json-schema.org/draft/2020-12/schema")
        self.assertEqual(tuple(schema["$defs"]), SCHEMA_NAMES)
        self.assertEqual(tuple(schema["x-digest-domains"]), DOMAINS)
        self.assertEqual([row["$ref"] for row in schema["oneOf"]], [f"#/$defs/{name}" for name in SCHEMA_NAMES])
        for name, definition in schema["$defs"].items():
            self.assertEqual(definition["properties"]["schema"]["const"], name)

        object_schema_count = 0

        def walk(value: object) -> None:
            nonlocal object_schema_count
            if isinstance(value, dict):
                if "$ref" in value:
                    self.assertTrue(value["$ref"].startswith("#/"))
                    self.assertIsInstance(resolve_pointer(schema, value["$ref"]), dict)
                if value.get("type") == "object":
                    object_schema_count += 1
                    self.assertIs(value.get("additionalProperties"), False)
                for child in value.values():
                    walk(child)
            elif isinstance(value, list):
                for child in value:
                    walk(child)

        walk(schema)
        self.assertGreater(object_schema_count, 6)

    def test_validators_are_independent_stdlib_executors_without_behavior_oracles(self) -> None:
        python_path = PACKET / "validate_vectors.py"
        node_path = PACKET / "validate_vectors.mjs"
        python_source = python_path.read_text("utf-8")
        node_source = node_path.read_text("utf-8")
        tree = ast.parse(python_source)
        imports = {
            alias.name.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imports.update(
            node.module.split(".")[0]
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )
        self.assertLessEqual(imports, {"__future__", "base64", "binascii", "hashlib", "json", "re", "struct", "sys", "unicodedata", "pathlib", "typing"})
        self.assertEqual(re.findall(r'from\s+"([^"]+)"', node_source), ["node:crypto", "node:fs", "node:path", "node:url"])
        self.assertNotIn("validate_vectors.mjs", python_source)
        self.assertNotIn("validate_vectors.py", node_source)
        for source in (python_source, node_source):
            self.assertNotIn("rocs_cli", source)
            self.assertNotIn("semantic-release-v0", source)
            self.assertNotIn("semantic-pi-delivery", source)

        python_runner = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "run_attempt")
        spec_keys = {
            node.slice.value
            for node in ast.walk(python_runner)
            if isinstance(node, ast.Subscript)
            and isinstance(node.value, ast.Name)
            and node.value.id == "spec"
            and isinstance(node.slice, ast.Constant)
            and isinstance(node.slice.value, str)
        }
        self.assertFalse({"id", "expected"} & spec_keys)
        node_runner = node_source[node_source.index("function runAttempt"):node_source.index("function frozenAggregate")]
        self.assertNotRegex(node_runner, r"\bspec\s*(?:\.id|\[\s*['\"]id['\"]\s*\])")
        self.assertNotRegex(node_runner, r"\bspec\s*(?:\.expected|\[\s*['\"]expected['\"]\s*\])")

    def test_standalone_validators_report_full_independent_conformance(self) -> None:
        reports = []
        for language in ("python", "node"):
            with self.subTest(language=language):
                completed = run_validator(ROOT, language)
                self.assertEqual(completed.returncode, 0, completed.stderr)
                report = json.loads(completed.stdout)
                self.assertEqual(report["cases"], 16)
                self.assertEqual(report["host_fixtures"], 13)
                self.assertEqual(report["accepted_cases"], 3)
                self.assertEqual(report["schema_count"], 6)
                self.assertEqual(report["digest_domains"], 8)
                self.assertEqual(report["unused_events"], 0)
                self.assertEqual(report["vector_sha256"], VECTOR_SHA256)
                self.assertEqual(report["frozen_aggregate_sha256"], FROZEN_AGGREGATE)
                self.assertEqual(report["accepted_object_aggregate_sha256"], ACCEPTED_AGGREGATE)
                reports.append(report)
        self.assertNotEqual(reports[0]["implementation"], reports[1]["implementation"])
        for key in set(reports[0]) - {"implementation"}:
            self.assertEqual(reports[0][key], reports[1][key])

    def test_expected_and_case_id_mutations_are_not_behavior_oracles(self) -> None:
        with tempfile.TemporaryDirectory(prefix="semantic-pi-insertion-") as raw:
            candidate = Path(raw) / "repo"
            packet = candidate / "docs" / "project" / "semantic-pi-insertion-evidence-v1"
            packet.mkdir(parents=True)
            (candidate / "scripts").mkdir()
            for name in ("protocol.schema.json", "validate_vectors.py", "validate_vectors.mjs"):
                shutil.copy2(PACKET / name, packet / name)
            for name in FROZEN_PATHS:
                destination = candidate / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, destination)
            shutil.copy2(ROOT / "scripts" / "tool_versions.json", candidate / "scripts" / "tool_versions.json")

            vectors_path = candidate / "docs" / "project" / "semantic-pi-insertion-evidence-v1-vectors.json"
            pristine = json.loads(vectors_path.read_text("utf-8"))
            wrong_expected = json.loads(json.dumps(pristine))
            wrong_expected["cases"][0]["expected"]["error_or_null"]["error_code"] = "internal_failure"
            vectors_path.write_text(json.dumps(wrong_expected, ensure_ascii=False, indent=2) + "\n", "utf-8")
            for language in ("python", "node"):
                with self.subTest(language=language, mutation="expected"):
                    completed = run_validator(candidate, language)
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn("case result mismatch", completed.stderr)

            renamed = json.loads(json.dumps(pristine))
            renamed["cases"][0]["id"] = "aaa-abort-before-witness"
            vectors_path.write_text(json.dumps(renamed, ensure_ascii=False, indent=2) + "\n", "utf-8")
            for language in ("python", "node"):
                with self.subTest(language=language, mutation="case-id"):
                    completed = run_validator(candidate, language)
                    self.assertNotEqual(completed.returncode, 0)
                    self.assertIn("frozen vector SHA-256 mismatch", completed.stderr)
                    self.assertNotIn("case result mismatch", completed.stderr)


if __name__ == "__main__":
    unittest.main()
