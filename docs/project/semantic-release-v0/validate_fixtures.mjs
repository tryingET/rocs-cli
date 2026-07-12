#!/usr/bin/env node
/** Independent Node verifier: no Python imports, subprocesses, or shared code. */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const fail = (message) => { throw new Error(message); };
const load = (name) => JSON.parse(readFileSync(join(root, name), "utf8"));
const schema = load("protocol.schema.json");
const golden = load("golden-fixtures.json");
const differential = load("differential-fixtures.json");
const coordinateDomain = "semantic-release.coordinate.v0";
const rows = {
  "semantic-source-manifest.v0": ["source-manifest", "source_manifest_digest"],
  "semantic-material-manifest.v0": ["material-manifest", "material_manifest_digest"],
  "semantic-owner-set.v0": ["owner-set", "owner_set_digest"],
  "semantic-approval-predicate.v0": ["approval-predicate", "approval_predicate_digest"],
  "semantic-owner-policy.v0": ["owner-policy", "owner_policy_digest"],
  "semantic-trust-root.v0": ["trust-root", "trust_root_digest"],
  "semantic-trust-rotation.v0": ["trust-rotation", "trust_rotation_digest"],
  "semantic-trust-revocation.v0": ["trust-revocation", "trust_revocation_digest"],
  "semantic-compatibility-policy.v0": ["compatibility-policy", "compatibility_policy_digest"],
  "semantic-compatibility-report.v0": ["compatibility-report", "compatibility_report_digest"],
  "semantic-compatibility-override.v0": ["compatibility-override", "compatibility_override_digest"],
  "semantic-deprecation-record.v0": ["deprecation-record", "deprecation_record_digest"],
  "semantic-removal-record.v0": ["removal-record", "removal_record_digest"],
  "semantic-tombstone-registry.v0": ["tombstone-registry", "tombstone_registry_digest"],
  "semantic-payload-projection.v0": ["payload-projection", "payload_projection_digest"],
  "semantic-capsule-archive-linkage.v0": ["capsule-archive-linkage", "capsule_archive_linkage_digest"],
  "semantic-release-capsule.v0": ["capsule", "capsule_digest"],
  "semantic-ak-decision-reference.v0": ["ak-decision-reference", "ak_decision_reference_digest"],
  "semantic-owner-approval.v0": ["owner-approval", "owner_approval_digest"],
  "semantic-build-receipt.v0": ["build-receipt", "build_receipt_digest"],
  "semantic-publication-transaction.v0": ["publication-transaction", "publication_transaction_digest"],
  "semantic-publication-journal.v0": ["publication-journal", "publication_journal_digest"],
  "semantic-publication-commit-marker.v0": ["publication-commit-marker", "publication_commit_marker_digest"],
  "semantic-owner-publication.v0": ["owner-publication", "owner_publication_digest"],
  "semantic-publication-status-transition.v0": ["publication-status-transition", "publication_status_transition_digest"],
  "semantic-consumer-intent.v0": ["consumer-intent", "consumer_intent_digest"],
  "semantic-owner-acceptance.v0": ["owner-acceptance", "owner_acceptance_digest"],
  "semantic-materialization-verification-receipt.v0": ["materialization-verification", "materialization_verification_receipt_digest"],
  "semantic-activation-receipt.v0": ["activation", "activation_receipt_digest"],
  "semantic-rocs-generation-receipt.v0": ["rocs-generation", "rocs_generation_receipt_digest"],
  "semantic-pi-delivery-receipt.v0": ["pi-delivery", "pi_delivery_receipt_digest"],
  "semantic-ak-evidence-linkage.v0": ["ak-evidence-linkage", "ak_evidence_linkage_digest"],
  "semantic-rollback-request.v0": ["rollback-request", "rollback_request_digest"],
  "semantic-rollback-receipt.v0": ["rollback-receipt", "rollback_receipt_digest"],
  "semantic-audit-envelope.v0": ["audit-envelope", "audit_envelope_digest"],
  "semantic-protocol-error.v0": ["error", "error_digest"],
};
const digestFields = Object.fromEntries(Object.entries(rows).map(([key, [domain, field]]) => [key, [`semantic-release.${domain}.v0`, field]]));

