/** Strict JSON, canonicalization, digest, and schema primitives. */

import { createHash } from "node:crypto";

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

export {
  ACCEPTED_AGGREGATE,
  ConformanceError,
  DECIMAL_RE,
  DIGEST_RE,
  DOMAINS,
  FROZEN_AGGREGATE,
  HOOKS,
  ID_RE,
  MAX_INT,
  OBJECT_DOMAINS,
  ProtocolFailure,
  REVISION,
  SCHEMA_NAMES,
  SPAN_RE,
  StrictJSONError,
  VECTOR_SHA256,
  canonicalBase64,
  inspectSchema,
  jcsBytes,
  objectDigest,
  rawDigest,
  requireCondition,
  same,
  schemaMatches,
  sha256,
  snapshotText,
  strictJSONLoads,
};
