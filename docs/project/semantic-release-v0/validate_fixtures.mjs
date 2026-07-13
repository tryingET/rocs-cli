#!/usr/bin/env node
/** Independent revision-13 sharded authority-graph verifier: no Python imports, subprocesses, or shared code. */
import { createHash } from "node:crypto";
import { closeSync, constants, fstatSync, lstatSync, openSync, readdirSync, readSync } from "node:fs";
import { basename, dirname, join, resolve as pathResolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const fail = (message) => { throw new Error(message); };
const maxSafe = Number.MAX_SAFE_INTEGER;
const maxJsonFileBytes = 16 * 1024 * 1024;
const maxJsonDepth = 64;
const maxTotalJsonBytes = 256 * 1024 * 1024;
const maxShards = 64;
const maxDeadlineMs = 300000;
const processStartedNs = process.hrtime.bigint();
let processDeadlineNs = processStartedNs + BigInt(maxDeadlineMs) * 1000000n;
const deadlineCheck = (stage) => { if (process.hrtime.bigint() > processDeadlineNs) fail(`transport deadline exceeded ${stage}`); };
const configureDeadline = (deadlineMs) => { const configured = processStartedNs + BigInt(deadlineMs) * 1000000n; if (configured < processDeadlineNs) processDeadlineNs = configured; deadlineCheck("after manifest limit configuration"); };
const shardNamePattern = /^differential-fixtures-shard-[0-9]{3}\.json$/u;

function strictJson(text) {
  deadlineCheck("before JSON parse");
  let at = 0;
  const ws = () => { while (/[\u0009\u000a\u000d\u0020]/u.test(text[at] ?? "")) at++; };
  const string = () => {
    const start = at++; let closed = false;
    while (at < text.length) {
      const c = text[at++];
      if (c === "\\") { if (at >= text.length) fail("truncated escape"); at++; continue; }
      if (c === "\"") { closed = true; break; }
      if (c.codePointAt(0) < 0x20) fail("raw control in string");
    }
    if (!closed) fail("unterminated string");
    try { return JSON.parse(text.slice(start, at)); } catch { fail("invalid JSON string token"); }
  };
  const value = (depth = 1) => {
    if (depth > maxJsonDepth) fail("JSON nesting depth exceeds 64");
    ws(); const c = text[at];
    if (c === "{") {
      at++; ws(); const out = Object.create(null); const keys = new Set();
      if (text[at] === "}") { at++; return out; }
      while (true) {
        if (text[at] !== "\"") fail("object key must be string");
        const key = string(); if (keys.has(key)) fail(`duplicate JSON key ${key}`); keys.add(key); ws();
        if (text[at++] !== ":") fail("missing colon"); out[key] = value(depth + 1); ws();
        const end = text[at++]; if (end === "}") return out; if (end !== ",") fail("missing object comma"); ws();
      }
    }
    if (c === "[") {
      at++; ws(); const out = []; if (text[at] === "]") { at++; return out; }
      while (true) { out.push(value(depth + 1)); ws(); const end = text[at++]; if (end === "]") return out; if (end !== ",") fail("missing array comma"); ws(); }
    }
    if (c === "\"") return string();
    for (const [token, result] of [["true", true], ["false", false], ["null", null]]) if (text.startsWith(token, at)) { at += token.length; return result; }
    const start = at; while (at < text.length && !/[\s,\]}]/u.test(text[at])) at++;
    const token = text.slice(start, at);
    if (!/^(?:0|[1-9][0-9]*)$/u.test(token)) fail(`non-canonical integer token ${token}`);
    const number = Number(token); if (!Number.isSafeInteger(number)) fail("unsafe integer token"); return number;
  };
  const result = value(); ws(); if (at !== text.length) fail("trailing JSON data"); validateIjson(result); deadlineCheck("after JSON parse"); return result;
}

function loadBytes(name, strictUnderLimit = false, expected = null) {
  const path = join(root, name);
  if (constants.O_NOFOLLOW === undefined) fail(`${name}: no-follow open unavailable`);
  let fd; try { fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW | (constants.O_CLOEXEC ?? 0)); }
  catch { fail(`${name}: unavailable, non-regular, or symlink JSON file`); }
  let bytes;
  try {
    const before = fstatSync(fd, { bigint: true });
    if (!before.isFile() || before.size < 0n || before.size > BigInt(maxJsonFileBytes) || strictUnderLimit && before.size >= BigInt(maxJsonFileBytes)) fail(`${name}: JSON file is not regular or exceeds limit`);
    const bounded = Buffer.allocUnsafe(maxJsonFileBytes + 1); let length = 0;
    while (length < bounded.length) { deadlineCheck(`before read ${name}`); const count = readSync(fd, bounded, length, bounded.length - length, null); deadlineCheck(`after read ${name}`); if (count === 0) break; length += count; }
    bytes = bounded.subarray(0, length);
    const after = fstatSync(fd, { bigint: true }); let current;
    try { current = lstatSync(path, { bigint: true }); } catch { fail(`${name}: JSON file replaced during read`); }
    const fields = ["dev", "ino", "mode", "size", "mtimeNs", "ctimeNs"];
    if (!after.isFile() || !current.isFile() || fields.some((key) => before[key] !== after[key] || before[key] !== current[key])
      || BigInt(bytes.length) !== before.size || bytes.length > maxJsonFileBytes || strictUnderLimit && bytes.length >= maxJsonFileBytes) fail(`${name}: JSON file replaced, grew, or changed during bounded read`);
  } finally { closeSync(fd); }
  deadlineCheck(`before hash ${name}`);
  const rawSha256 = createHash("sha256").update(bytes).digest("hex");
  deadlineCheck(`after hash ${name}`);
  if (expected !== null && (bytes.length !== expected.byteLength || rawSha256 !== expected.sha256)) fail(`${name}: JSON raw byte/hash mismatch`);
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) fail(`${name}: BOM forbidden`);
  let text; try { text = new TextDecoder("utf-8", { fatal: true }).decode(bytes); } catch { fail(`${name}: malformed UTF-8`); }
  deadlineCheck(`before decode/parse ${name}`); const value = strictJson(text); deadlineCheck(`after decode/parse ${name}`);
  return [value, bytes];
}
function load(name) { return loadBytes(name)[0]; }

const schema = load("protocol.schema.json");
const golden = load("golden-fixtures.json");
const differentialManifest = load("differential-fixtures.json");
const coordinateDomain = "semantic-release.coordinate.v0";
const rows = {
  "semantic-source-manifest.v0": ["source-manifest", "source_manifest_digest"], "semantic-material-manifest.v0": ["material-manifest", "material_manifest_digest"],
  "semantic-owner-set.v0": ["owner-set", "owner_set_digest"], "semantic-approval-predicate.v0": ["approval-predicate", "approval_predicate_digest"],
  "semantic-owner-policy.v0": ["owner-policy", "owner_policy_digest"], "semantic-trust-root.v0": ["trust-root", "trust_root_digest"],
  "semantic-trust-rotation.v0": ["trust-rotation", "trust_rotation_digest"], "semantic-trust-revocation.v0": ["trust-revocation", "trust_revocation_digest"],
  "semantic-compatibility-policy.v0": ["compatibility-policy", "compatibility_policy_digest"], "semantic-compatibility-report.v0": ["compatibility-report", "compatibility_report_digest"],
  "semantic-compatibility-override.v0": ["compatibility-override", "compatibility_override_digest"], "semantic-deprecation-record.v0": ["deprecation-record", "deprecation_record_digest"],
  "semantic-removal-record.v0": ["removal-record", "removal_record_digest"], "semantic-tombstone-registry.v0": ["tombstone-registry", "tombstone_registry_digest"], "semantic-tombstone-history-proof.v0": ["tombstone-history-proof", "semantic_tombstone_history_proof_digest"], "semantic-publication-ledger-head.v0": ["publication-ledger-head", "publication_ledger_head_digest"], "semantic-accepted-lifecycle-ledger-record.v0": ["accepted-lifecycle-ledger-record", "accepted_lifecycle_ledger_record_digest"],
  "semantic-payload-projection.v0": ["payload-projection", "payload_projection_digest"], "semantic-capsule-archive-linkage.v0": ["capsule-archive-linkage", "capsule_archive_linkage_digest"],
  "semantic-release-capsule.v0": ["capsule", "capsule_digest"], "semantic-ak-decision-reference.v0": ["ak-decision-reference", "ak_decision_reference_digest"],
  "semantic-owner-approval.v0": ["owner-approval", "owner_approval_digest"], "semantic-build-receipt.v0": ["build-receipt", "build_receipt_digest"],
  "semantic-publication-transaction.v0": ["publication-transaction", "publication_transaction_digest"], "semantic-publication-journal.v0": ["publication-journal", "publication_journal_digest"],
  "semantic-publication-recovery-intent-marker.v0": ["publication-recovery-intent-marker", "publication_recovery_intent_marker_digest"],
  "semantic-publication-commit-marker.v0": ["publication-commit-marker", "publication_commit_marker_digest"],
  "semantic-publication-recovery-state-receipt.v0": ["publication-recovery-state-receipt", "publication_recovery_state_receipt_digest"], "semantic-owner-publication.v0": ["owner-publication", "owner_publication_digest"],
  "semantic-publication-status-transition.v0": ["publication-status-transition", "publication_status_transition_digest"], "semantic-consumer-intent.v0": ["consumer-intent", "consumer_intent_digest"],
  "semantic-owner-acceptance.v0": ["owner-acceptance", "owner_acceptance_digest"], "semantic-materialization-verification-receipt.v0": ["materialization-verification", "materialization_verification_receipt_digest"],
  "semantic-activation-receipt.v0": ["activation", "activation_receipt_digest"], "semantic-rocs-generation-receipt.v0": ["rocs-generation", "rocs_generation_receipt_digest"],
  "semantic-pi-delivery-receipt.v0": ["pi-delivery", "pi_delivery_receipt_digest"], "semantic-ak-evidence-linkage.v0": ["ak-evidence-linkage", "ak_evidence_linkage_digest"],
  "semantic-rollback-request.v0": ["rollback-request", "rollback_request_digest"], "semantic-rollback-technical-receipt.v0": ["rollback-technical-receipt", "rollback_technical_receipt_digest"], "semantic-rollback-availability-receipt.v0": ["rollback-availability-receipt", "rollback_available_artifact_digest"],
  "semantic-rollback-availability-proof.v0": ["rollback-availability-proof", "rollback_availability_proof_digest"],
  "semantic-rollback-history-transition.v0": ["rollback-history-transition", "rollback_history_transition_digest"],
  "semantic-rollback-receipt.v0": ["rollback-receipt", "rollback_receipt_digest"],
  "semantic-non-authorizing-task-contract.v0": ["non-authorizing-task-contract", "non_authorizing_task_contract_digest"],
  "semantic-audit-envelope.v0": ["audit-envelope", "audit_envelope_digest"], "semantic-protocol-error.v0": ["error", "error_digest"],
  "semantic-owner-acquisition-capability-pin.v0": ["owner-acquisition-capability-pin", "capability_pin_digest"],
  "semantic-authority-acquisition-config.v0": ["authority-acquisition-config", "authority_acquisition_config_digest"],
  "semantic-owner-store-read-receipt.v0": ["owner-store-read-receipt", "owner_store_read_receipt_digest"],
  "semantic-authority-snapshot.v0": ["authority-snapshot", "authority_snapshot_digest"],
  "semantic-authority-rule-role-manifest.v0": ["authority-rule-role-manifest", "authority_rule_role_manifest_digest"],
  "semantic-authority-proof-bundle.v0": ["authority-proof-bundle", "authority_proof_bundle_digest"], "semantic-authority-verifier-input.v0": ["authority-verifier-input", "authority_verifier_input_digest"],
};
const digestFields = Object.fromEntries(Object.entries(rows).map(([kind, [domain, field]]) => [kind, [`semantic-release.${domain}.v0`, field]]));

function validateIjson(value, path = "$", depth = 1) {
  if (depth > maxJsonDepth) fail(`${path}: JSON nesting depth exceeds 64`);
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "number") { if (!Number.isSafeInteger(value) || value < 0) fail(`${path}: unsafe integer`); return; }
  if (typeof value === "string") {
    if (value.normalize("NFC") !== value || [...value].some((c) => { const n = c.codePointAt(0); return n >= 0xd800 && n <= 0xdfff || n >= 0xfdd0 && n <= 0xfdef || (n & 0xffff) === 0xfffe || (n & 0xffff) === 0xffff; })) fail(`${path}: invalid Unicode`);
    return;
  }
  if (Array.isArray(value)) { value.forEach((x, i) => validateIjson(x, `${path}/${i}`, depth + 1)); return; }
  if (typeof value === "object") { Object.entries(value).forEach(([k, v]) => { validateIjson(k, `${path}/key`, depth + 1); validateIjson(v, `${path}/${k}`, depth + 1); }); return; }
  fail(`${path}: invalid JSON kind`);
}