function validateIjson(value, path = "$") {
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value) || value < 0) fail(`${path}: non-safe nonnegative integer`);
    return;
  }
  if (typeof value === "string") {
    if (value.normalize("NFC") !== value || [...value].some((c) => {
      const n = c.codePointAt(0); return (n >= 0xd800 && n <= 0xdfff) || (n >= 0xfdd0 && n <= 0xfdef) || (n & 0xffff) === 0xfffe || (n & 0xffff) === 0xffff;
    })) fail(`${path}: invalid Unicode`);
    return;
  }
  if (Array.isArray(value)) { value.forEach((x, i) => validateIjson(x, `${path}/${i}`)); return; }
  if (typeof value === "object") { Object.entries(value).forEach(([k, v]) => { validateIjson(k, `${path}/key`); validateIjson(v, `${path}/${k}`); }); return; }
  fail(`${path}: invalid JSON kind`);
}

// JavaScript's default string ordering is UTF-16 code-unit ordering, as JCS requires.
function jcs(value) {
  validateIjson(value);
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(jcs).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${jcs(value[key])}`).join(",")}}`;
}
function digest(domain, bytes) {
  return `sha256:${createHash("sha256").update(Buffer.from(domain, "ascii")).update(Buffer.from([0])).update(bytes).digest("hex")}`;
}
function objectDigest(instance, domain, omitted) {
  const copy = structuredClone(instance);
  if (omitted !== null) {
    if (!(omitted in copy)) fail(`missing self digest ${omitted}`);
    delete copy[omitted];
  }
  const canonical = jcs(copy);
  return [canonical, digest(domain, Buffer.from(canonical, "utf8"))];
}
function resolve(reference) {
  if (!reference.startsWith("#/")) fail(`external schema ref ${reference}`);
  return reference.slice(2).split("/").reduce((node, token) => node[token.replaceAll("~1", "/").replaceAll("~0", "~")], schema);
}
function structural(instance, shape, path = "$") {
  if (shape.$ref) return structural(instance, resolve(shape.$ref), path);
  if (shape.oneOf) {
    const matches = shape.oneOf.filter((option) => { try { structural(instance, option, path); return true; } catch { return false; } }).length;
    if (matches !== 1) fail(`${path}: oneOf matched ${matches}`);
    return;
  }
  if (Object.hasOwn(shape, "const") && JSON.stringify(instance) !== JSON.stringify(shape.const)) fail(`${path}: const`);
  if (shape.enum && !shape.enum.some((x) => JSON.stringify(x) === JSON.stringify(instance))) fail(`${path}: enum`);
  if (shape.type === "object") {
    if (instance === null || Array.isArray(instance) || typeof instance !== "object") fail(`${path}: object`);
    for (const key of shape.required ?? []) if (!(key in instance)) fail(`${path}: missing ${key}`);
    if (shape.additionalProperties === false) for (const key of Object.keys(instance)) if (!(key in shape.properties)) fail(`${path}: unknown ${key}`);
    for (const [key, value] of Object.entries(instance)) if (shape.properties[key]) structural(value, shape.properties[key], `${path}/${key}`);
  } else if (shape.type === "array") {
    if (!Array.isArray(instance) || instance.length < (shape.minItems ?? 0) || instance.length > (shape.maxItems ?? Number.MAX_SAFE_INTEGER)) fail(`${path}: array`);
    instance.forEach((x, i) => structural(x, shape.items, `${path}/${i}`));
  } else if (shape.type === "string") {
    if (typeof instance !== "string" || instance.length < (shape.minLength ?? 0) || instance.length > (shape.maxLength ?? Number.MAX_SAFE_INTEGER)) fail(`${path}: string`);
    if (shape.pattern && !(new RegExp(shape.pattern, "u")).test(instance)) fail(`${path}: pattern`);
  } else if (shape.type === "integer") {
    if (!Number.isInteger(instance) || instance < (shape.minimum ?? -Number.MAX_SAFE_INTEGER) || instance > (shape.maximum ?? Number.MAX_SAFE_INTEGER)) fail(`${path}: integer`);
  } else if (shape.type === "boolean" && typeof instance !== "boolean") fail(`${path}: boolean`);
  else if (shape.type === "null" && instance !== null) fail(`${path}: null`);
}
function pointer(value, path) {
  return path.split("/").slice(1).reduce((node, token) => node[token.replaceAll("~1", "/").replaceAll("~0", "~")], value);
}
const eq = (a, b) => JSON.stringify(a) === JSON.stringify(b);
const embeddedDigestValid = (subject) => {
  const [domain, omitted] = digestFields[subject.schema];
  return objectDigest(subject, domain, omitted)[1] === subject[omitted];
};
const semver = (v) => v.match(/^(\d+)\.(\d+)\.(\d+)/).slice(1).map(Number);
const compare = (a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2];
function strictUtc(value) {
  const match = value.match(/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z$/);
  if (!match) return false;
  const [, ys, mos, ds, hs, mis, ss] = match; const parts = [ys, mos, ds, hs, mis, ss].map(Number);
  const date = new Date(0); date.setUTCFullYear(parts[0], parts[1] - 1, parts[2]); date.setUTCHours(parts[3], parts[4], parts[5], 0);
  return date.getUTCFullYear() === parts[0] && date.getUTCMonth() === parts[1] - 1 && date.getUTCDate() === parts[2] && date.getUTCHours() === parts[3] && date.getUTCMinutes() === parts[4] && date.getUTCSeconds() === parts[5];
}
function evaluate(rule, subject, context) {
  if (rule === "digest") return embeddedDigestValid(subject) ? null : "digest_mismatch";
  if (rule === "approval_threshold") {
    const members = new Map(context.owner_set.members.map((x) => [x.owner_id, x])); const owners = new Set();
    for (const vote of subject.votes) { const member = members.get(vote.owner_id); if (!member || !member.key_ids.includes(vote.owner_key_id)) return "approval_threshold_unsatisfied"; if (member.status === "revoked") return "trust_revoked"; owners.add(vote.owner_id); }
    const needed = context.predicate.mode === "unanimous" ? [...members.values()].filter((x) => x.status === "active").length : context.predicate.threshold;
    return owners.size >= needed ? null : "approval_threshold_unsatisfied";
  }
  if (rule === "trust_rotation") { if (context.revoked.includes(subject.old_trust_root_digest)) return "trust_revoked"; return subject.old_trust_root_digest === context.current_root_digest ? null : "trust_reference_stale"; }
  if (rule === "compatibility_policy") {
    const categories = subject.category_rules.map((x) => x.category); const expected = new Set(["addition", "documentation", "compatible_refinement", "deprecation", "removal", "rename", "constraint_change", "relation_change", "identifier_reuse", "other"]);
    return categories.length === 10 && new Set(categories).size === 10 && categories.every((x) => expected.has(x)) ? null : "compatibility_rejected";
  }
  if (rule === "compatibility") {
    const policy = context.policy; if (subject.compatibility_policy_digest !== policy.compatibility_policy_digest) return "compatibility_rejected";
    const rules = new Map(policy.category_rules.map((x) => [x.category, x]));
    for (const change of subject.changes) { const r = rules.get(change.category); if (!r || change.classification !== r.classification || change.semver_effect !== r.semver_effect || (r.condition_rule === null) !== (change.condition_id === null)) return "compatibility_rejected"; }
    const effectRank = { patch: 0, minor: 1, major: 2, unknown: 3 }, classRank = { compatible: 0, conditionally_compatible: 1, breaking: 2, unknown: 3 };
    if (subject.changes.length && (subject.required_semver_effect !== subject.changes.reduce((a, x) => effectRank[x.semver_effect] > effectRank[a] ? x.semver_effect : a, "patch") || subject.classification !== subject.changes.reduce((a, x) => classRank[x.classification] > classRank[a] ? x.classification : a, "compatible"))) return "compatibility_rejected";
    if (subject.classification === "unknown") return "compatibility_unknown";
    const conditions = new Map(subject.conditions.map((x) => [x.condition_id, x]));
    const conditionTrue = (c) => { const computed = c.kind === "evidence_digest_equals" ? c.expected_digest !== null && c.expected_digest === c.actual_digest && c.expected_integer === null && c.actual_integer === null : c.expected_digest === null && c.actual_digest === null && c.expected_integer !== null && c.actual_integer !== null && c.actual_integer >= c.expected_integer; return c.satisfied === computed && computed; };
    for (const change of subject.changes) if (change.condition_id) { const c = conditions.get(change.condition_id), r = rules.get(change.category); if (!c || c.kind !== r.condition_rule.condition_kind || !conditionTrue(c)) return "compatibility_rejected"; }
    const old = semver(context.prior_version), next = semver(subject.candidate_version); if (compare(next, old) <= 0) return "semver_violation";
    const e = subject.required_semver_effect; const valid = e === "patch" && next[0] === old[0] && next[1] === old[1] || e === "minor" && (next[0] > old[0] || next[0] === old[0] && next[1] > old[1]) || e === "major" && next[0] > old[0];
    return valid ? null : "semver_violation";
  }
  if (rule === "lifecycle") return subject.deprecation_record_digest === context.deprecation.deprecation_record_digest && subject.removed_ledger_revision - context.deprecation.introduced_ledger_revision >= context.minimum ? null : "lifecycle_violation";
  if (rule === "tombstone_reuse") { const ids = new Set(context.tombstones.entries.map((x) => x.semantic_id)); return subject.changes.some((x) => x.category === "identifier_reuse" && ids.has(x.semantic_id)) ? "lifecycle_violation" : null; }
  if (rule === "publication_cas") {
    if (subject.operation === "publish" && subject.status_reason_digest !== null || ["withdraw", "revoke"].includes(subject.operation) && subject.status_reason_digest === null) return "lifecycle_violation";
    if (context.existing_replay_key === subject.replay_key_digest && eq(context.existing_coordinate, subject.coordinate)) return null;
    if (subject.expected_prior_revision !== context.current_revision) return "publication_conflict";
    return subject.expected_prior_head_digest === context.current_head ? null : "publication_fork";
  }
  if (rule === "version_binding") { const old = context.existing_coordinate, next = subject.coordinate; return old.namespace === next.namespace && old.semantic_version === next.semantic_version && old.capsule_digest !== next.capsule_digest ? "version_conflict" : null; }
  if (rule === "publication_transition") {
    const { transaction: tx, journal: journal, marker } = context; const op = subject.to_status === "withdrawn" ? "withdraw" : "revoke";
    return subject.transaction_digest === tx.publication_transaction_digest && subject.journal_digest === journal.publication_journal_digest && subject.commit_marker_digest === marker.publication_commit_marker_digest && tx.operation === op && eq(tx.coordinate, subject.coordinate) && tx.status_reason_digest === subject.reason_digest && journal.transaction_digest === tx.publication_transaction_digest && journal.state === "committed" && journal.linearized && marker.transaction_digest === tx.publication_transaction_digest && marker.journal_digest === journal.publication_journal_digest && marker.ledger_revision === subject.ledger_revision && marker.fsync_complete ? null : "lifecycle_violation";
  }
  if (rule === "publication_recovery") {
    if (["prepared", "aborted"].includes(subject.state) && !subject.linearized && subject.recovery_action === "discard_staging") return null;
    if (subject.state === "committing" && subject.linearized && subject.recovery_action === "complete_commit") return null;
    if (subject.state === "committed" && subject.linearized && subject.recovery_action === "none") return null;
    return "recovery_needed";
  }
  if (rule === "projection") {
    const p = context.projection, c = context.capsule, a = context.archive_linkage, payload = new Map(context.payload_manifest.entries.map((x) => [x.path, x])), consumer = new Map(context.consumer_manifest.entries.map((x) => [x.path, x])), archive = new Map(context.archive_manifest.entries.map((x) => [x.path, x]));
    let rows = p.entries.length === payload.size && payload.size === consumer.size;
    for (const row of p.entries) { const relative = row.capsule_path.startsWith(`${a.payload_root}/`) ? row.capsule_path.slice(a.payload_root.length + 1) : row.capsule_path; const pe = payload.get(relative), ce = consumer.get(row.consumer_path), ae = archive.get(row.capsule_path); if (!pe || !ce || !ae || !["kind", "mode", "byte_length", "content_digest"].every((k) => pe[k] === ce[k] && pe[k] === ae[k]) || row.mode !== pe.mode || row.byte_length !== (pe.byte_length ?? null) || row.content_digest !== (pe.content_digest ?? null)) rows = false; }
    const valid = rows && a.archive_manifest_digest === context.archive_manifest.material_manifest_digest && p.payload_manifest_digest === context.payload_manifest.material_manifest_digest && p.consumer_manifest_digest === context.consumer_manifest.material_manifest_digest && subject.payload_projection_digest === p.payload_projection_digest && p.payload_projection_digest === c.payload_projection_digest && subject.capsule_archive_linkage_digest === a.capsule_archive_linkage_digest && a.capsule_archive_linkage_digest === c.capsule_archive_linkage_digest && subject.source_payload_manifest_digest === p.payload_manifest_digest && subject.expected_consumer_manifest_digest === p.consumer_manifest_digest && p.consumer_manifest_digest === subject.actual_consumer_manifest_digest;
    return valid ? null : "projection_mismatch";
  }
  if (rule === "rollback") {
    const target = context.request.target, before = subject.active_state_before, after = subject.active_state_after;
    if (subject.result === "failed") return eq(after, before) && eq(subject.history_head_after, subject.history_head_before) && subject.error_digest ? null : "history_conflict";
    if (target.kind === "semantic" && (!eq(after.runtime_identity, before.runtime_identity) || !eq(after.coordinate, target.target_coordinate))) return "history_conflict";
    if (target.kind === "runtime" && (!eq(after.coordinate, before.coordinate) || !eq(after.runtime_identity, target.target_runtime_identity) || !target.runtime_revalidation_receipt_digest)) return "rollback_unavailable";
    if (target.kind === "no_prior_disable" && (after.enabled || after.coordinate !== null)) return "history_conflict";
    if (subject.result === "partial_failure" && (!subject.stages.some((x) => x.result === "failed") || eq(after, before))) return "history_conflict";
    if (!["failed", "partial_failure"].includes(subject.result) && (subject.error_digest !== null || eq(subject.history_head_after, subject.history_head_before))) return "history_conflict";
    return null;
  }
  if (rule === "generation_activation") { const a = context.activation; return a.status === "activated" && a.revoked_by_digest === null && a.superseded_by_activation_receipt_digest === null && subject.activation_receipt_digest === context.current_activation_digest ? null : "activation_not_current"; }
  if (rule === "utc") return strictUtc(subject.recorded_at) ? null : "malformed_input";
  if (rule === "ak_decision") return subject.lifecycle_state === "accepted" && subject.adr_reference.status === "accepted" && subject.revocation_digest === null ? null : "self_certification";
  if (rule === "acceptance_binding") { const d = context.decision; return subject.acceptance_authority.kind === "consumer_owner" && subject.acceptance_authority.id === subject.consumer_repository.owner && subject.decision_reference_digest === d.ak_decision_reference_digest && subject.governing_scope_digest === d.scope_digest && d.lifecycle_state === "accepted" && d.revocation_digest === null ? null : "self_certification"; }
  if (rule === "activation_binding") { const d = context.decision; return subject.gate_decision_reference_digest === d.ak_decision_reference_digest && ["activation_target_digest", "evidence_criteria_digest", "rollback_plan_digest", "stop_conditions_digest"].every((k) => subject[k] === d[k]) ? null : "self_certification"; }
  if (rule === "pi_variant" || rule === "ak_optional_pi") return null;
  fail(`unknown rule ${rule}`);
}

