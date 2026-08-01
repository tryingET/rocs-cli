#!/usr/bin/env node
/* Independent Node stdlib oracle for the committed semantic-router-v0 fixtures. */
import { createHash } from "node:crypto";
import { inflateSync } from "node:zlib";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const fixtureRoot = join(root, "docs/project/semantic-router-v0");
const discoveryRoot = join(root, "docs/project/semantic-discovery-v0");
const readJson = (path) => strictParse(readFileSync(path));
const assert = (condition, message) => { if (!condition) throw new Error(message); };

class LimitError extends Error {}
function strictParse(raw, { byteLimit=Number.MAX_SAFE_INTEGER, maxDepth=Number.MAX_SAFE_INTEGER, maxItems=Number.MAX_SAFE_INTEGER }={}) {
  let text; let items=0;
  if (raw.length > byteLimit) throw new LimitError("byte limit");
  if (raw.length >= 3 && raw[0] === 0xef && raw[1] === 0xbb && raw[2] === 0xbf) throw new Error("BOM forbidden");
  try { text = new TextDecoder("utf-8", { fatal: true }).decode(raw); }
  catch { throw new Error("invalid UTF-8"); }
  if (text.startsWith("\ufeff")) throw new Error("BOM forbidden");
  let index = 0;
  const ws = () => { while (/[ \t\r\n]/.test(text[index] ?? "")) index++; };
  const scalar = (value) => {
    for (let i = 0; i < value.length; i++) {
      const unit = value.charCodeAt(i);
      if (unit >= 0xd800 && unit <= 0xdbff) {
        if (++i >= value.length || value.charCodeAt(i) < 0xdc00 || value.charCodeAt(i) > 0xdfff) throw new Error("lone surrogate");
      } else if (unit >= 0xdc00 && unit <= 0xdfff) throw new Error("lone surrogate");
    }
    return value;
  };
  const string = () => {
    const start = index++;
    let escaped = false;
    while (index < text.length) {
      const ch = text[index++];
      if (escaped) escaped = false;
      else if (ch === "\\") escaped = true;
      else if (ch === '"') {
        const value = JSON.parse(text.slice(start, index));
        return scalar(value);
      }
    }
    throw new Error("unterminated string");
  };
  const value = (depth=0) => {
    ws();
    const ch = text[index];
    if (ch === '"') return string();
    if (ch === "{") {
      if (++depth > maxDepth) throw new LimitError("depth limit");
      index++; ws();
      const result = Object.create(null); const keys = new Set();
      if (text[index] === "}") { index++; return result; }
      while (true) {
        ws(); if (text[index] !== '"') throw new Error("object key required");
        const key = string(); if (keys.has(key)) throw new Error("duplicate key"); keys.add(key);
        if (++items > maxItems) throw new LimitError("item limit");
        ws(); if (text[index++] !== ":") throw new Error("colon required");
        result[key] = value(depth); ws();
        if (text[index] === "}") { index++; return result; }
        if (text[index++] !== ",") throw new Error("comma required");
      }
    }
    if (ch === "[") {
      if (++depth > maxDepth) throw new LimitError("depth limit");
      index++; ws(); const result = [];
      if (text[index] === "]") { index++; return result; }
      while (true) {
        if (++items > maxItems) throw new LimitError("item limit");
        result.push(value(depth)); ws();
        if (text[index] === "]") { index++; return result; }
        if (text[index++] !== ",") throw new Error("comma required");
      }
    }
    for (const [token, result] of [["true", true], ["false", false], ["null", null]]) {
      if (text.startsWith(token, index)) { index += token.length; return result; }
    }
    const match = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?/.exec(text.slice(index));
    if (!match) throw new Error("value required");
    index += match[0].length;
    if (/[.eE]/.test(match[0])) throw new Error("floating point forbidden");
    const integer = BigInt(match[0]);
    if (integer < -9007199254740991n || integer > 9007199254740991n) throw new Error("unsafe integer");
    return Number(integer);
  };
  const result = value(); ws();
  if (index !== text.length) throw new Error("trailing JSON");
  return result;
}

