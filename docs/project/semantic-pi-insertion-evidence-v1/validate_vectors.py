#!/usr/bin/env python3
"""Independent stdlib conformance runner for Decision 85 insertion evidence."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from python.common import (
    ACCEPTED_AGGREGATE,
    DOMAINS,
    FROZEN_AGGREGATE,
    ID_RE,
    OBJECT_DOMAINS,
    REVISION,
    SCHEMA_NAMES,
    VECTOR_SHA256,
    ConformanceError,
    StrictJSONError,
    inspect_schema,
    jcs_bytes,
    object_digest,
    require,
    same,
    schema_matches,
    strict_json_loads,
)
from python.protocol import run_attempt


def frozen_aggregate(repo: Path) -> str:
    names = sorted(
        (
            "docs/project/semantic-pi-insertion-evidence-v1-problem-brief.md",
            "docs/project/semantic-pi-insertion-evidence-v1-evidence-note.md",
            "docs/project/semantic-pi-insertion-evidence-v1-rfc.md",
            "docs/project/semantic-pi-insertion-evidence-v1-review-set-plan.md",
            "docs/project/semantic-pi-insertion-evidence-v1-vectors.json",
        ),
        key=lambda name: name.encode(),
    )
    rows = bytearray()
    for name in names:
        raw = (repo / name).read_bytes()
        rows.extend(f"{name}\t{len(raw)}\t{hashlib.sha256(raw).hexdigest()}\n".encode())
    return hashlib.sha256(rows).hexdigest()


def validate_shells(vectors: dict[str, Any]) -> None:
    require(set(vectors) == {"schema", "protocol_revision", "cases", "host_fixtures", "accepted_object_aggregate_sha256"}, "vector root keys mismatch")
    require(vectors["schema"] == SCHEMA_NAMES[5] and vectors["protocol_revision"] == REVISION, "vector identity mismatch")
    require(isinstance(vectors["cases"], list) and len(vectors["cases"]) == 16, "case count mismatch")
    require(isinstance(vectors["host_fixtures"], list) and len(vectors["host_fixtures"]) == 13, "host fixture count mismatch")
    case_keys = {
        "id", "input_bytes_base64", "contribution_bytes_base64", "initial_generation", "initial_next_attempt_id",
        "handler_registration_index", "deadline_monotonic_ns", "events", "expected",
    }
    fixture_keys = {
        "id", "baseline_case_id", "events", "expected_terminal_state", "expected_provider_operations_before_record",
        "expected_model_operations_before_record", "expected_control_results",
    }
    for case in vectors["cases"]:
        require(isinstance(case, dict) and set(case) == case_keys and ID_RE.fullmatch(case["id"]) is not None, "invalid case shell")
    for fixture in vectors["host_fixtures"]:
        require(isinstance(fixture, dict) and set(fixture) == fixture_keys and ID_RE.fullmatch(fixture["id"]) is not None, "invalid fixture shell")
    for values, label in ((vectors["cases"], "case"), (vectors["host_fixtures"], "fixture")):
        ids = [item["id"] for item in values]
        require(len(ids) == len(set(ids)) and ids == sorted(ids, key=lambda value: value.encode()), f"{label} IDs are not unique ASCII-sorted IDs")


def main() -> int:
    packet = Path(__file__).resolve().parent
    repo = packet.parents[2]
    vector_path = packet.parent / "semantic-pi-insertion-evidence-v1-vectors.json"
    schema = strict_json_loads((packet / "protocol.schema.json").read_bytes(), "protocol.schema.json")
    vectors_raw = vector_path.read_bytes()
    vectors = strict_json_loads(vectors_raw, vector_path.name)
    require(isinstance(schema, dict) and isinstance(vectors, dict), "schema and vectors must be JSON objects")
    inspect_schema(schema)
    validate_shells(vectors)

    case_runs: list[tuple[str, dict[str, Any]]] = []
    case_inputs: dict[str, dict[str, Any]] = {}
    core = (
        "input_bytes_base64", "contribution_bytes_base64", "initial_generation", "initial_next_attempt_id",
        "handler_registration_index", "deadline_monotonic_ns", "events",
    )
    for case in vectors["cases"]:
        execution_input = {key: case[key] for key in core}
        actual, _ = run_attempt(execution_input, False)
        case_runs.append((case["id"], actual))
        case_inputs[case["id"]] = execution_input

    fixture_runs: list[tuple[str, dict[str, Any]]] = []
    for fixture in vectors["host_fixtures"]:
        baseline = case_inputs.get(fixture["baseline_case_id"])
        require(baseline is not None, "host fixture baseline does not exist")
        execution_input = dict(baseline)
        execution_input["events"] = fixture["events"]
        _, metadata = run_attempt(execution_input, True)
        fixture_runs.append((fixture["id"], metadata))

    vector_schema = schema["$defs"][SCHEMA_NAMES[5]]
    require(schema_matches(vectors, vector_schema, schema), "frozen vector set does not satisfy protocol schema")
    cases_by_id = {case["id"]: case for case in vectors["cases"]}
    fixtures_by_id = {fixture["id"]: fixture for fixture in vectors["host_fixtures"]}
    for case_id, actual in case_runs:
        expected = cases_by_id[case_id]["expected"]
        require(same(actual, expected), f"case result mismatch: {case_id}")
        for value in actual.values():
            if isinstance(value, dict) and value.get("schema") in OBJECT_DOMAINS:
                name = value["schema"]
                require(schema_matches(value, schema["$defs"][name], schema), f"actual object schema mismatch: {case_id}/{name}")
                domain, self_field = OBJECT_DOMAINS[name]
                require(value[self_field] == object_digest(domain, value, self_field), f"actual object digest mismatch: {case_id}/{name}")
    for fixture_id, actual in fixture_runs:
        expected_source = fixtures_by_id[fixture_id]
        expected = {
            "terminal_state": expected_source["expected_terminal_state"],
            "provider_operations_before_record": expected_source["expected_provider_operations_before_record"],
            "model_operations_before_record": expected_source["expected_model_operations_before_record"],
            "control_results": expected_source["expected_control_results"],
        }
        require(same(actual, expected), f"host fixture result mismatch: {fixture_id}")

    accepted = sorted(((case_id, value) for case_id, value in case_runs if value["accepted"]), key=lambda row: row[0].encode())
    aggregate_bytes = b"".join(
        jcs_bytes(value[field])
        for _, value in accepted
        for field in ("request_or_null", "witness_or_null", "acknowledgement_or_null", "record_or_null")
    )
    accepted_hash = hashlib.sha256(aggregate_bytes).hexdigest()
    vector_hash = hashlib.sha256(vectors_raw).hexdigest()
    frozen_hash = frozen_aggregate(repo)
    require(len(accepted) == 3, "accepted case count mismatch")
    require(accepted_hash == vectors["accepted_object_aggregate_sha256"] == ACCEPTED_AGGREGATE, "accepted-object aggregate mismatch")
    require(vector_hash == VECTOR_SHA256, "frozen vector SHA-256 mismatch")
    require(frozen_hash == FROZEN_AGGREGATE, "frozen five-file aggregate mismatch")
    tools = strict_json_loads((repo / "scripts/tool_versions.json").read_bytes(), "tool_versions.json")
    require(isinstance(tools, dict) and tools.get("node") == "26.9.0", "Node validator pin must be exactly 26.9.0")
    report = {
        "accepted_cases": len(accepted),
        "accepted_object_aggregate_sha256": accepted_hash,
        "cases": len(case_runs),
        "digest_domains": len(DOMAINS),
        "frozen_aggregate_sha256": frozen_hash,
        "host_fixtures": len(fixture_runs),
        "implementation": "python-stdlib-independent",
        "node_pin": tools["node"],
        "schema_count": len(SCHEMA_NAMES),
        "unused_events": 0,
        "vector_sha256": vector_hash,
    }
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ConformanceError, StrictJSONError, OSError) as exc:
        print(f"semantic-pi-insertion conformance failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