validateIjson(schema); validateIjson(golden); validateIjson(differential);
if (schema.$schema !== "https://json-schema.org/draft/2020-12/schema") fail("wrong schema draft");
(function closed(node, path = "$") { if (Array.isArray(node)) return node.forEach((x, i) => closed(x, `${path}/${i}`)); if (node && typeof node === "object") { if (node.type === "object" && node.additionalProperties !== false) fail(`open object ${path}`); if (node.$ref) resolve(node.$ref); Object.entries(node).forEach(([k, v]) => closed(v, `${path}/${k}`)); } })(schema);
const records = new Map();
for (const record of golden.records) {
  if (records.has(record.name)) fail(`duplicate record ${record.name}`);
  structural(record.instance, schema); const [canonical, computed] = objectDigest(record.instance, record.domain, record.omitted_field);
  if (canonical !== record.canonical_preimage || computed !== record.digest || record.omitted_field !== null && record.instance[record.omitted_field] !== computed) fail(`${record.name}: digest mismatch`);
  if (record.instance.schema === "semantic-audit-envelope.v0" && !strictUtc(record.instance.recorded_at)) fail("invalid golden UTC");
  records.set(record.name, record);
}
for (const raw of golden.raw_preimages) if (digest(raw.domain, Buffer.from(raw.preimage_utf8, "utf8")) !== raw.digest) fail(`${raw.name}: raw digest`);
for (const assertion of golden.chain_assertions) if (pointer(records.get(assertion.record).instance, assertion.instance_path) !== records.get(assertion.equals_record).digest) fail(`chain ${assertion.record}`);
let accepted = 0, rejected = 0;
for (const item of differential.cases) {
  let valid = true; try { structural(item.subject, schema); } catch { valid = false; }
  if (valid !== item.schema_valid) fail(`${item.name}: schema_valid expected ${item.schema_valid}, got ${valid}`);
  if (item.rule !== "digest" && !embeddedDigestValid(item.subject)) fail(`${item.name}: masked by digest`);
  const actual = valid ? evaluate(item.rule, item.subject, item.context) : item.expected_error;
  if (actual !== item.expected_error) fail(`${item.name}: expected ${item.expected_error}, got ${actual}`);
  actual === null ? accepted++ : rejected++;
}
console.log(`schema: Draft 2020-12, ${Object.keys(digestFields).length + 1} protocol types, all object shapes closed`);
console.log(`golden: ${records.size} object preimages and ${golden.raw_preimages.length} raw preimages independently recomputed`);
console.log(`chain: ${golden.chain_assertions.length} exact digest links verified`);
console.log(`differential: ${differential.cases.length} cases (${accepted} accepted transitions, ${rejected} expected rejections)`);
console.log("result: PASS (independent Node verifier; no Python imports or subprocesses)");