const quote = (value) => JSON.stringify(value);
function jcs(value) {
  if (value === null) return "null";
  if (value === true) return "true";
  if (value === false) return "false";
  if (typeof value === "number") { assert(Number.isSafeInteger(value), "non-I-JSON number"); return String(value); }
  if (typeof value === "string") return quote(value);
  if (Array.isArray(value)) return `[${value.map(jcs).join(",")}]`;
  const keys = Object.keys(value).sort();
  return `{${keys.map((key) => `${quote(key)}:${jcs(value[key])}`).join(",")}}`;
}
const utf8 = (value) => Buffer.from(value, "utf8");
const sha = (value) => createHash("sha256").update(value).digest("hex");
const domains = {
  routing_policy: ["rocs.routing-policy.v0", "routing_policy_digest"],
  provenance_manifest: ["rocs.routing-provenance.v0", "provenance_manifest_digest"],
  caller_request: ["rocs.route-caller-request.v0", null],
  effective_execution: ["rocs.route-effective-execution.v0", "effective_execution_digest"],
  result: ["rocs.route-result.v0", "result_digest"],
};
function digest(kind, value) {
  const [domain, field] = domains[kind];
  assert(domain, `unknown digest kind ${kind}`);
  const preimage = structuredClone(value); if (field) delete preimage[field];
  return `sha256:${sha(Buffer.concat([Buffer.from(domain, "ascii"), Buffer.from([0]), utf8(jcs(preimage))]))}`;
}

const own = (object, key) => Object.prototype.hasOwnProperty.call(object, key);
const same = (left, right) => typeof left === typeof right && jcs(left) === jcs(right);
const typeOk = (value, type) => ({
  object: value !== null && typeof value === "object" && !Array.isArray(value),
  array: Array.isArray(value), string: typeof value === "string",
  integer: Number.isSafeInteger(value), boolean: typeof value === "boolean", null: value === null,
})[type] ?? false;
const dateTimeOk = (value) => {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d+)?(?:Z|([+-])(\d{2}):(\d{2}))$/.exec(value);
  if (!match) return false;
  const [year, month, day, hour, minute, second] = match.slice(1, 7).map(Number);
  const days = new Date(Date.UTC(year, month, 0)).getUTCDate();
  return month >= 1 && month <= 12 && day >= 1 && day <= days && hour <= 23 && minute <= 59 && second <= 59
    && (!match[8] || (Number(match[8]) <= 23 && Number(match[9]) <= 59));
};

class RegistryError extends Error {}
function validator(routeSchema, discoverySchema) {
  const allowedExternal = "https://ai-society.local/rocs/semantic-discovery-v0/protocol.schema.json#/$defs/result";
  const resolve = (schema, rootSchema) => {
    if (!schema.$ref) return [schema, rootSchema];
    if (schema.$ref === allowedExternal) return [discoverySchema.$defs.result, discoverySchema];
    if (!schema.$ref.startsWith("#/$defs/")) throw new RegistryError("nonlocal schema reference");
    const found = rootSchema.$defs[schema.$ref.slice(8)];
    if (!found) throw new RegistryError("unresolved schema reference");
    return [found, rootSchema];
  };
  const check = (instance, inputSchema, rootSchema = routeSchema) => {
    let [schema, activeRoot] = resolve(inputSchema, rootSchema);
    if (schema.oneOf) return schema.oneOf.filter((branch) => check(instance, branch, activeRoot).length === 0).length === 1 ? [] : ["oneOf"];
    if (own(schema, "const") && !same(instance, schema.const)) return ["const"];
    if (schema.enum && !schema.enum.some((choice) => same(instance, choice))) return ["enum"];
    const types = Array.isArray(schema.type) ? schema.type : schema.type ? [schema.type] : [];
    if (types.length && !types.some((type) => typeOk(instance, type))) return ["type"];
    const issues = [];
    if (typeOk(instance, "object")) {
      for (const key of schema.required ?? []) if (!own(instance, key)) issues.push(`required:${key}`);
      if (schema.additionalProperties === false) for (const key of Object.keys(instance)) if (!own(schema.properties ?? {}, key)) issues.push(`additional:${key}`);
      for (const [key, child] of Object.entries(schema.properties ?? {})) if (own(instance, key)) issues.push(...check(instance[key], child, activeRoot));
    } else if (Array.isArray(instance)) {
      if (instance.length < (schema.minItems ?? 0)) issues.push("minItems");
      if (own(schema, "maxItems") && instance.length > schema.maxItems) issues.push("maxItems");
      if (schema.items) for (const child of instance) issues.push(...check(child, schema.items, activeRoot));
    } else if (typeof instance === "string") {
      const length = [...instance].length;
      if (length < (schema.minLength ?? 0)) issues.push("minLength");
      if (own(schema, "maxLength") && length > schema.maxLength) issues.push("maxLength");
      if (schema.pattern && !(new RegExp(`${schema.pattern}(?![\\s\\S])`, "u")).test(instance)) issues.push("pattern");
      if (schema.format === "date-time" && !dateTimeOk(instance)) issues.push("format");
    } else if (Number.isSafeInteger(instance)) {
      if (own(schema, "minimum") && instance < schema.minimum) issues.push("minimum");
      if (own(schema, "maximum") && instance > schema.maximum) issues.push("maximum");
    }
    return issues;
  };
  return (instance, name) => check(instance, routeSchema.$defs[name]);
}