// JavaScript key ordering is UTF-16 code-unit ordering, as RFC 8785 requires.
function jcs(value) {
  validateIjson(value);
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(jcs).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${jcs(value[key])}`).join(",")}}`;
}
function digest(domain, bytes) { return `sha256:${createHash("sha256").update(Buffer.from(domain, "ascii")).update(Buffer.from([0])).update(bytes).digest("hex")}`; }
const typedDigest = (domain, value) => digest(domain, Buffer.from(jcs(value), "utf8"));
const actionDigest = (value) => typedDigest("semantic-release.approval-action.v0", value);
const changeDigest = (value) => typedDigest("semantic-release.compatibility-change.v0", value);
function objectDigest(instance, domain, omitted) {
  const copy = structuredClone(instance); if (omitted !== null) { if (!Object.hasOwn(copy, omitted)) fail(`missing self digest ${omitted}`); delete copy[omitted]; }
  const canonical = jcs(copy); return [canonical, digest(domain, Buffer.from(canonical, "utf8"))];
}
function resolve(reference) {
  if (!reference.startsWith("#/")) fail(`external schema ref ${reference}`);
  return reference.slice(2).split("/").reduce((node, token) => { const key = token.replaceAll("~1", "/").replaceAll("~0", "~"); if (!Object.hasOwn(node, key)) fail(`missing schema ref token ${key}`); return node[key]; }, schema);
}
function structural(instance, shape, path = "$") {
  if (shape.$ref) return structural(instance, resolve(shape.$ref), path);
  if (shape.oneOf) { const matches = shape.oneOf.filter((option) => { try { structural(instance, option, path); return true; } catch { return false; } }).length; if (matches !== 1) fail(`${path}: oneOf ${matches}`); return; }
  if (Object.hasOwn(shape, "const") && !eq(instance, shape.const)) fail(`${path}: const`);
  if (shape.enum && !shape.enum.some((x) => eq(x, instance))) fail(`${path}: enum`);
  if (shape.type === "object") {
    if (instance === null || Array.isArray(instance) || typeof instance !== "object") fail(`${path}: object`);
    for (const key of shape.required ?? []) if (!Object.hasOwn(instance, key)) fail(`${path}: missing ${key}`);
    if (shape.additionalProperties === false) for (const key of Object.keys(instance)) if (!Object.hasOwn(shape.properties, key)) fail(`${path}: unknown ${key}`);
    for (const [key, value] of Object.entries(instance)) if (Object.hasOwn(shape.properties, key)) structural(value, shape.properties[key], `${path}/${key}`);
  } else if (shape.type === "array") {
    if (!Array.isArray(instance) || instance.length < (shape.minItems ?? 0) || instance.length > (shape.maxItems ?? maxSafe)) fail(`${path}: array`);
    instance.forEach((x, i) => structural(x, shape.items, `${path}/${i}`));
  } else if (shape.type === "string") {
    if (typeof instance !== "string" || [...instance].length < (shape.minLength ?? 0) || [...instance].length > (shape.maxLength ?? maxSafe)) fail(`${path}: string`);
    if (shape.pattern && !(new RegExp(shape.pattern, "u")).test(instance)) fail(`${path}: pattern`);
  } else if (shape.type === "integer") {
    if (!Number.isSafeInteger(instance) || instance < (shape.minimum ?? -maxSafe) || instance > (shape.maximum ?? maxSafe)) fail(`${path}: integer`);
  } else if (shape.type === "boolean" && typeof instance !== "boolean") fail(`${path}: boolean`);
  else if (shape.type === "null" && instance !== null) fail(`${path}: null`);
}
const eq = (a, b) => jcs(a) === jcs(b);
const exactKeys = (value, keys) => value !== null && !Array.isArray(value) && typeof value === "object" && eq(Object.keys(value).sort(), [...keys].sort());
function stableJsonStat(name, strictUnderLimit = false) {
  deadlineCheck(`before stat ${name}`);
  const path = join(root, name);
  if (constants.O_NOFOLLOW === undefined) fail(`${name}: no-follow open unavailable`);
  let fd; try { fd = openSync(path, constants.O_RDONLY | constants.O_NOFOLLOW | (constants.O_CLOEXEC ?? 0)); }
  catch { fail(`${name}: unavailable, non-regular, or symlink JSON file`); }
  let size;
  try {
    const before = fstatSync(fd, { bigint: true }), after = fstatSync(fd, { bigint: true }); let current;
    try { current = lstatSync(path, { bigint: true }); } catch { fail(`${name}: JSON file replaced during stat`); }
    const fields = ["dev", "ino", "mode", "size", "mtimeNs", "ctimeNs"];
    if (!before.isFile() || !after.isFile() || !current.isFile() || fields.some((key) => before[key] !== after[key] || before[key] !== current[key])
      || before.size < 0n || before.size > BigInt(maxJsonFileBytes) || strictUnderLimit && before.size >= BigInt(maxJsonFileBytes)) fail(`${name}: unstable, non-regular, or oversized JSON stat`);
    size = Number(before.size);
  } finally { closeSync(fd); }
  deadlineCheck(`after stat ${name}`); return size;
}
function transportLimitResult(limits, totalJsonBytes, shardCount, elapsedMs) { return totalJsonBytes > limits.max_total_json_bytes || shardCount > limits.max_shards || elapsedMs > limits.deadline_ms ? "transport_limit_exceeded" : null; }
function loadShardedDifferential(manifest) {
  const topKeys = ["schema", "protocol", "rfc_revision", "limits", "transport_limit_cases", "aggregate", "source_case_explicitness_audit", "authority_rule_role_manifest", "authority_edge_registry", "shards"];
  if (!exactKeys(manifest, topKeys) || manifest.schema !== "semantic-differential-fixture-manifest.v0" || manifest.protocol !== "semantic-release-v0" || manifest.rfc_revision !== "semantic-release-revision-v13") fail("differential shard manifest identity/closure");
  const limits = manifest.limits, limitKeys = ["max_total_json_bytes", "max_shards", "deadline_ms"];
  if (!exactKeys(limits, limitKeys) || limitKeys.some((key) => !Number.isSafeInteger(limits[key]) || limits[key] < 1)
    || limits.max_total_json_bytes > maxTotalJsonBytes || limits.max_shards > maxShards || limits.deadline_ms > maxDeadlineMs) fail("differential transport limits shape/bound");
  configureDeadline(limits.deadline_ms);
  const transportCases = manifest.transport_limit_cases, transportCaseKeys = ["name", "limit_kind", "observed_total_json_bytes", "observed_shard_count", "observed_elapsed_ms", "expected_error"];
  const expectedTransportCases = new Map([
    ["transport_aggregate_json_bytes_overflow_rejected", "max_total_json_bytes"],
    ["transport_deadline_overflow_rejected", "deadline_ms"],
    ["transport_shard_count_overflow_rejected", "max_shards"],
  ]);
  if (!Array.isArray(transportCases) || !eq(transportCases.map((row) => row?.name), [...expectedTransportCases.keys()].sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b))))) fail("transport conformance case identity/order");
  for (const item of transportCases) {
    deadlineCheck(`before transport case ${item?.name}`);
    if (!exactKeys(item, transportCaseKeys) || item.limit_kind !== expectedTransportCases.get(item.name) || item.expected_error !== "transport_limit_exceeded"
      || [item.observed_total_json_bytes, item.observed_shard_count, item.observed_elapsed_ms].some((value) => !Number.isSafeInteger(value) || value < 0)) fail("transport conformance case shape");
    const observations = [["max_total_json_bytes", item.observed_total_json_bytes], ["max_shards", item.observed_shard_count], ["deadline_ms", item.observed_elapsed_ms]], violations = observations.filter(([key, observed]) => observed > limits[key]).map(([key]) => key);
    const actual = transportLimitResult(limits, item.observed_total_json_bytes, item.observed_shard_count, item.observed_elapsed_ms);
    if (!eq(violations, [item.limit_kind]) || actual !== item.expected_error) fail(`transport conformance case outcome ${item.name}`);
    deadlineCheck(`after transport case ${item.name}`);
  }
  const aggregate = manifest.aggregate;
  if (!exactKeys(aggregate, ["case_count", "raw_case_count", "sha256"]) || !Number.isSafeInteger(aggregate.case_count) || aggregate.case_count < 0 || !Number.isSafeInteger(aggregate.raw_case_count) || aggregate.raw_case_count < 0 || !/^[0-9a-f]{64}$/u.test(aggregate.sha256)) fail("differential aggregate metadata shape");
  const inventory = manifest.shards, rowKeys = ["path", "byte_length", "sha256", "case_count", "raw_case_count"];
  if (!Array.isArray(inventory) || inventory.length === 0 || inventory.length > limits.max_shards || inventory.length > maxShards) fail("differential shard inventory count");
  const paths = inventory.map((row) => row?.path);
  if (paths.some((path) => typeof path !== "string")) fail("differential shard inventory order");
  const ordered = [...paths].sort((a, b) => Buffer.compare(Buffer.from(a, "utf8"), Buffer.from(b, "utf8")));
  if (!eq(paths, ordered) || new Set(paths).size !== paths.length) fail("differential shard inventory order");
  for (let index = 0; index < inventory.length; index++) {
    const row = inventory[index];
    if (!exactKeys(row, rowKeys) || !shardNamePattern.test(row.path) || basename(row.path) !== row.path || row.path.includes(":") || row.path.includes("/") || row.path.includes("\\") || !Number.isSafeInteger(row.byte_length) || row.byte_length < 0 || !Number.isSafeInteger(row.case_count) || row.case_count < 0 || !Number.isSafeInteger(row.raw_case_count) || row.raw_case_count < 0 || !/^[0-9a-f]{64}$/u.test(row.sha256)) fail(`differential shard inventory row ${index}`);
    const lexicalPath = pathResolve(root, row.path); if (dirname(lexicalPath) !== pathResolve(root)) fail("differential shard path traversal");
  }
  const actual = readdirSync(root).filter((name) => name.startsWith("differential-fixtures-shard-") && name.endsWith(".json")).sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b)));
  if (!eq(actual, paths)) fail("differential shard inventory has missing or extra files");
  const statSizes = [["protocol.schema.json", false], ["golden-fixtures.json", false], ["differential-fixtures.json", false], ...inventory.map((row) => [row.path, true])].map(([name, strict]) => stableJsonStat(name, strict));
  if (inventory.some((row, index) => statSizes[index + 3] !== row.byte_length)) fail("differential shard stable stat byte mismatch");
  const totalJsonBytes = statSizes.reduce((total, size) => total + size, 0);
  if (transportLimitResult(limits, totalJsonBytes, inventory.length, 0) !== null) fail("aggregate JSON transport limit exceeded before shard parsing");
  const cases = [], rawCases = [];
  for (let index = 0; index < inventory.length; index++) {
    deadlineCheck(`before shard ${index} read/hash/parse`);
    const row = inventory[index], [shard] = loadBytes(row.path, true, { byteLength: row.byte_length, sha256: row.sha256 });
    const shardKeys = ["schema", "protocol", "rfc_revision", "shard_index", "cases", "raw_json_cases"];
    if (!exactKeys(shard, shardKeys) || shard.schema !== "semantic-differential-fixture-shard.v0" || shard.protocol !== manifest.protocol || shard.rfc_revision !== manifest.rfc_revision || shard.shard_index !== index || !Array.isArray(shard.cases) || !Array.isArray(shard.raw_json_cases) || shard.cases.length !== row.case_count || shard.raw_json_cases.length !== row.raw_case_count) fail(`differential shard shape/count ${row.path}`);
    cases.push(...shard.cases); rawCases.push(...shard.raw_json_cases); deadlineCheck(`after shard ${index} read/hash/parse`);
  }
  const aggregatePreimage = { cases, raw_json_cases: rawCases }; deadlineCheck("before differential aggregate hash"); const aggregateSha256 = createHash("sha256").update(Buffer.from(jcs(aggregatePreimage), "utf8")).digest("hex"); deadlineCheck("after differential aggregate hash");
  if (cases.length !== aggregate.case_count || rawCases.length !== aggregate.raw_case_count || inventory.reduce((n, row) => n + row.case_count, 0) !== cases.length || inventory.reduce((n, row) => n + row.raw_case_count, 0) !== rawCases.length || aggregateSha256 !== aggregate.sha256) fail("differential shard aggregate reconstruction mismatch");
  return [{ protocol: manifest.protocol, rfc_revision: manifest.rfc_revision, source_case_explicitness_audit: manifest.source_case_explicitness_audit, authority_rule_role_manifest: manifest.authority_rule_role_manifest, authority_edge_registry: manifest.authority_edge_registry, cases, raw_json_cases: rawCases }, inventory, aggregateSha256, totalJsonBytes, transportCases.length];
}
const [differential, shardInventory, shardAggregateSha256, totalJsonBytes, transportCaseCount] = loadShardedDifferential(differentialManifest);
function pointer(value, path) { return path.split("/").slice(1).reduce((node, token) => { const key = token.replaceAll("~1", "/").replaceAll("~0", "~"); if (!Object.hasOwn(node, key)) fail(`missing pointer token ${key}`); return node[key]; }, value); }
const embeddedDigestValid = (subject) => { if (subject.schema === "semantic-release-coordinate.v0") return true; const [domain, omitted] = digestFields[subject.schema]; return objectDigest(subject, domain, omitted)[1] === subject[omitted]; };
const sortedUnique = (values) => eq(values, [...values].sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b)))) && new Set(values).size === values.length;
function checkOrder(instance) {
  const kind = instance.schema;
  if (["semantic-source-manifest.v0", "semantic-material-manifest.v0"].includes(kind)) { const keys = instance.entries.map((x) => [x.path, x.kind]); const ordered = [...keys].sort((a, b) => Buffer.compare(Buffer.from(a[0], "utf8"), Buffer.from(b[0], "utf8")) || Buffer.compare(Buffer.from(a[1], "utf8"), Buffer.from(b[1], "utf8"))); if (!eq(keys, ordered) || new Set(instance.entries.map((x) => x.path)).size !== keys.length) fail("manifest order"); }
  if (kind === "semantic-owner-set.v0" && (!sortedUnique(instance.members.map((x) => x.owner_id)) || instance.members.some((x) => !sortedUnique(x.key_ids)))) fail("owner order");
  if (kind === "semantic-trust-root.v0" && !sortedUnique(instance.key_ids)) fail("trust root key order");
  if (kind === "semantic-owner-approval.v0") { const keys = instance.votes.map((x) => [x.owner_id, x.owner_key_id]); const ordered = [...keys].sort((a, b) => Buffer.compare(Buffer.from(a[0]), Buffer.from(b[0])) || Buffer.compare(Buffer.from(a[1]), Buffer.from(b[1]))); if (!eq(keys, ordered) || new Set(keys.map(JSON.stringify)).size !== keys.length || actionDigest(instance.action) !== instance.action_digest || instance.votes.some((x) => x.approved_action_digest !== instance.action_digest)) fail("approval order/binding"); }
  if (kind === "semantic-publication-transaction.v0" && actionDigest(instance.approved_action) !== instance.approved_action_digest) fail("publication transaction action binding");
  if (kind === "semantic-compatibility-policy.v0" && !sortedUnique(instance.category_rules.map((x) => x.category))) fail("policy order");
  if (kind === "semantic-compatibility-report.v0") { const keys = instance.changes.map((x) => [x.semantic_id, x.category]); const ordered = [...keys].sort((a, b) => Buffer.compare(Buffer.from(a[0]), Buffer.from(b[0])) || Buffer.compare(Buffer.from(a[1]), Buffer.from(b[1]))); if (!eq(keys, ordered) || new Set(keys.map(JSON.stringify)).size !== keys.length || !sortedUnique(instance.conditions.map((x) => x.condition_id)) || !sortedUnique(instance.override_digests)) fail("compatibility order"); }
  if (kind === "semantic-tombstone-registry.v0" && !sortedUnique(instance.entries.map((x) => x.semantic_id))) fail("tombstone order");
  if (kind === "semantic-payload-projection.v0" && (!sortedUnique(instance.entries.map((x) => x.capsule_path)) || new Set(instance.entries.map((x) => x.consumer_path)).size !== instance.entries.length)) fail("projection bijection");
  if (kind === "semantic-release-capsule.v0" && !sortedUnique(instance.required_protocol_versions)) fail("protocol order");
  if (kind === "semantic-rocs-generation-receipt.v0" && (!sortedUnique(instance.candidate_ids) || !sortedUnique(instance.pack_digests))) fail("generation order");
  if (kind === "semantic-rollback-receipt.v0" && new Set(instance.stages.map((x) => x.stage)).size !== instance.stages.length) fail("stage uniqueness");
  if (kind === "semantic-non-authorizing-task-contract.v0") { const groups = [instance.dependencies.map((x) => x.reference_id), instance.prerequisites.map((x) => x.reference_id), instance.required_evidence.map((x) => x.reference_id), instance.stop_conditions.map((x) => x.condition_id)]; if (!sortedUnique(instance.allowed_paths) || groups.some((x) => !sortedUnique(x))) fail("task contract order"); }
  if (kind === "semantic-authority-acquisition-config.v0" && !sortedUnique(instance.pins.map((x) => x.capability_pin_id))) fail("authority acquisition pin order");
  if (kind === "semantic-authority-snapshot.v0" && !sortedUnique(instance.store_read_receipts.map((x) => x.observation_id))) fail("authority snapshot receipt order");
  if (kind === "semantic-authority-rule-role-manifest.v0") { if (!sortedUnique(instance.rules.map((x) => x.rule))) fail("authority manifest rule order"); for (const row of instance.rules) { const groups = [row.role_mappings.map((x) => x.role), row.required_roles, row.edge_ids, row.role_edge_links.map((x) => x.edge_id)]; if (groups.some((x) => !sortedUnique(x)) || row.role_mappings.some((x) => !sortedUnique(x.sources) || !sortedUnique(x.expected_schemas)) || row.role_edge_links.some((x) => !sortedUnique(x.role_ids) || !eq(x.role_owners.map((item) => item.role), x.role_ids))) fail("authority manifest role order"); } }
  if (kind === "semantic-authority-proof-bundle.v0" && !sortedUnique(instance.nodes.map((x) => x.bundle_key))) fail("proof bundle order");
  if (kind === "semantic-authority-verifier-input.v0") { const groups = [instance.receipt_bindings.map((x) => x.role), instance.node_bindings.map((x) => x.role), instance.parameter_bindings.map((x) => x.role), instance.required_observation_ids, instance.required_role_ids, instance.required_edge_ids]; if (groups.some((x) => !sortedUnique(x))) fail("authority verifier input order"); }
  if (kind === "semantic-protocol-error.v0" && !sortedUnique(instance.details.map((x) => x.key))) fail("error order");
}
function checkClaimScope(instance) {
  const expected = { "semantic-owner-acceptance.v0": ["acceptance_authority", "consumer_owner"], "semantic-materialization-verification-receipt.v0": ["issuer", "rocs"], "semantic-activation-receipt.v0": ["issuer", "consumer_owner"], "semantic-rocs-generation-receipt.v0": ["issuer", "rocs"], "semantic-pi-delivery-receipt.v0": ["issuer", "pi"], "semantic-ak-evidence-linkage.v0": ["issuer", "ak"], "semantic-rollback-request.v0": ["issuer", "consumer_owner"], "semantic-rollback-availability-proof.v0": ["issuer", "rocs"], "semantic-rollback-history-transition.v0": ["issuer", "consumer_owner"], "semantic-rollback-receipt.v0": ["issuer", "recovery_controller"] };
  const row = expected[instance.schema]; if (row && instance[row[0]].kind !== row[1]) fail("issuer_scope_violation");
  const adapter = pinnedAdapterIssuers.get(instance.schema); if (adapter && !eq(instance.issuer, { kind: adapter[0], id: adapter[1] })) fail("issuer_scope_violation");
  if (instance.schema === "semantic-publication-recovery-intent-marker.v0" && instance.issuer.kind !== "recovery_controller") fail("issuer_scope_violation");
  if (instance.schema === "semantic-publication-recovery-state-receipt.v0") { const kind = instance.phase === "before" ? "semantic_owner" : "recovery_controller"; if (instance.issuer.kind !== kind) fail("issuer_scope_violation"); }
  if (instance.schema === "semantic-rollback-technical-receipt.v0") { const kind = { materialization: "rocs", runtime_revalidation: "rocs", disable_contract: "consumer_owner", rehearsal: "recovery_controller", health: "recovery_controller" }[instance.receipt_kind]; if (instance.issuer.kind !== kind) fail("issuer_scope_violation"); }
  if (instance.schema === "semantic-rollback-availability-receipt.v0") { const kind = { semantic_target: "rocs", runtime_target: "rocs", disable_target: "consumer_owner", recovery_runtime: "recovery_controller" }[instance.artifact_kind]; if (instance.issuer.kind !== kind) fail("issuer_scope_violation"); }
}
class ContextError extends Error { constructor(code) { super(code); this.code = code; } }
function expectedContext(value, expectedSchema, expectedDigest = null, referenceError = "digest_mismatch") {
  const schemas = Array.isArray(expectedSchema) ? expectedSchema : [expectedSchema];
  try { validateIjson(value); structural(value, schema); } catch { throw new ContextError("malformed_input"); }
  if (!schemas.includes(value.schema)) throw new ContextError("malformed_input");
  let actualDigest;
  if (value.schema === "semantic-release-coordinate.v0") actualDigest = objectDigest(value, coordinateDomain, null)[1];
  else { if (!embeddedDigestValid(value)) throw new ContextError("digest_mismatch"); actualDigest = value[digestFields[value.schema][1]]; }
  try { checkOrder(value); checkClaimScope(value); } catch (error) { throw new ContextError(error.message === "issuer_scope_violation" ? "issuer_scope_violation" : "malformed_input"); }
  if (expectedDigest !== null && actualDigest !== expectedDigest) throw new ContextError(referenceError);
  return value;
}
function expectedShapeContext(value, definition) {
  try { validateIjson(value); structural(value, schema.$defs[definition]); } catch { throw new ContextError("malformed_input"); }
  return value;
}
const authorityBearingRules = new Set(["acceptance_binding", "activation_binding", "ak_decision", "ak_optional_pi", "approval_threshold", "compatibility", "generation_activation", "governance_contracts", "lifecycle", "projection", "publication_cas", "publication_commit", "publication_recovery", "publication_transition", "rollback", "tombstone_reuse", "trust_revocation", "trust_rotation", "version_binding"]);
const allRules = new Set(["acceptance_binding", "activation_binding", "ak_decision", "ak_optional_pi", "approval_threshold", "compatibility", "compatibility_policy", "digest", "generation_activation", "governance_contracts", "lifecycle", "pi_delivery", "pi_variant", "projection", "publication_cas", "publication_commit", "publication_journal_shape", "publication_recovery", "publication_transition", "rollback", "tombstone_reuse", "trust_revocation", "trust_rotation", "utc", "version_binding"]);
const expectedAuthorityEdgeCount = 141;
const expectedAuthorityRegistryDigest = "sha256:d78991ce172d795de35d8fe640fe4cdb266a260980d9d72c1b29a3c0ed30b9a3";
const expectedAuthorityManifestDigest = "sha256:687d3e6c6be239d92bc5d5663c48ac18f8a6124cb9b6a99e0b0623b643ebc476";
const expectedSourceAuditDigest = "sha256:03644461360e9790a10d6b43830e94f694bf0003aa74b10564eb01270b0a408d";
const pinnedAkRepository = { owner: "agent-kernel-owner", repository_id: "agent-kernel", canonical_locator: "local://softwareco/owned/agent-kernel", identity_revision: 9 };
const pinnedRocsRepository = { owner: "rocs-owner", repository_id: "rocs-cli", canonical_locator: "local://core/rocs-cli", identity_revision: 4 };
const pinnedPiRepository = { owner: "pi-owner", repository_id: "pi-adapter", canonical_locator: "local://softwareco/pi-adapter", identity_revision: 1 };
const pinnedAdapterIssuers = new Map([
  ["semantic-rocs-generation-receipt.v0", ["rocs", pinnedRocsRepository.repository_id]],
  ["semantic-pi-delivery-receipt.v0", ["pi", pinnedPiRepository.repository_id]],
  ["semantic-ak-evidence-linkage.v0", ["ak", pinnedAkRepository.repository_id]],
]);
let authorityManifest = null;
let authorityManifestByRule = new Map();
const requiredReceiptRoles = Object.fromEntries(Object.entries({
  ak_optional_pi: ["canonical_task_states"],
  approval_threshold: [],
  trust_rotation: ["current_root_digest", "revoked", "canonical_store_head", "current_decision_record_digest"],
  trust_revocation: ["prior_revision", "prior_head", "canonical_store_head", "current_decision_record_digest"],
  compatibility: ["canonical_store_head", "current_decision_record_digest"],
  lifecycle: ["canonical_deprecation_head", "canonical_deprecation_revision", "canonical_removal_head", "canonical_removal_revision", "canonical_store_head", "current_deprecation_decision_record_digest", "current_removal_decision_record_digest", "deprecation_prior_head", "current_lifecycle_head", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "tombstone_genesis_anchor"],
  publication_commit: ["canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_journal_head"],
  publication_transition: ["canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_journal_head"],
  publication_recovery: ["canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_publication_revision", "canonical_publication_head", "canonical_publication_status_digest", "canonical_publication_journal_head", "canonical_recovery_journal_head", "canonical_recovery_transaction_digest", "canonical_recovery_resulting_revision", "canonical_recovery_resulting_head", "canonical_recovery_resulting_status_digest", "canonical_store_head", "current_decision_record_digest", "external_trust_root_pin", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests"],
  tombstone_reuse: ["canonical_lifecycle_tombstone_head", "tombstone_genesis_anchor"], projection: ["canonical_lifecycle_tombstone_head", "tombstone_genesis_anchor"],
  publication_cas: ["current_revision", "current_head", "existing_replay_key", "existing_coordinate", "existing_operation"],
  version_binding: ["existing_coordinate"], ak_decision: ["canonical_store_head", "current_decision_record_digest"],
  acceptance_binding: ["canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"],
  activation_binding: ["canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"],
  generation_activation: ["canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"],
  rollback: ["canonical_store_head", "current_decision_record_digest", "current_acceptance_digest", "current_acceptance_revision", "current_activation_digest", "current_activation_revision", "canonical_history_head", "canonical_recovery_controller_id", "canonical_recovery_runtime_identity", "canonical_recovery_epoch", "canonical_trust_root_digest", "canonical_trust_revocation_revision", "canonical_trust_revocation_head", "revoked_trust_digests", "canonical_publication_revision", "canonical_publication_head"],
  governance_contracts: ["canonical_task_states"],
}).map(([rule, roles]) => [rule, new Set(roles)]));
const missingAnchorNegatives = new Map([
  ["authority_required_anchor_is_mandatory", new Set(["canonical_store_head"])],
  ["canonical_ak_authority_requires_independent_store_head_fact", new Set(["canonical_store_head"])],
  ["canonical_ak_authority_requires_independent_current_record_fact", new Set(["current_decision_record_digest"])],
]);
const voteRules = new Set(["approval_threshold", "trust_rotation", "trust_revocation", "compatibility", "lifecycle", "publication_commit", "publication_recovery", "publication_transition"]);
const protocolRoleSchemas = {"acceptance":"semantic-owner-acceptance.v0","activation":"semantic-activation-receipt.v0","activation_availability":"semantic-rollback-availability-proof.v0","ak_linkage":"semantic-ak-evidence-linkage.v0","approval":"semantic-owner-approval.v0","archive_linkage":"semantic-capsule-archive-linkage.v0","archive_manifest":"semantic-material-manifest.v0","availability":"semantic-rollback-availability-proof.v0","capsule":"semantic-release-capsule.v0","consumer_contract":"semantic-non-authorizing-task-contract.v0","consumer_manifest":"semantic-material-manifest.v0","decision":"semantic-ak-decision-reference.v0","deprecation":"semantic-deprecation-record.v0","tombstone_history":"semantic-tombstone-history-proof.v0","deprecation_approval":"semantic-owner-approval.v0","deprecation_canonical_ledger":"semantic-publication-ledger-head.v0","deprecation_decision":"semantic-ak-decision-reference.v0","deprecation_journal":"semantic-publication-journal.v0","deprecation_ledger":"semantic-accepted-lifecycle-ledger-record.v0","deprecation_marker":"semantic-publication-commit-marker.v0","deprecation_prior_journal":"semantic-publication-journal.v0","deprecation_prior_status":"semantic-owner-publication.v0","deprecation_publication":"semantic-owner-publication.v0","deprecation_transaction":"semantic-publication-transaction.v0","disable_artifact":"semantic-rollback-availability-receipt.v0","disable_contract_technical":"semantic-rollback-technical-receipt.v0","disable_rehearsal_technical":"semantic-rollback-technical-receipt.v0","existing_coordinate":"semantic-release-coordinate.v0","generation":"semantic-rocs-generation-receipt.v0","history_after":"semantic-rollback-history-transition.v0","intent":"semantic-consumer-intent.v0","journal":"semantic-publication-journal.v0","marker":"semantic-publication-commit-marker.v0","intent_marker":"semantic-publication-recovery-intent-marker.v0","before":"semantic-publication-recovery-state-receipt.v0","after":"semantic-publication-recovery-state-receipt.v0","materialization":"semantic-materialization-verification-receipt.v0","new_root":"semantic-trust-root.v0","old_root":"semantic-trust-root.v0","override":"semantic-compatibility-override.v0","owner_policy":"semantic-owner-policy.v0","owner_set":"semantic-owner-set.v0","payload_manifest":"semantic-material-manifest.v0","pi_receipt":"semantic-pi-delivery-receipt.v0","predicate":"semantic-approval-predicate.v0","previous_activation":"semantic-activation-receipt.v0","prior_journal":"semantic-publication-journal.v0","prior_status":["semantic-owner-publication.v0","semantic-publication-status-transition.v0"] ,"projection":"semantic-payload-projection.v0","recovery_artifact":"semantic-rollback-availability-receipt.v0","recovery_health_technical":"semantic-rollback-technical-receipt.v0","recovery_rehearsal_technical":"semantic-rollback-technical-receipt.v0","removal_approval":"semantic-owner-approval.v0","removal_canonical_ledger":"semantic-publication-ledger-head.v0","removal_decision":"semantic-ak-decision-reference.v0","removal_journal":"semantic-publication-journal.v0","removal_ledger":"semantic-accepted-lifecycle-ledger-record.v0","removal_marker":"semantic-publication-commit-marker.v0","removal_prior_journal":"semantic-publication-journal.v0","removal_publication":"semantic-owner-publication.v0","removal_transaction":"semantic-publication-transaction.v0","request":"semantic-rollback-request.v0","resulting_status":["semantic-owner-publication.v0","semantic-publication-status-transition.v0"],"resulting_tombstones":"semantic-tombstone-registry.v0","runtime_artifact":"semantic-rollback-availability-receipt.v0","runtime_materialization_technical":"semantic-rollback-technical-receipt.v0","runtime_revalidation_technical":"semantic-rollback-technical-receipt.v0","semantic_artifact":"semantic-rollback-availability-receipt.v0","semantic_materialization_technical":"semantic-rollback-technical-receipt.v0","transaction":"semantic-publication-transaction.v0","trust_root":"semantic-trust-root.v0","tombstones":"semantic-tombstone-registry.v0"};
const semanticProofSchemas = new Set(["semantic-accepted-lifecycle-ledger-record.v0","semantic-approval-predicate.v0","semantic-compatibility-override.v0","semantic-compatibility-policy.v0","semantic-compatibility-report.v0","semantic-deprecation-record.v0","semantic-owner-approval.v0","semantic-owner-policy.v0","semantic-owner-publication.v0","semantic-owner-set.v0","semantic-publication-commit-marker.v0","semantic-publication-journal.v0","semantic-publication-ledger-head.v0","semantic-publication-status-transition.v0","semantic-publication-transaction.v0","semantic-release-capsule.v0","semantic-release-coordinate.v0","semantic-removal-record.v0","semantic-source-manifest.v0","semantic-tombstone-registry.v0","semantic-tombstone-history-proof.v0","semantic-trust-revocation.v0","semantic-trust-root.v0","semantic-trust-rotation.v0"]);
const rocsProofSchemas = new Set(["semantic-build-receipt.v0","semantic-capsule-archive-linkage.v0","semantic-material-manifest.v0","semantic-materialization-verification-receipt.v0","semantic-payload-projection.v0","semantic-rocs-generation-receipt.v0","semantic-rollback-availability-proof.v0"]);
const consumerProofSchemas = new Set(["semantic-activation-receipt.v0","semantic-consumer-intent.v0","semantic-owner-acceptance.v0","semantic-rollback-request.v0","semantic-rollback-history-transition.v0"]);
const akProofSchemas = new Set(["semantic-ak-decision-reference.v0","semantic-ak-evidence-linkage.v0"]), recoveryProofSchemas = new Set(["semantic-rollback-receipt.v0","semantic-publication-recovery-intent-marker.v0","semantic-publication-recovery-state-receipt.v0"]);
const repositories = {
  semantic_owner: { owner: "semantic-owner", repository_id: "ontology-kernel", canonical_locator: "local://core/ontology-kernel", identity_revision: 1 },
  ak: { owner: "agent-kernel-owner", repository_id: "agent-kernel", canonical_locator: "local://softwareco/owned/agent-kernel", identity_revision: 9 },
  consumer_owner: { owner: "consumer-owner", repository_id: "pi-canary-consumer", canonical_locator: "local://softwareco/pi-canary-consumer", identity_revision: 3 },
  rocs: { owner: "rocs-owner", repository_id: "rocs-cli", canonical_locator: "local://core/rocs-cli", identity_revision: 4 },
  recovery_controller: { owner: "rocs-owner", repository_id: "rocs-cli", canonical_locator: "local://core/rocs-cli", identity_revision: 4 },
  pi: { owner: "pi-owner", repository_id: "pi-adapter", canonical_locator: "local://softwareco/pi-adapter", identity_revision: 1 },
};
const setEqual = (a, b) => a.size === b.size && [...a].every((x) => b.has(x));
const authorityArtifactDigest = (value) => value.schema === "semantic-release-coordinate.v0" ? objectDigest(value, coordinateDomain, null)[1] : value[digestFields[value.schema][1]];
function decodeAuthorityFact(value) { if (value.kind === "null") return null; if (value.kind === "empty_list") return []; if (value.kind === "empty_map") return Object.create(null); return value.value; }
function expectedRoleSchemas(rule, role, artifact) {
  if (role.startsWith("overrides:")) return ["semantic-compatibility-override.v0"];
  if (role.startsWith("override_approvals:")) return ["semantic-owner-approval.v0"];
  const base = role.split(":", 1)[0]; if (base === "policy") return [["compatibility", "lifecycle"].includes(rule) ? "semantic-compatibility-policy.v0" : "semantic-owner-policy.v0"];
  const expected = protocolRoleSchemas[base] ?? artifact.schema; return Array.isArray(expected) ? expected : [expected];
}
function proofAuthority(rule, role, artifact, schemaName) {
  let issuer;
  if (["semantic-publication-recovery-intent-marker.v0", "semantic-publication-recovery-state-receipt.v0"].includes(schemaName)) issuer = structuredClone(artifact.issuer);
  else if (schemaName === "semantic-rollback-technical-receipt.v0") { const kind = { materialization: "rocs", runtime_revalidation: "rocs", disable_contract: "consumer_owner", rehearsal: "recovery_controller", health: "recovery_controller" }[artifact.receipt_kind]; issuer = { kind, id: { rocs: "rocs-cli", consumer_owner: "consumer-owner", recovery_controller: "recovery" }[kind] }; }
  else if (schemaName === "semantic-rollback-availability-receipt.v0") { const kind = { semantic_target: "rocs", runtime_target: "rocs", disable_target: "consumer_owner", recovery_runtime: "recovery_controller" }[artifact.artifact_kind]; issuer = { kind, id: { rocs: "rocs-cli", consumer_owner: "consumer-owner", recovery_controller: "recovery" }[kind] }; }
  else if (schemaName === "semantic-non-authorizing-task-contract.v0") issuer = { kind: artifact.task_kind === "single_canary_consumer" ? "consumer_owner" : "ak", id: artifact.task_owner_id };
  else if (semanticProofSchemas.has(schemaName)) issuer = { kind: "semantic_owner", id: "semantic-owner" };
  else if (rocsProofSchemas.has(schemaName)) issuer = artifact.issuer ?? { kind: "rocs", id: "rocs-cli" };
  else if (consumerProofSchemas.has(schemaName)) issuer = artifact.issuer ?? artifact.acceptance_authority ?? { kind: "consumer_owner", id: "consumer-owner" };
  else if (akProofSchemas.has(schemaName)) issuer = artifact.issuer ?? { kind: "ak", id: "agent-kernel-owner" };
  else if (recoveryProofSchemas.has(schemaName)) issuer = artifact.issuer ?? { kind: "recovery_controller", id: "recovery" };
  else if (schemaName === "semantic-pi-delivery-receipt.v0") issuer = artifact.issuer;
  else issuer = artifact.issuer ?? { kind: "rocs", id: "rocs-cli" };
  const claim = { semantic_owner: "semantic_owner_fact", ak: "ak_canonical_fact", consumer_owner: "consumer_owner_fact", rocs: "rocs_technical_fact", recovery_controller: "recovery_controller_fact", pi: "pi_delivery_fact" }[issuer.kind];
  return [issuer, claim, structuredClone(repositories[issuer.kind])];
}
const authorityFactDigest = (factSchema, factValue) => typedDigest("semantic-release.authority-fact.v0", { fact_schema: factSchema, fact_value: factValue });
function acquisitionCapabilityDigest(fields) { const keys = ["owner_surface", "owner_repository", "acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest"]; return typedDigest("semantic-release.owner-acquisition-capability.v0", Object.fromEntries(keys.map((key) => [key, fields[key]]))); }
function freshnessToken(fields) { const keys = ["role", "category", "owner_surface", "owner_id", "owner_repository", "acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest", "store_id", "canonical_store_locator", "store_head_digest", "store_revision", "revocation_head_digest", "fact_schema", "fact_digest", "action_epoch", "required_action_epoch_floor"], value = Object.fromEntries(keys.map((key) => [key, fields[key]])); return typedDigest("semantic-release.owner-store-freshness-cas.v0", value); }
function manifestMapping(ruleEntry, role) { const matches = ruleEntry.role_mappings.filter((row) => row.role_prefix === null ? row.role === role : role.startsWith(row.role_prefix)); if (matches.length !== 1) throw new ContextError("self_certification"); return matches[0]; }
function expectedVoteReceipts(subject, nodeArtifacts) {
  const approvals = []; if (subject.schema === "semantic-owner-approval.v0") approvals.push(["subject", subject]);
  for (const [role, artifact] of nodeArtifacts) if (artifact.schema === "semantic-owner-approval.v0") approvals.push([role, artifact]);
  const result = new Map(); for (const [approvalRole, approval] of approvals) for (const vote of approval.votes) { const role = `vote-proof:${approvalRole}:${vote.owner_id}`; if (result.has(role)) throw new ContextError("malformed_input"); result.set(role, { owner_id: vote.owner_id, owner_key_id: vote.owner_key_id, approved_action_digest: vote.approved_action_digest, approval_proof_digest: vote.approval_proof_digest }); }
  return result;
}
function authorityPreflight(rule, subject, context) {
  if (!eq(Object.keys(context).sort(), ["acquisition_config", "authority_snapshot", "proof_bundle", "verifier_input"])) throw new ContextError("malformed_input");
  const ruleManifest = authorityManifestByRule.get(rule); if (authorityManifest === null || !ruleManifest) throw new ContextError("self_certification");
  const config = expectedContext(context.acquisition_config, "semantic-authority-acquisition-config.v0"), verifier = expectedContext(context.verifier_input, "semantic-authority-verifier-input.v0"), snapshot = expectedContext(context.authority_snapshot, "semantic-authority-snapshot.v0"), bundle = expectedContext(context.proof_bundle, "semantic-authority-proof-bundle.v0"), subjectDigest = authorityArtifactDigest(subject), expectedEdges = new Set(ruleManifest.edge_ids);
  if (!(verifier.rule === bundle.rule && bundle.rule === rule && verifier.subject_schema === bundle.subject_schema && bundle.subject_schema === subject.schema && verifier.subject_digest === bundle.subject_digest && bundle.subject_digest === subjectDigest
    && verifier.authority_rule_role_manifest_digest === authorityManifest.authority_rule_role_manifest_digest && verifier.authority_acquisition_config_digest === snapshot.authority_acquisition_config_digest && snapshot.authority_acquisition_config_digest === config.authority_acquisition_config_digest
    && verifier.authority_snapshot_digest === bundle.authority_snapshot_digest && bundle.authority_snapshot_digest === snapshot.authority_snapshot_digest && verifier.authority_proof_bundle_digest === bundle.authority_proof_bundle_digest
    && verifier.required_action_epoch_floor === config.required_action_epoch_floor && eq(snapshot.collator, config.collator) && snapshot.collation_scope === config.collation_scope)) throw new ContextError("self_certification");
  if (!setEqual(new Set(verifier.required_edge_ids), expectedEdges) || verifier.required_edge_ids.length !== expectedEdges.size) throw new ContextError("self_certification");
  const pins = new Map(config.pins.map((row) => [row.capability_pin_id, row])), receipts = new Map(snapshot.store_read_receipts.map((row) => [row.observation_id, row]));
  if (pins.size !== config.pins.length || receipts.size !== snapshot.store_read_receipts.length) throw new ContextError("malformed_input");
  const bindingObservations = new Set(verifier.receipt_bindings.map((row) => row.observation_id)), bindingPins = new Set(verifier.receipt_bindings.map((row) => row.capability_pin_id));
  if (!setEqual(new Set(receipts.keys()), bindingObservations) || !setEqual(new Set(verifier.required_observation_ids), bindingObservations) || !setEqual(new Set(pins.keys()), bindingPins) || verifier.receipt_bindings.length !== bindingObservations.size) throw new ContextError("self_certification");
  if (snapshot.action_epoch < config.required_action_epoch_floor) throw new ContextError("issuer_scope_violation");
  const resolved = Object.create(null), receiptRoles = new Set();
  const categoryProfiles = {
    semantic_trust: ["semantic_owner", "semantic-owner", repositories.semantic_owner], semantic_revocation: ["semantic_owner", "semantic-owner", repositories.semantic_owner], semantic_publication: ["semantic_owner", "semantic-owner", repositories.semantic_owner], semantic_lifecycle: ["semantic_owner", "semantic-owner", repositories.semantic_owner],
    ak_store: ["ak", "agent-kernel-owner", repositories.ak], ak_decision: ["ak", "agent-kernel-owner", repositories.ak], ak_task: ["ak", "agent-kernel-owner", repositories.ak],
    consumer_acceptance: ["consumer_owner", "consumer-owner", repositories.consumer_owner], consumer_activation: ["consumer_owner", "consumer-owner", repositories.consumer_owner], consumer_history: ["consumer_owner", "consumer-owner", repositories.consumer_owner], recovery_controller: ["recovery_controller", "recovery", repositories.recovery_controller],
  };
  for (const binding of verifier.receipt_bindings) {
    const role = binding.role, mapping = manifestMapping(ruleManifest, role), row = receipts.get(binding.observation_id), pin = pins.get(binding.capability_pin_id); if (!row || !pin) throw new ContextError("self_certification");
    try { structural(pin, schema); structural(row, schema); if (!embeddedDigestValid(pin) || !embeddedDigestValid(row)) throw new ContextError("digest_mismatch"); checkOrder(pin); checkOrder(row); } catch (error) { if (error instanceof ContextError) throw error; throw new ContextError("malformed_input"); }
    if (!(row.role === pin.role && pin.role === role && row.category === pin.category && pin.category === binding.category && row.capability_pin_id === pin.capability_pin_id && pin.capability_pin_id === binding.capability_pin_id && row.capability_pin_digest === pin.capability_pin_digest && row.acquisition_capability_digest === pin.acquisition_capability_digest && pin.acquisition_capability_digest === binding.acquisition_capability_digest)) throw new ContextError("issuer_scope_violation");
    if (!eq(mapping.sources, ["receipt"]) || mapping.category !== row.category) throw new ContextError("issuer_scope_violation");
    if (mapping.capability_pin_id !== null) { if (binding.capability_pin_id !== mapping.capability_pin_id || mapping.capability_pin_prefix !== null) throw new ContextError("issuer_scope_violation"); }
    else if (mapping.capability_pin_prefix === null || !binding.capability_pin_id.startsWith(mapping.capability_pin_prefix)) throw new ContextError("issuer_scope_violation");
    let expectedSurface, expectedId, expectedRepo;
    if (row.category === "semantic_vote") { expectedSurface = "semantic_owner"; expectedId = decodeAuthorityFact(row.fact_value)?.owner_id; expectedRepo = repositories.semantic_owner; if (mapping.role_prefix !== "vote-proof:" || expectedId === undefined || mapping.owner_surface !== expectedSurface || mapping.owner_id !== null || !eq(mapping.owner_repository, expectedRepo)) throw new ContextError("issuer_scope_violation"); }
    else { const profile = categoryProfiles[row.category]; if (!profile) throw new ContextError("issuer_scope_violation"); [expectedSurface, expectedId, expectedRepo] = profile; if (mapping.role_prefix !== null || mapping.owner_surface !== expectedSurface || mapping.owner_id !== expectedId || !eq(mapping.owner_repository, expectedRepo)) throw new ContextError("issuer_scope_violation"); }
    if (!(pin.owner_surface === row.issuer.kind && row.issuer.kind === binding.owner_surface && binding.owner_surface === expectedSurface && pin.owner_id === row.issuer.id && row.issuer.id === binding.owner_id && binding.owner_id === expectedId && eq(pin.owner_repository, row.owner_repository) && eq(row.owner_repository, binding.owner_repository) && eq(binding.owner_repository, expectedRepo) && !eq(row.issuer, config.collator))) throw new ContextError("issuer_scope_violation");
    for (const key of ["acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest", "store_id", "canonical_store_locator", "store_head_digest", "store_revision", "revocation_head_digest", "fact_schema", "fact_digest", "fact_value", "freshness_cas_token_digest", "required_action_epoch_floor"]) if (!eq(pin[key], row[key])) throw new ContextError("issuer_scope_violation");
    for (const key of ["acquisition_contract", "acquisition_contract_digest", "acquisition_distribution_digest", "acquisition_capability_digest"]) if (!eq(binding[key], row[key]) || !eq(mapping[key], row[key])) throw new ContextError("issuer_scope_violation");
    if (row.acquisition_capability_digest !== acquisitionCapabilityDigest({ owner_surface: expectedSurface, owner_repository: expectedRepo, acquisition_contract: row.acquisition_contract, acquisition_contract_digest: row.acquisition_contract_digest, acquisition_distribution_digest: row.acquisition_distribution_digest })) throw new ContextError("issuer_scope_violation");
    const expectedFactSchema = row.category === "semantic_vote" ? "semantic-owner-vote-proof-fact.v0" : `semantic-authority-${row.category.replaceAll("_", "-")}-fact.v0`;
    if (row.fact_schema !== expectedFactSchema || !eq(mapping.expected_schemas, [expectedFactSchema]) || row.fact_digest !== authorityFactDigest(row.fact_schema, row.fact_value)) throw new ContextError("issuer_scope_violation");
    const fields = { role, category: row.category, owner_surface: row.issuer.kind, owner_id: row.issuer.id, owner_repository: row.owner_repository, acquisition_contract: row.acquisition_contract, acquisition_contract_digest: row.acquisition_contract_digest, acquisition_distribution_digest: row.acquisition_distribution_digest, store_id: row.store_id, canonical_store_locator: row.canonical_store_locator, store_head_digest: row.store_head_digest, store_revision: row.store_revision, revocation_head_digest: row.revocation_head_digest, fact_schema: row.fact_schema, fact_digest: row.fact_digest, action_epoch: row.action_epoch, required_action_epoch_floor: row.required_action_epoch_floor };
    if (row.freshness_cas_token_digest !== freshnessToken(fields) || row.action_epoch !== snapshot.action_epoch || row.action_epoch < row.required_action_epoch_floor || row.required_action_epoch_floor !== config.required_action_epoch_floor) throw new ContextError("issuer_scope_violation");
    if (role === "canonical_store_head") { const value = decodeAuthorityFact(row.fact_value), storeMetadata = Object.fromEntries(["store_id", "canonical_store_locator", "store_revision", "store_head_digest", "revocation_head_digest"].map((key) => [key, row[key]])); if (!eq(value, storeMetadata)) throw new ContextError("issuer_scope_violation"); }
    if (receiptRoles.has(role)) throw new ContextError("malformed_input"); receiptRoles.add(role); resolved[role] = decodeAuthorityFact(row.fact_value);
  }
  if (rule === "publication_recovery") {
    const coherentRoles = new Set(["canonical_publication_revision", "canonical_publication_head", "canonical_publication_status_digest", "canonical_publication_journal_head", "canonical_recovery_journal_head", "canonical_recovery_transaction_digest", "canonical_recovery_resulting_revision", "canonical_recovery_resulting_head", "canonical_recovery_resulting_status_digest"]);
    const coherentRows = [...receipts.values()].filter((row) => coherentRoles.has(row.role));
    if (!setEqual(new Set(coherentRows.map((row) => row.role)), coherentRoles)) throw new ContextError("self_certification");
    const keys = ["owner_repository", "store_id", "canonical_store_locator", "store_head_digest", "store_revision", "revocation_head_digest", "action_epoch"];
    if (new Set(coherentRows.map((row) => jcs(Object.fromEntries(keys.map((key) => [key, row[key]]))))).size !== 1) throw new ContextError("issuer_scope_violation");
  }
  const nodes = new Map(bundle.nodes.map((row) => [row.bundle_key, row])); if (nodes.size !== bundle.nodes.length) throw new ContextError("malformed_input"); if (!setEqual(new Set(verifier.node_bindings.map((row) => row.bundle_key)), new Set(nodes.keys()))) throw new ContextError("self_certification");
  const nodeRoles = new Set(), nodeArtifacts = new Map(), lists = Object.create(null), maps = Object.create(null);
  for (const binding of verifier.node_bindings) {
    const role = binding.role, node = nodes.get(binding.bundle_key), artifact = node.artifact, mapping = manifestMapping(ruleManifest, role); expectedContext(artifact, artifact.schema);
    if (node.artifact_schema !== artifact.schema || node.bundle_key !== authorityArtifactDigest(artifact)) throw new ContextError("digest_mismatch");
    const schemas = expectedRoleSchemas(rule, role, artifact); if (!schemas.includes(binding.expected_schema) || !schemas.includes(artifact.schema) || !mapping.expected_schemas.includes(artifact.schema) || !mapping.sources.includes("node")) throw new ContextError("malformed_input");
    const [issuer, claim, repository] = proofAuthority(rule, role, artifact, artifact.schema), embedded = artifact.issuer ?? artifact.acceptance_authority; if (embedded !== undefined && !eq(node.issuer, embedded)) throw new ContextError("issuer_scope_violation");
    if (!eq(node.issuer, issuer) || !eq(node.owner_repository, repository) || node.claim_scope !== claim || binding.expected_issuer_kind !== issuer.kind || binding.expected_issuer_id !== issuer.id || !eq(binding.expected_owner_repository, repository) || binding.expected_claim_scope !== claim || mapping.owner_surface !== issuer.kind || mapping.owner_id !== issuer.id || !eq(mapping.owner_repository, repository)) throw new ContextError("issuer_scope_violation");
    if (nodeRoles.has(role)) throw new ContextError("malformed_input"); nodeRoles.add(role); nodeArtifacts.set(role, artifact);
    if (role.startsWith("overrides:")) (lists.overrides ??= []).push([role, artifact]); else if (role.startsWith("override_approvals:")) (maps.override_approvals ??= Object.create(null))[role.slice(role.indexOf(":") + 1)] = artifact; else resolved[role] = artifact;
  }
  const parameterRoles = new Set(), parameterValues = Object.create(null);
  for (const binding of verifier.parameter_bindings) { const role = binding.role, mapping = manifestMapping(ruleManifest, role); if (!mapping.sources.includes("parameter") || parameterRoles.has(role)) throw new ContextError("self_certification"); parameterRoles.add(role); parameterValues[role] = decodeAuthorityFact(binding.value); resolved[role] = parameterValues[role]; }
  const allRoles = new Set([...receiptRoles, ...nodeRoles, ...parameterRoles]); if ([...receiptRoles].some((role) => nodeRoles.has(role) || parameterRoles.has(role)) || [...nodeRoles].some((role) => parameterRoles.has(role)) || !setEqual(new Set(verifier.required_role_ids), allRoles) || verifier.required_role_ids.length !== allRoles.size) throw new ContextError("self_certification");
  if (ruleManifest.required_roles.some((role) => !allRoles.has(role))) throw new ContextError("self_certification");
  for (const mapping of ruleManifest.role_mappings) { const count = [...allRoles].filter((role) => mapping.role_prefix === null ? role === mapping.role : role.startsWith(mapping.role_prefix)).length; if (count < mapping.minimum_cardinality || count > mapping.maximum_cardinality) throw new ContextError("self_certification"); }
  const expectedReceipts = new Set(requiredReceiptRoles[rule] ?? []), voteFacts = expectedVoteReceipts(subject, nodeArtifacts); for (const role of voteFacts.keys()) expectedReceipts.add(role); if (!setEqual(receiptRoles, expectedReceipts)) throw new ContextError("self_certification"); for (const [role, fact] of voteFacts) if (!eq(resolved[role], fact)) throw new ContextError("issuer_scope_violation");
  if (Object.hasOwn(parameterValues, "overrides")) { const values = (lists.overrides ?? []).sort((a, b) => Buffer.compare(Buffer.from(a[0]), Buffer.from(b[0]))).map((x) => x[1]); if (!eq(parameterValues.overrides, values.map(authorityArtifactDigest))) throw new ContextError("self_certification"); resolved.overrides = values; }
  if (Object.hasOwn(parameterValues, "override_approvals")) { const values = maps.override_approvals ?? Object.create(null); if (!eq(parameterValues.override_approvals, Object.keys(values).sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b))))) throw new ContextError("self_certification"); resolved.override_approvals = values; }
  if (Object.hasOwn(resolved, "canonical_task_states")) {
    const taskReceipt = [...receipts.values()].find((row) => row.role === "canonical_task_states"); if (!taskReceipt) throw new ContextError("self_certification");
    const expectedHead = Object.fromEntries(["store_id", "canonical_store_locator", "store_revision", "store_head_digest", "revocation_head_digest"].map((key) => [key, taskReceipt[key]]));
    for (const taskState of resolved.canonical_task_states) if (!eq(taskState.repository, taskReceipt.owner_repository) || !eq(taskState.ak_store_head, expectedHead)) throw new ContextError("issuer_scope_violation");
    const decision = resolved.decision; if (decision !== undefined && decision !== null && (!eq(decision.ak_repository, taskReceipt.owner_repository) || !eq(decision.ak_store_head, expectedHead))) throw new ContextError("issuer_scope_violation");
  }
  resolved._authority_task_states = resolved.canonical_task_states ?? []; resolved._authority_snapshot_digest = snapshot.authority_snapshot_digest; return resolved;
}

