#!/usr/bin/env node
/** Independent Node stdlib conformance runner for Decision 85 insertion evidence. */

import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  ACCEPTED_AGGREGATE,
  DOMAINS,
  FROZEN_AGGREGATE,
  ID_RE,
  OBJECT_DOMAINS,
  REVISION,
  SCHEMA_NAMES,
  VECTOR_SHA256,
  inspectSchema,
  jcsBytes,
  objectDigest,
  requireCondition,
  same,
  schemaMatches,
  sha256,
  strictJSONLoads,
} from "./node/common.mjs";
import { runAttempt } from "./node/protocol.mjs";

function frozenAggregate(repo) {
  const names = ["docs/project/semantic-pi-insertion-evidence-v1-problem-brief.md", "docs/project/semantic-pi-insertion-evidence-v1-evidence-note.md", "docs/project/semantic-pi-insertion-evidence-v1-rfc.md", "docs/project/semantic-pi-insertion-evidence-v1-review-set-plan.md", "docs/project/semantic-pi-insertion-evidence-v1-vectors.json"].sort((left, right) => Buffer.compare(Buffer.from(left), Buffer.from(right)));
  const rows = names.map((name) => { const raw = readFileSync(resolve(repo, name)); return Buffer.from(`${name}\t${raw.length}\t${sha256(raw)}\n`); });
  return sha256(Buffer.concat(rows));
}
function validateShells(vectors) {
  requireCondition(same(Object.keys(vectors).sort(), ["accepted_object_aggregate_sha256", "cases", "host_fixtures", "protocol_revision", "schema"]), "vector root keys mismatch");
  requireCondition(vectors.schema === SCHEMA_NAMES[5] && vectors.protocol_revision === REVISION, "vector identity mismatch");
  requireCondition(Array.isArray(vectors.cases) && vectors.cases.length === 16, "case count mismatch");
  requireCondition(Array.isArray(vectors.host_fixtures) && vectors.host_fixtures.length === 13, "host fixture count mismatch");
  const caseKeys = ["id", "input_bytes_base64", "contribution_bytes_base64", "initial_generation", "initial_next_attempt_id", "handler_registration_index", "deadline_monotonic_ns", "events", "expected"].sort();
  const fixtureKeys = ["id", "baseline_case_id", "events", "expected_terminal_state", "expected_provider_operations_before_record", "expected_model_operations_before_record", "expected_control_results"].sort();
  vectors.cases.forEach((item) => requireCondition(item !== null && typeof item === "object" && same(Object.keys(item).sort(), caseKeys) && ID_RE.test(item.id), "invalid case shell"));
  vectors.host_fixtures.forEach((item) => requireCondition(item !== null && typeof item === "object" && same(Object.keys(item).sort(), fixtureKeys) && ID_RE.test(item.id), "invalid fixture shell"));
  for (const [values, label] of [[vectors.cases, "case"], [vectors.host_fixtures, "fixture"]]) {
    const ids = values.map((item) => item.id); const ordered = [...ids].sort((left, right) => Buffer.compare(Buffer.from(left), Buffer.from(right)));
    requireCondition(new Set(ids).size === ids.length && same(ids, ordered), `${label} IDs are not unique ASCII-sorted IDs`);
  }
}
function main() {
  const packet = dirname(fileURLToPath(import.meta.url)); const repo = resolve(packet, "../../..");
  const vectorPath = resolve(packet, "../semantic-pi-insertion-evidence-v1-vectors.json");
  const schema = strictJSONLoads(readFileSync(resolve(packet, "protocol.schema.json")), "protocol.schema.json");
  const vectorsRaw = readFileSync(vectorPath); const vectors = strictJSONLoads(vectorsRaw, "semantic-pi-insertion-evidence-v1-vectors.json");
  requireCondition(schema !== null && typeof schema === "object" && vectors !== null && typeof vectors === "object", "schema and vectors must be JSON objects");
  inspectSchema(schema); validateShells(vectors);
  const core = ["input_bytes_base64", "contribution_bytes_base64", "initial_generation", "initial_next_attempt_id", "handler_registration_index", "deadline_monotonic_ns", "events"];
  const caseRuns = []; const caseInputs = new Map();
  for (const vectorCase of vectors.cases) {
    const executionInput = Object.fromEntries(core.map((key) => [key, vectorCase[key]])); const [actual] = runAttempt(executionInput, false);
    caseRuns.push([vectorCase.id, actual]); caseInputs.set(vectorCase.id, executionInput);
  }
  const fixtureRuns = [];
  for (const fixture of vectors.host_fixtures) {
    const baseline = caseInputs.get(fixture.baseline_case_id); requireCondition(baseline !== undefined, "host fixture baseline does not exist");
    const [, metadata] = runAttempt({ ...baseline, events: fixture.events }, true); fixtureRuns.push([fixture.id, metadata]);
  }
  requireCondition(schemaMatches(vectors, schema.$defs[SCHEMA_NAMES[5]], schema), "frozen vector set does not satisfy protocol schema");
  const casesByID = new Map(vectors.cases.map((item) => [item.id, item])); const fixturesByID = new Map(vectors.host_fixtures.map((item) => [item.id, item]));
  for (const [caseID, actual] of caseRuns) {
    const expected = casesByID.get(caseID).expected; requireCondition(same(actual, expected), `case result mismatch: ${caseID}`);
    for (const value of Object.values(actual)) {
      if (value !== null && typeof value === "object" && OBJECT_DOMAINS.has(value.schema)) {
        const name = value.schema; requireCondition(schemaMatches(value, schema.$defs[name], schema), `actual object schema mismatch: ${caseID}/${name}`);
        const [domain, selfField] = OBJECT_DOMAINS.get(name); requireCondition(value[selfField] === objectDigest(domain, value, selfField), `actual object digest mismatch: ${caseID}/${name}`);
      }
    }
  }
  for (const [fixtureID, actual] of fixtureRuns) {
    const source = fixturesByID.get(fixtureID);
    const expected = { terminal_state: source.expected_terminal_state, provider_operations_before_record: source.expected_provider_operations_before_record, model_operations_before_record: source.expected_model_operations_before_record, control_results: source.expected_control_results };
    requireCondition(same(actual, expected), `host fixture result mismatch: ${fixtureID}`);
  }
  const accepted = caseRuns.filter(([, value]) => value.accepted).sort(([left], [right]) => Buffer.compare(Buffer.from(left), Buffer.from(right)));
  const aggregateParts = [];
  for (const [, value] of accepted) for (const field of ["request_or_null", "witness_or_null", "acknowledgement_or_null", "record_or_null"]) aggregateParts.push(jcsBytes(value[field]));
  const acceptedHash = sha256(Buffer.concat(aggregateParts)); const vectorHash = sha256(vectorsRaw); const frozenHash = frozenAggregate(repo);
  requireCondition(accepted.length === 3, "accepted case count mismatch");
  requireCondition(acceptedHash === vectors.accepted_object_aggregate_sha256 && acceptedHash === ACCEPTED_AGGREGATE, "accepted-object aggregate mismatch");
  requireCondition(vectorHash === VECTOR_SHA256, "frozen vector SHA-256 mismatch"); requireCondition(frozenHash === FROZEN_AGGREGATE, "frozen five-file aggregate mismatch");
  const tools = strictJSONLoads(readFileSync(resolve(repo, "scripts/tool_versions.json")), "tool_versions.json");
  requireCondition(tools.node === "26.1.0", "Node validator pin must be exactly 26.1.0");
  requireCondition(process.versions.node === tools.node, `Node runtime ${process.versions.node} does not match exact pin ${tools.node}`);
  console.log(JSON.stringify({ accepted_cases: accepted.length, accepted_object_aggregate_sha256: acceptedHash, cases: caseRuns.length, digest_domains: DOMAINS.length, frozen_aggregate_sha256: frozenHash, host_fixtures: fixtureRuns.length, implementation: "node-stdlib-independent", node_pin: tools.node, schema_count: SCHEMA_NAMES.length, unused_events: 0, vector_sha256: vectorHash }));
}
try { main(); } catch (error) { console.error(`semantic-pi-insertion conformance failed: ${error.message}`); process.exitCode = 1; }