// Unicode-15 data is compressed into this verifier. Native Node Unicode is never
// used for assignment, Letter/Number classification, or casefolding. NFKC is safe
// for already-assigned code points because Unicode normalization is version-stable.
const unpack = (encoded) => JSON.parse(inflateSync(Buffer.from(encoded, "base64")).toString("utf8"));
const ASSIGNED15 = unpack("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");
const LETTER_NUMBER15 = unpack("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");
const CASEFOLD15 = unpack("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");
const WHITE15 = new Set([9,10,11,12,13,32,133,160,5760,...Array.from({length:11},(_,i)=>8192+i),8232,8233,8239,8287,12288]);
const inRanges = (point, ranges) => {
  let low=0, high=ranges.length-1;
  while (low<=high) { const mid=(low+high)>>1, range=ranges[mid]; if (point<range[0]) high=mid-1; else if (point>range[1]) low=mid+1; else return true; }
  return false;
};
function normalize15(value) {
  const version15 = [...value].map((ch) => inRanges(ch.codePointAt(0), ASSIGNED15) ? ch : "\u0001").join("").normalize("NFKC");
  let folded="";
  for (const ch of version15) folded += CASEFOLD15[ch.codePointAt(0).toString(16)] ?? ch;
  const words=[]; let current="";
  for (const ch of folded) { const point=ch.codePointAt(0); if (WHITE15.has(point)) { if (current) words.push(current); current=""; } else current+=ch; }
  if (current) words.push(current);
  return words.join(" ");
}
function tokens15(value) {
  const tokens=[]; let current="";
  for (const ch of normalize15(value)) { const point=ch.codePointAt(0); if (inRanges(point, LETTER_NUMBER15)) current+=ch; else if (current) { tokens.push(current); current=""; } }
  if (current) tokens.push(current);
  return tokens;
}
function alternativeTokens(alternative) {
  const tokens = tokens15(alternative.value); const canonical = tokens.join(" ");
  assert(canonical === alternative.value, "noncanonical alternative");
  assert(alternative.kind === "token" ? tokens.length === 1 : alternative.kind === "phrase" && tokens.length >= 2, "invalid alternative kind/width");
  return tokens;
}
function matchGroup(query, group) {
  const matches = [];
  for (const alternative of group.any_of) {
    const wanted = alternativeTokens(alternative);
    for (let start = 0; start + wanted.length <= query.length; start++) {
      if (wanted.every((token, offset) => token === query[start + offset])) {
        matches.push({ group_id: group.group_id, kind: alternative.kind, value: alternative.value, start_token: start, end_token: start + wanted.length });
      }
    }
  }
  matches.sort((a, b) => a.start_token - b.start_token || a.end_token - b.end_token || (a.kind === b.kind ? Buffer.compare(utf8(a.value), utf8(b.value)) : a.kind === "token" ? -1 : 1));
  return matches[0] ?? null;
}
function matchClauses(owner, positiveKey, scope, ontId, routeId, query) {
  const output = [];
  for (const [polarity, key] of [["support", positiveKey], ["exclusion", "exclude_any"]]) {
    for (const clause of owner[key]) {
      const witnesses = clause.all_of.map((group) => matchGroup(query, group));
      if (witnesses.every(Boolean)) output.push({ scope, ont_id: ontId, joint_route_id: routeId, polarity, clause_id: clause.clause_id, witnesses: witnesses.sort((a, b) => Buffer.compare(utf8(a.group_id), utf8(b.group_id))) });
    }
  }
  return output;
}
const evidenceOrder = { domain: 0, concept: 1, joint_route: 2 };
function evaluate(policy, queryText) {
  const query = tokens15(queryText); const evidence = matchClauses(policy.domain, "admit_any", "domain", null, null, query);
  const plus = evidence.filter((x) => x.polarity === "support").map((x) => x.clause_id).sort();
  const minus = evidence.filter((x) => x.polarity === "exclusion").map((x) => x.clause_id).sort();
  let admission;
  if (!plus.length && !minus.length) admission = ["abstained", "no_policy_domain_support"];
  else if (!plus.length) admission = ["abstained", "explicit_domain_exclusion"];
  else if (minus.length) admission = ["abstained", "domain_support_exclusion_conflict"];
  else admission = ["admitted", "domain_support"];
  const supported = [], conflicted = []; let routeId = null; let routing;
  if (admission[0] !== "admitted") routing = ["not_evaluated", "admission_abstained", []];
  else {
    for (const concept of policy.concepts) {
      const found = matchClauses(concept, "support_any", "concept", concept.ont_id, null, query); evidence.push(...found);
      const pos = found.some((x) => x.polarity === "support"), neg = found.some((x) => x.polarity === "exclusion");
      if (pos && neg) conflicted.push(concept.ont_id); else if (pos) supported.push(concept.ont_id);
    }
    if (conflicted.length) routing = ["abstained", "concept_support_exclusion_conflict", []];
    else if (!supported.length) routing = ["abstained", "no_concept_support", []];
    else if (supported.length === 1) routing = ["single", "single_supported_concept", supported];
    else {
      const joint = policy.joint_routes.find((item) => jcs(item.ont_ids) === jcs(supported));
      if (!joint) routing = ["ambiguous", "multiple_supported_without_joint_route", []];
      else {
        const found = matchClauses(joint, "support_any", "joint_route", null, joint.joint_route_id, query); evidence.push(...found);
        const pos = found.some((x) => x.polarity === "support"), neg = found.some((x) => x.polarity === "exclusion");
        if (!pos) routing = ["ambiguous", "multiple_supported_without_joint_route", []];
        else if (neg) routing = ["abstained", "joint_route_exclusion", []];
        else { routeId = joint.joint_route_id; routing = ["multi", "explicit_joint_route", supported]; }
      }
    }
  }
  evidence.sort((a, b) => evidenceOrder[a.scope] - evidenceOrder[b.scope] || Buffer.compare(utf8(a.ont_id ?? ""), utf8(b.ont_id ?? "")) || Buffer.compare(utf8(a.joint_route_id ?? ""), utf8(b.joint_route_id ?? "")) || (a.polarity === b.polarity ? 0 : a.polarity === "support" ? -1 : 1) || Buffer.compare(utf8(a.clause_id), utf8(b.clause_id)));
  return {
    admission: { state: admission[0], reason: admission[1], support_clause_ids: plus, exclusion_clause_ids: minus },
    routing: { state: routing[0], reason: routing[1], selected_ont_ids: routing[2], supported_ont_ids: supported, conflicted_ont_ids: conflicted, joint_route_id: routeId },
    evidence,
  };
}

