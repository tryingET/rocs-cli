#!/usr/bin/env node
/** Independent Node stdlib conformance runner for Decision 85 insertion evidence. */

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const MAX_INT = 9_007_199_254_740_991;
const REVISION = "semantic-pi-insertion-evidence-v1-r1";
const VECTOR_SHA256 = "e23437e075f49c36e7487deeec2ab8126cd8fb14c0dbf07bf48d17e466525ed4";
const FROZEN_AGGREGATE = "272c892af593ff10ddb056b1914f20372308fe8a47ca28b3ca04ca8e27882991";
const ACCEPTED_AGGREGATE = "e1a715cd868bdd9807eecb798b29ac02342697cc2afd9ac8eb7d9b6296b97a7e";
const SCHEMA_NAMES = [
  "semantic-pi-insertion-request.v1",
  "pi.prompt-chain-application-witness.v1",
  "semantic-pi-insertion-acknowledgement.v1",
  "pi.prompt-chain-insertion-record.v1",
  "semantic-pi-insertion-error.v1",
  "semantic-pi-insertion-vector-set.v1",
];
const DOMAINS = [
  "semantic-pi-insertion.request.v1",
  "pi.prompt-chain-application-witness.v1",
  "semantic-pi-insertion.acknowledgement.v1",
  "pi.prompt-chain-insertion-record.v1",
  "semantic-pi-insertion.error.v1",
  "semantic-pi-insertion.input-prompt-bytes.v1",
  "semantic-pi-insertion.contribution-bytes.v1",
  "pi.prompt-chain-bytes.v1",
];
const OBJECT_DOMAINS = new Map([
  [SCHEMA_NAMES[0], [DOMAINS[0], "request_digest"]],
  [SCHEMA_NAMES[1], [DOMAINS[1], "witness_digest"]],
  [SCHEMA_NAMES[2], [DOMAINS[2], "acknowledgement_digest"]],
  [SCHEMA_NAMES[3], [DOMAINS[3], "insertion_record_digest"]],
  [SCHEMA_NAMES[4], [DOMAINS[4], "error_digest"]],
]);
const HOOKS = [
  "before_reservation", "after_reservation", "during_prepare", "after_prepare",
  "before_apply", "after_apply", "after_assignment", "after_readback", "before_witness",
  "after_witness", "during_applied", "after_applied", "before_record_commit",
  "after_record_commit", "after_guard_release", "after_failure",
];
const DIGEST_RE = /^sha256:[0-9a-f]{64}$/u;
const ID_RE = /^[a-z][a-z0-9-]*$/u;
const DECIMAL_RE = /^(?:0|[1-9][0-9]*)$/u;
const SPAN_RE = /^(0|[1-9][0-9]*):(0|[1-9][0-9]*)$/u;
const utf8Decoder = new TextDecoder("utf-8", { fatal: true, ignoreBOM: true });

class ConformanceError extends Error {}
class StrictJSONError extends ConformanceError {}
class ProtocolFailure extends Error {
  constructor(stage, code) {
    super(`${stage}/${code}`);
    this.stage = stage;
    this.code = code;
  }
}

function requireCondition(condition, message) {
  if (!condition) throw new ConformanceError(message);
}

function validScalarText(value) {
  if (value.normalize("NFC") !== value) return false;
  for (const character of value) {
    const point = character.codePointAt(0);
    if ((point >= 0xd800 && point <= 0xdfff) || (point >= 0xfdd0 && point <= 0xfdef)
      || (point & 0xffff) === 0xfffe || (point & 0xffff) === 0xffff) return false;
  }
  return true;
}

class StrictJSONParser {
  constructor(raw, label) {
    if (raw.length >= 3 && raw[0] === 0xef && raw[1] === 0xbb && raw[2] === 0xbf) {
      throw new StrictJSONError(`${label}: BOM is forbidden`);
    }
    try {
      this.source = utf8Decoder.decode(raw);
    } catch (error) {
      throw new StrictJSONError(`${label}: invalid UTF-8: ${error.message}`);
    }
    this.label = label;
    this.position = 0;
  }

