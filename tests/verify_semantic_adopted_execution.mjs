#!/usr/bin/env node
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const corpus = JSON.parse(fs.readFileSync(path.join(root, "tests/fixtures/semantic-adopted-policy-v1/execution-corpus.json"), "utf8"));
const errors = [
  "projection_invalid", "principal_separation", "b0_coverage", "history_boundary",
  "reservation_process", "custody_order", "attempt_verdict_branch",
  "retry_rerun_forbidden", "closure_required",
];
const roles = [
  "semantic_owner", "policy_author", "development_author", "acceptance_author",
  "operational_author", "annotator", "annotator", "adjudicator", "custodian",
  "independent_reviewer", "evaluator_operator", "implementer",
];
const keys = [
  "principals", "b0_covered_principals", "b0_assessor_principal", "history",
  "reservation_count", "process_invocations", "attempt_state", "passes", "outcome",
  "timeline", "retry_count", "rerun_count", "closed",
];
const timelineKeys = ["proof", "channel", "launch", "handoff", "receipt", "closure"];
const branches = [
  [[false, false, false, false, false], 0, [], "not_started", "indeterminate"],
  [[true, false, false, false, false], 0, [], "not_started", "indeterminate"],
  [[true, true, true, false, false], 0, [], "not_started", "indeterminate"],
  [[true, true, true, false, false], 1, [], "interrupted", "indeterminate"],
  [[true, true, true, true, false], 1, [], "interrupted", "indeterminate"],
  [[true, true, true, true, true], 1, [], "interrupted", "indeterminate"],
  [[true, true, true, true, true], 1, ["primary"], "interrupted", "indeterminate"],
  [[true, true, true, true, true], 1, ["primary", "immediate_repeat"], "completed", "pass"],
];

function canonical(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
}
const exactKeys = (value, expected) => value && typeof value === "object" && !Array.isArray(value)
  && canonical(Object.keys(value).sort()) === canonical([...expected].sort());
const integer = (value) => Number.isSafeInteger(value);
function shapeValid(value) {
  if (!exactKeys(value, keys) || !Array.isArray(value.principals)) return false;
  if (!value.principals.every((item) => exactKeys(item, ["role", "principal_id"])
      && typeof item.role === "string" && typeof item.principal_id === "string")) return false;
  if (!Array.isArray(value.b0_covered_principals)
      || !value.b0_covered_principals.every((item) => typeof item === "string")
      || typeof value.b0_assessor_principal !== "string") return false;
  if (!exactKeys(value.history, ["base", "activated", "terminal"])
      || !Object.values(value.history).every(integer)) return false;
  if (!exactKeys(value.timeline, timelineKeys)
      || !Object.values(value.timeline).every((item) => item === null || integer(item))) return false;
  if (!["reservation_count", "process_invocations", "retry_count", "rerun_count"].every((key) => integer(value[key]))) return false;
  return typeof value.attempt_state === "string" && Array.isArray(value.passes)
    && value.passes.every((item) => typeof item === "string")
    && typeof value.outcome === "string" && typeof value.closed === "boolean";
}
function verify(value) {
  if (!shapeValid(value)) return ["projection_invalid"];
  const found = [];
  const ids = value.principals.map((item) => item.principal_id);
  if (value.principals.length !== 12
      || canonical(value.principals.map((item) => item.role)) !== canonical(roles)
      || ids.some((item) => !item) || new Set(ids).size !== 12) found.push("principal_separation");
  const covered = value.b0_covered_principals;
  if (covered.length !== 10 || new Set(covered).size !== 10 || covered.includes(value.b0_assessor_principal)
      || !ids.includes(value.b0_assessor_principal) || covered.some((item) => !ids.includes(item))) found.push("b0_coverage");
  const h = value.history;
  if (!(h.base >= 12 && h.base <= 254 && h.activated === h.base + 1
      && h.activated <= 255 && h.terminal === h.activated + 1 && h.terminal <= 256)) found.push("history_boundary");
  if (value.reservation_count !== 1 || ![0, 1].includes(value.process_invocations)) found.push("reservation_process");
  const present = timelineKeys.slice(0, 5).map((key) => value.timeline[key] !== null);
  const ordered = timelineKeys.map((key) => value.timeline[key]).filter((item) => item !== null);
  if (ordered.some((item) => item < 0) || new Set(ordered).size !== ordered.length || ordered.some((item, index) => index && item < ordered[index - 1])) found.push("custody_order");
  const actual = [present, value.process_invocations, value.passes, value.attempt_state, value.outcome];
  if (!branches.some((branch) => canonical(branch) === canonical(actual))) found.push("attempt_verdict_branch");
  if (value.retry_count !== 0 || value.rerun_count !== 0) found.push("retry_rerun_forbidden");
  if (!value.closed || value.timeline.closure === null) found.push("closure_required");
  return found;
}

assert.equal(corpus.schema, "semantic-adopted-execution-corpus.v1");
assert.deepEqual(corpus.error_kinds, errors);
const results = corpus.cases.map((testCase) => {
  const errorKinds = verify(testCase.projection);
  assert.deepEqual(errorKinds, testCase.expected_error_kinds, testCase.name);
  assert(errorKinds.every((kind) => errors.includes(kind)), testCase.name);
  return { ok: errorKinds.length === 0, error_kinds: errorKinds };
});
process.stdout.write(`${canonical(results)}\n`);