function validateRuleContext(rule, subject, context) {
  let typed = [];
  const canonicalRules = new Set(["trust_rotation", "trust_revocation", "publication_commit", "publication_transition", "publication_recovery", "rollback", "generation_activation", "ak_decision", "acceptance_binding", "activation_binding"]);
  if (canonicalRules.has(rule) && (context.canonical_store_head === undefined || context.current_decision_record_digest === undefined)) throw new ContextError("self_certification");
  if (rule === "lifecycle" && (context.canonical_store_head === undefined || context.current_deprecation_decision_record_digest === undefined || context.current_removal_decision_record_digest === undefined)) throw new ContextError("self_certification");
  if (rule === "activation_binding" && (context.current_activation_digest === undefined || context.current_activation_revision === undefined || ((context.current_activation_digest === null) !== (context.current_activation_revision === null)))) throw new ContextError("self_certification");
  if (rule === "approval_threshold") typed = [["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["policy", "semantic-owner-policy.v0"]];
  else if (rule === "trust_rotation") typed = [["old_root", "semantic-trust-root.v0"], ["new_root", "semantic-trust-root.v0"], ["approval", "semantic-owner-approval.v0"], ["policy", "semantic-owner-policy.v0"], ["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["decision", "semantic-ak-decision-reference.v0"]];
  else if (rule === "trust_revocation") typed = [["approval", "semantic-owner-approval.v0"], ["policy", "semantic-owner-policy.v0"], ["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["decision", "semantic-ak-decision-reference.v0"]];
  else if (rule === "compatibility") { typed = [["policy", "semantic-compatibility-policy.v0"]]; for (const value of context.overrides) expectedContext(value, "semantic-compatibility-override.v0"); for (const value of Object.values(context.override_approvals)) expectedContext(value, "semantic-owner-approval.v0"); if (context.overrides.length) { if (context.canonical_store_head === undefined || context.current_decision_record_digest === undefined) throw new ContextError("self_certification"); typed.push(["owner_policy", "semantic-owner-policy.v0"], ["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["decision", "semantic-ak-decision-reference.v0"]); } }
  else if (rule === "lifecycle") { typed = [["deprecation", "semantic-deprecation-record.v0"], ["policy", "semantic-compatibility-policy.v0"], ["resulting_tombstones", "semantic-tombstone-registry.v0"], ["tombstone_history", "semantic-tombstone-history-proof.v0"], ["deprecation_ledger", "semantic-accepted-lifecycle-ledger-record.v0"], ["removal_ledger", "semantic-accepted-lifecycle-ledger-record.v0"], ["deprecation_publication", "semantic-owner-publication.v0"], ["removal_publication", "semantic-owner-publication.v0"], ["deprecation_transaction", "semantic-publication-transaction.v0"], ["removal_transaction", "semantic-publication-transaction.v0"], ["deprecation_journal", "semantic-publication-journal.v0"], ["removal_journal", "semantic-publication-journal.v0"], ["deprecation_marker", "semantic-publication-commit-marker.v0"], ["removal_marker", "semantic-publication-commit-marker.v0"], ["deprecation_approval", "semantic-owner-approval.v0"], ["removal_approval", "semantic-owner-approval.v0"], ["deprecation_prior_status", "semantic-owner-publication.v0"], ["removal_prior_status", ["semantic-owner-publication.v0", "semantic-publication-status-transition.v0"]], ["deprecation_prior_journal", "semantic-publication-journal.v0"], ["removal_prior_journal", "semantic-publication-journal.v0"], ["deprecation_canonical_ledger", "semantic-publication-ledger-head.v0"], ["removal_canonical_ledger", "semantic-publication-ledger-head.v0"], ["owner_policy", "semantic-owner-policy.v0"], ["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["trust_root", "semantic-trust-root.v0"], ["deprecation_decision", "semantic-ak-decision-reference.v0"], ["removal_decision", "semantic-ak-decision-reference.v0"]]; expectedShapeContext(context.external_trust_root_pin, "externalTrustRootPin"); expectedShapeContext(context.tombstone_genesis_anchor, "tombstoneGenesisAnchor"); }
  else if (rule === "tombstone_reuse") { typed = [["tombstones", "semantic-tombstone-registry.v0"], ["tombstone_history", "semantic-tombstone-history-proof.v0"]]; expectedShapeContext(context.tombstone_genesis_anchor, "tombstoneGenesisAnchor"); }
  else if (rule === "publication_commit") { typed = [["transaction", "semantic-publication-transaction.v0"], ["journal", "semantic-publication-journal.v0"], ["marker", "semantic-publication-commit-marker.v0"], ["approval", "semantic-owner-approval.v0"], ["trust_root", "semantic-trust-root.v0"], ["prior_journal", "semantic-publication-journal.v0"], ["prior_status", "semantic-owner-publication.v0"], ["policy", "semantic-owner-policy.v0"], ["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["decision", "semantic-ak-decision-reference.v0"]]; expectedShapeContext(context.external_trust_root_pin, "externalTrustRootPin"); }
  else if (rule === "publication_transition") { typed = [["transaction", "semantic-publication-transaction.v0"], ["journal", "semantic-publication-journal.v0"], ["marker", "semantic-publication-commit-marker.v0"], ["prior_status", ["semantic-owner-publication.v0", "semantic-publication-status-transition.v0"]], ["approval", "semantic-owner-approval.v0"], ["trust_root", "semantic-trust-root.v0"], ["policy", "semantic-owner-policy.v0"], ["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["prior_journal", "semantic-publication-journal.v0"], ["decision", "semantic-ak-decision-reference.v0"]]; expectedShapeContext(context.external_trust_root_pin, "externalTrustRootPin"); }
  else if (rule === "publication_recovery") { typed = [["transaction", "semantic-publication-transaction.v0"], ["resulting_status", ["semantic-owner-publication.v0", "semantic-publication-status-transition.v0"]], ["before", "semantic-publication-recovery-state-receipt.v0"], ["after", "semantic-publication-recovery-state-receipt.v0"], ["prior_status", ["semantic-owner-publication.v0", "semantic-publication-status-transition.v0"]], ["prior_journal", "semantic-publication-journal.v0"], ["approval", "semantic-owner-approval.v0"], ["policy", "semantic-owner-policy.v0"], ["owner_set", "semantic-owner-set.v0"], ["predicate", "semantic-approval-predicate.v0"], ["decision", "semantic-ak-decision-reference.v0"], ["trust_root", "semantic-trust-root.v0"]]; if (context.intent_marker !== null) typed.push(["intent_marker", "semantic-publication-recovery-intent-marker.v0"]); if (context.marker !== null) typed.push(["marker", "semantic-publication-commit-marker.v0"]); expectedShapeContext(context.before.state, "publicationRecoveryState"); expectedShapeContext(context.after.state, "publicationRecoveryState"); expectedShapeContext(context.external_trust_root_pin, "externalTrustRootPin"); }
  else if (rule === "projection") { expectedShapeContext(context.tombstone_genesis_anchor, "tombstoneGenesisAnchor"); typed = [["projection", "semantic-payload-projection.v0"], ["capsule", "semantic-release-capsule.v0"], ["archive_linkage", "semantic-capsule-archive-linkage.v0"], ["payload_manifest", "semantic-material-manifest.v0"], ["consumer_manifest", "semantic-material-manifest.v0"], ["archive_manifest", "semantic-material-manifest.v0"], ["tombstones", "semantic-tombstone-registry.v0"], ["tombstone_history", "semantic-tombstone-history-proof.v0"]]; }
  else if (rule === "rollback") { typed = [["request", "semantic-rollback-request.v0"], ["activation", "semantic-activation-receipt.v0"], ["decision", "semantic-ak-decision-reference.v0"], ["intent", "semantic-consumer-intent.v0"], ["acceptance", "semantic-owner-acceptance.v0"], ["materialization", "semantic-materialization-verification-receipt.v0"], ["availability", "semantic-rollback-availability-proof.v0"], ["recovery_artifact", "semantic-rollback-availability-receipt.v0"]]; const names = { semantic_artifact: "semantic-rollback-availability-receipt.v0", runtime_artifact: "semantic-rollback-availability-receipt.v0", disable_artifact: "semantic-rollback-availability-receipt.v0", history_after: "semantic-rollback-history-transition.v0", ak_linkage: "semantic-ak-evidence-linkage.v0", pi_receipt: "semantic-pi-delivery-receipt.v0" }; for (const [key, name] of Object.entries(names)) if (context[key] !== null && context[key] !== undefined) expectedContext(context[key], name); expectedShapeContext(context.canonical_history_head, "historyHead"); }
  else if (rule === "pi_delivery") typed = [["generation", "semantic-rocs-generation-receipt.v0"]];
  else if (rule === "ak_optional_pi") { if (!eq(Object.keys(context).filter((key) => !key.startsWith("_")).sort(), ["activation", "canonical_task_states", "decision", "generation", "pi_receipt"])) throw new ContextError("self_certification"); if (!Array.isArray(context.canonical_task_states) || context.canonical_task_states.length !== 1) throw new ContextError("self_certification"); expectedShapeContext(context.canonical_task_states[0], "akTaskState"); typed = [["decision", "semantic-ak-decision-reference.v0"], ["activation", "semantic-activation-receipt.v0"], ["generation", "semantic-rocs-generation-receipt.v0"]]; if (context.pi_receipt !== null) expectedContext(context.pi_receipt, "semantic-pi-delivery-receipt.v0"); }
  else if (rule === "generation_activation") typed = [["activation", "semantic-activation-receipt.v0"], ["decision", "semantic-ak-decision-reference.v0"], ["intent", "semantic-consumer-intent.v0"], ["acceptance", "semantic-owner-acceptance.v0"], ["materialization", "semantic-materialization-verification-receipt.v0"], ["availability", "semantic-rollback-availability-proof.v0"]];
  else if (rule === "ak_decision") expectedShapeContext(context.canonical_store_head, "akStoreHead");
  else if (rule === "acceptance_binding") typed = [["decision", "semantic-ak-decision-reference.v0"], ["intent", "semantic-consumer-intent.v0"]];
  else if (rule === "activation_binding") typed = [["decision", "semantic-ak-decision-reference.v0"], ["intent", "semantic-consumer-intent.v0"], ["acceptance", "semantic-owner-acceptance.v0"], ["materialization", "semantic-materialization-verification-receipt.v0"], ["availability", "semantic-rollback-availability-proof.v0"]];
  else if (rule === "governance_contracts") typed = [["consumer_contract", "semantic-non-authorizing-task-contract.v0"]];
  else if (rule === "version_binding") expectedContext(context.existing_coordinate, "semantic-release-coordinate.v0");
  else if (rule === "publication_cas" && context.existing_coordinate !== null) expectedContext(context.existing_coordinate, "semantic-release-coordinate.v0");
  if (["rollback", "generation_activation", "activation_binding"].includes(rule)) { const closure = [["activation_availability", "semantic-rollback-availability-proof.v0"], ["semantic_artifact", "semantic-rollback-availability-receipt.v0"], ["runtime_artifact", "semantic-rollback-availability-receipt.v0"], ["disable_artifact", "semantic-rollback-availability-receipt.v0"], ["recovery_artifact", "semantic-rollback-availability-receipt.v0"], ["semantic_materialization_technical", "semantic-rollback-technical-receipt.v0"], ["runtime_materialization_technical", "semantic-rollback-technical-receipt.v0"], ["runtime_revalidation_technical", "semantic-rollback-technical-receipt.v0"], ["disable_contract_technical", "semantic-rollback-technical-receipt.v0"], ["disable_rehearsal_technical", "semantic-rollback-technical-receipt.v0"], ["recovery_rehearsal_technical", "semantic-rollback-technical-receipt.v0"], ["recovery_health_technical", "semantic-rollback-technical-receipt.v0"]]; typed.push(...closure.filter(([key]) => context[key] !== null && context[key] !== undefined)); }
  for (const key of ["current_revision", "prior_revision", "canonical_deprecation_revision", "canonical_removal_revision", "current_acceptance_revision", "current_activation_revision", "current_activation_head_revision", "canonical_trust_revocation_revision", "canonical_publication_revision", "canonical_recovery_epoch", "canonical_recovery_resulting_revision"]) if (context[key] !== undefined && context[key] !== null && (!Number.isSafeInteger(context[key]) || context[key] < 0)) throw new ContextError("malformed_input");
  for (const key of ["current_head", "existing_replay_key", "current_root_digest", "prior_head", "deprecation_prior_head", "current_lifecycle_head", "canonical_deprecation_head", "canonical_removal_head", "current_activation_digest", "current_decision_record_digest", "current_deprecation_decision_record_digest", "current_removal_decision_record_digest", "canonical_trust_root_digest", "canonical_trust_revocation_head", "canonical_publication_head", "current_acceptance_digest", "canonical_publication_journal_head", "canonical_recovery_journal_head", "canonical_publication_status_digest", "canonical_recovery_transaction_digest", "canonical_recovery_resulting_head", "canonical_recovery_resulting_status_digest"]) if (context[key] !== undefined && context[key] !== null && (typeof context[key] !== "string" || !/^sha256:[0-9a-f]{64}$/u.test(context[key]))) throw new ContextError("malformed_input");
  if (context.revoked !== undefined && (!Array.isArray(context.revoked) || context.revoked.some((x) => typeof x !== "string" || !/^sha256:[0-9a-f]{64}$/u.test(x)))) throw new ContextError("malformed_input");
  if (context.revoked_trust_digests !== undefined && (!Array.isArray(context.revoked_trust_digests) || context.revoked_trust_digests.some((x) => typeof x !== "string" || !/^sha256:[0-9a-f]{64}$/u.test(x)))) throw new ContextError("malformed_input");
  if (context.prior_version !== undefined) { try { semver(context.prior_version); } catch { throw new ContextError("malformed_input"); } }
  if (context.override_approvals !== undefined) for (const [key, value] of Object.entries(context.override_approvals)) { const approval = expectedContext(value, "semantic-owner-approval.v0"); if (key !== approval.owner_approval_digest) throw new ContextError("digest_mismatch"); }
  for (const [key, name] of typed) expectedContext(context[key], name);
  if (rule === "publication_commit") { expectedContext(context.transaction, "semantic-publication-transaction.v0", subject.transaction_digest, "lifecycle_violation"); expectedContext(context.approval, "semantic-owner-approval.v0", subject.owner_approval_digest, "lifecycle_violation"); expectedContext(context.prior_journal, "semantic-publication-journal.v0", context.prior_journal_digest, "lifecycle_violation"); }
  else if (rule === "publication_transition") { expectedContext(context.transaction, "semantic-publication-transaction.v0", subject.transaction_digest, "lifecycle_violation"); expectedContext(context.prior_status, ["semantic-owner-publication.v0", "semantic-publication-status-transition.v0"], subject.prior_status_record_digest, "lifecycle_violation"); expectedContext(context.approval, "semantic-owner-approval.v0", subject.owner_approval_digest, "lifecycle_violation"); expectedContext(context.prior_journal, "semantic-publication-journal.v0", context.prior_journal_digest, "lifecycle_violation"); }
  else if (rule === "rollback") { expectedContext(context.request, "semantic-rollback-request.v0", subject.rollback_request_digest, "history_conflict"); expectedContext(context.availability, "semantic-rollback-availability-proof.v0", subject.availability_proof_digest, "rollback_unavailable"); }
  else if (rule === "activation_binding") { expectedContext(context.acceptance, "semantic-owner-acceptance.v0", subject.owner_acceptance_digest, "self_certification"); expectedContext(context.materialization, "semantic-materialization-verification-receipt.v0", subject.materialization_verification_receipt_digest, "self_certification"); expectedContext(context.availability, "semantic-rollback-availability-proof.v0", subject.rollback_availability_proof_digest, "rollback_unavailable"); }
  else if (rule === "projection") { expectedContext(context.projection, "semantic-payload-projection.v0", subject.payload_projection_digest, "projection_mismatch"); expectedContext(context.archive_linkage, "semantic-capsule-archive-linkage.v0", subject.capsule_archive_linkage_digest, "projection_mismatch"); }
  if (context.canonical_lifecycle_tombstone_head !== undefined) expectedShapeContext(context.canonical_lifecycle_tombstone_head, "lifecycleTombstoneHead");
  if (context.previous_activation !== undefined && context.previous_activation !== null) expectedContext(context.previous_activation, "semantic-activation-receipt.v0");
  if (context.canonical_store_head !== undefined) expectedShapeContext(context.canonical_store_head, "akStoreHead");
}
const semverPattern = /^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)(?:-((?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9][0-9]*|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/u;
const semver = (v) => { if (typeof v !== "string" || [...v].length < 5 || [...v].length > 256) fail("bad semver"); const m = v.match(semverPattern); if (!m) fail("bad semver"); return m.slice(1); };
const compareIntegerText = (a, b) => a.length - b.length || Buffer.compare(Buffer.from(a, "ascii"), Buffer.from(b, "ascii"));
function compare(a, b) { for (let i = 0; i < 3; i++) { const c = compareIntegerText(a[i], b[i]); if (c) return c; } const ap = a[3], bp = b[3]; if (ap === undefined || bp === undefined) return ap === bp ? 0 : ap === undefined ? 1 : -1; const aa = ap.split("."), bb = bp.split("."); for (let i = 0; i < Math.min(aa.length, bb.length); i++) { const x = aa[i], y = bb[i]; if (x === y) continue; const xn = /^\d+$/u.test(x), yn = /^\d+$/u.test(y); if (xn && yn) return compareIntegerText(x, y); if (xn !== yn) return xn ? -1 : 1; return Buffer.compare(Buffer.from(x), Buffer.from(y)); } return aa.length - bb.length; }

function strictUtc(value) {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$/u); if (!match) return false;
  const parts = match.slice(1).map(Number); if (parts[0] < 1 || parts[0] > 9999) return false;
  const date = new Date(0); date.setUTCFullYear(parts[0], parts[1] - 1, parts[2]); date.setUTCHours(parts[3], parts[4], parts[5], 0);
  return date.getUTCFullYear() === parts[0] && date.getUTCMonth() === parts[1] - 1 && date.getUTCDate() === parts[2] && date.getUTCHours() === parts[3] && date.getUTCMinutes() === parts[4] && date.getUTCSeconds() === parts[5];
}
function conditionTrue(c) {
  const computed = c.kind === "evidence_digest_equals" ? c.expected_digest !== null && c.expected_digest === c.actual_digest && c.expected_integer === null && c.actual_integer === null : c.expected_digest === null && c.actual_digest === null && c.expected_integer !== null && c.actual_integer !== null && c.actual_integer >= c.expected_integer;
  return c.satisfied === computed && computed;
}
function technicalReceiptValid(receipt, kind, issuerKind, referenced = null) { return receipt.receipt_kind === kind && receipt.issuer.kind === issuerKind && receipt.outcome === "valid" && receipt.referenced_receipt_digest === referenced; }
function rollbackAvailabilityValid(intent, acceptance, materialization, proof, context, suppliedTarget = null) {
  const target = suppliedTarget ?? intent.rollback_target;
  if (!(proof.consumer_intent_digest === intent.consumer_intent_digest && intent.consumer_intent_digest === materialization.consumer_intent_digest && proof.owner_acceptance_digest === acceptance.owner_acceptance_digest && acceptance.owner_acceptance_digest === materialization.owner_acceptance_digest && proof.materialization_verification_receipt_digest === materialization.materialization_verification_receipt_digest && proof.recovery_controller_id === context.canonical_recovery_controller_id && proof.recovery_epoch === proof.availability_epoch && proof.availability_epoch === context.canonical_recovery_epoch && proof.availability_epoch >= acceptance.acceptance_epoch && proof.target_kind === target.kind && proof.recovery_runtime_available)) return false;
  const recovery = context.recovery_artifact, rr = context.recovery_rehearsal_technical, rh = context.recovery_health_technical;
  if (!(recovery.issuer.kind === "recovery_controller" && recovery.issuer.id === proof.recovery_controller_id && proof.recovery_controller_id === context.canonical_recovery_controller_id && rr.issuer.id === rh.issuer.id && rh.issuer.id === recovery.issuer.id && recovery.artifact_kind === "recovery_runtime" && recovery.rollback_available_artifact_digest === proof.recovery_artifact_digest && eq(recovery.runtime_identity, proof.recovery_runtime_identity) && eq(proof.recovery_runtime_identity, context.canonical_recovery_runtime_identity) && recovery.rehearsal_receipt_digest === rr.rollback_technical_receipt_digest && recovery.health_receipt_digest === rh.rollback_technical_receipt_digest && technicalReceiptValid(rr, "rehearsal", "recovery_controller") && technicalReceiptValid(rh, "health", "recovery_controller", rr.rollback_technical_receipt_digest) && rr.subject_digest === recovery.runtime_identity.distribution_digest && rh.subject_digest === recovery.runtime_identity.distribution_digest && rr.coordinate === null && rh.coordinate === null && eq(rr.runtime_identity, rh.runtime_identity) && eq(rh.runtime_identity, recovery.runtime_identity) && recovery.availability_epoch === proof.availability_epoch)) return false;
  if (["semantic", "combined"].includes(target.kind)) { const st = target.kind === "semantic" ? target : target.semantic_stage, artifact = context.semantic_artifact, receipt = context.semantic_materialization_technical; if (!(artifact.issuer.kind === "rocs" && artifact.issuer.id === receipt.issuer.id && receipt.issuer.id === materialization.issuer.id && artifact.artifact_kind === "semantic_target" && artifact.rollback_available_artifact_digest === proof.semantic_target_artifact_digest && eq(artifact.coordinate, st.target_coordinate) && eq(st.target_coordinate, proof.semantic_coordinate) && artifact.materialization_receipt_digest === st.target_materialization_receipt_digest && st.target_materialization_receipt_digest === proof.semantic_materialization_receipt_digest && proof.semantic_materialization_receipt_digest === receipt.rollback_technical_receipt_digest && technicalReceiptValid(receipt, "materialization", "rocs") && receipt.subject_digest === st.target_coordinate.capsule_digest && eq(receipt.coordinate, st.target_coordinate) && eq(receipt.runtime_identity, materialization.runtime_identity))) return false; }
  if (["runtime", "combined"].includes(target.kind)) { const rt = target.kind === "runtime" ? target : target.runtime_stage, artifact = context.runtime_artifact, mat = context.runtime_materialization_technical, rv = context.runtime_revalidation_technical; if (!(artifact.issuer.kind === "rocs" && artifact.issuer.id === mat.issuer.id && mat.issuer.id === rv.issuer.id && rv.issuer.id === materialization.issuer.id && artifact.artifact_kind === "runtime_target" && artifact.rollback_available_artifact_digest === proof.runtime_target_artifact_digest && eq(artifact.runtime_identity, rt.target_runtime_identity) && eq(rt.target_runtime_identity, proof.runtime_identity) && artifact.materialization_receipt_digest === rt.target_materialization_receipt_digest && rt.target_materialization_receipt_digest === proof.runtime_materialization_receipt_digest && proof.runtime_materialization_receipt_digest === mat.rollback_technical_receipt_digest && artifact.runtime_revalidation_receipt_digest === rt.runtime_revalidation_receipt_digest && rt.runtime_revalidation_receipt_digest === proof.runtime_revalidation_receipt_digest && proof.runtime_revalidation_receipt_digest === rv.rollback_technical_receipt_digest && technicalReceiptValid(mat, "materialization", "rocs") && technicalReceiptValid(rv, "runtime_revalidation", "rocs", mat.rollback_technical_receipt_digest) && mat.subject_digest === rt.target_runtime_identity.distribution_digest && rv.subject_digest === materialization.coordinate.capsule_digest && eq(mat.coordinate, materialization.coordinate) && eq(rv.coordinate, materialization.coordinate) && eq(mat.runtime_identity, rv.runtime_identity) && eq(rv.runtime_identity, rt.target_runtime_identity))) return false; }
  if (target.kind === "no_prior_disable") { const artifact = context.disable_artifact, contract = context.disable_contract_technical, rehearsal = context.disable_rehearsal_technical; if (!(artifact.issuer.kind === "consumer_owner" && artifact.issuer.id === contract.issuer.id && contract.issuer.id === acceptance.acceptance_authority.id && rehearsal.issuer.id === recovery.issuer.id && artifact.artifact_kind === "disable_target" && artifact.rollback_available_artifact_digest === proof.disable_target_artifact_digest && artifact.disable_contract_digest === target.disable_contract_digest && target.disable_contract_digest === proof.disable_contract_digest && proof.disable_contract_digest === contract.rollback_technical_receipt_digest && artifact.rehearsal_receipt_digest === target.rehearsal_receipt_digest && target.rehearsal_receipt_digest === proof.rehearsal_receipt_digest && proof.rehearsal_receipt_digest === rehearsal.rollback_technical_receipt_digest && technicalReceiptValid(contract, "disable_contract", "consumer_owner") && technicalReceiptValid(rehearsal, "rehearsal", "recovery_controller", contract.rollback_technical_receipt_digest) && contract.subject_digest === context.decision.rollback_plan_digest && rehearsal.subject_digest === contract.rollback_technical_receipt_digest && contract.coordinate === null && rehearsal.coordinate === null && eq(contract.runtime_identity, materialization.runtime_identity) && eq(rehearsal.runtime_identity, materialization.runtime_identity))) return false; }
  return true;
}
function semanticTrustCurrent(intent, materialization, context) { const trust = intent.trust_reference; return eq(materialization.trust_reference, trust) && trust.trust_root_digest === context.canonical_trust_root_digest && trust.local_revocation_revision === context.canonical_trust_revocation_revision && trust.local_revocation_head_digest === context.canonical_trust_revocation_head && trust.publication_ledger_revision === context.canonical_publication_revision && trust.publication_digest === context.canonical_publication_head && !context.revoked_trust_digests.includes(trust.trust_root_digest); }
function activationChainValid(activation, context, candidate = false) {
  const intent = context.intent, acceptance = context.acceptance, materialization = context.materialization, decision = context.decision, availability = context.activation_availability ?? context.availability, previous = context.previous_activation;
  let continuity;
  if (candidate) {
    const pd = context.current_activation_digest, pr = context.current_activation_revision;
    const genesis = pd === null && pr === null && previous === null && activation.activation_revision === 1 && activation.prior_activation_revision === null && activation.previous_activation_receipt_digest === null && activation.current_activation_head_digest === null;
    const successor = pd !== null && pr !== null && previous !== null && previous.activation_receipt_digest === pd && previous.activation_revision === pr && activation.previous_activation_receipt_digest === pd && activation.current_activation_head_digest === pd && activation.prior_activation_revision === pr && activation.activation_revision === pr + 1 && activation.activation_epoch > previous.activation_epoch;
    continuity = genesis || successor;
  } else continuity = previous === null ? activation.activation_revision === 1 && activation.prior_activation_revision === null && activation.previous_activation_receipt_digest === null && activation.current_activation_head_digest === null : activation.previous_activation_receipt_digest === previous.activation_receipt_digest && activation.current_activation_head_digest === previous.activation_receipt_digest && activation.prior_activation_revision === previous.activation_revision && activation.activation_revision === previous.activation_revision + 1 && activation.activation_epoch > previous.activation_epoch;
  return decisionCurrent(decision, context) && continuity && semanticTrustCurrent(intent, materialization, context) && activation.status === "activated" && activation.revoked_by_digest === null && activation.superseded_by_activation_receipt_digest === null && activation.issuer.kind === "consumer_owner" && activation.issuer.id === activation.consumer_owner_issuer_id && activation.consumer_owner_issuer_id === intent.consumer_repository.owner && activation.consumer_intent_digest === intent.consumer_intent_digest && activation.owner_acceptance_digest === acceptance.owner_acceptance_digest && activation.materialization_verification_receipt_digest === materialization.materialization_verification_receipt_digest && activation.rollback_availability_proof_digest === availability.rollback_availability_proof_digest && rollbackAvailabilityValid(intent, acceptance, materialization, availability, context) && acceptance.consumer_intent_digest === intent.consumer_intent_digest && intent.consumer_intent_digest === materialization.consumer_intent_digest && materialization.owner_acceptance_digest === acceptance.owner_acceptance_digest && eq(activation.consumer_repository, acceptance.consumer_repository) && eq(acceptance.consumer_repository, intent.consumer_repository) && eq(intent.consumer_repository, materialization.consumer_repository) && eq(activation.coordinate, intent.desired_coordinate) && eq(intent.desired_coordinate, materialization.coordinate) && eq(activation.runtime_identity, intent.runtime_identity) && eq(intent.runtime_identity, materialization.runtime_identity) && eq(activation.canary_scope, acceptance.canary_scope) && eq(acceptance.canary_scope, intent.canary_scope) && eq(intent.canary_scope, materialization.canary_scope) && eq(activation.canary_scope.consumer_repository, activation.consumer_repository) && acceptance.acceptance_authority.kind === "consumer_owner" && acceptance.acceptance_authority.id === intent.consumer_repository.owner && acceptance.revoked_by_digest === null && acceptance.owner_acceptance_digest === context.current_acceptance_digest && acceptance.acceptance_revision === context.current_acceptance_revision && intent.intent_revision <= acceptance.valid_through_intent_revision && activation.acceptance_epoch === acceptance.acceptance_epoch && acceptance.acceptance_epoch <= availability.availability_epoch && availability.availability_epoch <= activation.activation_epoch && activation.activation_epoch <= acceptance.activation_epoch_not_after && intent.decision_reference_digest === acceptance.decision_reference_digest && acceptance.decision_reference_digest === activation.gate_decision_reference_digest && activation.gate_decision_reference_digest === decision.ak_decision_reference_digest && acceptance.governing_scope_digest === decision.scope_digest && materialization.rollback_ready && materialization.journal_state === "committed" && eq(materialization.rollback_target, intent.rollback_target) && materialization.verifier_contract_digest === intent.verifier_contract_digest && materialization.compatibility_outcome === intent.accepted_compatibility && activation.activation_target_digest === decision.activation_target_digest && ["evidence_criteria_digest", "rollback_plan_digest", "stop_conditions_digest"].every((k) => activation[k] === decision[k]);
}

function decisionCurrent(subject, context) {
  const canonical = context.canonical_store_head;
  return subject.lifecycle_state === "accepted" && subject.adr_reference.status === "accepted" && subject.revocation_digest === null && subject.superseded_by_decision_record_digest === null && eq(subject.ak_store_head, canonical) && context.current_decision_record_digest === subject.decision_record_digest;
}

function requiredPublicationAction(tx, context, priorStatus) {
  const action = tx.approved_action;
  if (tx.operation === "publish") {
    if (action.kind !== "release") return null;
    return { kind: "release", coordinate: structuredClone(tx.coordinate), source_manifest_digest: action.source_manifest_digest,
      candidate_capsule_digest: tx.coordinate.capsule_digest, compatibility_report_digest: action.compatibility_report_digest };
  }
  const priorDigest = priorStatus.owner_publication_digest ?? priorStatus.publication_status_transition_digest, priorState = priorStatus.status ?? priorStatus.to_status;
  if (priorDigest === undefined || priorState === undefined || !["withdraw", "revoke"].includes(tx.operation)) return null;
  return { kind: tx.operation === "withdraw" ? "publication_withdrawal" : "publication_revocation", operation: tx.operation,
    namespace: tx.namespace, owner_policy_digest: context.policy.owner_policy_digest, owner_set_digest: context.owner_set.owner_set_digest,
    approval_predicate_digest: context.predicate.approval_predicate_digest, coordinate: structuredClone(tx.coordinate),
    prior_status_record_digest: priorDigest, prior_status: priorState, reason_digest: tx.status_reason_digest,
    expected_prior_revision: tx.expected_prior_revision, expected_prior_head_digest: tx.expected_prior_head_digest };
}
function transactionActionShapeValid(tx) {
  const action = tx.approved_action; if (actionDigest(action) !== tx.approved_action_digest) return false;
  if (tx.operation === "publish") return action.kind === "release" && eq(action.coordinate, tx.coordinate) && action.candidate_capsule_digest === tx.coordinate.capsule_digest && tx.status_reason_digest === null;
  const expectedKind = tx.operation === "withdraw" ? "publication_withdrawal" : "publication_revocation";
  return action.kind === expectedKind && action.operation === tx.operation && action.namespace === tx.namespace && eq(action.coordinate, tx.coordinate)
    && action.reason_digest === tx.status_reason_digest && action.prior_status_record_digest === tx.expected_prior_head_digest
    && action.expected_prior_revision === tx.expected_prior_revision && action.expected_prior_head_digest === tx.expected_prior_head_digest
    && tx.status_reason_digest !== null;
}
function publicationAuthorityValid(approval, context, tx, priorStatus) {
  const root = context.trust_root, pin = context.external_trust_root_pin, policy = context.policy, ownerSet = context.owner_set, predicate = context.predicate, coordinate = tx.coordinate;
  const requiredAction = requiredPublicationAction(tx, context, priorStatus);
  const actionExact = requiredAction !== null && eq(tx.approved_action, requiredAction) && tx.approved_action_digest === actionDigest(requiredAction)
    && eq(approval.action, tx.approved_action) && approval.action_digest === tx.approved_action_digest;
  const trustExact = root.namespace === pin.namespace && pin.namespace === policy.namespace && policy.namespace === ownerSet.namespace && ownerSet.namespace === predicate.namespace && predicate.namespace === approval.namespace && approval.namespace === coordinate.namespace && root.owner_policy_digest === pin.owner_policy_digest && pin.owner_policy_digest === policy.owner_policy_digest && policy.owner_policy_digest === approval.owner_policy_digest && root.owner_set_digest === pin.owner_set_digest && pin.owner_set_digest === ownerSet.owner_set_digest && ownerSet.owner_set_digest === approval.owner_set_digest && root.trust_root_id === pin.trust_root_id && root.trust_root_revision === pin.trust_root_revision && root.trust_root_digest === pin.trust_root_digest && pin.trust_root_digest === context.canonical_trust_root_digest && root.status === "active" && pin.revocation_revision === context.canonical_trust_revocation_revision && pin.revocation_head_digest === context.canonical_trust_revocation_head && !context.revoked_trust_digests.includes(root.trust_root_digest) && !approval.votes.some((vote) => context.revoked_trust_digests.includes(vote.approval_proof_digest));
  return trustExact && evaluate("approval_threshold", approval, { policy, owner_set: ownerSet, predicate }, true) === null && approval.decision_reference_digest === context.decision.ak_decision_reference_digest && decisionCurrent(context.decision, context) && actionExact;
}
function priorPublicationChainValid(tx, prior, journal) { const pd = prior.owner_publication_digest ?? prior.publication_status_transition_digest; return pd === tx.expected_prior_head_digest && prior.ledger_revision === tx.expected_prior_revision && journal.transaction_digest === prior.transaction_digest && journal.resulting_record_digest === pd && journal.resulting_ledger_head_digest === pd && journal.resulting_ledger_revision === prior.ledger_revision && journal.state === "committed" && journal.linearized && journal.recovery_action === "none"; }

function lifecyclePublicationEndpointValid(prefix, context) {
  const pub = context[`${prefix}_publication`], tx = context[`${prefix}_transaction`], journal = context[`${prefix}_journal`], marker = context[`${prefix}_marker`], approval = context[`${prefix}_approval`], prior = context[`${prefix}_prior_status`], priorJournal = context[`${prefix}_prior_journal`], ledger = context[`${prefix}_canonical_ledger`], decision = context[`${prefix}_decision`], result = pub.owner_publication_digest;
  const authority = { policy: context.owner_policy, owner_set: context.owner_set, predicate: context.predicate, decision, canonical_store_head: context.canonical_store_head, current_decision_record_digest: context[`current_${prefix}_decision_record_digest`], trust_root: context.trust_root, external_trust_root_pin: context.external_trust_root_pin, canonical_trust_root_digest: context.canonical_trust_root_digest, canonical_trust_revocation_revision: context.canonical_trust_revocation_revision, canonical_trust_revocation_head: context.canonical_trust_revocation_head, revoked_trust_digests: context.revoked_trust_digests };
  return publicationAuthorityValid(approval, authority, tx, prior) && priorPublicationChainValid(tx, prior, priorJournal) && tx.operation === "publish" && tx.status_reason_digest === null && eq(tx.coordinate, pub.coordinate) && tx.namespace === tx.coordinate.namespace && tx.coordinate.namespace === pub.ledger_namespace && pub.ledger_namespace === pub.coordinate.namespace && pub.transaction_digest === tx.publication_transaction_digest && tx.publication_transaction_digest === journal.transaction_digest && journal.transaction_digest === marker.transaction_digest && pub.owner_approval_digest === tx.owner_approval_digest && tx.owner_approval_digest === approval.owner_approval_digest && pub.trust_root_digest === context.trust_root.trust_root_digest && pub.ledger_revision === tx.expected_prior_revision + 1 && journal.prior_journal_digest === priorJournal.publication_journal_digest && journal.state === "committed" && journal.linearized && journal.recovery_action === "none" && journal.resulting_record_digest === result && journal.resulting_ledger_head_digest === result && journal.resulting_ledger_revision === pub.ledger_revision && marker.journal_digest === journal.publication_journal_digest && marker.resulting_record_digest === result && marker.resulting_ledger_head_digest === result && marker.resulting_ledger_revision === pub.ledger_revision && marker.fsync_complete && ledger.namespace === pub.ledger_namespace && ledger.ledger_revision === pub.ledger_revision && ledger.ledger_head_digest === result && ledger.status_record_digest === result && ledger.transaction_digest === tx.publication_transaction_digest && ledger.journal_digest === journal.publication_journal_digest && ledger.commit_marker_digest === marker.publication_commit_marker_digest && ledger.prior_ledger_head_digest === tx.expected_prior_head_digest;
}

function tombstoneHistoryValid(proof, current, genesisAnchor) {
  if (genesisAnchor.semantic_owner_id !== "semantic-owner" || genesisAnchor.namespace !== current.namespace || genesisAnchor.genesis_registry_revision !== 1 || !eq(proof.issuer, { kind: "semantic_owner", id: "semantic-owner" }) || proof.namespace !== current.namespace || proof.current_lifecycle_head_digest !== current.lifecycle_head_digest || proof.current_registry_digest !== current.tombstone_registry_digest || proof.current_registry_revision !== current.registry_revision) return false;
  const revisions = proof.revisions; if (!revisions.length || revisions.length !== current.registry_revision) return false;
  let previous = null; const priorSemanticIds = new Set(), priorLifecycleHeads = new Set();
  for (let index = 0; index < revisions.length; index++) {
    const expectedRevision = index + 1, { registry, authorized_delta: delta } = revisions[index];
    try { if (!embeddedDigestValid(registry)) return false; checkOrder(registry); } catch { return false; }
    if (registry.namespace !== proof.namespace || registry.registry_revision !== expectedRevision || delta.resulting_lifecycle_head_digest !== registry.lifecycle_head_digest) return false;
    if (previous === null) {
      if (expectedRevision !== 1 || registry.prior_registry_digest !== null || registry.tombstone_registry_digest !== genesisAnchor.genesis_registry_digest || registry.registry_revision !== genesisAnchor.genesis_registry_revision || registry.lifecycle_head_digest !== genesisAnchor.genesis_lifecycle_head_digest || registry.namespace !== genesisAnchor.namespace || delta.authorization_kind !== "genesis" || delta.prior_lifecycle_head_digest !== null || !eq(delta.added_entries, registry.entries)) return false;
    } else {
      const priorEntries = new Map(previous.entries.map((row) => [row.semantic_id, row])), currentEntries = new Map(registry.entries.map((row) => [row.semantic_id, row])), added = delta.added_entries, addedIds = new Set(added.map((row) => row.semantic_id));
      if (registry.prior_registry_digest !== previous.tombstone_registry_digest || delta.authorization_kind !== "removal" || delta.prior_lifecycle_head_digest !== previous.lifecycle_head_digest || added.length !== 1 || addedIds.size !== added.length || [...addedIds].some((id) => priorSemanticIds.has(id)) || registry.entries.length !== previous.entries.length + 1 || priorLifecycleHeads.has(registry.lifecycle_head_digest) || delta.authorization_record_digest !== registry.lifecycle_head_digest || added.some((row) => row.origin_record_digest !== delta.authorization_record_digest) || [...priorEntries].some(([key, value]) => !currentEntries.has(key) || !eq(currentEntries.get(key), value)) || currentEntries.size !== new Set([...priorEntries.keys(), ...addedIds]).size || added.some((row) => !eq(currentEntries.get(row.semantic_id), row))) return false;
    }
    registry.entries.forEach((row) => priorSemanticIds.add(row.semantic_id)); priorLifecycleHeads.add(registry.lifecycle_head_digest); previous = registry;
  }
  return eq(previous, current);
}

function evaluate(rule, subject, context, resolved = false) {
  if (!resolved) { try { context = authorityPreflight(rule, subject, context); } catch (error) { if (error instanceof ContextError) return error.code; throw error; } }
  if (rule !== "digest") { try { validateRuleContext(rule, subject, context); } catch (error) { if (error instanceof ContextError) return error.code; throw error; } }
  if (rule === "digest") return embeddedDigestValid(subject) ? null : "digest_mismatch";
  if (rule === "approval_threshold") {
    const ownerSet = context.owner_set, predicate = context.predicate, policy = context.policy;
    const exact = subject.namespace === policy.namespace && policy.namespace === ownerSet.namespace && ownerSet.namespace === predicate.namespace && subject.owner_policy_digest === policy.owner_policy_digest && subject.owner_set_digest === policy.owner_set_digest && policy.owner_set_digest === ownerSet.owner_set_digest && subject.approval_predicate_digest === policy.approval_predicate_digest && policy.approval_predicate_digest === predicate.approval_predicate_digest;
    if (!exact) return "approval_threshold_unsatisfied";
    const members = new Map(ownerSet.members.map((x) => [x.owner_id, x])), active = new Set([...members].filter(([, x]) => x.status === "active").map(([id]) => id)), owners = new Set();
    if (actionDigest(subject.action) !== subject.action_digest) return "approval_threshold_unsatisfied";
    for (const vote of subject.votes) { const member = members.get(vote.owner_id); if (member?.status === "revoked") return "trust_revoked"; if (!member || !member.key_ids.includes(vote.owner_key_id) || vote.approved_action_digest !== subject.action_digest || owners.has(vote.owner_id)) return "approval_threshold_unsatisfied"; owners.add(vote.owner_id); }
    const needed = predicate.threshold; if (predicate.mode === "unanimous" && needed !== active.size || predicate.mode === "threshold" && (needed < 1 || needed > active.size)) return "approval_threshold_unsatisfied";
    const approved = predicate.mode === "unanimous" ? owners.size === active.size && [...owners].every((x) => active.has(x)) : owners.size >= needed; return approved ? null : "approval_threshold_unsatisfied";
  }
  if (rule === "trust_rotation") {
    const { old_root: old, new_root: next, approval, policy, owner_set: ownerSet, predicate } = context; if (context.revoked.includes(old.trust_root_digest)) return "trust_revoked"; const action = approval.action;
    const authority = subject.namespace === old.namespace && old.namespace === next.namespace && next.namespace === policy.namespace && policy.namespace === ownerSet.namespace && ownerSet.namespace === predicate.namespace && predicate.namespace === approval.namespace && subject.owner_policy_digest === policy.owner_policy_digest && policy.owner_policy_digest === old.owner_policy_digest && old.owner_policy_digest === next.owner_policy_digest && next.owner_policy_digest === approval.owner_policy_digest && subject.owner_set_digest === policy.owner_set_digest && policy.owner_set_digest === old.owner_set_digest && old.owner_set_digest === next.owner_set_digest && next.owner_set_digest === approval.owner_set_digest && approval.owner_set_digest === ownerSet.owner_set_digest && subject.approval_predicate_digest === policy.approval_predicate_digest && policy.approval_predicate_digest === approval.approval_predicate_digest && approval.approval_predicate_digest === predicate.approval_predicate_digest;
    const transition = subject.old_trust_root_digest === context.current_root_digest && subject.old_trust_root_digest === old.trust_root_digest && subject.old_trust_root_id === old.trust_root_id && subject.old_trust_root_revision === old.trust_root_revision && subject.new_trust_root_digest === next.trust_root_digest && subject.new_trust_root_id === next.trust_root_id && subject.new_trust_root_revision === next.trust_root_revision && next.trust_root_revision === old.trust_root_revision + 1 && next.prior_trust_root_digest === old.trust_root_digest && subject.rotation_revision === next.trust_root_revision;
    const actionFields = { kind: "trust_rotation", namespace: subject.namespace, old_trust_root_digest: subject.old_trust_root_digest, new_trust_root_digest: subject.new_trust_root_digest, owner_policy_digest: subject.owner_policy_digest, owner_set_digest: subject.owner_set_digest, approval_predicate_digest: subject.approval_predicate_digest, new_trust_root_revision: subject.new_trust_root_revision, rotation_revision: subject.rotation_revision };
    const approvalThresholdValid = evaluate("approval_threshold", approval, { policy, owner_set: ownerSet, predicate }, true) === null;
    const valid = authority && transition && approvalThresholdValid && subject.approval_digest === approval.owner_approval_digest && approval.decision_reference_digest === context.decision.ak_decision_reference_digest && decisionCurrent(context.decision, context) && eq(action, actionFields) && actionDigest(action) === approval.action_digest; return valid ? null : "trust_reference_stale";
  }
  if (rule === "trust_revocation") {
    const { approval, policy, owner_set: ownerSet, predicate } = context, action = approval.action;
    const authority = subject.namespace === policy.namespace && policy.namespace === ownerSet.namespace && ownerSet.namespace === predicate.namespace && predicate.namespace === approval.namespace && approval.owner_policy_digest === policy.owner_policy_digest && approval.owner_set_digest === policy.owner_set_digest && policy.owner_set_digest === ownerSet.owner_set_digest && approval.approval_predicate_digest === policy.approval_predicate_digest && policy.approval_predicate_digest === predicate.approval_predicate_digest;
    const approvalThresholdValid = evaluate("approval_threshold", approval, { policy, owner_set: ownerSet, predicate }, true) === null;
    const valid = authority && approvalThresholdValid && subject.revocation_revision === context.prior_revision + 1 && subject.prior_revocation_digest === context.prior_head && subject.owner_approval_digest === approval.owner_approval_digest && approval.decision_reference_digest === context.decision.ak_decision_reference_digest && decisionCurrent(context.decision, context) && action.kind === "trust_revocation" && actionDigest(action) === approval.action_digest && ["namespace", "target_kind", "target_digest", "effective_ledger_revision", "reason_digest", "prior_revocation_digest", "revocation_revision"].every((k) => eq(subject[k], action[k])) && action.owner_policy_digest === policy.owner_policy_digest && action.owner_set_digest === ownerSet.owner_set_digest && action.approval_predicate_digest === predicate.approval_predicate_digest; return valid ? null : "trust_reference_stale";
  }
  if (rule === "compatibility_policy") { const cats = subject.category_rules.map((x) => x.category), expected = new Set(["addition", "documentation", "compatible_refinement", "deprecation", "removal", "constraint_change", "relation_change", "identifier_reuse", "other"]); return cats.length === 9 && new Set(cats).size === 9 && cats.every((x) => expected.has(x)) ? null : "compatibility_rejected"; }
  if (rule === "compatibility") {
    const policy = context.policy; if (subject.compatibility_policy_digest !== policy.compatibility_policy_digest) return "compatibility_rejected";
    const rules = new Map(policy.category_rules.map((x) => [x.category, x])), conditions = new Map(subject.conditions.map((x) => [x.condition_id, x])); if (conditions.size !== subject.conditions.length) return "compatibility_rejected";
    const overrideRows = context.overrides, overrides = new Map(overrideRows.map((x) => [x.change_digest, x])); if (overrides.size !== overrideRows.length) return "compatibility_rejected";
    const usedConditions = new Set(), usedOverrides = [], effective = [], knownChanges = new Set();
    for (const change of subject.changes) {
      const row = rules.get(change.category); if (!row || change.classification !== row.classification || change.semver_effect !== row.semver_effect || (row.condition_rule === null) !== (change.condition_id === null)) return "compatibility_rejected";
      let classification = change.classification, effect = change.semver_effect;
      if (change.condition_id !== null) { const c = conditions.get(change.condition_id); usedConditions.add(change.condition_id); if (!c || c.kind !== row.condition_rule.condition_kind || !conditionTrue(c)) return "compatibility_rejected"; }
      const cd = changeDigest(change), override = overrides.get(cd); if (override) {
        knownChanges.add(cd); const approval = context.override_approvals[override.owner_approval_digest], action = approval?.action;
        const expectedAction = { kind: "compatibility_override", namespace: override.namespace, compatibility_policy_digest: override.compatibility_policy_digest, change: override.change, change_digest: override.change_digest, from_classification: override.from_classification, from_semver_effect: override.from_semver_effect, to_classification: override.to_classification, semver_effect_floor: override.semver_effect_floor, condition: override.condition };
        const ranks = { patch: 0, minor: 1, major: 2, unknown: 2 }, nonLowering = ranks[override.semver_effect_floor] >= ranks[effect];
        const approvalValid = approval && evaluate("approval_threshold", approval, { policy: context.owner_policy, owner_set: context.owner_set, predicate: context.predicate }, true) === null;
        const valid = approvalValid && approval.decision_reference_digest === context.decision.ak_decision_reference_digest && decisionCurrent(context.decision, context) && approval.namespace === override.namespace && context.owner_policy.compatibility_policy_digest === subject.compatibility_policy_digest && row.override_allowed && change.category !== "identifier_reuse" && override.namespace === subject.namespace && override.compatibility_policy_digest === subject.compatibility_policy_digest && eq(override.change, change) && override.change_digest === cd && override.from_classification === classification && override.from_semver_effect === effect && conditionTrue(override.condition) && nonLowering && eq(action, expectedAction) && actionDigest(action) === approval.action_digest;
        if (!valid) return "compatibility_rejected"; classification = override.to_classification; effect = override.semver_effect_floor; usedOverrides.push(override.compatibility_override_digest);
      }
      effective.push([classification, effect]);
    }
    const conditionRefs = subject.changes.filter((x) => x.condition_id !== null).map((x) => x.condition_id);
    if (conditionRefs.length !== new Set(conditionRefs).size || conditions.size !== usedConditions.size || conditionRefs.length !== conditions.size || [...conditions.keys()].some((x) => !usedConditions.has(x)) || !eq([...usedOverrides].sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b))), subject.override_digests) || overrides.size !== knownChanges.size) return "compatibility_rejected";
    const cr = { compatible: 0, conditionally_compatible: 1, breaking: 2, unknown: 3 }, er = { patch: 0, minor: 1, major: 2, unknown: 3 };
    const classification = effective.reduce((a, x) => cr[x[0]] > cr[a] ? x[0] : a, "compatible"), effect = effective.reduce((a, x) => er[x[1]] > er[a] ? x[1] : a, "patch");
    if (subject.classification !== classification || subject.required_semver_effect !== effect) return "compatibility_rejected"; if (classification === "unknown" || effect === "unknown") return "compatibility_unknown";
    const old = semver(context.prior_version), next = semver(subject.candidate_version); if (compare(next, old) <= 0) return "semver_violation";
    const majorCmp = compareIntegerText(next[0], old[0]), minorCmp = compareIntegerText(next[1], old[1]);
    const valid = effect === "patch" && majorCmp === 0 && minorCmp === 0 && compareIntegerText(next[2], old[2]) > 0 || effect === "minor" && (majorCmp > 0 || majorCmp === 0 && minorCmp > 0) || effect === "major" && majorCmp > 0; return valid ? null : "semver_violation";
  }
  if (rule === "lifecycle") {
    const dep = context.deprecation, policy = context.policy, resulting = context.resulting_tombstones, historyProof = context.tombstone_history;
    const historyValid = tombstoneHistoryValid(historyProof, resulting, context.tombstone_genesis_anchor), prior = historyProof.revisions.length >= 2 ? historyProof.revisions.at(-2).registry : null;
    const expected = prior === null ? [] : [...prior.entries.map((x) => structuredClone(x)), { semantic_id: subject.semantic_id, reason: "removed", origin_record_digest: subject.removal_record_digest }].sort((a, b) => Buffer.compare(Buffer.from(a.semantic_id), Buffer.from(b.semantic_id)));
    const exactChain = dep.prior_lifecycle_digest === context.deprecation_prior_head && subject.prior_lifecycle_digest === context.current_lifecycle_head && subject.prior_lifecycle_digest === dep.deprecation_record_digest;
    const valid = prior !== null && historyValid && subject.namespace === dep.namespace && dep.namespace === dep.introduced_coordinate.namespace && dep.namespace === subject.removed_coordinate.namespace && subject.namespace === policy.namespace && subject.namespace === prior.namespace && subject.namespace === resulting.namespace && subject.semantic_id === dep.semantic_id && subject.deprecation_record_digest === dep.deprecation_record_digest && exactChain && subject.deprecation_ledger_revision === dep.introduced_ledger_revision && subject.removed_ledger_revision > subject.deprecation_ledger_revision && subject.required_interval === policy.minimum_deprecation_releases && subject.removed_ledger_revision - subject.deprecation_ledger_revision >= subject.required_interval && subject.compatibility_policy_digest === policy.compatibility_policy_digest && subject.prior_tombstone_registry_digest === prior.tombstone_registry_digest && resulting.prior_registry_digest === prior.tombstone_registry_digest && resulting.lifecycle_head_digest === subject.removal_record_digest && resulting.registry_revision === prior.registry_revision + 1 && !prior.entries.some((x) => x.semantic_id === subject.semantic_id) && eq(resulting.entries, expected);
    const depLedger = context.deprecation_ledger, remLedger = context.removal_ledger, depPub = context.deprecation_publication, remPub = context.removal_publication;
    const accepted = depLedger.namespace === remLedger.namespace && remLedger.namespace === subject.namespace && depLedger.ledger_revision === dep.introduced_ledger_revision && depLedger.ledger_revision === context.canonical_deprecation_revision && depLedger.ledger_head_digest === context.canonical_deprecation_head && depLedger.ledger_head_digest === depPub.owner_publication_digest && eq(depLedger.coordinate, dep.introduced_coordinate) && eq(depLedger.coordinate, depPub.coordinate) && depLedger.publication_status_record_digest === depPub.owner_publication_digest && remLedger.ledger_revision === subject.removed_ledger_revision && remLedger.ledger_revision === context.canonical_removal_revision && remLedger.ledger_head_digest === context.canonical_removal_head && remLedger.ledger_head_digest === remPub.owner_publication_digest && eq(remLedger.coordinate, subject.removed_coordinate) && eq(remLedger.coordinate, remPub.coordinate) && remLedger.publication_status_record_digest === remPub.owner_publication_digest && depPub.status === "published" && remPub.status === "published" && depLedger.accepted_for_lifecycle && remLedger.accepted_for_lifecycle;
    const ledgerBindings = depLedger.publication_transaction_digest === context.deprecation_transaction.publication_transaction_digest && depLedger.publication_journal_digest === context.deprecation_journal.publication_journal_digest && depLedger.publication_commit_marker_digest === context.deprecation_marker.publication_commit_marker_digest && depLedger.owner_approval_digest === context.deprecation_approval.owner_approval_digest && depLedger.trust_root_digest === context.trust_root.trust_root_digest && depLedger.canonical_ledger_digest === context.deprecation_canonical_ledger.publication_ledger_head_digest && remLedger.publication_transaction_digest === context.removal_transaction.publication_transaction_digest && remLedger.publication_journal_digest === context.removal_journal.publication_journal_digest && remLedger.publication_commit_marker_digest === context.removal_marker.publication_commit_marker_digest && remLedger.owner_approval_digest === context.removal_approval.owner_approval_digest && remLedger.trust_root_digest === context.trust_root.trust_root_digest && remLedger.canonical_ledger_digest === context.removal_canonical_ledger.publication_ledger_head_digest;
    const endpoints = lifecyclePublicationEndpointValid("deprecation", context) && lifecyclePublicationEndpointValid("removal", context); return valid && accepted && ledgerBindings && endpoints ? null : "lifecycle_violation";
  }
  if (rule === "tombstone_reuse") { const current = context.canonical_lifecycle_tombstone_head, tombstones = context.tombstones, ids = new Set(tombstones.entries.map((x) => x.semantic_id)); const currentExact = subject.namespace === current.namespace && current.namespace === tombstones.namespace && current.lifecycle_head_digest === tombstones.lifecycle_head_digest && current.tombstone_registry_digest === tombstones.tombstone_registry_digest && current.tombstone_registry_revision === tombstones.registry_revision && tombstoneHistoryValid(context.tombstone_history, tombstones, context.tombstone_genesis_anchor); return currentExact && !subject.changes.some((x) => ids.has(x.semantic_id)) ? null : "lifecycle_violation"; }
  if (rule === "publication_cas") { if (!transactionActionShapeValid(subject)) return "lifecycle_violation"; if (subject.operation === "publish" && subject.status_reason_digest !== null || ["withdraw", "revoke"].includes(subject.operation) && subject.status_reason_digest === null) return "lifecycle_violation"; if (context.existing_replay_key === subject.replay_key_digest && eq(context.existing_coordinate, subject.coordinate) && context.existing_operation === subject.operation) return null; if (subject.expected_prior_revision !== context.current_revision) return "publication_conflict"; return subject.expected_prior_head_digest === context.current_head ? null : "publication_fork"; }
  if (rule === "version_binding") { const old = context.existing_coordinate, next = subject.coordinate; return old.namespace === next.namespace && old.semantic_version === next.semantic_version && old.capsule_digest !== next.capsule_digest ? "version_conflict" : null; }
  if (rule === "publication_commit") {
    const tx = context.transaction, journal = context.journal, marker = context.marker, result = subject.owner_publication_digest;
    const authorityValid = publicationAuthorityValid(context.approval, context, tx, context.prior_status), priorValid = priorPublicationChainValid(tx, context.prior_status, context.prior_journal) && tx.expected_prior_revision === context.canonical_publication_revision && tx.expected_prior_head_digest === context.canonical_publication_head && context.prior_journal.publication_journal_digest === context.canonical_publication_journal_head;
    const valid = authorityValid && priorValid && tx.operation === "publish" && tx.status_reason_digest === null && subject.transaction_digest === tx.publication_transaction_digest && tx.publication_transaction_digest === journal.transaction_digest && journal.transaction_digest === marker.transaction_digest && eq(subject.coordinate, tx.coordinate) && subject.ledger_namespace === tx.namespace && tx.namespace === tx.coordinate.namespace && subject.owner_approval_digest === tx.owner_approval_digest && tx.owner_approval_digest === context.approval.owner_approval_digest && subject.trust_root_digest === context.trust_root.trust_root_digest && subject.prior_publication_digest === tx.expected_prior_head_digest && subject.ledger_revision === tx.expected_prior_revision + 1 && journal.state === "committed" && journal.linearized && journal.recovery_action === "none" && journal.resulting_record_digest === result && journal.resulting_ledger_head_digest === result && journal.resulting_ledger_revision === subject.ledger_revision && journal.prior_journal_digest === context.prior_journal_digest && context.prior_journal_digest === context.prior_journal.publication_journal_digest && marker.journal_digest === journal.publication_journal_digest && marker.resulting_record_digest === result && marker.resulting_ledger_head_digest === result && marker.resulting_ledger_revision === subject.ledger_revision && marker.fsync_complete; return valid ? null : "lifecycle_violation";
  }
  if (rule === "publication_transition") {
    const tx = context.transaction, journal = context.journal, marker = context.marker, result = subject.publication_status_transition_digest, op = subject.to_status === "withdrawn" ? "withdraw" : "revoke", prior = context.prior_status;
    const priorDigest = prior.owner_publication_digest ?? prior.publication_status_transition_digest, priorStatus = prior.status ?? prior.to_status;
    const validFrom = subject.from_status === priorStatus && priorDigest === subject.prior_status_record_digest && eq(prior.coordinate, subject.coordinate) && prior.ledger_revision === tx.expected_prior_revision;
    const approval = context.approval;
    const authorityValid = publicationAuthorityValid(approval, context, tx, prior);
    const valid = validFrom && priorPublicationChainValid(tx, prior, context.prior_journal) && tx.expected_prior_revision === context.canonical_publication_revision && tx.expected_prior_head_digest === context.canonical_publication_head && context.prior_journal.publication_journal_digest === context.canonical_publication_journal_head && authorityValid && tx.operation === op && tx.owner_approval_digest === approval.owner_approval_digest && approval.owner_approval_digest === subject.owner_approval_digest && tx.publication_transaction_digest === subject.transaction_digest && subject.transaction_digest === journal.transaction_digest && journal.transaction_digest === marker.transaction_digest && eq(tx.coordinate, subject.coordinate) && tx.owner_approval_digest === subject.owner_approval_digest && tx.status_reason_digest === subject.reason_digest && tx.expected_prior_head_digest === subject.prior_status_record_digest && tx.expected_prior_revision + 1 === subject.ledger_revision && journal.state === "committed" && journal.linearized && journal.recovery_action === "none" && journal.prior_journal_digest === context.prior_journal_digest && context.prior_journal_digest === context.prior_journal.publication_journal_digest && journal.resulting_record_digest === result && journal.resulting_ledger_head_digest === result && journal.resulting_ledger_revision === subject.ledger_revision && marker.journal_digest === journal.publication_journal_digest && marker.resulting_record_digest === result && marker.resulting_ledger_head_digest === result && marker.resulting_ledger_revision === subject.ledger_revision && marker.fsync_complete; return valid ? null : "lifecycle_violation";
  }
  if (rule === "publication_journal_shape") { const validTuple = ["prepared", "aborted"].includes(subject.state) && !subject.linearized && subject.recovery_action === "discard_staging" || subject.state === "committing" && subject.linearized && subject.recovery_action === "complete_commit" || subject.state === "committed" && subject.linearized && subject.recovery_action === "none"; return validTuple ? null : "recovery_needed"; }
  if (rule === "publication_recovery") {
    const tx = context.transaction, result = context.resulting_status, intent = context.intent_marker, marker = context.marker;
    const beforeReceipt = context.before, afterReceipt = context.after, before = beforeReceipt.state, after = afterReceipt.state, prior = context.prior_status, priorJournal = context.prior_journal;
    const controllerExact = subject.recovery_controller_id === context.canonical_recovery_controller_id && eq(subject.recovery_runtime_identity, context.canonical_recovery_runtime_identity) && subject.recovery_epoch === context.canonical_recovery_epoch
      && beforeReceipt.phase === "before" && eq(beforeReceipt.issuer, { kind: "semantic_owner", id: beforeReceipt.semantic_owner_id }) && beforeReceipt.semantic_owner_id === "semantic-owner"
      && afterReceipt.phase === "after" && eq(afterReceipt.issuer, { kind: "recovery_controller", id: afterReceipt.recovery_controller_id })
      && beforeReceipt.recovery_controller_id === afterReceipt.recovery_controller_id && afterReceipt.recovery_controller_id === subject.recovery_controller_id
      && beforeReceipt.recovery_epoch === afterReceipt.recovery_epoch && afterReceipt.recovery_epoch === subject.recovery_epoch
      && beforeReceipt.semantic_owner_id === afterReceipt.semantic_owner_id && beforeReceipt.namespace === afterReceipt.namespace && afterReceipt.namespace === tx.namespace
      && beforeReceipt.transaction_digest === afterReceipt.transaction_digest && afterReceipt.transaction_digest === tx.publication_transaction_digest
      && beforeReceipt.recovery_journal_digest === afterReceipt.recovery_journal_digest && afterReceipt.recovery_journal_digest === subject.publication_journal_digest;
    if (!controllerExact) return "recovery_needed";
    const validTuple = ["prepared", "aborted"].includes(subject.state) && !subject.linearized && subject.recovery_action === "discard_staging" || subject.state === "committing" && subject.linearized && subject.recovery_action === "complete_commit" || subject.state === "committed" && subject.linearized && subject.recovery_action === "none";
    if (!validTuple) return "recovery_needed";
    const priorDigest = prior.owner_publication_digest ?? prior.publication_status_transition_digest, resultDigest = result.owner_publication_digest ?? result.publication_status_transition_digest, priorStatus = prior.status ?? prior.to_status;
    const observedRevision = subject.linearized ? result.ledger_revision : prior.ledger_revision, observedDigest = subject.linearized ? resultDigest : priorDigest;
    const canonicalBefore = priorDigest !== undefined && resultDigest !== undefined && before.revision === context.canonical_publication_revision && before.revision === observedRevision
      && before.head === context.canonical_publication_head && before.head === observedDigest && before.status_record_digest === context.canonical_publication_status_digest && before.status_record_digest === observedDigest
      && subject.prior_journal_digest === context.canonical_publication_journal_head && subject.prior_journal_digest === priorJournal.publication_journal_digest
      && subject.publication_journal_digest === context.canonical_recovery_journal_head && priorPublicationChainValid(tx, prior, priorJournal)
      && (subject.linearized || tx.expected_prior_revision === before.revision && tx.expected_prior_head_digest === before.head);
    const transitionExpected = context.canonical_recovery_transaction_digest === subject.transaction_digest
      && context.canonical_recovery_resulting_revision === subject.resulting_ledger_revision
      && context.canonical_recovery_resulting_head === subject.resulting_ledger_head_digest
      && context.canonical_recovery_resulting_status_digest === subject.resulting_record_digest;
    const authorityValid = publicationAuthorityValid(context.approval, context, tx, prior);
    const commonResult = authorityValid && resultDigest !== undefined && subject.transaction_digest === tx.publication_transaction_digest && tx.publication_transaction_digest === result.transaction_digest
      && subject.resulting_record_digest === subject.resulting_ledger_head_digest && subject.resulting_record_digest === resultDigest
      && subject.resulting_ledger_revision === result.ledger_revision && result.ledger_revision === tx.expected_prior_revision + 1
      && eq(tx.coordinate, result.coordinate) && tx.owner_approval_digest === result.owner_approval_digest && result.owner_approval_digest === context.approval.owner_approval_digest;
    let resultJoin;
    if (result.schema === "semantic-owner-publication.v0") resultJoin = tx.operation === "publish" && tx.status_reason_digest === null && result.status === "published" && result.ledger_namespace === tx.namespace && tx.namespace === tx.coordinate.namespace && result.prior_publication_digest === priorDigest;
    else { const operation = result.to_status === "withdrawn" ? "withdraw" : "revoke"; resultJoin = tx.operation === operation && tx.status_reason_digest === result.reason_digest && result.prior_status_record_digest === priorDigest && result.from_status === priorStatus && eq(prior.coordinate, result.coordinate) && tx.namespace === tx.coordinate.namespace; }
    const markerJoin = marker !== null && embeddedDigestValid(marker) && marker.fsync_complete && marker.journal_digest === subject.publication_journal_digest && marker.transaction_digest === subject.transaction_digest && marker.resulting_record_digest === subject.resulting_record_digest && marker.resulting_ledger_head_digest === subject.resulting_ledger_head_digest && marker.resulting_ledger_revision === subject.resulting_ledger_revision;
    const common = canonicalBefore && transitionExpected && commonResult && resultJoin, committedReplay = subject.state === "committed" && subject.linearized && subject.recovery_action === "none";
    if (committedReplay) {
      const replayState = before.revision === subject.resulting_ledger_revision && before.head === subject.resulting_ledger_head_digest && before.status_record_digest === subject.resulting_record_digest && before.intent_marker_digest === null && marker !== null && before.durable_commit_marker_digest === marker.publication_commit_marker_digest && !before.staging_present;
      return common && intent === null && markerJoin && replayState && eq(after, before) ? null : "recovery_needed";
    }
    if (intent === null) return "self_certification";
    const intentJoin = eq(intent.issuer, { kind: "recovery_controller", id: subject.recovery_controller_id }) && intent.marker_semantics === "non_durable_intent_only" && !intent.fsync_complete && !intent.durable_commit_marker_present
      && intent.journal_digest === subject.publication_journal_digest && intent.transaction_digest === subject.transaction_digest
      && intent.resulting_record_digest === subject.resulting_record_digest && intent.resulting_ledger_head_digest === subject.resulting_ledger_head_digest
      && intent.resulting_ledger_revision === subject.resulting_ledger_revision;
    const activeBefore = before.intent_marker_digest === intent.publication_recovery_intent_marker_digest && before.durable_commit_marker_digest === null && before.staging_present;
    if (!(common && intentJoin && activeBefore)) return "recovery_needed";
    if (!subject.linearized) {
      if (marker !== null || after.revision !== before.revision || after.head !== before.head || after.status_record_digest !== before.status_record_digest || after.intent_marker_digest !== null || after.durable_commit_marker_digest !== null || after.staging_present) return "recovery_needed";
    } else if (!markerJoin || after.revision !== before.revision || after.head !== before.head || after.status_record_digest !== before.status_record_digest || after.revision !== subject.resulting_ledger_revision || after.head !== subject.resulting_ledger_head_digest || after.status_record_digest !== subject.resulting_record_digest || after.intent_marker_digest !== null || marker === null || after.durable_commit_marker_digest !== marker.publication_commit_marker_digest || after.staging_present) return "recovery_needed";
    return null;
  }
  if (rule === "projection") {
    const p = context.projection, capsule = context.capsule, archiveLink = context.archive_linkage, payload = new Map(context.payload_manifest.entries.map((x) => [x.path, x])), consumer = new Map(context.consumer_manifest.entries.map((x) => [x.path, x])), archive = new Map(context.archive_manifest.entries.map((x) => [x.path, x]));
    const src = p.entries.map((x) => x.capsule_path), dst = p.entries.map((x) => x.consumer_path), expectedSrc = new Set([...payload.keys()].map((x) => `${archiveLink.payload_root}/${x}`)); let rowsOk = new Set(src).size === src.length && new Set(dst).size === dst.length && src.length === expectedSrc.size && src.every((x) => expectedSrc.has(x)) && dst.length === consumer.size && dst.every((x) => consumer.has(x));
    for (const row of p.entries) { const relative = row.capsule_path.slice(archiveLink.payload_root.length + 1), pe = payload.get(relative), ce = consumer.get(row.consumer_path), ae = archive.get(row.capsule_path); if (!pe || !ce || !ae || !["kind", "mode", "byte_length", "content_digest"].every((k) => pe[k] === ce[k] && pe[k] === ae[k]) || row.mode !== pe.mode || row.byte_length !== (pe.byte_length ?? null) || row.content_digest !== (pe.content_digest ?? null)) rowsOk = false; }
    const meta = archiveLink.capsule_metadata, metaBytes = Buffer.from(jcs(meta), "utf8"), metaEntry = archive.get(archiveLink.capsule_metadata_path), acyclic = eq(Object.keys(meta).sort(), ["identity_mode", "namespace", "payload_manifest_digest", "schema", "semantic_version"]) && meta.namespace === capsule.namespace && meta.semantic_version === capsule.semantic_version && meta.payload_manifest_digest === capsule.payload_manifest_digest && metaEntry?.content_digest === archiveLink.capsule_metadata_content_digest && archiveLink.capsule_metadata_content_digest === digest("semantic-release.raw-blob.v0", metaBytes) && metaEntry?.byte_length === metaBytes.length;
    const expectedArchivePaths = new Set([archiveLink.capsule_metadata_path, archiveLink.payload_root, ...[...payload.keys()].map((x) => `${archiveLink.payload_root}/${x}`)]), rootEntry = archive.get(archiveLink.payload_root), archiveExact = archive.size === expectedArchivePaths.size && [...archive.keys()].every((x) => expectedArchivePaths.has(x)) && eq(rootEntry, { path: archiveLink.payload_root, kind: "directory", mode: 493 });
    const currentTombstones = context.canonical_lifecycle_tombstone_head, tombstones = context.tombstones;
    const tombstoneCurrent = currentTombstones.namespace === tombstones.namespace && tombstones.namespace === capsule.namespace
      && currentTombstones.lifecycle_head_digest === tombstones.lifecycle_head_digest && tombstones.lifecycle_head_digest === capsule.lifecycle_head_digest
      && currentTombstones.tombstone_registry_digest === tombstones.tombstone_registry_digest && tombstones.tombstone_registry_digest === capsule.tombstone_registry_digest
      && currentTombstones.tombstone_registry_revision === tombstones.registry_revision && tombstones.registry_revision === capsule.tombstone_registry_revision
      && tombstoneHistoryValid(context.tombstone_history, tombstones, context.tombstone_genesis_anchor);
    const capsuleCoordinate = { schema: "semantic-release-coordinate.v0", namespace: capsule.namespace, semantic_version: capsule.semantic_version, capsule_digest: capsule.capsule_digest };
    const valid = rowsOk && acyclic && archiveExact && tombstoneCurrent && eq(subject.coordinate, capsuleCoordinate) && archiveLink.archive_manifest_digest === context.archive_manifest.material_manifest_digest && p.payload_manifest_digest === context.payload_manifest.material_manifest_digest && p.consumer_manifest_digest === context.consumer_manifest.material_manifest_digest && subject.payload_projection_digest === p.payload_projection_digest && p.payload_projection_digest === capsule.payload_projection_digest && subject.capsule_archive_linkage_digest === archiveLink.capsule_archive_linkage_digest && archiveLink.capsule_archive_linkage_digest === capsule.capsule_archive_linkage_digest && subject.source_payload_manifest_digest === p.payload_manifest_digest && subject.expected_consumer_manifest_digest === p.consumer_manifest_digest && p.consumer_manifest_digest === subject.actual_consumer_manifest_digest; return valid ? null : "projection_mismatch";
  }
  if (rule === "rollback") {
    const request = context.request, target = request.target, before = subject.active_state_before, after = subject.active_state_after, activation = context.activation, decision = context.decision;
    const currentDigest = context.current_activation_digest, currentRevision = context.current_activation_revision, canonicalHistory = context.canonical_history_head;
    const activationCurrent = activation.activation_receipt_digest === currentDigest && activation.activation_revision === currentRevision && activation.status === "activated" && activation.revoked_by_digest === null && activation.superseded_by_activation_receipt_digest === null;
    const requestValid = activationCurrent && request.issuer.kind === "consumer_owner" && request.issuer.id === activation.consumer_repository.owner && activation.consumer_repository.owner === context.intent.consumer_repository.owner && eq(request.target, context.intent.rollback_target) && eq(context.intent.rollback_target, context.materialization.rollback_target) && request.active_activation_receipt_digest === currentDigest && request.from_state.enabled && eq(request.from_state.coordinate, activation.coordinate) && eq(request.from_state.runtime_identity, activation.runtime_identity) && request.owner_decision_reference_digest === decision.ak_decision_reference_digest && decisionCurrent(decision, context) && request.recovery_controller_id === context.canonical_recovery_controller_id && request.recovery_epoch === context.canonical_recovery_epoch && eq(request.recovery_runtime_identity, context.canonical_recovery_runtime_identity) && !eq(request.recovery_runtime_identity, request.from_state.runtime_identity); if (!requestValid) return "rollback_unavailable";
    const proof = context.availability;
    if (!proof || !embeddedDigestValid(proof) || subject.availability_proof_digest !== proof.rollback_availability_proof_digest || proof.target_kind !== target.kind || !eq(proof.recovery_runtime_identity, request.recovery_runtime_identity) || !proof.recovery_runtime_available || !rollbackAvailabilityValid(context.intent, context.acceptance, context.materialization, proof, context, target)) return "rollback_unavailable";
    const expectedProof = { semantic_materialization_receipt_digest: null, semantic_coordinate: null, runtime_materialization_receipt_digest: null, runtime_identity: null, runtime_revalidation_receipt_digest: null, disable_contract_digest: null, rehearsal_receipt_digest: null, semantic_target_artifact_digest: null, runtime_target_artifact_digest: null, disable_target_artifact_digest: null, recovery_artifact_digest: context.recovery_artifact.rollback_available_artifact_digest };
    if (["semantic", "combined"].includes(target.kind)) { const st = target.kind === "semantic" ? target : target.semantic_stage; expectedProof.semantic_materialization_receipt_digest = st.target_materialization_receipt_digest; expectedProof.semantic_coordinate = st.target_coordinate; expectedProof.semantic_target_artifact_digest = context.semantic_artifact.rollback_available_artifact_digest; }
    if (["runtime", "combined"].includes(target.kind)) { const rt = target.kind === "runtime" ? target : target.runtime_stage; expectedProof.runtime_materialization_receipt_digest = rt.target_materialization_receipt_digest; expectedProof.runtime_identity = rt.target_runtime_identity; expectedProof.runtime_revalidation_receipt_digest = rt.runtime_revalidation_receipt_digest; expectedProof.runtime_target_artifact_digest = context.runtime_artifact.rollback_available_artifact_digest; }
    if (target.kind === "no_prior_disable") { expectedProof.disable_contract_digest = target.disable_contract_digest; expectedProof.rehearsal_receipt_digest = target.rehearsal_receipt_digest; expectedProof.disable_target_artifact_digest = context.disable_artifact.rollback_available_artifact_digest; }
    if (Object.entries(expectedProof).some(([k, v]) => !eq(proof[k], v))) return "rollback_unavailable";
    const recovery = context.recovery_artifact; let artifactsValid = recovery.artifact_kind === "recovery_runtime" && eq(recovery.runtime_identity, request.recovery_runtime_identity) && recovery.health_receipt_digest !== null && recovery.rehearsal_receipt_digest !== null && recovery.independently_available;
    if (["semantic", "combined"].includes(target.kind)) { const st = target.kind === "semantic" ? target : target.semantic_stage, artifact = context.semantic_artifact; artifactsValid &&= artifact.artifact_kind === "semantic_target" && eq(artifact.coordinate, st.target_coordinate) && artifact.materialization_receipt_digest === st.target_materialization_receipt_digest; }
    if (["runtime", "combined"].includes(target.kind)) { const rt = target.kind === "runtime" ? target : target.runtime_stage, artifact = context.runtime_artifact; artifactsValid &&= artifact.artifact_kind === "runtime_target" && eq(artifact.runtime_identity, rt.target_runtime_identity) && artifact.materialization_receipt_digest === rt.target_materialization_receipt_digest && artifact.runtime_revalidation_receipt_digest === rt.runtime_revalidation_receipt_digest; }
    if (target.kind === "no_prior_disable") { const artifact = context.disable_artifact; artifactsValid &&= artifact.artifact_kind === "disable_target" && artifact.disable_contract_digest === target.disable_contract_digest && artifact.rehearsal_receipt_digest === target.rehearsal_receipt_digest; }
    if (!artifactsValid || !activationChainValid(activation, context)) return "rollback_unavailable";
    if (subject.issuer.id !== subject.recovery_controller_id || subject.recovery_controller_id !== context.canonical_recovery_controller_id || subject.recovery_epoch !== request.recovery_epoch || subject.recovery_epoch !== context.canonical_recovery_epoch || subject.rollback_request_digest !== request.rollback_request_digest || subject.request_target_kind !== target.kind || !eq(before, request.from_state) || !before.enabled || before.coordinate === null || !eq(subject.history_head_before, canonicalHistory)) return "history_conflict";
    let names = { semantic: ["semantic"], runtime: ["runtime"], no_prior_disable: ["disable"] }[target.kind]; if (target.kind === "combined") names = target.stage_order === "semantic_then_runtime" ? ["semantic", "runtime"] : ["runtime", "semantic"];
    if (!eq(subject.stages.map((x) => x.stage), names) || subject.stage_order !== (target.kind === "combined" ? target.stage_order : null) || subject.stages.some((x) => (x.result === "failed") !== (x.error_digest !== null))) return "history_conflict";
    const states = subject.stages.map((x) => x.result), failedIndexes = states.map((x, i) => x === "failed" ? i : -1).filter((x) => x >= 0);
    if (failedIndexes.length > 1 || failedIndexes.length && states.slice(failedIndexes[0] + 1).some((x) => x !== "not_started") || states.includes("not_started") && states.slice(states.indexOf("not_started") + 1).some((x) => x !== "not_started")) return "history_conflict";
    const computed = structuredClone(before); for (const stage of subject.stages) if (stage.result === "completed") { if (stage.stage === "semantic") computed.coordinate = target.kind === "semantic" ? target.target_coordinate : target.semantic_stage.target_coordinate; else if (stage.stage === "runtime") computed.runtime_identity = target.kind === "runtime" ? target.target_runtime_identity : target.runtime_stage.target_runtime_identity; else { computed.enabled = false; computed.coordinate = null; } }
    const failed = subject.stages.filter((x) => x.result === "failed"), completed = subject.stages.filter((x) => x.result === "completed"), failureStage = failed[0]?.stage ?? null, failureError = failed[0]?.error_digest ?? null;
    if (subject.failure_stage !== failureStage || subject.error_digest !== failureError) return "history_conflict";
    if (subject.result === "partial_failure" && (target.kind !== "combined" || !failed.length || !completed.length)) return "history_conflict";
    const runtimeProof = target.kind === "runtime" ? target.runtime_revalidation_receipt_digest : target.runtime_stage?.runtime_revalidation_receipt_digest; if (completed.some((x) => x.stage === "runtime") && subject.runtime_revalidation_receipt_digest !== runtimeProof) return "rollback_unavailable"; if (!completed.some((x) => x.stage === "runtime") && subject.runtime_revalidation_receipt_digest !== null) return "history_conflict";
    if ((subject.ak_evidence_linkage_digest === null) !== (subject.pi_delivery_receipt_digest === null)) return "history_conflict";
    if (subject.ak_evidence_linkage_digest !== null) { const ak = context.ak_linkage, pi = context.pi_receipt; if (!ak || !pi || subject.ak_evidence_linkage_digest !== ak.ak_evidence_linkage_digest || subject.pi_delivery_receipt_digest !== pi.pi_delivery_receipt_digest || ak.pi_delivery_receipt_digest !== subject.pi_delivery_receipt_digest || ak.activation_receipt_digest !== request.active_activation_receipt_digest) return "history_conflict"; }
    if (subject.result === "failed") return failed.length && !completed.length && eq(after, before) && eq(subject.history_head_after, canonicalHistory) && subject.supersedes_activation_receipt_digest === null ? null : "history_conflict";
    if (!eq(after, computed)) return "history_conflict";
    const history = context.history_after, expectedKind = target.kind === "no_prior_disable" ? "disable" : "rollback";
    const historyValid = history && embeddedDigestValid(history) && eq(subject.history_head_after, { kind: expectedKind, digest: history.rollback_history_transition_digest }) && history.rollback_request_digest === request.rollback_request_digest && history.result === subject.result && eq(history.active_state_before, before) && eq(history.active_state_after, after) && eq(history.stages, subject.stages) && history.failure_stage === subject.failure_stage && history.error_digest === subject.error_digest && eq(history.history_head_before, canonicalHistory) && history.supersedes_activation_receipt_digest === subject.supersedes_activation_receipt_digest;
    if (!historyValid) return "history_conflict";
    if (subject.result === "partial_failure") return target.kind === "combined" && failed.length && completed.length && subject.supersedes_activation_receipt_digest === null ? null : "history_conflict";
    const result = target.kind === "no_prior_disable" ? "disabled" : "rolled_back"; let valid = subject.result === result && !failed.length && completed.length === subject.stages.length && subject.supersedes_activation_receipt_digest === currentDigest; if (target.kind === "no_prior_disable") valid &&= eq(after.runtime_identity, before.runtime_identity); return valid ? null : "history_conflict";
  }
  if (rule === "generation_activation") { const a = context.activation, valid = activationChainValid(a, context) && a.activation_receipt_digest === context.current_activation_digest && a.status === "activated" && a.revoked_by_digest === null && a.superseded_by_activation_receipt_digest === null && subject.activation_receipt_digest === subject.activation_head_digest && subject.activation_head_digest === context.current_activation_digest && subject.activation_head_revision === context.current_activation_revision && context.current_activation_revision === a.activation_revision && eq(subject.consumer_repository, a.consumer_repository) && eq(subject.v0_canary_scope, a.canary_scope) && eq(subject.v0_canary_scope.consumer_repository, subject.consumer_repository) && eq(subject.coordinate, a.coordinate) && eq(subject.runtime_identity, a.runtime_identity); return valid ? null : "activation_not_current"; }
  if (rule === "utc") return strictUtc(subject.recorded_at) ? null : "malformed_input";
  if (rule === "ak_decision") return decisionCurrent(subject, context) ? null : "self_certification";
  if (rule === "acceptance_binding") { const d = context.decision, intent = context.intent, valid = subject.consumer_intent_digest === intent.consumer_intent_digest && eq(subject.consumer_repository, intent.consumer_repository) && subject.acceptance_authority.kind === "consumer_owner" && subject.acceptance_authority.id === subject.consumer_repository.owner && subject.decision_reference_digest === intent.decision_reference_digest && subject.decision_reference_digest === d.ak_decision_reference_digest && subject.governing_scope_digest === d.scope_digest && eq(subject.canary_scope, intent.canary_scope) && eq(subject.canary_scope.consumer_repository, subject.consumer_repository) && intent.intent_revision <= subject.valid_through_intent_revision && subject.revoked_by_digest === null && subject.owner_acceptance_digest === context.current_acceptance_digest && subject.acceptance_revision === context.current_acceptance_revision && decisionCurrent(d, context); return valid ? null : "self_certification"; }
  if (rule === "activation_binding") return activationChainValid(subject, context, true) ? null : "self_certification";
  if (rule === "governance_contracts") {
    const consumer = context.consumer_contract, expectedPaths = ["config/semantic-release/canary.json", "docs/project/semantic-release-canary-evidence.md", "scripts/ci/semantic-release-canary.sh"];
    const repos = { ak: { owner: "agent-kernel-owner", repository_id: "agent-kernel", canonical_locator: "local://softwareco/owned/agent-kernel", identity_revision: 9 }, rocs: { owner: "rocs-owner", repository_id: "rocs-cli", canonical_locator: "local://core/rocs-cli", identity_revision: 4 }, owner: { owner: "semantic-owner", repository_id: "ontology-kernel", canonical_locator: "local://core/ontology-kernel", identity_revision: 1 }, consumer: { owner: "consumer-owner", repository_id: "pi-canary-consumer", canonical_locator: "local://softwareco/pi-canary-consumer", identity_revision: 3 } };
    const references = (rows, expected, contractName, group) => { if (!eq(rows.map((x) => x.reference_id), Object.keys(expected).sort())) return false; const stateMap = { accepted_current: "accepted", completed_current: "completed", evidence_accepted_current: "evidence_accepted" }; return rows.every((row) => { const [repoKey, state] = expected[row.reference_id]; if (!eq(row.repository, repos[repoKey]) || row.required_state !== state) return false; if (row.resolution === "unresolved_candidate") return ["ak_store_head", "task_id", "task_record_digest", "artifact_digest", "observed_canonical_state"].every((k) => row[k] === null); if (row.resolution !== "resolved") return false; const observed = row.observed_canonical_state, anchors = context._authority_task_states.filter((anchor) => eq(anchor, observed)); return anchors.length === 1 && eq(observed.repository, row.repository) && eq(observed.ak_store_head, row.ak_store_head) && observed.task_id === row.task_id && observed.task_record_digest === row.task_record_digest && observed.artifact_digest === row.artifact_digest && observed.state === stateMap[state]; }); };
    const stopSet = (contract, expected, contractName) => contract.stop_conditions.length === Object.keys(expected).length && contract.stop_conditions.every((row) => { const x = expected[row.condition_kind]; if (!x) return false; const [cid, factId, repoKey] = x; return row.condition_id === cid && row.fact_reference.reference_id === factId && row.trigger_state === "unsatisfied_or_noncurrent" && row.required_effect === "stop_before_mutation" && row.resume_state === "accepted_current" && references([row.fact_reference], { [factId]: [repoKey, "accepted_current"] }, contractName, "stop"); });
    const akPrereqs = Object.fromEntries(["adr:0053", "decision:53", "plan:decision-53-implementation", "plan:decision-53-validation-rollout-rollback"].map((x) => [x, ["ak", "accepted_current"]]));
    const akEvidence = { "accepted-decision-reference": ["ak", "evidence_accepted_current"], "deterministic-rerun": ["rocs", "evidence_accepted_current"], "docs-strict": ["rocs", "evidence_accepted_current"], "node-validator": ["rocs", "evidence_accepted_current"], "owner-task-references": ["ak", "evidence_accepted_current"], "python-validator": ["rocs", "evidence_accepted_current"], "rollback-rehearsal": ["rocs", "evidence_accepted_current"] };
    const akStops = { stale_or_revoked_decision: ["stale-or-revoked-decision", "fact:stale-or-revoked-decision", "ak"], store_head_drift: ["store-head-drift", "fact:store-head-drift", "ak"], scope_drift: ["scope-drift", "fact:scope-drift", "ak"], missing_owner_task: ["missing-owner-task", "fact:missing-owner-task", "ak"], owner_substitution: ["attempted-owner-substitution", "fact:attempted-owner-substitution", "ak"], authorization_escalation: ["attempted-use-as-authorization", "fact:attempted-use-as-authorization", "ak"] };
    const consumerDependencies = { "candidate-decision-53-ak-coordination": ["ak", "completed_current"], "candidate-decision-53-rocs-implementation": ["rocs", "completed_current"], "candidate-decision-53-semantic-owner-publication": ["owner", "completed_current"] };
    const consumerPrereqs = { "adr:0053": ["ak", "accepted_current"], "consent:pi-canary-consumer-owner": ["consumer", "accepted_current"], "decision:53": ["ak", "accepted_current"], "plan:decision-53-implementation": ["ak", "accepted_current"], "plan:decision-53-validation-rollout-rollback": ["ak", "accepted_current"] };
    const consumerEvidence = { "activation-receipt": ["consumer", "evidence_accepted_current"], "canary-evidence": ["consumer", "evidence_accepted_current"], "consumer-intent-and-acceptance": ["consumer", "evidence_accepted_current"], "exact-materialization-receipt": ["rocs", "evidence_accepted_current"], "rollback-availability-proof": ["rocs", "evidence_accepted_current"], "rollback-history": ["consumer", "evidence_accepted_current"], "rollback-rehearsal": ["rocs", "evidence_accepted_current"], "scoped-gate-decision": ["ak", "evidence_accepted_current"] };
    const consumerStops = { missing_owner_consent: ["missing-owner-consent", "fact:missing-owner-consent", "consumer"], rollback_unavailable: ["target-or-recovery-unavailable", "fact:target-or-recovery-unavailable", "consumer"], stale_semantic_trust_or_ledger: ["stale-semantic-trust-or-ledger", "fact:stale-semantic-trust-or-ledger", "owner"], stale_ak_decision_or_store: ["stale-ak-decision-or-store", "fact:stale-ak-decision-or-store", "ak"], stale_consumer_activation_or_history: ["stale-consumer-activation-or-history", "fact:stale-consumer-activation-or-history", "consumer"], projection_or_issuer_drift: ["projection-or-issuer-drift", "fact:projection-or-issuer-drift", "rocs"], validator_failure: ["failed-validator", "fact:failed-validator", "rocs"], compatibility_failure: ["unknown-or-incompatible", "fact:unknown-or-incompatible", "owner"], missing_rollback_rehearsal: ["missing-rollback-rehearsal", "fact:missing-rollback-rehearsal", "rocs"], protocol_scope_expansion: ["protocol-scope-expansion", "fact:protocol-scope-expansion", "consumer"] };
    const noAuthority = [subject, consumer].every((x) => !x.authorizes_execution && !x.authorizes_publication && !x.authorizes_adoption && x.contract_status === "candidate_not_created");
    const exact = subject.task_contract_id === "decision-53-ak-coordination" && subject.task_id === "candidate-decision-53-ak-coordination" && subject.task_owner_id === subject.rollback_owner.id && subject.task_owner_id === "agent-kernel-owner" && subject.rollback_owner.kind === "ak" && subject.task_kind === "ak_coordination" && eq(subject.repository, repos.ak) && eq(subject.allowed_paths, []) && eq(subject.dependencies, []) && references(subject.prerequisites, akPrereqs, "ak", "prerequisites") && references(subject.required_evidence, akEvidence, "ak", "required_evidence") && stopSet(subject, akStops, "ak") && subject.authority_scope === "coordination_only" && consumer.task_contract_id === "decision-53-single-canary-consumer" && consumer.task_id === "candidate-decision-53-single-canary-consumer" && consumer.task_owner_id === consumer.rollback_owner.id && consumer.task_owner_id === "consumer-owner" && consumer.rollback_owner.kind === "consumer_owner" && consumer.task_kind === "single_canary_consumer" && eq(consumer.repository, repos.consumer) && eq(consumer.allowed_paths, expectedPaths) && references(consumer.dependencies, consumerDependencies, "consumer", "dependencies") && references(consumer.prerequisites, consumerPrereqs, "consumer", "prerequisites") && references(consumer.required_evidence, consumerEvidence, "consumer", "required_evidence") && stopSet(consumer, consumerStops, "consumer") && consumer.authority_scope === "consumer_owner_candidate_only";
    return noAuthority && subject.task_contract_id !== consumer.task_contract_id && exact ? null : "self_certification";
  }
  if (rule === "pi_delivery") { const generation = context.generation; let valid = subject.rocs_generation_receipt_digest === generation.rocs_generation_receipt_digest && eq(subject.consumer_repository, generation.consumer_repository) && eq(subject.v0_canary_scope, generation.v0_canary_scope) && eq(subject.v0_canary_scope.consumer_repository, subject.consumer_repository); if (subject.delivery_outcome === "delivered") valid &&= subject.delivered_effective_execution_digest === generation.effective_execution_digest; return valid ? null : "activation_not_current"; }
  if (rule === "ak_optional_pi") {
    const task = context.canonical_task_states[0], decision = context.decision, activation = context.activation, generation = context.generation, piReceipt = context.pi_receipt;
    const exact = eq(subject.issuer, { kind: "ak", id: pinnedAkRepository.repository_id }) && eq(task.repository, pinnedAkRepository) && eq(decision.ak_repository, pinnedAkRepository)
      && eq(task.ak_store_head, decision.ak_store_head) && task.state === "evidence_accepted" && subject.task_reference_digest === task.task_record_digest
      && subject.decision_reference_digest === decision.ak_decision_reference_digest && subject.evidence_record_digest === task.artifact_digest
      && subject.activation_receipt_digest === activation.activation_receipt_digest && subject.rocs_generation_receipt_digest === generation.rocs_generation_receipt_digest
      && activation.gate_decision_reference_digest === decision.ak_decision_reference_digest && generation.activation_receipt_digest === activation.activation_receipt_digest;
    if (!exact) return "self_certification";
    if (subject.pi_delivery_receipt_digest === null) return piReceipt === null ? null : "self_certification";
    if (piReceipt === null || subject.pi_delivery_receipt_digest !== piReceipt.pi_delivery_receipt_digest || evaluate("pi_delivery", piReceipt, { generation }, true) !== null) return "self_certification";
    return null;
  }
  if (rule === "pi_variant") return null;
  fail(`unknown differential rule ${rule}`);
}

function receiptAuditTuple(receipt) {
  const factValue = structuredClone(receipt.fact_value);
  return {
    receipt_kind: receipt.role.startsWith("vote-proof:") ? "vote" : "store",
    observation_id: receipt.observation_id,
    role: receipt.role,
    owner_repository: structuredClone(receipt.owner_repository),
    store_id: receipt.store_id,
    canonical_store_locator: receipt.canonical_store_locator,
    store_head_digest: receipt.store_head_digest,
    store_revision: receipt.store_revision,
    revocation_head_digest: receipt.revocation_head_digest,
    action_epoch: receipt.action_epoch,
    fact_schema: receipt.fact_schema,
    fact_digest: receipt.fact_digest,
    fact_value: factValue,
    vote_tuple: factValue.kind === "owner_vote_proof" ? structuredClone(factValue.value) : null,
  };
}

function validateReceiptAuditTuple(value, caseName, allowInvalidFactDigest = false) {
  const keys = new Set(["receipt_kind", "observation_id", "role", "owner_repository", "store_id", "canonical_store_locator", "store_head_digest", "store_revision", "revocation_head_digest", "action_epoch", "fact_schema", "fact_digest", "fact_value", "vote_tuple"]);
  if (!value || typeof value !== "object" || Array.isArray(value) || !setEqual(new Set(Object.keys(value)), keys) || !["store", "vote"].includes(value.receipt_kind)) fail(`source-case receipt tuple shape ${caseName}`);
  structural(value.owner_repository, schema.$defs.repositoryIdentity);
  structural(value.fact_value, schema.$defs.authorityFactValue);
  if (typeof value.observation_id !== "string" || value.observation_id.length === 0
    || typeof value.role !== "string" || value.role.length === 0
    || typeof value.store_id !== "string" || value.store_id.length === 0
    || typeof value.canonical_store_locator !== "string" || value.canonical_store_locator.length === 0
    || value.revocation_head_digest !== null && !/^sha256:[0-9a-f]{64}$/u.test(value.revocation_head_digest)
    || !/^sha256:[0-9a-f]{64}$/u.test(value.store_head_digest)
    || !Number.isSafeInteger(value.store_revision) || value.store_revision < 0
    || !Number.isSafeInteger(value.action_epoch) || value.action_epoch < 0
    || !/^sha256:[0-9a-f]{64}$/u.test(value.fact_digest)
    || !allowInvalidFactDigest && value.fact_digest !== authorityFactDigest(value.fact_schema, value.fact_value)) fail(`source-case receipt tuple value ${caseName}:${value.role}`);
  const expectedVote = value.receipt_kind === "vote" ? decodeAuthorityFact(value.fact_value) : null;
  if (!eq(value.vote_tuple, expectedVote) || (value.receipt_kind === "vote") !== value.role.startsWith("vote-proof:")) fail(`source-case vote tuple ${caseName}:${value.role}`);
}

function validateSourceCaseExplicitnessAudit(cases, registryRows) {
  const audit = differential.source_case_explicitness_audit;
  const topKeys = new Set(["schema", "revision", "inference_policy", "source_case_count", "authority_case_count", "store_metadata_tuple_count", "vote_proof_fact_count", "final_receipt_count", "registered_mutation_count", "registered_receipt_mutations", "cases", "source_case_explicitness_audit_digest"]);
  if (!audit || !setEqual(new Set(Object.keys(audit)), topKeys)) fail("source-case explicitness audit shape");
  const preimage = structuredClone(audit); delete preimage.source_case_explicitness_audit_digest;
  if (audit.schema !== "semantic-release-source-case-explicitness-audit.v13"
    || audit.revision !== "semantic-release-revision-v13"
    || audit.inference_policy !== "explicit_source_and_expected_final_receipts_no_silent_mismatch"
    || audit.source_case_explicitness_audit_digest !== typedDigest("semantic-release.source-case-explicitness-audit.v13", preimage)
    || audit.source_case_explicitness_audit_digest !== expectedSourceAuditDigest) fail("source-case explicitness audit digest/policy");
  const byteSort = (a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b));
  const jcsSort = (a, b) => byteSort(jcs(a), jcs(b));
  const caseByName = new Map(cases.map((item) => [item.name, item]));
  const edgeById = new Map(registryRows.map((row) => [row.edge_id, row]));
  const expectedNames = [...caseByName.keys()].sort(byteSort);
  if (!Array.isArray(audit.cases) || !eq(audit.cases.map((row) => row.case_name), expectedNames) || audit.cases.length !== caseByName.size) fail("source-case explicitness audit case coverage/order");
  const mutationRows = audit.registered_receipt_mutations;
  if (!Array.isArray(mutationRows)
    || !eq(mutationRows.map((row) => row.mutation_id), mutationRows.map((row) => row.mutation_id).sort(byteSort))
    || new Set(mutationRows.map((row) => row.mutation_id)).size !== mutationRows.length) fail("registered source mutation order");
  const mutationById = new Map();
  const mutationKeys = new Set(["case_name", "mutation_id", "mode", "descriptor_edge_ids", "source_receipt_tuples", "expected_final_receipt_tuples"]);
  for (const mutation of mutationRows) {
    if (!setEqual(new Set(Object.keys(mutation)), mutationKeys)) fail("registered source mutation shape");
    if (!["add", "replace"].includes(mutation.mode) || !sortedUnique(mutation.descriptor_edge_ids)) fail(`registered source mutation mode/linkage ${mutation.mutation_id}`);
    const item = caseByName.get(mutation.case_name);
    if (!item || item.expected_error === null || mutation.source_receipt_tuples.length !== mutation.expected_final_receipt_tuples.length) fail(`registered source mutation identity ${mutation.mutation_id}`);
    for (const edgeId of mutation.descriptor_edge_ids) {
      const edge = edgeById.get(edgeId);
      if (!edge || edge.drift_fixture !== mutation.case_name || edge.semantic_mutations.length === 0) fail(`registered source mutation descriptor linkage ${mutation.mutation_id}:${edgeId}`);
    }
    for (const value of mutation.source_receipt_tuples) validateReceiptAuditTuple(value, mutation.case_name);
    for (const value of mutation.expected_final_receipt_tuples) validateReceiptAuditTuple(value, mutation.case_name, true);
    mutationById.set(mutation.mutation_id, mutation);
  }
  let storeCount = 0, voteCount = 0, authorityCount = 0, finalCount = 0;
  const rowKeys = new Set(["case_name", "rule", "source_receipts", "expected_final_receipts", "registered_mutation_ids"]);
  for (const row of audit.cases) {
    deadlineCheck(`before source-audit case ${row?.case_name}`);
    if (!setEqual(new Set(Object.keys(row)), rowKeys)) fail("source-case audit row shape");
    const item = caseByName.get(row.case_name); if (!item || row.rule !== item.rule) fail(`source-case audit identity ${row.case_name}`);
    if (authorityBearingRules.has(item.rule)) authorityCount++;
    const sourceReceipts = row.source_receipts, expectedFinal = row.expected_final_receipts;
    if (!eq(sourceReceipts, [...sourceReceipts].sort(jcsSort)) || !eq(expectedFinal, [...expectedFinal].sort(jcsSort)) || !sortedUnique(row.registered_mutation_ids)) fail(`source-case receipt tuple order ${item.name}`);
    for (const value of sourceReceipts) validateReceiptAuditTuple(value, item.name);
    for (const value of expectedFinal) validateReceiptAuditTuple(value, item.name, true);
    const graph = item.context, verifier = graph.verifier_input;
    const nodeByKey = new Map(graph.proof_bundle.nodes.map((node) => [node.bundle_key, node.artifact]));
    const nodeArtifacts = new Map(verifier.node_bindings.filter((binding) => nodeByKey.has(binding.bundle_key)).map((binding) => [binding.role, nodeByKey.get(binding.bundle_key)]));
    const expectedVotes = voteRules.has(item.rule) ? expectedVoteReceipts(item.subject, nodeArtifacts) : new Map();
    const expectedStoreRoles = new Set(requiredReceiptRoles[item.rule] ?? []); for (const role of missingAnchorNegatives.get(item.name) ?? []) expectedStoreRoles.delete(role);
    const sourceStore = sourceReceipts.filter((value) => value.receipt_kind === "store"), sourceVotes = sourceReceipts.filter((value) => value.receipt_kind === "vote");
    if (!setEqual(new Set(sourceStore.map((value) => value.role)), expectedStoreRoles) || sourceStore.length !== expectedStoreRoles.size
      || !setEqual(new Set(sourceVotes.map((value) => value.role)), new Set(expectedVotes.keys())) || sourceVotes.length !== expectedVotes.size) fail(`source-case explicit role coverage ${item.name}`);
    const ruleManifest = authorityManifestByRule.get(item.rule);
    for (const value of sourceReceipts) {
      const mapping = manifestMapping(ruleManifest, value.role);
      if (!eq(value.owner_repository, mapping.owner_repository) || value.action_epoch !== 100) fail(`source-case source tuple owner/epoch ${item.name}:${value.role}`);
      if (value.observation_id !== `receipt:${item.rule}:${value.role}`) fail(`source-case source observation ${item.name}:${value.role}`);
    }
    for (const value of sourceVotes) if (!eq(value.vote_tuple, expectedVotes.get(value.role))) fail(`source-case explicit vote fact drift ${item.name}:${value.role}`);
    const mutations = row.registered_mutation_ids.map((id) => mutationById.get(id));
    if (mutations.some((mutation) => !mutation || mutation.case_name !== item.name)) fail(`source-case mutation linkage ${item.name}`);
    const reconstructed = structuredClone(sourceReceipts);
    for (const mutation of mutations) {
      for (let index = 0; index < mutation.source_receipt_tuples.length; index++) {
        const sourceTuple = mutation.source_receipt_tuples[index], finalTuple = mutation.expected_final_receipt_tuples[index];
        const sourceIndex = reconstructed.findIndex((value) => eq(value, sourceTuple));
        if (!sourceReceipts.some((value) => eq(value, sourceTuple)) || mutation.mode === "replace" && sourceIndex < 0) fail(`source-case mutation source tuple ${item.name}`);
        if (mutation.mode === "replace") reconstructed.splice(sourceIndex, 1);
        reconstructed.push(structuredClone(finalTuple));
      }
    }
    reconstructed.sort(jcsSort);
    if (!eq(reconstructed, expectedFinal)) fail(`source-case expected-final reconstruction ${item.name}`);
    const actualFinal = graph.authority_snapshot.store_read_receipts.map(receiptAuditTuple).sort(jcsSort);
    if (!eq(actualFinal, expectedFinal)) fail(`source-case final receipt mismatch ${item.name}`);
    storeCount += sourceStore.length; voteCount += sourceVotes.length; finalCount += actualFinal.length;
    deadlineCheck(`after source-audit case ${item.name}`);
  }
  const usedMutations = audit.cases.flatMap((row) => row.registered_mutation_ids);
  if (usedMutations.length !== new Set(usedMutations).size || !setEqual(new Set(usedMutations), new Set(mutationById.keys()))) fail("registered source mutation bijection");
  if (audit.source_case_count !== audit.cases.length || audit.authority_case_count !== authorityCount
    || audit.store_metadata_tuple_count !== storeCount || audit.vote_proof_fact_count !== voteCount
    || audit.final_receipt_count !== finalCount || audit.registered_mutation_count !== mutationRows.length) fail("source-case explicitness audit counters");
  return [storeCount, voteCount, finalCount, mutationRows.length];
}

validateIjson(schema); validateIjson(golden); validateIjson(differential);
if (schema.$schema !== "https://json-schema.org/draft/2020-12/schema") fail("wrong schema draft");
(function closed(node, path = "$") { if (Array.isArray(node)) return node.forEach((x, i) => closed(x, `${path}/${i}`)); if (node && typeof node === "object") { if (node.type === "object" && node.additionalProperties !== false) fail(`open object ${path}`); if (node.$ref) resolve(node.$ref); Object.entries(node).forEach(([k, v]) => closed(v, `${path}/${k}`)); } })(schema);
authorityManifest = differential.authority_rule_role_manifest;

function mutationFactValue(value) { if (value.kind === "null") return null; if (value.kind === "empty_list") return []; if (value.kind === "empty_map") return Object.create(null); return structuredClone(value.value); }
function semanticAuthorityView(item) {
  const graph = item.context, config = graph.acquisition_config, snapshot = graph.authority_snapshot, bundle = graph.proof_bundle, verifier = graph.verifier_input;
  const context = { acquisition: { verifier_identity: structuredClone(config.verifier_identity), collator: structuredClone(config.collator), collation_scope: config.collation_scope, required_action_epoch_floor: config.required_action_epoch_floor, live_acquisition_implemented: config.live_acquisition_implemented, action_epoch: snapshot.action_epoch }, receipts: Object.create(null), nodes: Object.create(null), parameters: Object.create(null), unbound_pins: [], unbound_receipts: [], unbound_nodes: [] };
  const pinsUsed = new Set(), receiptsUsed = new Set(), nodesUsed = new Set();
  for (const binding of verifier.receipt_bindings) {
    const pinCandidates = [], receiptCandidates = [];
    config.pins.forEach((row, index) => { if (row.capability_pin_id === binding.capability_pin_id) { pinCandidates.push(structuredClone(row)); pinsUsed.add(index); } });
    snapshot.store_read_receipts.forEach((row, index) => { if (row.observation_id === binding.observation_id) { receiptCandidates.push(structuredClone(row)); receiptsUsed.add(index); } });
    context.receipts[binding.role] = { binding: structuredClone(binding), pin_candidates: pinCandidates, receipt_candidates: receiptCandidates };
  }
  context.unbound_pins = config.pins.filter((_, index) => !pinsUsed.has(index)).map((row) => structuredClone(row));
  context.unbound_receipts = snapshot.store_read_receipts.filter((_, index) => !receiptsUsed.has(index)).map((row) => structuredClone(row));
  for (const binding of verifier.node_bindings) {
    const candidates = [];
    bundle.nodes.forEach((row, index) => { if (row.bundle_key === binding.bundle_key) { const copy = structuredClone(row); delete copy.bundle_key; candidates.push(copy); nodesUsed.add(index); } });
    const cleanBinding = structuredClone(binding); delete cleanBinding.bundle_key;
    context.nodes[binding.role] = { binding: cleanBinding, node_candidates: candidates };
  }
  context.unbound_nodes = bundle.nodes.filter((_, index) => !nodesUsed.has(index)).map((row) => { const copy = structuredClone(row); delete copy.bundle_key; return copy; });
  for (const binding of verifier.parameter_bindings) context.parameters[binding.role] = mutationFactValue(binding.value);
  return { rule: item.rule, subject: structuredClone(item.subject), context };
}
function collectDigestCorrespondence(oldValue, newValue, path, pairs) {
  if (oldValue !== null && newValue !== null && typeof oldValue === "object" && typeof newValue === "object" && !Array.isArray(oldValue) && !Array.isArray(newValue)) {
    const oldSchema = oldValue.schema, newSchema = newValue.schema;
    if (oldSchema === newSchema && Object.hasOwn(digestFields, oldSchema)) { const field = digestFields[oldSchema][1]; if (typeof oldValue[field] === "string" && typeof newValue[field] === "string") pairs.push([oldValue[field], newValue[field], path || "/"]); }
    for (const field of ["action_digest", "change_digest", "fact_digest", "freshness_cas_token_digest"]) if (typeof oldValue[field] === "string" && typeof newValue[field] === "string") pairs.push([oldValue[field], newValue[field], `${path || "/"}/${field}`]);
    for (const key of Object.keys(oldValue).filter((key) => Object.hasOwn(newValue, key))) collectDigestCorrespondence(oldValue[key], newValue[key], `${path}/${key.replaceAll("~", "~0").replaceAll("/", "~1")}`, pairs);
  } else if (Array.isArray(oldValue) && Array.isArray(newValue)) for (let index = 0; index < Math.min(oldValue.length, newValue.length); index++) collectDigestCorrespondence(oldValue[index], newValue[index], `${path}/${index}`, pairs);
}
function stripDigestCascade(value, references) {
  if (typeof value === "string") return references.get(value) ?? value;
  if (Array.isArray(value)) return value.map((row) => stripDigestCascade(row, references));
  if (value !== null && typeof value === "object") { const result = Object.create(null), selfField = Object.hasOwn(digestFields, value.schema) ? digestFields[value.schema][1] : null; for (const [key, row] of Object.entries(value)) if (key !== selfField && key !== "fact_digest" && key !== "freshness_cas_token_digest") result[key] = stripDigestCascade(row, references); return result; }
  return value;
}
function normalizedSemanticPair(positive, driftCase) {
  const oldValue = semanticAuthorityView(positive), newValue = semanticAuthorityView(driftCase), pairs = []; collectDigestCorrespondence(oldValue, newValue, "", pairs); const references = new Map();
  for (const [oldDigest, newDigest, path] of pairs) { const stable = `semantic-ref:${typedDigest("semantic-release.semantic-reference-path.v13", path)}`; if (!references.has(oldDigest) || stable < references.get(oldDigest)) references.set(oldDigest, stable); if (!references.has(newDigest) || stable < references.get(newDigest)) references.set(newDigest, stable); }
  return [stripDigestCascade(oldValue, references), stripDigestCascade(newValue, references)];
}
const mutationMissing = Symbol("missing");
function mutationHash(value) { const payload = { present: value !== mutationMissing }; if (value !== mutationMissing) payload.value = value; return typedDigest("semantic-release.semantic-mutation-value.v13", payload); }
function semanticDiff(oldValue, newValue, path, rows) {
  if (oldValue !== mutationMissing && newValue !== mutationMissing && oldValue !== null && newValue !== null && typeof oldValue === "object" && typeof newValue === "object" && !Array.isArray(oldValue) && !Array.isArray(newValue)) {
    const keys = [...new Set([...Object.keys(oldValue), ...Object.keys(newValue)])].sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b))); for (const key of keys) semanticDiff(Object.hasOwn(oldValue, key) ? oldValue[key] : mutationMissing, Object.hasOwn(newValue, key) ? newValue[key] : mutationMissing, `${path}/${key.replaceAll("~", "~0").replaceAll("/", "~1")}`, rows); return;
  }
  if (Array.isArray(oldValue) && Array.isArray(newValue)) { for (let index = 0; index < Math.max(oldValue.length, newValue.length); index++) semanticDiff(index < oldValue.length ? oldValue[index] : mutationMissing, index < newValue.length ? newValue[index] : mutationMissing, `${path}/${index}`, rows); return; }
  if (oldValue !== mutationMissing && newValue !== mutationMissing && typeof oldValue === typeof newValue && eq(oldValue, newValue)) return;
  rows.push({ path: path || "/", old_semantic_hash: mutationHash(oldValue), new_semantic_hash: mutationHash(newValue) });
}
function semanticMutationDescriptors(positive, driftCase) { const [oldValue, newValue] = normalizedSemanticPair(positive, driftCase), rows = []; semanticDiff(oldValue, newValue, "", rows); return rows.sort((a, b) => Buffer.compare(Buffer.from(a.path), Buffer.from(b.path))); }
function descriptorRoleIds(descriptors) { const roles = new Set(); for (const row of descriptors) { const parts = row.path.split("/"); if (parts[1] === "subject") roles.add("subject"); else if (parts.length > 3 && parts[1] === "context" && ["receipts", "nodes", "parameters"].includes(parts[2])) { const role = parts[3].replaceAll("~1", "/").replaceAll("~0", "~"); roles.add(role === "surplus-role" ? "authority_graph" : role); } else roles.add("authority_graph"); } return [...roles].sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b))); }

function derivedEdgeRoleOwner(item, role) {
  const ruleRow = authorityManifestByRule.get(item.rule), mapping = manifestMapping(ruleRow, role), verifier = item.context.verifier_input;
  let owner;
  if (role === "subject") { if (!mapping.expected_schemas.includes(item.subject.schema) || !eq(mapping.sources, ["subject"])) fail(`edge subject mapping drift ${item.name}`); const [issuer, , repository] = proofAuthority(item.rule, role, item.subject, item.subject.schema); owner = { owner_surface: issuer.kind, owner_id: issuer.id, owner_repository: repository }; }
  else if (role === "authority_graph") owner = { owner_surface: mapping.owner_surface, owner_id: mapping.owner_id, owner_repository: mapping.owner_repository };
  else {
    const receiptMatches = verifier.receipt_bindings.filter((row) => row.role === role), nodeMatches = verifier.node_bindings.filter((row) => row.role === role);
    if (receiptMatches.length) { if (receiptMatches.length !== 1) fail(`edge receipt role ambiguity ${item.name}:${role}`); const row = receiptMatches[0]; owner = { owner_surface: row.owner_surface, owner_id: row.owner_id, owner_repository: row.owner_repository }; }
    else if (nodeMatches.length) { if (nodeMatches.length !== 1) fail(`edge node role ambiguity ${item.name}:${role}`); const row = nodeMatches[0]; owner = { owner_surface: row.expected_issuer_kind, owner_id: row.expected_issuer_id, owner_repository: row.expected_owner_repository }; }
    else { const ownerId = mapping.owner_id === null && mapping.role_prefix === "vote-proof:" ? role.slice(role.lastIndexOf(":") + 1) : mapping.owner_id; owner = { owner_surface: mapping.owner_surface, owner_id: ownerId, owner_repository: mapping.owner_repository }; }
  }
  if (owner.owner_surface === null || owner.owner_id === null || owner.owner_repository === null) fail(`edge role owner unresolved ${item.name}:${role}`);
  return structuredClone(owner);
}

structural(authorityManifest, schema); checkOrder(authorityManifest); if (!embeddedDigestValid(authorityManifest) || authorityManifest.authority_rule_role_manifest_digest !== expectedAuthorityManifestDigest) fail("authority manifest full-tuple digest drift");
if (!setEqual(new Set(authorityManifest.rules.map((row) => row.rule)), allRules) || authorityManifest.rules.length !== allRules.size) fail("authority manifest rule coverage drift");
if (!setEqual(new Set(authorityManifest.rules.filter((row) => row.authority_bearing).map((row) => row.rule)), authorityBearingRules)) fail("authority-bearing rule classification drift");
authorityManifestByRule = new Map(authorityManifest.rules.map((row) => [row.rule, row]));
if (golden.protocol !== "semantic-release-v0" || golden.rfc_revision !== "semantic-release-revision-v13") fail("golden fixture revision drift");
const registry = differential.authority_edge_registry, registryKeys = new Set(["edge_id", "rule", "description", "ownership", "role_owners", "role_ids", "positive_fixture", "drift_fixture", "expected_error", "semantic_mutations", "edge_linkage_digest"]), mutationKeys = new Set(["path", "old_semantic_hash", "new_semantic_hash"]);
if (!Array.isArray(registry) || registry.length !== expectedAuthorityEdgeCount) fail("authority edge registry cardinality drift");
if (!sortedUnique(registry.map((row) => row.edge_id)) || typedDigest("semantic-release.authority-edge-registry.v13", registry) !== expectedAuthorityRegistryDigest) fail("authority edge registry full-tuple identity/order drift");
const registryIds = new Set(registry.map((row) => row.edge_id)), registryById = new Map(registry.map((row) => [row.edge_id, row])), manifestEdgeIds = [];
for (const row of registry) {
  if (!setEqual(new Set(Object.keys(row)), registryKeys) || !authorityBearingRules.has(row.rule)) fail(`authority edge tuple drift ${row.edge_id}`);
  if (!sortedUnique(row.role_ids)) fail(`authority edge role linkage order ${row.edge_id}`);
  if (!eq(row.role_owners.map((item) => item.role), row.role_ids) || row.role_owners.some((item) => !setEqual(new Set(Object.keys(item)), new Set(["role", "owner"])))) fail(`authority edge role owner coverage ${row.edge_id}`);
  for (const item of row.role_owners) structural(item.owner, schema.$defs.authorityOwnerTuple);
  const ownersByJcs = new Map(row.role_owners.map((item) => [jcs(item.owner), item.owner])), expectedOwners = [...ownersByJcs].sort((a, b) => Buffer.compare(Buffer.from(a[0]), Buffer.from(b[0]))).map((item) => item[1]), expectedKind = expectedOwners.length === 1 ? "single_owner" : "multi_owner";
  if (!eq(row.ownership, { kind: expectedKind, owners: expectedOwners }) || expectedKind === "multi_owner" && expectedOwners.length < 2) fail(`authority edge closed ownership tuple ${row.edge_id}`);
  if (!Array.isArray(row.semantic_mutations) || row.semantic_mutations.length === 0 || !sortedUnique(row.semantic_mutations.map((item) => item.path)) || row.semantic_mutations.some((item) => !setEqual(new Set(Object.keys(item)), mutationKeys) || !/^sha256:[0-9a-f]{64}$/u.test(item.old_semantic_hash) || !/^sha256:[0-9a-f]{64}$/u.test(item.new_semantic_hash))) fail(`authority semantic mutation descriptor shape ${row.edge_id}`);
  const linkage = { edge_id: row.edge_id, rule: row.rule, ownership: row.ownership, role_owners: row.role_owners, role_ids: row.role_ids, positive_fixture: row.positive_fixture, drift_fixture: row.drift_fixture, expected_error: row.expected_error };
  if (row.edge_linkage_digest !== typedDigest("semantic-release.authority-edge-linkage.v13", linkage)) fail(`authority edge linkage digest ${row.edge_id}`);
}
for (const ruleRow of authorityManifest.rules) {
  if ((ruleRow.edge_ids.length > 0) !== ruleRow.authority_bearing) fail(`authority manifest edge coverage ${ruleRow.rule}`);
  if (!eq(ruleRow.role_edge_links.map((link) => link.edge_id), ruleRow.edge_ids)) fail(`authority role/edge order ${ruleRow.rule}`);
  for (const mapping of ruleRow.role_mappings) { const acquisition = [mapping.acquisition_contract, mapping.acquisition_contract_digest, mapping.acquisition_distribution_digest, mapping.acquisition_capability_digest]; if (eq(mapping.sources, ["receipt"]) ? acquisition.some((value) => value === null) : acquisition.some((value) => value !== null)) fail(`manifest acquisition tuple ${ruleRow.rule}:${mapping.role}`); }
  for (const link of ruleRow.role_edge_links) {
    const edge = registryById.get(link.edge_id), expectedLink = edge ? { edge_id: edge.edge_id, ownership: edge.ownership, role_owners: edge.role_owners, role_ids: edge.role_ids, edge_linkage_digest: edge.edge_linkage_digest } : null;
    if (!edge || edge.rule !== ruleRow.rule || !eq(link, expectedLink)) fail(`manifest/registry full owner linkage ${link.edge_id}`);
    for (const roleOwner of link.role_owners) {
      const role = roleOwner.role, matches = ruleRow.role_mappings.filter((mapping) => mapping.role_prefix === null ? mapping.role === role : role.startsWith(mapping.role_prefix));
      if (matches.length !== 1) fail(`manifest role/edge linkage ${link.edge_id}:${role}`);
      const mapping = matches[0], expectedOwnerId = mapping.owner_id === null && mapping.role_prefix === "vote-proof:" ? role.slice(role.lastIndexOf(":") + 1) : mapping.owner_id;
      const expectedOwner = { owner_surface: mapping.owner_surface, owner_id: expectedOwnerId, owner_repository: mapping.owner_repository };
      if (expectedOwner.owner_surface === null || expectedOwner.owner_id === null || expectedOwner.owner_repository === null || !eq(roleOwner.owner, expectedOwner)) fail(`manifest mechanically derived edge owner ${link.edge_id}:${role}`);
    }
    manifestEdgeIds.push(link.edge_id);
  }
}
if (new Set(manifestEdgeIds).size !== manifestEdgeIds.length || !setEqual(new Set(manifestEdgeIds), registryIds)) fail("manifest/registry edge bijection drift");
const records = new Map();
for (const record of golden.records) {
  if (records.has(record.name)) fail(`duplicate record ${record.name}`); structural(record.instance, schema); checkOrder(record.instance); checkClaimScope(record.instance);
  const [domain, omitted] = record.instance.schema === "semantic-release-coordinate.v0" ? [coordinateDomain, null] : digestFields[record.instance.schema];
  if (record.domain !== domain || record.omitted_field !== omitted) fail(`${record.name}: fixture digest metadata drift`);
  const [canonical, computed] = objectDigest(record.instance, domain, omitted); if (canonical !== record.canonical_preimage || computed !== record.digest || omitted !== null && record.instance[omitted] !== computed) fail(`${record.name}: digest mismatch`);
  if (record.instance.schema === "semantic-audit-envelope.v0" && !strictUtc(record.instance.recorded_at)) fail("invalid golden UTC"); records.set(record.name, record);
}
for (const raw of golden.raw_preimages) if (digest(raw.domain, Buffer.from(raw.preimage_utf8, "utf8")) !== raw.digest) fail(`${raw.name}: raw digest`);
for (const assertion of golden.chain_assertions) if (pointer(records.get(assertion.record).instance, assertion.instance_path) !== records.get(assertion.equals_record).digest) fail(`chain ${assertion.record}`);
const [sourceStoreCount, sourceVoteCount, finalReceiptCount, sourceMutationCount] = validateSourceCaseExplicitnessAudit(differential.cases, registry);
let accepted = 0, rejected = 0; const caseResults = new Map(), caseByName = new Map();
for (const item of differential.cases) {
  deadlineCheck(`before differential case ${item?.name}`);
  let valid = true; try { structural(item.subject, schema); } catch { valid = false; }
  if (valid !== item.schema_valid) fail(`${item.name}: schema_valid expected ${item.schema_valid}, got ${valid}`);
  if (item.rule !== "digest" && !embeddedDigestValid(item.subject)) fail(`${item.name}: masked by digest`);
  let actual = valid ? null : item.expected_error;
  if (valid) { try { checkClaimScope(item.subject); } catch { actual = "issuer_scope_violation"; } if (actual === null) actual = evaluate(item.rule, item.subject, item.context); }
  if (actual === null) { try { checkOrder(item.subject); } catch { actual = "malformed_input"; } }
  if (actual !== item.expected_error) fail(`${item.name}: expected ${item.expected_error}, got ${actual}`); if (caseResults.has(item.name)) fail(`duplicate differential case ${item.name}`); caseResults.set(item.name, actual); caseByName.set(item.name, item); actual === null ? accepted++ : rejected++; deadlineCheck(`after differential case ${item.name}`);
}
for (const row of registry) {
  deadlineCheck(`before authority edge case ${row?.edge_id}`);
  if (caseResults.get(row.positive_fixture) !== null || caseResults.get(row.drift_fixture) !== row.expected_error) fail(`authority edge fixture outcome drift ${row.edge_id}`);
  if (!caseByName.has(row.positive_fixture) || !caseByName.has(row.drift_fixture)) fail(`authority edge fixture missing ${row.edge_id}`);
  const recomputed = semanticMutationDescriptors(caseByName.get(row.positive_fixture), caseByName.get(row.drift_fixture));
  if (!eq(recomputed, row.semantic_mutations)) fail(`authority semantic mutation descriptor mismatch ${row.edge_id}`);
  if (!eq(descriptorRoleIds(recomputed), row.role_ids)) fail(`authority mutation role linkage mismatch ${row.edge_id}`);
  const roleOwners = row.role_ids.map((role) => ({ role, owner: derivedEdgeRoleOwner(caseByName.get(row.positive_fixture), role) }));
  const ownersByJcs = new Map(roleOwners.map((item) => [jcs(item.owner), item.owner])), owners = [...ownersByJcs].sort((a, b) => Buffer.compare(Buffer.from(a[0]), Buffer.from(b[0]))).map((item) => item[1]), ownership = { kind: owners.length === 1 ? "single_owner" : "multi_owner", owners };
  if (!eq(row.role_owners, roleOwners) || !eq(row.ownership, ownership)) fail(`authority edge owner not derived from concrete roles ${row.edge_id}`);
  deadlineCheck(`after authority edge case ${row.edge_id}`);
}
let rawAccepted = 0, rawRejected = 0;
for (const item of differential.raw_json_cases) { deadlineCheck(`before raw JSON case ${item?.name}`); let actual = null; try { const parsed = strictJson(item.raw_json); if ((item.required_own_keys ?? []).some((key) => !Object.hasOwn(parsed, key))) actual = "malformed_input"; } catch { actual = "malformed_input"; } if (actual !== item.expected_error) fail(`${item.name}: expected ${item.expected_error}, got ${actual}`); actual === null ? rawAccepted++ : rawRejected++; deadlineCheck(`after raw JSON case ${item.name}`); }
console.log(`schema: Draft 2020-12, ${schema.oneOf.length} protocol types, all object shapes closed`);
console.log(`golden: ${records.size} object preimages and ${golden.raw_preimages.length} raw preimages independently recomputed`);
console.log(`chain: ${golden.chain_assertions.length} exact digest links verified`);
const roleCount = authorityManifest.rules.reduce((total, row) => total + row.role_mappings.length, 0);
console.log(`authority manifest: ${authorityManifest.rules.length} rules (${authorityBearingRules.size} authority-bearing), ${roleCount} role mappings; registry bijection complete`);
console.log(`authority graph: ${registry.length} full owner/repository/linkage edges; normalized semantic-mutation descriptors independently recomputed`);
console.log(`shards: ${shardInventory.length} files, ${shardInventory.reduce((total, row) => total + row.byte_length, 0)} bytes, aggregate sha256:${shardAggregateSha256}`);
console.log(`transport: ${totalJsonBytes} aggregate JSON bytes; ${transportCaseCount} closed overflow cases evaluated; monotonic deadline enforced`);
console.log(`source-case audit: ${differential.cases.length} cases, ${sourceStoreCount} explicit store tuples, ${sourceVoteCount} explicit vote facts, ${finalReceiptCount} exact final receipts, ${sourceMutationCount} registered mutations; no silent mismatch`);
console.log(`differential: ${differential.cases.length} cases (${accepted} accepted transitions, ${rejected} expected rejections)`);
console.log(`raw-json: ${differential.raw_json_cases.length} lexical cases (${rawAccepted} accepted, ${rawRejected} expected rejections)`);
console.log("result: PASS (independent Node token-aware verifier; no Python imports or subprocesses)");