  fail(message) { throw new StrictJSONError(`${this.label}: ${message} at character ${this.position}`); }
  whitespace() {
    while (this.position < this.source.length && /[\u0009\u000a\u000d\u0020]/u.test(this.source[this.position])) this.position += 1;
  }
  parse() {
    this.whitespace();
    const value = this.value();
    this.whitespace();
    if (this.position !== this.source.length) this.fail("trailing bytes");
    return value;
  }
  value() {
    const character = this.source[this.position];
    if (character === "{") return this.object();
    if (character === "[") return this.array();
    if (character === '"') return this.string();
    if (character === "t") return this.literal("true", true);
    if (character === "f") return this.literal("false", false);
    if (character === "n") return this.literal("null", null);
    if (character === "-" || (character >= "0" && character <= "9")) return this.number();
    this.fail("expected JSON value");
  }
  literal(token, value) {
    if (this.source.slice(this.position, this.position + token.length) !== token) this.fail(`invalid literal ${token}`);
    this.position += token.length;
    return value;
  }
  number() {
    const start = this.position;
    if (this.source[this.position] === "-") this.position += 1;
    if (this.source[this.position] === "0") {
      this.position += 1;
      if (/[0-9]/u.test(this.source[this.position] ?? "")) this.fail("leading zero in integer");
    } else {
      if (!/[1-9]/u.test(this.source[this.position] ?? "")) this.fail("invalid integer");
      while (/[0-9]/u.test(this.source[this.position] ?? "")) this.position += 1;
    }
    if (/[.eE]/u.test(this.source[this.position] ?? "")) this.fail("floats and exponents are forbidden");
    const token = this.source.slice(start, this.position);
    let integer;
    try { integer = BigInt(token); } catch { this.fail("invalid integer"); }
    if (integer < 0n || integer > BigInt(MAX_INT)) this.fail("integer outside I-JSON range");
    return Number(integer);
  }
  unicodeEscape() {
    const token = this.source.slice(this.position, this.position + 4);
    if (!/^[0-9a-fA-F]{4}$/u.test(token)) this.fail("invalid Unicode escape");
    this.position += 4;
    return Number.parseInt(token, 16);
  }
  string() {
    this.position += 1;
    let result = "";
    while (this.position < this.source.length) {
      let unit = this.source.charCodeAt(this.position++);
      if (unit === 0x22) {
        if (!validScalarText(result)) this.fail("string is not an NFC Unicode scalar string");
        return result;
      }
      if (unit === 0x5c) {
        const escape = this.source[this.position++];
        const simple = { '"': '"', "\\": "\\", "/": "/", b: "\b", f: "\f", n: "\n", r: "\r", t: "\t" };
        if (Object.hasOwn(simple, escape)) { result += simple[escape]; continue; }
        if (escape !== "u") this.fail("invalid string escape");
        unit = this.unicodeEscape();
        if (unit >= 0xd800 && unit <= 0xdbff) {
          if (this.source.slice(this.position, this.position + 2) !== "\\u") this.fail("lone high surrogate");
          this.position += 2;
          const low = this.unicodeEscape();
          if (low < 0xdc00 || low > 0xdfff) this.fail("invalid surrogate pair");
          result += String.fromCodePoint(0x10000 + ((unit - 0xd800) << 10) + low - 0xdc00);
        } else {
          if (unit >= 0xdc00 && unit <= 0xdfff) this.fail("lone low surrogate");
          result += String.fromCodePoint(unit);
        }
        continue;
      }
      if (unit < 0x20) this.fail("unescaped control character");
      if (unit >= 0xd800 && unit <= 0xdbff) {
        const low = this.source.charCodeAt(this.position++);
        if (low < 0xdc00 || low > 0xdfff) this.fail("invalid raw surrogate pair");
        result += String.fromCodePoint(0x10000 + ((unit - 0xd800) << 10) + low - 0xdc00);
      } else {
        if (unit >= 0xdc00 && unit <= 0xdfff) this.fail("lone raw low surrogate");
        result += String.fromCodePoint(unit);
      }
    }
    this.fail("unterminated string");
  }
  array() {
    this.position += 1; this.whitespace();
    const result = [];
    if (this.source[this.position] === "]") { this.position += 1; return result; }
    while (true) {
      result.push(this.value()); this.whitespace();
      const delimiter = this.source[this.position++];
      if (delimiter === "]") return result;
      if (delimiter !== ",") this.fail("expected array delimiter");
      this.whitespace();
    }
  }
  object() {
    this.position += 1; this.whitespace();
    const result = Object.create(null);
    if (this.source[this.position] === "}") { this.position += 1; return result; }
    while (true) {
      if (this.source[this.position] !== '"') this.fail("object key must be a string");
      const key = this.string();
      if (Object.hasOwn(result, key)) this.fail(`duplicate key ${key}`);
      this.whitespace();
      if (this.source[this.position++] !== ":") this.fail("expected object colon");
      this.whitespace(); result[key] = this.value(); this.whitespace();
      const delimiter = this.source[this.position++];
      if (delimiter === "}") return result;
      if (delimiter !== ",") this.fail("expected object delimiter");
      this.whitespace();
    }
  }
}

