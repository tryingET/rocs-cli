#!/usr/bin/env node
/** Independent revision-4 Node verifier: no Python imports, subprocesses, or shared code. */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = dirname(fileURLToPath(import.meta.url));
const fail = (message) => { throw new Error(message); };
const maxSafe = Number.MAX_SAFE_INTEGER;

function strictJson(text) {
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
  const value = () => {
    ws(); const c = text[at];
    if (c === "{") {
      at++; ws(); const out = Object.create(null); const keys = new Set();
      if (text[at] === "}") { at++; return out; }
      while (true) {
        if (text[at] !== "\"") fail("object key must be string");
        const key = string(); if (keys.has(key)) fail(`duplicate JSON key ${key}`); keys.add(key); ws();
        if (text[at++] !== ":") fail("missing colon"); out[key] = value(); ws();
        const end = text[at++]; if (end === "}") return out; if (end !== ",") fail("missing object comma"); ws();
      }
    }
    if (c === "[") {
      at++; ws(); const out = []; if (text[at] === "]") { at++; return out; }
      while (true) { out.push(value()); ws(); const end = text[at++]; if (end === "]") return out; if (end !== ",") fail("missing array comma"); ws(); }
    }
    if (c === "\"") return string();
    for (const [token, result] of [["true", true], ["false", false], ["null", null]]) if (text.startsWith(token, at)) { at += token.length; return result; }
    const start = at; while (at < text.length && !/[\s,\]}]/u.test(text[at])) at++;
    const token = text.slice(start, at);
    if (!/^(?:0|[1-9][0-9]*)$/u.test(token)) fail(`non-canonical integer token ${token}`);
    const number = Number(token); if (!Number.isSafeInteger(number)) fail("unsafe integer token"); return number;
  };
  const result = value(); ws(); if (at !== text.length) fail("trailing JSON data"); validateIjson(result); return result;
}

function load(name) {
  const bytes = readFileSync(join(root, name));
  if (bytes.length >= 3 && bytes[0] === 0xef && bytes[1] === 0xbb && bytes[2] === 0xbf) fail(`${name}: BOM forbidden`);
  let text; try { text = new TextDecoder("utf-8", { fatal: true }).decode(bytes); } catch { fail(`${name}: malformed UTF-8`); }
  return strictJson(text);
}

const schema = load("protocol.schema.json");
const golden = load("golden-fixtures.json");
const differential = load("differential-fixtures.json");
const coordinateDomain = "semantic-release.coordinate.v0";
const rows = {
  "semantic-source-manifest.v0": ["source-manifest", "source_manifest_digest"], "semantic-material-manifest.v0": ["material-manifest", "material_manifest_digest"],
  "semantic-owner-set.v0": ["owner-set", "owner_set_digest"], "semantic-approval-predicate.v0": ["approval-predicate", "approval_predicate_digest"],
  "semantic-owner-policy.v0": ["owner-policy", "owner_policy_digest"], "semantic-trust-root.v0": ["trust-root", "trust_root_digest"],
  "semantic-trust-rotation.v0": ["trust-rotation", "trust_rotation_digest"], "semantic-trust-revocation.v0": ["trust-revocation", "trust_revocation_digest"],
  "semantic-compatibility-policy.v0": ["compatibility-policy", "compatibility_policy_digest"], "semantic-compatibility-report.v0": ["compatibility-report", "compatibility_report_digest"],
  "semantic-compatibility-override.v0": ["compatibility-override", "compatibility_override_digest"], "semantic-deprecation-record.v0": ["deprecation-record", "deprecation_record_digest"],
  "semantic-removal-record.v0": ["removal-record", "removal_record_digest"], "semantic-tombstone-registry.v0": ["tombstone-registry", "tombstone_registry_digest"],
  "semantic-payload-projection.v0": ["payload-projection", "payload_projection_digest"], "semantic-capsule-archive-linkage.v0": ["capsule-archive-linkage", "capsule_archive_linkage_digest"],
  "semantic-release-capsule.v0": ["capsule", "capsule_digest"], "semantic-ak-decision-reference.v0": ["ak-decision-reference", "ak_decision_reference_digest"],
  "semantic-owner-approval.v0": ["owner-approval", "owner_approval_digest"], "semantic-build-receipt.v0": ["build-receipt", "build_receipt_digest"],
  "semantic-publication-transaction.v0": ["publication-transaction", "publication_transaction_digest"], "semantic-publication-journal.v0": ["publication-journal", "publication_journal_digest"],
  "semantic-publication-commit-marker.v0": ["publication-commit-marker", "publication_commit_marker_digest"], "semantic-owner-publication.v0": ["owner-publication", "owner_publication_digest"],
  "semantic-publication-status-transition.v0": ["publication-status-transition", "publication_status_transition_digest"], "semantic-consumer-intent.v0": ["consumer-intent", "consumer_intent_digest"],
  "semantic-owner-acceptance.v0": ["owner-acceptance", "owner_acceptance_digest"], "semantic-materialization-verification-receipt.v0": ["materialization-verification", "materialization_verification_receipt_digest"],
  "semantic-activation-receipt.v0": ["activation", "activation_receipt_digest"], "semantic-rocs-generation-receipt.v0": ["rocs-generation", "rocs_generation_receipt_digest"],
  "semantic-pi-delivery-receipt.v0": ["pi-delivery", "pi_delivery_receipt_digest"], "semantic-ak-evidence-linkage.v0": ["ak-evidence-linkage", "ak_evidence_linkage_digest"],
  "semantic-rollback-request.v0": ["rollback-request", "rollback_request_digest"],
  "semantic-rollback-availability-proof.v0": ["rollback-availability-proof", "rollback_availability_proof_digest"],
  "semantic-rollback-history-transition.v0": ["rollback-history-transition", "rollback_history_transition_digest"],
  "semantic-rollback-receipt.v0": ["rollback-receipt", "rollback_receipt_digest"],
  "semantic-non-authorizing-task-contract.v0": ["non-authorizing-task-contract", "non_authorizing_task_contract_digest"],
  "semantic-audit-envelope.v0": ["audit-envelope", "audit_envelope_digest"], "semantic-protocol-error.v0": ["error", "error_digest"],
};
const digestFields = Object.fromEntries(Object.entries(rows).map(([kind, [domain, field]]) => [kind, [`semantic-release.${domain}.v0`, field]]));