const routeSchema = readJson(join(fixtureRoot, "protocol.schema.json"));
const discoverySchema = readJson(join(discoveryRoot, "protocol.schema.json"));
const golden = readJson(join(fixtureRoot, "golden-fixtures.json"));
const differential = readJson(join(fixtureRoot, "differential-fixtures.json"));
const validate = validator(routeSchema, discoverySchema);
const definitions = { request: "routeRequest", policy: "routingPolicy", provenance: "provenanceManifest", effective_execution: "routeEffectiveExecution", result: "routeResult", error: "routeErrorEnvelope", capabilities: "routeCapabilities" };
for (const [name, definition] of Object.entries(definitions)) assert(validate(golden.valid[name], definition).length === 0, `${name} schema invalid`);

const fixtureKinds = { routing_policy: "policy", provenance_manifest: "provenance", caller_request: "request", effective_execution: "effective_execution", result: "result" };
const digestNames = { routing_policy: "routing_policy_digest", provenance_manifest: "provenance_manifest_digest", caller_request: "caller_request_digest", effective_execution: "effective_execution_digest", result: "result_digest" };
for (const [kind, name] of Object.entries(fixtureKinds)) {
  assert(digest(kind, golden.valid[name]) === golden.digests[digestNames[kind]], `${kind} digest mismatch`);
  const [_, field] = domains[kind]; const preimage = structuredClone(golden.valid[name]); if (field) delete preimage[field];
  const committed = differential.canonical_preimages[kind];
  assert(utf8(jcs(preimage)).toString("hex") === committed.jcs_utf8_hex, `${kind} JCS bytes mismatch`);
}
const {request, policy, provenance, effective_execution: effective, result} = golden.valid;
assert(request.expected_routing_policy_digest === policy.routing_policy_digest, "request policy binding mismatch");
assert(request.expected_provenance_manifest_digest === provenance.provenance_manifest_digest, "request provenance binding mismatch");
assert(policy.provenance_manifest_digest === provenance.provenance_manifest_digest, "policy provenance binding mismatch");
for (const envelope of [effective, result]) {
  assert(envelope.caller_request_digest === golden.digests.caller_request_digest, "caller binding mismatch");
  assert(envelope.routing_policy_digest === policy.routing_policy_digest, "policy lineage mismatch");
  assert(envelope.provenance_manifest_digest === provenance.provenance_manifest_digest, "provenance lineage mismatch");
}
const coordinates=[];
const collect = (owner, positive) => { for (const key of [positive,"exclude_any"]) for (const clause of owner[key]) for (const group of clause.all_of) for (const alternative of group.any_of) coordinates.push([clause.clause_id,group.group_id,alternative.kind,alternative.value]); };
collect(policy.domain,"admit_any"); for (const concept of policy.concepts) collect(concept,"support_any"); for (const route of policy.joint_routes) collect(route,"support_any");
const recordCoordinates=provenance.records.map((record)=>[record.clause_id,record.group_id,record.kind,record.value]);
const coordinateOrder=(left,right)=>Buffer.compare(utf8(left[0]),utf8(right[0]))||Buffer.compare(utf8(left[1]),utf8(right[1]))||(left[2]===right[2]?0:left[2]==="token"?-1:1)||Buffer.compare(utf8(left[3]),utf8(right[3]));
assert(jcs(recordCoordinates)===jcs([...coordinates].sort(coordinateOrder)), "provenance bijection/order mismatch");
const badDate=structuredClone(provenance); badDate.records[0].created_at="not-rfc3339";
assert(validate(badDate,"provenanceManifest").includes("format"), "date-time validator bypass");
const badPath=structuredClone(policy); badPath.authority.path+="\n";
assert(validate(badPath,"routingPolicy").includes("pattern"), "terminal-newline path bypass");
assert(jcs({ "\ue000": 1, "\u{10000}": 2 }) === '{"𐀀":2,"":1}', "UTF-16 key ordering mismatch");
for (const item of differential.tokenization) assert(jcs(tokens15(item.raw)) === jcs(item.expected), `tokenization mismatch: ${item.raw}`);
const expected = evaluate(golden.valid.policy, golden.valid.request.query);
assert(jcs(expected.admission) === jcs(golden.valid.result.admission), "admission oracle mismatch");
assert(jcs(expected.routing) === jcs(golden.valid.result.routing), "routing oracle mismatch");
assert(jcs(expected.evidence) === jcs(golden.valid.result.evidence), "evidence oracle mismatch");
const parseOutcome = (raw, byteLimit=262144, oversizeKind="invalid_request", malformedKind="invalid_request") => {
  try { return ["parsed", strictParse(raw,{byteLimit,maxDepth:32,maxItems:20000})]; }
  catch (error) { return [error instanceof LimitError ? (raw.length>byteLimit?oversizeKind:"resource_exhausted") : malformedKind, null]; }
};
for (const item of differential.parser_cases) assert(parseOutcome(Buffer.from(item.raw_utf8_hex,"hex"))[0]===item.expected_kind, `parser kind mismatch: ${item.case}`);
const requestRaw=utf8(jcs(request));
assert(parseOutcome(Buffer.concat([requestRaw,Buffer.alloc(262144-requestRaw.length,32)]))[0]==="parsed", "request max-byte boundary rejected");
assert(parseOutcome(Buffer.concat([requestRaw,Buffer.alloc(262145-requestRaw.length,32)]))[0]==="invalid_request", "request max+1 boundary accepted");
assert(parseOutcome(Buffer.alloc(262144,32))[0]==="invalid_request" && parseOutcome(Buffer.alloc(262145,32))[0]==="invalid_request", "whitespace exhaustion mapping");
assert(parseOutcome(utf8("[".repeat(32)+"0"+"]".repeat(32)))[0]==="parsed", "depth max rejected");
assert(parseOutcome(utf8("[".repeat(33)+"0"+"]".repeat(33)))[0]==="resource_exhausted", "depth max+1 accepted");
assert(parseOutcome(utf8(`[${Array(20000).fill("0").join(",")}]`))[0]==="parsed", "item max rejected");
assert(parseOutcome(utf8(`[${Array(20001).fill("0").join(",")}]`))[0]==="resource_exhausted", "item max+1 accepted");
assert(parseOutcome(utf8(`{\"n\":${"9".repeat(10000)}}`))[0]==="invalid_request", "huge integer accepted");
assert(parseOutcome(Buffer.alloc(1048577,32),1048576,"resource_exhausted")[0]==="resource_exhausted", "policy absolute byte sentinel accepted");
assert(parseOutcome(Buffer.from("{"),1048576,"resource_exhausted","invalid_policy")[0]==="invalid_policy", "malformed policy mapping");
assert(parseOutcome(Buffer.from("{"),8388608,"resource_exhausted","invalid_policy")[0]==="invalid_policy", "malformed provenance mapping");
const poisonedSchema=structuredClone(routeSchema); poisonedSchema.$defs.routeResult.properties.discovery_result.$ref="https://remote.invalid/schema";
let registryOutcome="ok";
try { validator(poisonedSchema,discoverySchema)(result,"routeResult"); }
catch (error) { registryOutcome=error instanceof RegistryError ? "incompatible" : "internal"; }
assert(registryOutcome==="incompatible","unknown schema resolver did not map exactly to incompatible");
const requestOutcome = (candidate) => {
  const raw=utf8(jcs(candidate)), parsed=parseOutcome(raw); if (parsed[0]!=="parsed") return parsed[0];
  if (utf8(candidate.query).length>candidate.discovery_limits.query_bytes) return "resource_exhausted";
  return validate(parsed[1],"routeRequest").length ? "invalid_request" : "ok";
};
const exactQuery=structuredClone(request); exactQuery.query="ä".repeat(8192);
const overQuery=structuredClone(request); overQuery.query="ä".repeat(8193);
assert(requestOutcome(exactQuery)==="ok" && requestOutcome(overQuery)==="resource_exhausted", "query byte/codepoint boundary");
const messages = {
  incompatible: "runtime is incompatible with semantic-router-v0", invalid_request: "route request is invalid",
  invalid_policy: "routing policy or provenance is invalid", invalid_ontology: "ontology corpus is invalid",
  resource_exhausted: "semantic router resource limit exceeded", snapshot_changed: "captured semantic router input changed",
  unsupported_identity: "semantic router identity is unsupported", internal: "semantic router internal failure",
};
assert(golden.valid.error.error.message === messages[golden.valid.error.error.kind], "unsafe error message");
assert(jcs(golden.valid.capabilities) === jcs({
  schema: "semantic-route-capabilities.v0", request_schemas: ["semantic-route-request.v0"],
  policy_schemas: ["semantic-routing-policy.v0"], provenance_schemas: ["semantic-routing-provenance.v0"],
  result_schemas: ["semantic-route-result.v0"], error_schemas: ["semantic-route-error.v0"],
  router_algorithms: ["rocs-symbolic-router-v0"], candidate_algorithms: ["rocs-lexical-v0"],
  unicode_data: ["15.0.0"], normalization: ["nfkc-casefold-ws-v0"], tokenization: ["unicode-ln-sequence-v0"], platforms: ["linux"],
}), "capabilities mismatch");
console.log("semantic-router-v0 golden verification passed");