function strictJSONLoads(raw, label) { return new StrictJSONParser(raw, label).parse(); }
function jcsBytes(value) {
  function render(item) {
    if (item === null) return "null";
    if (item === true) return "true";
    if (item === false) return "false";
    if (typeof item === "number" && Number.isSafeInteger(item) && item >= 0) return String(item);
    if (typeof item === "string" && validScalarText(item)) return JSON.stringify(item);
    if (Array.isArray(item)) return `[${item.map(render).join(",")}]`;
    if (item !== null && typeof item === "object" && Object.keys(item).every(validScalarText)) {
      return `{${Object.keys(item).sort().map((key) => `${render(key)}:${render(item[key])}`).join(",")}}`;
    }
    throw new ConformanceError("value is outside the restricted JCS profile");
  }
  return Buffer.from(render(value), "utf8");
}
function sha256(raw) { return createHash("sha256").update(raw).digest("hex"); }
function objectDigest(domain, value, selfField) {
  const preimage = Object.fromEntries(Object.entries(value).filter(([key]) => key !== selfField));
  return `sha256:${sha256(Buffer.concat([Buffer.from(domain), Buffer.from([0]), jcsBytes(preimage)]))}`;
}
function rawDigest(domain, raw) {
  const length = Buffer.alloc(8); length.writeBigUInt64BE(BigInt(raw.length));
  return `sha256:${sha256(Buffer.concat([Buffer.from(domain), Buffer.from([0]), length, raw]))}`;
}
function canonicalBase64(value, label) {
  requireCondition(typeof value === "string", `${label}: base64 value must be a string`);
  const syntax = /^(?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|[A-Za-z0-9+/]{3}=)?$/u;
  requireCondition(value.length % 4 === 0 && syntax.test(value), `${label}: invalid base64`);
  const raw = Buffer.from(value, "base64");
  requireCondition(raw.toString("base64") === value, `${label}: base64 is not canonical padded standard base64`);
  return raw;
}
function snapshotText(raw, minimum, maximum) {
  if (raw.length < minimum || raw.length > maximum) return false;
  try {
    const value = utf8Decoder.decode(raw);
    return validScalarText(value) && Buffer.from(value, "utf8").equals(raw);
  } catch { return false; }
}
function same(left, right) {
  if (left === null || right === null || typeof left !== "object" || typeof right !== "object") return Object.is(left, right);
  if (Array.isArray(left) !== Array.isArray(right)) return false;
  if (Array.isArray(left)) return left.length === right.length && left.every((value, index) => same(value, right[index]));
  const leftKeys = Object.keys(left); const rightKeys = Object.keys(right);
  return leftKeys.length === rightKeys.length && leftKeys.every((key) => Object.hasOwn(right, key) && same(left[key], right[key]));
}
function resolveRef(root, ref) {
  requireCondition(typeof ref === "string" && ref.startsWith("#/"), `non-local schema reference: ${ref}`);
  let value = root;
  for (const rawToken of ref.slice(2).split("/")) {
    const token = rawToken.replaceAll("~1", "/").replaceAll("~0", "~");
    requireCondition(value !== null && typeof value === "object" && Object.hasOwn(value, token), `unresolved local schema reference: ${ref}`);
    value = value[token];
  }
  return value;
}
function schemaMatches(instance, schema, root) {
  if (Object.hasOwn(schema, "$ref")) return schemaMatches(instance, resolveRef(root, schema.$ref), root);
  if (Object.hasOwn(schema, "oneOf") && schema.oneOf.filter((choice) => schemaMatches(instance, choice, root)).length !== 1) return false;
  if (Object.hasOwn(schema, "const") && !same(instance, schema.const)) return false;
  if (Object.hasOwn(schema, "enum") && !schema.enum.some((choice) => same(instance, choice))) return false;
  const checks = { null: instance === null, boolean: typeof instance === "boolean", integer: Number.isSafeInteger(instance), string: typeof instance === "string", array: Array.isArray(instance), object: instance !== null && typeof instance === "object" && !Array.isArray(instance) };
  if (schema.type !== undefined && !checks[schema.type]) return false;
  if (Number.isSafeInteger(instance) && (instance < (schema.minimum ?? instance) || instance > (schema.maximum ?? instance))) return false;
  if (typeof instance === "string") {
    if (instance.length < (schema.minLength ?? 0) || instance.length > (schema.maxLength ?? instance.length)) return false;
    if (schema.pattern !== undefined && !(new RegExp(schema.pattern, "u")).test(instance)) return false;
  }
  if (Array.isArray(instance)) {
    if (instance.length < (schema.minItems ?? 0) || instance.length > (schema.maxItems ?? instance.length)) return false;
    if (schema.items !== undefined && !instance.every((child) => schemaMatches(child, schema.items, root))) return false;
  }
  if (checks.object && (schema.properties !== undefined || schema.required !== undefined)) {
    const properties = schema.properties ?? {};
    if ((schema.required ?? []).some((key) => !Object.hasOwn(instance, key))) return false;
    if (schema.additionalProperties === false && Object.keys(instance).some((key) => !Object.hasOwn(properties, key))) return false;
    if (Object.entries(properties).some(([key, child]) => Object.hasOwn(instance, key) && !schemaMatches(instance[key], child, root))) return false;
  }
  return true;
}
function inspectSchema(schema) {
  requireCondition(schema.$schema === "https://json-schema.org/draft/2020-12/schema", "schema draft mismatch");
  requireCondition(same(Object.keys(schema.$defs ?? {}), SCHEMA_NAMES), "bundle must have exactly the six named top-level schemas");
  requireCondition(same(schema["x-digest-domains"], DOMAINS), "bundle must declare exactly the eight closed domains");
  requireCondition(same((schema.oneOf ?? []).map((choice) => choice.$ref), SCHEMA_NAMES.map((name) => `#/$defs/${name}`)), "root schema union mismatch");
  function walk(value) {
    if (Array.isArray(value)) value.forEach(walk);
    else if (value !== null && typeof value === "object") {
      if (Object.hasOwn(value, "$ref")) resolveRef(schema, value.$ref);
      if (value.type === "object") requireCondition(value.additionalProperties === false, "every object schema must be closed");
      Object.values(value).forEach(walk);
    }
  }
  walk(schema);
}