function validateIjson(value, path = "$") {
  if (value === null || typeof value === "boolean") return;
  if (typeof value === "number") { if (!Number.isSafeInteger(value) || value < 0) fail(`${path}: unsafe integer`); return; }
  if (typeof value === "string") {
    if (value.normalize("NFC") !== value || [...value].some((c) => { const n = c.codePointAt(0); return n >= 0xd800 && n <= 0xdfff || n >= 0xfdd0 && n <= 0xfdef || (n & 0xffff) === 0xfffe || (n & 0xffff) === 0xffff; })) fail(`${path}: invalid Unicode`);
    return;
  }
  if (Array.isArray(value)) { value.forEach((x, i) => validateIjson(x, `${path}/${i}`)); return; }
  if (typeof value === "object") { Object.entries(value).forEach(([k, v]) => { validateIjson(k, `${path}/key`); validateIjson(v, `${path}/${k}`); }); return; }
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
function pointer(value, path) { return path.split("/").slice(1).reduce((node, token) => { const key = token.replaceAll("~1", "/").replaceAll("~0", "~"); if (!Object.hasOwn(node, key)) fail(`missing pointer token ${key}`); return node[key]; }, value); }
const embeddedDigestValid = (subject) => { const [domain, omitted] = digestFields[subject.schema]; return objectDigest(subject, domain, omitted)[1] === subject[omitted]; };
const sortedUnique = (values) => eq(values, [...values].sort((a, b) => Buffer.compare(Buffer.from(a), Buffer.from(b)))) && new Set(values).size === values.length;
function checkOrder(instance) {
  const kind = instance.schema;
  if (["semantic-source-manifest.v0", "semantic-material-manifest.v0"].includes(kind)) { const keys = instance.entries.map((x) => [x.path, x.kind]); const ordered = [...keys].sort((a, b) => Buffer.compare(Buffer.from(a[0], "utf8"), Buffer.from(b[0], "utf8")) || Buffer.compare(Buffer.from(a[1], "utf8"), Buffer.from(b[1], "utf8"))); if (!eq(keys, ordered) || new Set(instance.entries.map((x) => x.path)).size !== keys.length) fail("manifest order"); }
  if (kind === "semantic-owner-set.v0" && (!sortedUnique(instance.members.map((x) => x.owner_id)) || instance.members.some((x) => !sortedUnique(x.key_ids)))) fail("owner order");
  if (kind === "semantic-owner-approval.v0") { const keys = instance.votes.map((x) => [x.owner_id, x.owner_key_id]); const ordered = [...keys].sort((a, b) => Buffer.compare(Buffer.from(a[0]), Buffer.from(b[0])) || Buffer.compare(Buffer.from(a[1]), Buffer.from(b[1]))); if (!eq(keys, ordered) || new Set(keys.map(JSON.stringify)).size !== keys.length || actionDigest(instance.action) !== instance.action_digest || instance.votes.some((x) => x.approved_action_digest !== instance.action_digest)) fail("approval order/binding"); }
  if (kind === "semantic-compatibility-policy.v0" && !sortedUnique(instance.category_rules.map((x) => x.category))) fail("policy order");
  if (kind === "semantic-compatibility-report.v0") { const keys = instance.changes.map((x) => [x.semantic_id, x.category]); const ordered = [...keys].sort((a, b) => Buffer.compare(Buffer.from(a[0]), Buffer.from(b[0])) || Buffer.compare(Buffer.from(a[1]), Buffer.from(b[1]))); if (!eq(keys, ordered) || new Set(keys.map(JSON.stringify)).size !== keys.length || !sortedUnique(instance.conditions.map((x) => x.condition_id)) || !sortedUnique(instance.override_digests)) fail("compatibility order"); }
  if (kind === "semantic-tombstone-registry.v0" && !sortedUnique(instance.entries.map((x) => x.semantic_id))) fail("tombstone order");
  if (kind === "semantic-payload-projection.v0" && (!sortedUnique(instance.entries.map((x) => x.capsule_path)) || new Set(instance.entries.map((x) => x.consumer_path)).size !== instance.entries.length)) fail("projection bijection");
  if (kind === "semantic-release-capsule.v0" && !sortedUnique(instance.required_protocol_versions)) fail("protocol order");
  if (kind === "semantic-rocs-generation-receipt.v0" && (!sortedUnique(instance.candidate_ids) || !sortedUnique(instance.pack_digests))) fail("generation order");
  if (kind === "semantic-rollback-receipt.v0" && new Set(instance.stages.map((x) => x.stage)).size !== instance.stages.length) fail("stage uniqueness");
  if (kind === "semantic-non-authorizing-task-contract.v0" && (!sortedUnique(instance.allowed_paths) || !sortedUnique(instance.required_evidence) || !sortedUnique(instance.stop_conditions))) fail("task contract order");
  if (kind === "semantic-protocol-error.v0" && !sortedUnique(instance.details.map((x) => x.key))) fail("error order");
}
function checkClaimScope(instance) {
  const expected = { "semantic-owner-acceptance.v0": ["acceptance_authority", "consumer_owner"], "semantic-materialization-verification-receipt.v0": ["issuer", "rocs"], "semantic-activation-receipt.v0": ["issuer", "consumer_owner"], "semantic-rocs-generation-receipt.v0": ["issuer", "rocs"], "semantic-pi-delivery-receipt.v0": ["issuer", "pi"], "semantic-ak-evidence-linkage.v0": ["issuer", "ak"], "semantic-rollback-request.v0": ["issuer", "consumer_owner"], "semantic-rollback-receipt.v0": ["issuer", "recovery_controller"] };
  const row = expected[instance.schema]; if (row && instance[row[0]].kind !== row[1]) fail("issuer_scope_violation");
}
const semver = (v) => v.match(/^(\d+)\.(\d+)\.(\d+)/u).slice(1).map(Number);
const compare = (a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2];
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
function decisionCurrent(subject, context) {
  const canonical = context.canonical_store_head ?? subject.ak_store_head;
  return subject.lifecycle_state === "accepted" && subject.adr_reference.status === "accepted" && subject.revocation_digest === null && subject.superseded_by_decision_record_digest === null && eq(subject.ak_store_head, canonical) && subject.ak_store_head.store_head_digest === canonical.store_head_digest && subject.ak_store_head.revocation_head_digest === canonical.revocation_head_digest && (context.current_decision_record_digest ?? subject.decision_record_digest) === subject.decision_record_digest;
}

function evaluate(rule, subject, context) {
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
    const approvalThresholdValid = evaluate("approval_threshold", approval, { policy, owner_set: ownerSet, predicate }) === null;
    const valid = authority && transition && approvalThresholdValid && subject.approval_digest === approval.owner_approval_digest && eq(action, actionFields) && actionDigest(action) === approval.action_digest; return valid ? null : "trust_reference_stale";
  }
  if (rule === "trust_revocation") {
    const { approval, policy, owner_set: ownerSet, predicate } = context, action = approval.action;
    const authority = subject.namespace === policy.namespace && policy.namespace === ownerSet.namespace && ownerSet.namespace === predicate.namespace && predicate.namespace === approval.namespace && approval.owner_policy_digest === policy.owner_policy_digest && approval.owner_set_digest === policy.owner_set_digest && policy.owner_set_digest === ownerSet.owner_set_digest && approval.approval_predicate_digest === policy.approval_predicate_digest && policy.approval_predicate_digest === predicate.approval_predicate_digest;
    const approvalThresholdValid = evaluate("approval_threshold", approval, { policy, owner_set: ownerSet, predicate }) === null;
    const valid = authority && approvalThresholdValid && subject.revocation_revision === context.prior_revision + 1 && subject.prior_revocation_digest === context.prior_head && subject.owner_approval_digest === approval.owner_approval_digest && action.kind === "trust_revocation" && actionDigest(action) === approval.action_digest && ["target_kind", "target_digest", "effective_ledger_revision", "reason_digest", "prior_revocation_digest", "revocation_revision"].every((k) => eq(subject[k], action[k])); return valid ? null : "trust_reference_stale";
  }
  if (rule === "compatibility_policy") { const cats = subject.category_rules.map((x) => x.category), expected = new Set(["addition", "documentation", "compatible_refinement", "deprecation", "removal", "rename", "constraint_change", "relation_change", "identifier_reuse", "other"]); return cats.length === 10 && new Set(cats).size === 10 && cats.every((x) => expected.has(x)) ? null : "compatibility_rejected"; }
  if (rule === "compatibility") {
    const policy = context.policy; if (subject.compatibility_policy_digest !== policy.compatibility_policy_digest) return "compatibility_rejected";
    const rules = new Map(policy.category_rules.map((x) => [x.category, x])), conditions = new Map(subject.conditions.map((x) => [x.condition_id, x])); if (conditions.size !== subject.conditions.length) return "compatibility_rejected";
    const overrideRows = context.overrides ?? [], overrides = new Map(overrideRows.map((x) => [x.change_digest, x])); if (overrides.size !== overrideRows.length) return "compatibility_rejected";
    const usedConditions = new Set(), usedOverrides = [], effective = [], knownChanges = new Set();
    for (const change of subject.changes) {
      const row = rules.get(change.category); if (!row || change.classification !== row.classification || change.semver_effect !== row.semver_effect || (row.condition_rule === null) !== (change.condition_id === null)) return "compatibility_rejected";
      let classification = change.classification, effect = change.semver_effect;
      if (change.condition_id !== null) { const c = conditions.get(change.condition_id); usedConditions.add(change.condition_id); if (!c || c.kind !== row.condition_rule.condition_kind || !conditionTrue(c)) return "compatibility_rejected"; }
      const cd = changeDigest(change), override = overrides.get(cd); if (override) {
        knownChanges.add(cd); const approval = (context.override_approvals ?? {})[override.owner_approval_digest], action = approval?.action;
        const expectedAction = { kind: "compatibility_override", namespace: override.namespace, compatibility_policy_digest: override.compatibility_policy_digest, change: override.change, change_digest: override.change_digest, from_classification: override.from_classification, from_semver_effect: override.from_semver_effect, to_classification: override.to_classification, semver_effect_floor: override.semver_effect_floor, condition: override.condition };
        const ranks = { patch: 0, minor: 1, major: 2, unknown: 2 }, nonLowering = ranks[override.semver_effect_floor] >= ranks[effect];
        const approvalValid = approval && evaluate("approval_threshold", approval, { policy: context.owner_policy, owner_set: context.owner_set, predicate: context.predicate }) === null;
        const valid = approvalValid && approval.namespace === override.namespace && context.owner_policy.compatibility_policy_digest === subject.compatibility_policy_digest && row.override_allowed && change.category !== "identifier_reuse" && override.namespace === subject.namespace && override.compatibility_policy_digest === subject.compatibility_policy_digest && eq(override.change, change) && override.change_digest === cd && override.from_classification === classification && override.from_semver_effect === effect && conditionTrue(override.condition) && nonLowering && eq(action, expectedAction) && actionDigest(action) === approval.action_digest;
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
    const valid = effect === "patch" && next[0] === old[0] && next[1] === old[1] || effect === "minor" && (next[0] > old[0] || next[0] === old[0] && next[1] > old[1]) || effect === "major" && next[0] > old[0]; return valid ? null : "semver_violation";
  }
  if (rule === "lifecycle") {
    const dep = context.deprecation, policy = context.policy, prior = context.prior_tombstones, resulting = context.resulting_tombstones;
    const expected = [...prior.entries.map((x) => structuredClone(x)), { semantic_id: subject.semantic_id, reason: context.reason ?? "removed", origin_record_digest: subject.removal_record_digest }].sort((a, b) => Buffer.compare(Buffer.from(a.semantic_id), Buffer.from(b.semantic_id)));
    const exactChain = dep.prior_lifecycle_digest === (context.deprecation_prior_head ?? null) && subject.prior_lifecycle_digest === (context.current_lifecycle_head ?? dep.deprecation_record_digest) && subject.prior_lifecycle_digest === dep.deprecation_record_digest;
    const valid = subject.namespace === dep.namespace && dep.namespace === dep.introduced_coordinate.namespace && dep.namespace === subject.removed_coordinate.namespace && subject.namespace === policy.namespace && subject.namespace === prior.namespace && subject.namespace === resulting.namespace && subject.semantic_id === dep.semantic_id && subject.deprecation_record_digest === dep.deprecation_record_digest && exactChain && subject.deprecation_ledger_revision === dep.introduced_ledger_revision && subject.removed_ledger_revision > subject.deprecation_ledger_revision && subject.required_interval === policy.minimum_deprecation_releases && subject.removed_ledger_revision - subject.deprecation_ledger_revision >= subject.required_interval && subject.compatibility_policy_digest === policy.compatibility_policy_digest && subject.prior_tombstone_registry_digest === prior.tombstone_registry_digest && resulting.prior_registry_digest === prior.tombstone_registry_digest && resulting.registry_revision === prior.registry_revision + 1 && !prior.entries.some((x) => x.semantic_id === subject.semantic_id) && eq(resulting.entries, expected); return valid ? null : "lifecycle_violation";
  }
  if (rule === "tombstone_reuse") { const ids = new Set(context.tombstones.entries.map((x) => x.semantic_id)); return subject.changes.some((x) => ids.has(x.semantic_id)) ? "lifecycle_violation" : null; }
  if (rule === "publication_cas") { if (subject.operation === "publish" && subject.status_reason_digest !== null || ["withdraw", "revoke"].includes(subject.operation) && subject.status_reason_digest === null) return "lifecycle_violation"; if (context.existing_replay_key === subject.replay_key_digest && eq(context.existing_coordinate, subject.coordinate) && (context.existing_operation ?? subject.operation) === subject.operation) return null; if (subject.expected_prior_revision !== context.current_revision) return "publication_conflict"; return subject.expected_prior_head_digest === context.current_head ? null : "publication_fork"; }
  if (rule === "version_binding") { const old = context.existing_coordinate, next = subject.coordinate; return old.namespace === next.namespace && old.semantic_version === next.semantic_version && old.capsule_digest !== next.capsule_digest ? "version_conflict" : null; }
  if (rule === "publication_commit") {
    const tx = context.transaction, journal = context.journal, marker = context.marker, result = subject.owner_publication_digest;
    const valid = tx.operation === "publish" && tx.status_reason_digest === null && subject.transaction_digest === tx.publication_transaction_digest && tx.publication_transaction_digest === journal.transaction_digest && journal.transaction_digest === marker.transaction_digest && eq(subject.coordinate, tx.coordinate) && subject.ledger_namespace === tx.namespace && tx.namespace === tx.coordinate.namespace && subject.owner_approval_digest === tx.owner_approval_digest && tx.owner_approval_digest === context.approval.owner_approval_digest && subject.trust_root_digest === context.trust_root.trust_root_digest && subject.prior_publication_digest === tx.expected_prior_head_digest && subject.ledger_revision === tx.expected_prior_revision + 1 && journal.state === "committed" && journal.linearized && journal.recovery_action === "none" && journal.resulting_record_digest === result && journal.resulting_ledger_head_digest === result && journal.resulting_ledger_revision === subject.ledger_revision && journal.prior_journal_digest === context.prior_journal_digest && marker.journal_digest === journal.publication_journal_digest && marker.resulting_record_digest === result && marker.resulting_ledger_head_digest === result && marker.resulting_ledger_revision === subject.ledger_revision && marker.fsync_complete; return valid ? null : "lifecycle_violation";
  }
  if (rule === "publication_transition") {
    const tx = context.transaction, journal = context.journal, marker = context.marker, result = subject.publication_status_transition_digest, op = subject.to_status === "withdrawn" ? "withdraw" : "revoke", prior = context.prior_status;
    const priorDigest = prior.owner_publication_digest ?? prior.publication_status_transition_digest, priorStatus = prior.status ?? prior.to_status;
    const validFrom = subject.from_status === priorStatus && priorDigest === subject.prior_status_record_digest && eq(prior.coordinate, subject.coordinate) && prior.ledger_revision === tx.expected_prior_revision;
    const valid = validFrom && tx.operation === op && tx.publication_transaction_digest === subject.transaction_digest && subject.transaction_digest === journal.transaction_digest && journal.transaction_digest === marker.transaction_digest && eq(tx.coordinate, subject.coordinate) && tx.owner_approval_digest === subject.owner_approval_digest && tx.status_reason_digest === subject.reason_digest && tx.expected_prior_head_digest === subject.prior_status_record_digest && tx.expected_prior_revision + 1 === subject.ledger_revision && journal.state === "committed" && journal.linearized && journal.recovery_action === "none" && journal.prior_journal_digest === context.prior_journal_digest && journal.resulting_record_digest === result && journal.resulting_ledger_head_digest === result && journal.resulting_ledger_revision === subject.ledger_revision && marker.journal_digest === journal.publication_journal_digest && marker.resulting_record_digest === result && marker.resulting_ledger_head_digest === result && marker.resulting_ledger_revision === subject.ledger_revision && marker.fsync_complete; return valid ? null : "lifecycle_violation";
  }
  if (rule === "publication_recovery") {
    const validTuple = ["prepared", "aborted"].includes(subject.state) && !subject.linearized && subject.recovery_action === "discard_staging" || subject.state === "committing" && subject.linearized && subject.recovery_action === "complete_commit" || subject.state === "committed" && subject.linearized && subject.recovery_action === "none"; if (!validTuple) return "recovery_needed";
    if (Object.keys(context).length) {
      const before = context.before, after = context.after, marker = context.marker;
      if (!subject.linearized && (after.revision !== before.revision || after.head !== before.head || after.marker !== null || after.staging_present || after.status_record_digest !== before.status_record_digest)) return "recovery_needed";
      const exactMarker = marker && embeddedDigestValid(marker) && eq(after.marker, marker) && marker.journal_digest === subject.publication_journal_digest && marker.transaction_digest === subject.transaction_digest && marker.resulting_record_digest === subject.resulting_record_digest && marker.resulting_ledger_head_digest === subject.resulting_ledger_head_digest && marker.resulting_ledger_revision === subject.resulting_ledger_revision;
      if (subject.linearized && (after.revision !== subject.resulting_ledger_revision || after.head !== subject.resulting_ledger_head_digest || after.status_record_digest !== subject.resulting_record_digest || !exactMarker || after.staging_present)) return "recovery_needed";
    } return null;
  }
  if (rule === "projection") {
    const p = context.projection, capsule = context.capsule, archiveLink = context.archive_linkage, payload = new Map(context.payload_manifest.entries.map((x) => [x.path, x])), consumer = new Map(context.consumer_manifest.entries.map((x) => [x.path, x])), archive = new Map(context.archive_manifest.entries.map((x) => [x.path, x]));
    const src = p.entries.map((x) => x.capsule_path), dst = p.entries.map((x) => x.consumer_path), expectedSrc = new Set([...payload.keys()].map((x) => `${archiveLink.payload_root}/${x}`)); let rowsOk = new Set(src).size === src.length && new Set(dst).size === dst.length && src.length === expectedSrc.size && src.every((x) => expectedSrc.has(x)) && dst.length === consumer.size && dst.every((x) => consumer.has(x));
    for (const row of p.entries) { const relative = row.capsule_path.slice(archiveLink.payload_root.length + 1), pe = payload.get(relative), ce = consumer.get(row.consumer_path), ae = archive.get(row.capsule_path); if (!pe || !ce || !ae || !["kind", "mode", "byte_length", "content_digest"].every((k) => pe[k] === ce[k] && pe[k] === ae[k]) || row.mode !== pe.mode || row.byte_length !== (pe.byte_length ?? null) || row.content_digest !== (pe.content_digest ?? null)) rowsOk = false; }
    const meta = archiveLink.capsule_metadata, metaBytes = Buffer.from(jcs(meta), "utf8"), metaEntry = archive.get(archiveLink.capsule_metadata_path), acyclic = eq(Object.keys(meta).sort(), ["identity_mode", "namespace", "payload_manifest_digest", "schema", "semantic_version"]) && meta.namespace === capsule.namespace && meta.semantic_version === capsule.semantic_version && meta.payload_manifest_digest === capsule.payload_manifest_digest && metaEntry?.content_digest === archiveLink.capsule_metadata_content_digest && archiveLink.capsule_metadata_content_digest === digest("semantic-release.raw-blob.v0", metaBytes) && metaEntry?.byte_length === metaBytes.length;
    const expectedArchivePaths = new Set([archiveLink.capsule_metadata_path, archiveLink.payload_root, ...[...payload.keys()].map((x) => `${archiveLink.payload_root}/${x}`)]), archiveExact = archive.size === expectedArchivePaths.size && [...archive.keys()].every((x) => expectedArchivePaths.has(x));
    const valid = rowsOk && acyclic && archiveExact && archiveLink.archive_manifest_digest === context.archive_manifest.material_manifest_digest && p.payload_manifest_digest === context.payload_manifest.material_manifest_digest && p.consumer_manifest_digest === context.consumer_manifest.material_manifest_digest && subject.payload_projection_digest === p.payload_projection_digest && p.payload_projection_digest === capsule.payload_projection_digest && subject.capsule_archive_linkage_digest === archiveLink.capsule_archive_linkage_digest && archiveLink.capsule_archive_linkage_digest === capsule.capsule_archive_linkage_digest && subject.source_payload_manifest_digest === p.payload_manifest_digest && subject.expected_consumer_manifest_digest === p.consumer_manifest_digest && p.consumer_manifest_digest === subject.actual_consumer_manifest_digest; return valid ? null : "projection_mismatch";
  }
  if (rule === "rollback") {
    const request = context.request, target = request.target, before = subject.active_state_before, after = subject.active_state_after, activation = context.activation, decision = context.decision;
    const currentDigest = context.current_activation_digest, currentRevision = context.current_activation_revision, canonicalHistory = context.canonical_history_head;
    const activationCurrent = activation.activation_receipt_digest === currentDigest && activation.activation_revision === currentRevision && activation.status === "activated" && activation.revoked_by_digest === null && activation.superseded_by_activation_receipt_digest === null;
    const requestValid = activationCurrent && request.issuer.kind === "consumer_owner" && request.active_activation_receipt_digest === currentDigest && request.from_state.enabled && eq(request.from_state.coordinate, activation.coordinate) && eq(request.from_state.runtime_identity, activation.runtime_identity) && request.owner_decision_reference_digest === decision.ak_decision_reference_digest && decisionCurrent(decision, context) && !eq(request.recovery_runtime_identity, request.from_state.runtime_identity); if (!requestValid) return "rollback_unavailable";
    const proof = context.availability;
    if (!proof || !embeddedDigestValid(proof) || subject.availability_proof_digest !== proof.rollback_availability_proof_digest || proof.rollback_request_digest !== request.rollback_request_digest || proof.target_kind !== target.kind || proof.canonical_activation_digest !== currentDigest || !eq(proof.recovery_runtime_identity, request.recovery_runtime_identity) || !proof.recovery_runtime_available) return "rollback_unavailable";
    const expectedProof = { semantic_materialization_receipt_digest: null, semantic_coordinate: null, runtime_materialization_receipt_digest: null, runtime_identity: null, runtime_revalidation_receipt_digest: null, disable_contract_digest: null, rehearsal_receipt_digest: null };
    if (["semantic", "combined"].includes(target.kind)) { const st = target.kind === "semantic" ? target : target.semantic_stage; expectedProof.semantic_materialization_receipt_digest = st.target_materialization_receipt_digest; expectedProof.semantic_coordinate = st.target_coordinate; }
    if (["runtime", "combined"].includes(target.kind)) { const rt = target.kind === "runtime" ? target : target.runtime_stage; expectedProof.runtime_materialization_receipt_digest = rt.target_materialization_receipt_digest; expectedProof.runtime_identity = rt.target_runtime_identity; expectedProof.runtime_revalidation_receipt_digest = rt.runtime_revalidation_receipt_digest; }
    if (target.kind === "no_prior_disable") { expectedProof.disable_contract_digest = target.disable_contract_digest; expectedProof.rehearsal_receipt_digest = target.rehearsal_receipt_digest; }
    if (Object.entries(expectedProof).some(([k, v]) => !eq(proof[k], v))) return "rollback_unavailable";
    if (subject.rollback_request_digest !== request.rollback_request_digest || subject.request_target_kind !== target.kind || !eq(before, request.from_state) || !before.enabled || before.coordinate === null || !eq(subject.history_head_before, canonicalHistory)) return "history_conflict";
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
  if (rule === "generation_activation") { const a = context.activation, valid = a.activation_receipt_digest === context.current_activation_digest && a.status === "activated" && a.revoked_by_digest === null && a.superseded_by_activation_receipt_digest === null && subject.activation_receipt_digest === subject.activation_head_digest && subject.activation_head_digest === context.current_activation_digest && subject.activation_head_revision === context.current_activation_revision && context.current_activation_revision === a.activation_revision && eq(subject.coordinate, a.coordinate) && eq(subject.runtime_identity, a.runtime_identity); return valid ? null : "activation_not_current"; }
  if (rule === "utc") return strictUtc(subject.recorded_at) ? null : "malformed_input";
  if (rule === "ak_decision") return decisionCurrent(subject, context) ? null : "self_certification";
  if (rule === "acceptance_binding") { const d = context.decision, valid = subject.acceptance_authority.kind === "consumer_owner" && subject.acceptance_authority.id === subject.consumer_repository.owner && subject.decision_reference_digest === d.ak_decision_reference_digest && subject.governing_scope_digest === d.scope_digest && decisionCurrent(d, context); return valid ? null : "self_certification"; }
  if (rule === "activation_binding") { const d = context.decision, valid = decisionCurrent(d, context) && subject.gate_decision_reference_digest === d.ak_decision_reference_digest && ["activation_target_digest", "evidence_criteria_digest", "rollback_plan_digest", "stop_conditions_digest"].every((k) => subject[k] === d[k]); return valid ? null : "self_certification"; }
  if (rule === "governance_contracts") {
    const consumer = context.consumer_contract, expectedPaths = ["config/semantic-release/canary.json", "docs/project/semantic-release-canary-evidence.md", "scripts/ci/semantic-release-canary.sh"];
    const noAuthority = [subject, consumer].every((x) => !x.authorizes_execution && !x.authorizes_publication && !x.authorizes_adoption && x.contract_status === "candidate_not_created");
    const separate = subject.task_contract_id !== consumer.task_contract_id && subject.rollback_owner.kind === "ak" && consumer.rollback_owner.kind === "consumer_owner";
    const exact = subject.task_kind === "ak_coordination" && subject.repository === "softwareco/owned/agent-kernel" && eq(subject.allowed_paths, []) && subject.authority_scope === "coordination_only" && consumer.task_kind === "first_consumer" && consumer.repository === "softwareco/pi-canary-consumer" && eq(consumer.allowed_paths, expectedPaths) && consumer.authority_scope === "consumer_owner_candidate_only";
    return noAuthority && separate && exact ? null : "self_certification";
  }
  if (["pi_variant", "ak_optional_pi"].includes(rule)) return null;
  fail(`unknown differential rule ${rule}`);
}

validateIjson(schema); validateIjson(golden); validateIjson(differential);
if (schema.$schema !== "https://json-schema.org/draft/2020-12/schema") fail("wrong schema draft");
(function closed(node, path = "$") { if (Array.isArray(node)) return node.forEach((x, i) => closed(x, `${path}/${i}`)); if (node && typeof node === "object") { if (node.type === "object" && node.additionalProperties !== false) fail(`open object ${path}`); if (node.$ref) resolve(node.$ref); Object.entries(node).forEach(([k, v]) => closed(v, `${path}/${k}`)); } })(schema);
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
let accepted = 0, rejected = 0;
for (const item of differential.cases) {
  let valid = true; try { structural(item.subject, schema); } catch { valid = false; }
  if (valid !== item.schema_valid) fail(`${item.name}: schema_valid expected ${item.schema_valid}, got ${valid}`);
  if (item.rule !== "digest" && !embeddedDigestValid(item.subject)) fail(`${item.name}: masked by digest`);
  let actual = valid ? null : item.expected_error;
  if (valid) { try { checkClaimScope(item.subject); } catch { actual = "issuer_scope_violation"; } if (actual === null) actual = evaluate(item.rule, item.subject, item.context); }
  if (actual === null) { try { checkOrder(item.subject); } catch { actual = "malformed_input"; } }
  if (actual !== item.expected_error) fail(`${item.name}: expected ${item.expected_error}, got ${actual}`); actual === null ? accepted++ : rejected++;
}
let rawAccepted = 0, rawRejected = 0;
for (const item of differential.raw_json_cases) { let actual = null; try { const parsed = strictJson(item.raw_json); if ((item.required_own_keys ?? []).some((key) => !Object.hasOwn(parsed, key))) actual = "malformed_input"; } catch { actual = "malformed_input"; } if (actual !== item.expected_error) fail(`${item.name}: expected ${item.expected_error}, got ${actual}`); actual === null ? rawAccepted++ : rawRejected++; }
console.log(`schema: Draft 2020-12, ${schema.oneOf.length} protocol types, all object shapes closed`);
console.log(`golden: ${records.size} object preimages and ${golden.raw_preimages.length} raw preimages independently recomputed`);
console.log(`chain: ${golden.chain_assertions.length} exact digest links verified`);
console.log(`differential: ${differential.cases.length} cases (${accepted} accepted transitions, ${rejected} expected rejections)`);
console.log(`raw-json: ${differential.raw_json_cases.length} lexical cases (${rawAccepted} accepted, ${rawRejected} expected rejections)`);
console.log("result: PASS (independent Node token-aware verifier; no Python imports or subprocesses)");