const COMMON_COMPAT = {
  reserve: ["after_reservation"], prepare_return_base64: ["during_prepare"], apply_span: ["after_apply"],
  assign_base64: ["after_assignment"], readback_base64: ["after_readback"], issue_witness: ["after_witness"],
  applied_return_digest: ["after_applied"], commit_record: ["after_record_commit"],
  abort_signal: HOOKS.filter((hook) => hook.startsWith("before_") || hook.startsWith("during_")),
  replace_ack_issuer: ["after_applied"], inject_ack_bytes_base64: ["after_applied"],
  invoke_nested_prompt: ["during_applied"], reserve_attempt_override: ["before_reservation"],
  replace_registration_component_id: ["before_reservation"], advance_monotonic_ns: HOOKS,
  reload_generation: HOOKS, clone_witness_json: ["before_witness", "after_witness"], consume_witness_twice: ["during_applied"],
};
const FIXTURE_COMPAT = {
  prompt_attempt: ["during_applied", "before_record_commit"], continuation_attempt: ["during_applied", "before_record_commit"],
  completion_attempt: ["during_applied", "before_record_commit"], provider_dispatch_attempt: ["during_applied", "before_record_commit"],
  model_invocation_attempt: ["during_applied", "before_record_commit"], contributor_callback_attempt: ["during_applied", "before_record_commit"],
  stale_api_call: ["after_failure"], detached_callback_call: ["during_applied"], provider_dispatch_eligibility: ["after_guard_release"],
  applied_throw: ["during_applied"], record_commit: ["after_record_commit", "after_failure"], create_registration_b: ["before_reservation"],
  consume_from_registration_b: ["during_applied"], consume_stale_witness: ["after_failure"], defer_applied: ["during_applied"],
  settle_applied: ["after_failure"], start_next_attempt: ["after_failure"], assign: ["after_assignment"], readback: ["after_readback"], witness_issued: ["after_witness"],
};
const EXACT_VALUES = {
  abort_signal: ["set"], invoke_nested_prompt: ["attempt"], clone_witness_json: ["true"], consume_witness_twice: ["true"],
  stale_api_call: ["rejected"], detached_callback_call: ["rejected"], provider_dispatch_eligibility: ["released"], applied_throw: ["error"],
  create_registration_b: ["other-component"], consume_from_registration_b: ["rejected"], consume_stale_witness: ["rejected"],
  defer_applied: ["pending"], settle_applied: ["late"], start_next_attempt: ["allowed"], assign: ["done"], readback: ["verified"],
  witness_issued: ["after_assign", "after_readback", "generation0"],
};
class Schedule {
  constructor(events, fixture) {
    requireCondition(Array.isArray(events) && events.length >= 1 && events.length <= 64, "events must contain 1..64 rows");
    const compatibility = { ...COMMON_COMPAT, ...(fixture ? FIXTURE_COMPAT : {}) };
    this.events = events; this.used = new Set();
    const seen = new Set(); const positions = [];
    events.forEach((event) => {
      requireCondition(event !== null && typeof event === "object" && same(Object.keys(event).sort(), ["at_hook", "kind", "value"]), "invalid event row");
      const { at_hook: hook, kind, value } = event;
      requireCondition(typeof hook === "string" && typeof kind === "string" && typeof value === "string", "event fields must be strings");
      requireCondition(Object.hasOwn(compatibility, kind) && compatibility[kind].includes(hook), `hook-incompatible or unknown event: ${hook}/${kind}`);
      requireCondition(!seen.has(`${hook}\0${kind}`), `duplicate event pair: ${hook}/${kind}`);
      seen.add(`${hook}\0${kind}`); positions.push(HOOKS.indexOf(hook)); Schedule.validateValue(kind, value);
    });
    requireCondition(positions.every((value, index) => index === 0 || positions[index - 1] <= value), "events are not in hook order");
  }
  static validateValue(kind, value) {
    if (["reserve", "reserve_attempt_override", "advance_monotonic_ns", "reload_generation"].includes(kind)) {
      requireCondition(DECIMAL_RE.test(value) && BigInt(value) <= BigInt(MAX_INT), `invalid decimal event value: ${kind}`);
    } else if (["prepare_return_base64", "assign_base64", "readback_base64", "inject_ack_bytes_base64"].includes(kind)) canonicalBase64(value, kind);
    else if (kind === "apply_span") {
      const match = SPAN_RE.exec(value); requireCondition(match !== null && match.slice(1).every((part) => BigInt(part) <= BigInt(MAX_INT)), "invalid apply span");
    } else if (["issue_witness", "applied_return_digest", "commit_record"].includes(kind)) requireCondition(DIGEST_RE.test(value), `invalid digest assertion: ${kind}`);
    else if (Object.hasOwn(EXACT_VALUES, kind)) requireCondition(EXACT_VALUES[kind].includes(value), `invalid event value: ${kind}=${value}`);
    else if (kind === "record_commit") requireCondition(["done", "forbidden"].includes(value), "invalid record_commit value");
    else if (kind.endsWith("_attempt")) {
      const allowed = kind === "contributor_callback_attempt" ? ["blocked", "reentry", "stale"] : ["blocked", "reentry"];
      requireCondition(allowed.includes(value), `invalid entrypoint event value: ${kind}=${value}`);
    } else requireCondition(value.length > 0, `empty event value: ${kind}`);
  }
  take(hook) {
    const rows = [];
    this.events.forEach((event, index) => {
      if (event.at_hook === hook) { requireCondition(!this.used.has(index), `event consumed twice at ${hook}`); this.used.add(index); rows.push(event); }
    });
    return rows;
  }
  finish() { requireCondition(this.used.size === this.events.length, "unreachable or unused event"); }
}

function makeRequest(generation, attempt, index, inputRaw, contribution) {
  const value = { schema: SCHEMA_NAMES[0], protocol_revision: REVISION, repository_id: "pi-extensions", component_id: "pi-ontology-workflows", package_name: "@tryinget/pi-ontology-workflows", execution_generation: generation, attempt_id: attempt, handler_registration_index: index, input_prompt_byte_length: inputRaw.length, input_prompt_digest: rawDigest(DOMAINS[5], inputRaw), contribution_byte_length: contribution.length, contribution_digest: rawDigest(DOMAINS[6], contribution) };
  value.request_digest = objectDigest(DOMAINS[0], value, "request_digest"); return value;
}
function makeWitness(request, assigned, readback, start, end) {
  const value = { schema: SCHEMA_NAMES[1], host_package: "@earendil-works/pi-coding-agent", protocol_revision: REVISION, request_digest: request.request_digest, execution_generation: request.execution_generation, attempt_id: request.attempt_id, handler_registration_index: request.handler_registration_index, assigned_prompt_chain_byte_length: assigned.length, assigned_prompt_chain_digest: rawDigest(DOMAINS[7], assigned), readback_prompt_chain_byte_length: readback.length, readback_prompt_chain_digest: rawDigest(DOMAINS[7], readback), contribution_start_byte_offset: start, contribution_end_byte_offset: end, observation_phase: "post_assignment_readback_pre_dispatch", provider_request_dispatched_at_observation: false, model_invocation_started_at_observation: false };
  value.witness_digest = objectDigest(DOMAINS[1], value, "witness_digest"); return value;
}
function makeAcknowledgement(request, witness) {
  const value = { schema: SCHEMA_NAMES[2], issuer: { kind: "pi_extension_component", id: "pi-ontology-workflows" }, request_digest: request.request_digest, witness_digest: witness.witness_digest, execution_generation: request.execution_generation, attempt_id: request.attempt_id, handler_registration_index: request.handler_registration_index, acknowledgement_outcome: "observed_inserted", claim_scope: "prompt_chain_insertion_only" };
  value.acknowledgement_digest = objectDigest(DOMAINS[2], value, "acknowledgement_digest"); return value;
}
function makeRecord(request, witness, acknowledgement) {
  const value = { schema: SCHEMA_NAMES[3], host_package: "@earendil-works/pi-coding-agent", protocol_revision: REVISION, request_digest: request.request_digest, witness_digest: witness.witness_digest, acknowledgement_digest: acknowledgement.acknowledgement_digest, execution_generation: request.execution_generation, attempt_id: request.attempt_id, handler_registration_index: request.handler_registration_index, insertion_outcome: "observed_inserted", claim_scope: "prompt_chain_insertion_only", provider_request_dispatched_at_record: false, model_invocation_started_at_record: false, record_phase: "acknowledged_pre_dispatch" };
  value.insertion_record_digest = objectDigest(DOMAINS[3], value, "insertion_record_digest"); return value;
}
function makeError(generation, attempt, stage, code) {
  const value = { schema: SCHEMA_NAMES[4], protocol_revision: REVISION, execution_generation: generation, attempt_id_or_null: attempt, stage, error_code: code, details: [] };
  value.error_digest = objectDigest(DOMAINS[4], value, "error_digest"); return value;
}

function runAttempt(spec, fixture) {
  const schedule = new Schedule(spec.events, fixture);
  const generation = spec.initial_generation; let nextAttempt = spec.initial_next_attempt_id;
  const index = spec.handler_registration_index; const deadline = spec.deadline_monotonic_ns;
  requireCondition([generation, nextAttempt, index, deadline].every((value) => Number.isSafeInteger(value) && value >= 0), "invalid attempt integer");
  const inputRaw = canonicalBase64(spec.input_bytes_base64, "input_bytes_base64");
  const defaultContribution = canonicalBase64(spec.contribution_bytes_base64, "contribution_bytes_base64");
  let currentGeneration = generation; let now = 0; let aborted = false;
  let registrationComponent = "pi-ontology-workflows"; let reservationOverride = null; let attempt = null;
  let request = null; let witness = null; let acknowledgement = null; let record = null;
  let state = "reserved"; let guardActive = false; let frameActive = false;
  const providerBeforeRecord = 0; const modelBeforeRecord = 0; const controls = [];
  let cloned = false; let reused = false; let poisoned = false; let deferred = false; let threw = false; let registrationB = false;
  let assignedDone = false; let readbackDone = false; let witnessDone = false;

  function generic(event) {
    if (event.kind === "advance_monotonic_ns") now = Number(event.value);
    else if (event.kind === "reload_generation") { requireCondition(Number(event.value) > currentGeneration, "reload_generation must advance generation"); currentGeneration = Number(event.value); }
    else if (event.kind === "abort_signal") aborted = true;
    else return false;
    return true;
  }
  function predicate(stage, before = []) {
    if (currentGeneration !== generation) throw new ProtocolFailure(stage, "stale_generation");
    for (const [established, code] of before) if (established) throw new ProtocolFailure(code === "reentry_attempt" ? "dispatch_guard" : "witness", code);
    if (aborted) throw new ProtocolFailure(stage, "aborted");
    if (now >= deadline) throw new ProtocolFailure(stage, "deadline_exceeded");
  }
  function addControl(kind, entrypointName) {
    requireCondition(attempt !== null, "control result before reservation");
    controls.push({ kind, entrypoint: entrypointName, execution_generation: generation, attempt_id: attempt });
  }
  function entrypoint(event) {
    const mapping = { prompt_attempt: "prompt", continuation_attempt: "continuation", completion_attempt: "completion", provider_dispatch_attempt: "provider_dispatch", model_invocation_attempt: "model_invocation", contributor_callback_attempt: "contributor_callback" };
    if (!Object.hasOwn(mapping, event.kind)) return false;
    if (event.value === "blocked") { requireCondition(guardActive, "blocked classification without guard"); addControl("dispatch_blocked", mapping[event.kind]); }
    else if (event.value === "reentry") { requireCondition(guardActive && frameActive, "reentry classification without matching frame"); poisoned = true; }
    else { addControl("stale_invocation", mapping[event.kind]); poisoned = guardActive; }
    return true;
  }

  let failure = null;
  try {
    for (const event of schedule.take("before_reservation")) {
      if (generic(event)) continue;
      if (event.kind === "reserve_attempt_override") reservationOverride = Number(event.value);
      else if (event.kind === "replace_registration_component_id") registrationComponent = event.value;
      else if (event.kind === "create_registration_b") registrationB = true;
    }
    if (registrationComponent !== "pi-ontology-workflows") throw new ProtocolFailure("registration", "identity_mismatch");
    if (currentGeneration !== generation) throw new ProtocolFailure("registration", "stale_generation");
    if (aborted) throw new ProtocolFailure("registration", "aborted");
    if (now >= deadline) throw new ProtocolFailure("registration", "deadline_exceeded");
    const candidate = reservationOverride === null ? nextAttempt : reservationOverride;
    if (nextAttempt === MAX_INT || candidate !== nextAttempt) throw new ProtocolFailure("registration", "attempt_reuse");
    attempt = candidate; nextAttempt += 1; guardActive = true; state = "reserved";
    for (const event of schedule.take("after_reservation")) { if (generic(event)) continue; requireCondition(event.kind === "reserve" && event.value === String(attempt), "reservation assertion failed"); }

    predicate("prepare"); state = "preparing"; frameActive = true; let contribution = defaultContribution;
    for (const event of schedule.take("during_prepare")) { if (generic(event)) continue; if (event.kind === "prepare_return_base64") contribution = canonicalBase64(event.value, "prepare_return_base64"); }
    predicate("prepare");
    if (!snapshotText(inputRaw, 0, 16_777_216) || !snapshotText(contribution, 1, 16_777_216)) throw new ProtocolFailure("prepare", "malformed_input");
    frameActive = false; state = "prepared"; request = makeRequest(generation, attempt, index, inputRaw, contribution);
    for (const event of schedule.take("after_prepare")) requireCondition(generic(event), "unsupported after_prepare event");
    for (const event of schedule.take("before_apply")) requireCondition(generic(event), "unsupported before_apply event");
    predicate("apply"); state = "applying"; let start = inputRaw.length; let end = inputRaw.length + contribution.length;
    for (const event of schedule.take("after_apply")) {
      if (generic(event)) continue;
      const match = SPAN_RE.exec(event.value); requireCondition(event.kind === "apply_span" && match !== null, "invalid apply event");
      start = Number(match[1]); end = Number(match[2]);
    }
    const assigned = start <= inputRaw.length ? Buffer.concat([inputRaw.subarray(0, start), contribution, inputRaw.subarray(start)]) : Buffer.concat([inputRaw, contribution]);
    if (!snapshotText(assigned, 1, 33_554_432)) throw new ProtocolFailure("apply", "malformed_input");
    const inserted = start < end && end <= assigned.length && end - start === contribution.length && assigned.subarray(start, end).equals(contribution);
    if (!inserted) throw new ProtocolFailure("apply", "contribution_not_inserted");
    predicate("assignment"); assignedDone = true; state = "assigned";
    for (const event of schedule.take("after_assignment")) {
      if (generic(event)) continue;
      if (event.kind === "assign_base64") requireCondition(canonicalBase64(event.value, "assign_base64").equals(assigned), "assignment assertion failed");
      else if (event.kind === "assign") requireCondition(event.value === "done" && assignedDone, "assignment order assertion failed");
    }
    let readback = assigned;
    for (const event of schedule.take("after_readback")) {
      if (generic(event)) continue;
      if (event.kind === "readback_base64") readback = canonicalBase64(event.value, "readback_base64");
      else if (event.kind === "readback") requireCondition(event.value === "verified" && assignedDone, "readback order assertion failed");
    }
    if (!snapshotText(readback, 1, 33_554_432)) throw new ProtocolFailure("readback", "malformed_input");
    predicate("readback"); if (!readback.equals(assigned)) throw new ProtocolFailure("readback", "readback_mismatch");
    readbackDone = true; state = "readback_verified";
    for (const event of schedule.take("before_witness")) { if (generic(event)) continue; if (event.kind === "clone_witness_json") cloned = true; }
    predicate("witness"); witness = makeWitness(request, assigned, readback, start, end); witnessDone = true; state = "witnessed";
    for (const event of schedule.take("after_witness")) {
      if (generic(event)) continue;
      if (event.kind === "issue_witness") requireCondition(event.value === witness.witness_digest, "witness digest assertion failed");
      else if (event.kind === "clone_witness_json") cloned = true;
      else if (event.kind === "witness_issued") {
        const facts = { after_assign: assignedDone, after_readback: readbackDone, generation0: generation === 0 };
        requireCondition(facts[event.value] && witnessDone, "witness order assertion failed");
      }
    }
    if (currentGeneration !== generation) throw new ProtocolFailure("acknowledgement", "stale_generation");
    if (cloned) throw new ProtocolFailure("witness", "witness_forged");

    state = "acknowledging"; frameActive = true;
    for (const event of schedule.take("during_applied")) {
      if (generic(event) || entrypoint(event)) continue;
      if (event.kind === "consume_witness_twice") reused = true;
      else if (event.kind === "invoke_nested_prompt") poisoned = true;
      else if (event.kind === "detached_callback_call") addControl("dispatch_blocked", "contributor_callback");
      else if (event.kind === "consume_from_registration_b") { requireCondition(registrationB, "registration B was not created"); addControl("stale_invocation", "contributor_callback"); poisoned = true; }
      else if (event.kind === "defer_applied") deferred = true;
      else if (event.kind === "applied_throw") threw = true;
    }
    predicate("acknowledgement", [[reused, "witness_reused"], [poisoned, "reentry_attempt"]]);
    if (threw) throw new ProtocolFailure("acknowledgement", "internal_failure");
    if (deferred) throw new ConformanceError("deferred callback remained pending without terminal observer");
    acknowledgement = makeAcknowledgement(request, witness); let malformedAck = false;
    for (const event of schedule.take("after_applied")) {
      if (generic(event)) continue;
      if (event.kind === "replace_ack_issuer") acknowledgement.issuer = { kind: "pi_extension_component", id: event.value };
      else if (event.kind === "inject_ack_bytes_base64") {
        try {
          const candidateAck = strictJSONLoads(canonicalBase64(event.value, event.kind), event.kind);
          if (candidateAck === null || typeof candidateAck !== "object" || Array.isArray(candidateAck)) throw new StrictJSONError("acknowledgement is not an object");
          acknowledgement = candidateAck;
        } catch (error) { if (!(error instanceof ConformanceError)) throw error; malformedAck = true; }
      } else if (event.kind === "applied_return_digest") requireCondition(acknowledgement.acknowledgement_digest === event.value, "acknowledgement digest assertion failed");
    }
    if (malformedAck) throw new ProtocolFailure("acknowledgement", "malformed_input");
    predicate("acknowledgement");
    const ackKeys = ["schema", "issuer", "request_digest", "witness_digest", "execution_generation", "attempt_id", "handler_registration_index", "acknowledgement_outcome", "claim_scope", "acknowledgement_digest"];
    const issuer = acknowledgement.issuer;
    const shapeOK = same(Object.keys(acknowledgement).sort(), [...ackKeys].sort())
      && issuer !== null && typeof issuer === "object" && !Array.isArray(issuer) && same(Object.keys(issuer).sort(), ["id", "kind"])
      && ["schema", "request_digest", "witness_digest", "acknowledgement_outcome", "claim_scope", "acknowledgement_digest"].every((key) => typeof acknowledgement[key] === "string")
      && ["execution_generation", "attempt_id", "handler_registration_index"].every((key) => Number.isSafeInteger(acknowledgement[key]))
      && Object.values(issuer).every((value) => typeof value === "string") && DIGEST_RE.test(acknowledgement.acknowledgement_digest);
    if (!shapeOK) throw new ProtocolFailure("acknowledgement", "malformed_input");
    if (!same(acknowledgement, makeAcknowledgement(request, witness))) throw new ProtocolFailure("acknowledgement", "acknowledgement_mismatch");
    frameActive = false;

    for (const event of schedule.take("before_record_commit")) { if (generic(event) || entrypoint(event)) continue; }
    predicate("record", [[false, "witness_reused"], [poisoned, "reentry_attempt"]]);
    record = makeRecord(request, witness, acknowledgement); state = "record_committed";
    for (const event of schedule.take("after_record_commit")) {
      if (generic(event)) continue;
      if (event.kind === "commit_record") requireCondition(event.value === record.insertion_record_digest, "record digest assertion failed");
      else if (event.kind === "record_commit") requireCondition(event.value === "done" && record !== null, "record commit assertion failed");
    }
    guardActive = false; state = "dispatch_eligible";
    for (const event of schedule.take("after_guard_release")) {
      if (generic(event)) continue;
      requireCondition(event.kind === "provider_dispatch_eligibility" && event.value === "released", "guard release assertion failed");
    }
    schedule.finish();
  } catch (error) {
    if (!(error instanceof ProtocolFailure)) throw error;
    failure = error; frameActive = false; guardActive = false; state = "failed";
    for (const event of schedule.take("after_failure")) {
      if (generic(event)) continue;
      if (event.kind === "settle_applied") requireCondition(event.value === "late" && deferred, "late settlement assertion failed");
      else if (event.kind === "start_next_attempt") requireCondition(event.value === "allowed" && attempt !== null && nextAttempt < MAX_INT, "next attempt was not released");
      else if (event.kind === "record_commit") requireCondition(event.value === "forbidden" && record === null, "record committed after failure");
      else if (["consume_stale_witness", "stale_api_call"].includes(event.kind)) { requireCondition(witnessDone && event.value === "rejected", "stale witness/API assertion failed"); addControl("stale_invocation", "contributor_callback"); }
    }
    schedule.finish();
  }
  const metadata = { terminal_state: state, provider_operations_before_record: providerBeforeRecord, model_operations_before_record: modelBeforeRecord, control_results: controls };
  const actual = failure === null
    ? { accepted: true, error_or_null: null, request_or_null: request, witness_or_null: witness, acknowledgement_or_null: acknowledgement, record_or_null: record }
    : { accepted: false, error_or_null: makeError(generation, attempt, failure.stage, failure.code), request_or_null: null, witness_or_null: null, acknowledgement_or_null: null, record_or_null: null };
  if (failure === null) requireCondition([request, witness, acknowledgement, record].every((value) => value !== null), "incomplete accepted execution");
  return [actual, metadata];
}

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
