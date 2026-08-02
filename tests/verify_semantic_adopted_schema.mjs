#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const assetPath = path.join(rootDir, "src/rocs_cli/_bootstrap_assets/semantic-router-adopted-policy-v1.schema.zlib");
const packetPath = path.join(rootDir, "docs/project/semantic-router-adopted-policy-v1/protocol.schema.json");
const corpusPath = path.join(rootDir, "tests/fixtures/semantic-adopted-policy-v1/schema-corpus.json");
const expectedSchemaHash = "5940be962e14f881f554a68bd9ba669f8a40d891228ac310dfd9a1a67f8a934f";
const expectedAssetHash = "47cf3f474c1a655595b0e90d192568ec8e99ab950ed4ad2d7bdfef86414c4d42";
const hash = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");

const compressed = fs.readFileSync(assetPath);
assert.equal(compressed.length, 18346);
assert.equal(hash(compressed), expectedAssetHash);
const schemaBytes = zlib.inflateSync(compressed, { maxOutputLength: 323225 });
assert.equal(schemaBytes.length, 323224);
assert.equal(hash(schemaBytes), expectedSchemaHash);
assert.deepEqual(schemaBytes, fs.readFileSync(packetPath));
const schema = JSON.parse(schemaBytes.toString("utf8"));
const corpus = JSON.parse(fs.readFileSync(corpusPath, "utf8"));
assert.equal(schema.$id, "urn:rocs:semantic-router-adopted-policy-v1");
assert.equal(Object.keys(schema.$defs).length, 69);
assert.equal(schema.oneOf.length, 54);

function canonical(value) {
  if (value === null || typeof value === "boolean" || typeof value === "number") return JSON.stringify(value);
  if (typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
}

function same(left, right) {
  return typeof left === typeof right && canonical(left) === canonical(right);
}

function pointer(root, reference) {
  assert.match(reference, /^#\//);
  let current = root;
  for (const raw of reference.slice(2).split("/")) {
    const token = raw.replaceAll("~1", "/").replaceAll("~0", "~");
    if (Array.isArray(current)) {
      assert.match(token, /^(?:0|[1-9][0-9]*)$/);
      assert(Number(token) < current.length);
      current = current[Number(token)];
    } else {
      assert(current && typeof current === "object" && Object.hasOwn(current, token));
      current = current[token];
    }
  }
  return current;
}

function walk(value, visit) {
  if (value && typeof value === "object") {
    visit(value);
    for (const child of Object.values(value)) walk(child, visit);
  }
}

const references = [];
walk(schema, (node) => { if (Object.hasOwn(node, "$ref")) references.push(node.$ref); });
assert.equal(references.length, 1115);
for (const reference of references) pointer(schema, reference);

const graph = new Map(Object.keys(schema.$defs).map((name) => [name, new Set()]));
for (const [name, definition] of Object.entries(schema.$defs)) {
  walk(definition, (node) => {
    if (typeof node.$ref === "string" && node.$ref.startsWith("#/$defs/")) {
      graph.get(name).add(node.$ref.slice(8).split("/", 1)[0]);
    }
  });
}
const visiting = new Set();
const visited = new Set();
function visitGraph(name) {
  assert(!visiting.has(name), `cyclic definition graph at ${name}`);
  if (visited.has(name)) return;
  visiting.add(name);
  for (const target of graph.get(name)) visitGraph(target);
  visiting.delete(name);
  visited.add(name);
}
for (const name of graph.keys()) visitGraph(name);
const reached = new Set();
function reach(name) {
  if (reached.has(name)) return;
  reached.add(name);
  for (const target of graph.get(name)) reach(target);
}
for (const branch of schema.oneOf) reach(branch.$ref.slice(8).split("/", 1)[0]);
assert.equal(reached.size, 68);
assert.deepEqual(Object.keys(schema.$defs).filter((name) => !reached.has(name)), ["hexDigest"]);

function typeMatches(instance, expected) {
  if (Array.isArray(expected)) return expected.some((choice) => typeMatches(instance, choice));
  if (expected === "null") return instance === null;
  if (expected === "array") return Array.isArray(instance);
  if (expected === "object") return instance !== null && typeof instance === "object" && !Array.isArray(instance);
  if (expected === "integer") return Number.isSafeInteger(instance);
  if (expected === "boolean") return typeof instance === "boolean";
  return typeof instance === expected;
}

function validDateTime(value) {
  const match = /^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):([0-5]\d):([0-5]\d|60)(?:\.\d+)?(Z|[+-][0-2]\d:[0-5]\d)$/.exec(value);
  if (!match) return false;
  const [year, month, day] = match.slice(1, 4).map(Number);
  const leapYear = year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
  const monthDays = [31, leapYear ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  if (day > monthDays[month - 1]) return false;
  if (match[7] !== "Z" && Number(match[7].slice(1, 3)) > 23) return false;
  if (match[6] === "60") return match[7] === "Z" && match[4] === "23" && match[5] === "59" && [[6, 30], [12, 31]].some(([m, d]) => month === m && day === d);
  return true;
}

function validate(instance, selected, root = schema) {
  if (selected === true) return [];
  if (selected === false || !selected || typeof selected !== "object" || Array.isArray(selected)) return ["schema"];
  const issues = [];
  if (selected.$ref) {
    issues.push(...validate(instance, pointer(root, selected.$ref), root));
    if (selected.$ref === "#/$defs/path" && typeof instance === "string" && Buffer.byteLength(instance, "utf8") > 1024) issues.push("maxBytes");
  }
  for (const branch of selected.allOf ?? []) issues.push(...validate(instance, branch, root));
  if (selected.oneOf) {
    const matches = selected.oneOf.filter((branch) => validate(instance, branch, root).length === 0).length;
    if (matches !== 1) issues.push("oneOf");
  }
  if (selected.if && validate(instance, selected.if, root).length === 0 && selected.then) {
    issues.push(...validate(instance, selected.then, root));
  }
  if (Object.hasOwn(selected, "const") && !same(instance, selected.const)) issues.push("const");
  if (selected.enum && !selected.enum.some((choice) => same(instance, choice))) issues.push("enum");
  if (selected.type && !typeMatches(instance, selected.type)) return [...issues, "type"];
  if (instance !== null && typeof instance === "object" && !Array.isArray(instance)) {
    const properties = selected.properties ?? {};
    for (const key of selected.required ?? []) if (!Object.hasOwn(instance, key)) issues.push("required");
    if (selected.additionalProperties === false) {
      for (const key of Object.keys(instance)) if (!Object.hasOwn(properties, key)) issues.push("additionalProperties");
    }
    for (const [key, childSchema] of Object.entries(properties)) {
      if (Object.hasOwn(instance, key)) issues.push(...validate(instance[key], childSchema, root));
    }
  } else if (Array.isArray(instance)) {
    if (instance.length < (selected.minItems ?? 0)) issues.push("minItems");
    if (selected.maxItems !== undefined && instance.length > selected.maxItems) issues.push("maxItems");
    if (selected.uniqueItems && new Set(instance.map(canonical)).size !== instance.length) issues.push("uniqueItems");
    const prefix = selected.prefixItems ?? [];
    prefix.slice(0, instance.length).forEach((childSchema, index) => issues.push(...validate(instance[index], childSchema, root)));
    if (selected.items === false && instance.length > prefix.length) issues.push("items");
    else if (selected.items && selected.items !== false) {
      const start = prefix.length || 0;
      for (let index = start; index < instance.length; index += 1) issues.push(...validate(instance[index], selected.items, root));
    }
  } else if (typeof instance === "string") {
    const codePoints = [...instance].length;
    if (codePoints < (selected.minLength ?? 0)) issues.push("minLength");
    if (selected.maxLength !== undefined && codePoints > selected.maxLength) issues.push("maxLength");
    if (selected.pattern && !(new RegExp(selected.pattern, "u")).test(instance)) issues.push("pattern");
    if (selected.format === "date-time" && !validDateTime(instance)) issues.push("format");
  } else if (Number.isSafeInteger(instance)) {
    if (selected.minimum !== undefined && instance < selected.minimum) issues.push("minimum");
    if (selected.maximum !== undefined && instance > selected.maximum) issues.push("maximum");
  }
  return issues;
}

function mergeInstance(left, right) {
  if (left && right && typeof left === "object" && typeof right === "object" && !Array.isArray(left) && !Array.isArray(right)) {
    const result = structuredClone(left);
    for (const [key, value] of Object.entries(right)) result[key] = Object.hasOwn(result, key) ? mergeInstance(result[key], value) : structuredClone(value);
    return result;
  }
  return right === null || right === undefined ? structuredClone(left) : structuredClone(right);
}
function variant(value, index) {
  if (!index) return value;
  const result = structuredClone(value);
  if (result && typeof result === "object" && !Array.isArray(result)) {
    for (const key of ["sequence", "checkpoint_sequence", "terminal_sequence"]) {
      if (Number.isInteger(result[key])) { result[key] += index; return result; }
    }
    for (const key of ["principal_id", "event_digest", "artifact_digest", "candidate_digest", "source_digest"]) {
      if (Object.hasOwn(result, key)) { result[key] = variant(result[key], index); return result; }
    }
    for (const key of Object.keys(result)) {
      const changed = variant(result[key], index);
      if (canonical(changed) !== canonical(result[key])) { result[key] = changed; return result; }
    }
  } else if (Array.isArray(result) && result.length) {
    result[0] = variant(result[0], index); return result;
  } else if (typeof result === "string") {
    if (result.startsWith("sha256:") || (/^[0-9a-f]{40}$/).test(result)) return `${result.slice(0, -1)}${(index % 16).toString(16)}`;
    if (/^[A-Za-z0-9._/:-]+$/.test(result)) return `${result}${index}`;
  } else if (Number.isInteger(result)) return result + index;
  return result;
}
function dedupeInstance(value) {
  if (value && typeof value === "object" && !Array.isArray(value)) return Object.fromEntries(Object.entries(value).map(([key, child]) => [key, dedupeInstance(child)]));
  if (!Array.isArray(value)) return value;
  const result = value.map(dedupeInstance);
  const seen = new Set();
  result.forEach((original, index) => {
    let child = original; let key = canonical(child); let attempts = 0;
    while (seen.has(key)) {
      attempts += 1; assert(attempts <= 32, "generated fixture cannot satisfy uniqueItems");
      child = variant(child, index + attempts); result[index] = child; key = canonical(child);
    }
    seen.add(key);
  });
  return result;
}
function buildInstance(selected, root, choices, current = null, depth = 0) {
  assert(depth <= 200, "fixture generation depth");
  if (selected === true || selected === false || !selected || typeof selected !== "object" || Array.isArray(selected)) return null;
  if (selected.$ref) {
    const name = selected.$ref.startsWith("#/$defs/") ? selected.$ref.slice(8).split("/", 1)[0] : current;
    const base = buildInstance(pointer(root, selected.$ref), root, choices, name, depth + 1);
    return mergeInstance(base, buildInstance(Object.fromEntries(Object.entries(selected).filter(([key]) => key !== "$ref")), root, choices, current, depth + 1));
  }
  if (Object.hasOwn(selected, "const")) return structuredClone(selected.const);
  if (selected.enum) return structuredClone(selected.enum[0]);
  if (selected.allOf) {
    let result = null;
    for (const child of selected.allOf) result = mergeInstance(result, buildInstance(child, root, choices, current, depth + 1));
    const rest = Object.fromEntries(Object.entries(selected).filter(([key]) => key !== "allOf"));
    return mergeInstance(result, buildInstance(rest, root, choices, current, depth + 1));
  }
  if (selected.oneOf) {
    const index = current && selected === root.$defs[current] ? (choices[current] ?? 0) : 0;
    const rest = Object.fromEntries(Object.entries(selected).filter(([key]) => key !== "oneOf"));
    return mergeInstance(buildInstance(rest, root, choices, current, depth + 1), buildInstance(selected.oneOf[index], root, choices, current, depth + 1));
  }
  const kind = Array.isArray(selected.type) ? selected.type[0] : selected.type;
  if (kind === "null") return null;
  if (kind === "boolean") return false;
  if (kind === "integer") return selected.minimum ?? 0;
  if (kind === "string" || selected.pattern || selected.format) {
    if (selected.format === "date-time" || selected.pattern === "Z$") return "2026-08-02T06:00:00Z";
    const expression = selected.pattern ?? "";
    if (expression.includes("sha256:")) return `sha256:${"a".repeat(64)}`;
    if (expression.includes("{40}")) return "a".repeat(40);
    if (expression.includes("{64}")) return "a".repeat(64);
    if (expression.includes("{43}")) return `${"A".repeat(43)}=`;
    if (expression.includes("A-Za-z0-9+/")) return "A".repeat(Math.max(4, selected.minLength ?? 0));
    if (expression.includes("co\\.software")) return "co.software.test";
    if (expression.includes("(?!/)")) return "path";
    return (selected.minLength ?? 0) <= 2 ? "id" : "x".repeat(selected.minLength);
  }
  if (kind === "array" || selected.items || selected.prefixItems) {
    const count = selected.minItems ?? (selected.prefixItems ?? []).length;
    const result = Array.from({ length: count }, (_, index) => buildInstance(index < (selected.prefixItems ?? []).length ? selected.prefixItems[index] : (selected.items ?? {}), root, choices, current, depth + 1));
    return selected.uniqueItems ? result.map(variant) : result;
  }
  if (kind === "object" || selected.properties || selected.required) {
    let result = Object.fromEntries(Object.entries(selected.properties ?? {}).map(([key, child]) => [key, buildInstance(child, root, choices, current, depth + 1)]));
    if (selected.if && validate(result, selected.if, root).length === 0 && selected.then) result = mergeInstance(result, buildInstance(selected.then, root, choices, current, depth + 1));
    return result;
  }
  return null;
}

for (const [definition, expected] of Object.entries(corpus.branch_inventory)) {
  const branches = schema.$defs[definition].oneOf;
  assert.equal(branches.length, expected);
  assert.equal(new Set(branches.map(canonical)).size, expected, `${definition} duplicate branch`);
}
function findProperty(node, name) {
  if (!node || typeof node !== "object" || Array.isArray(node)) return null;
  if (node.properties && Object.hasOwn(node.properties, name)) return node.properties[name];
  for (const key of ["allOf", "oneOf"]) {
    for (const child of node[key] ?? []) {
      const found = findProperty(child, name);
      if (found) return found;
    }
  }
  for (const child of Object.values(node.properties ?? {})) {
    const found = findProperty(child, name);
    if (found) return found;
  }
  return null;
}
function presence(node) {
  if (!node) return null;
  if (node.type === "null") return false;
  if (node.$ref || (node.type !== undefined && node.type !== "null")) return true;
  const states = new Set((node.oneOf ?? []).map(presence));
  return states.size === 1 ? [...states][0] : null;
}
function passKinds(node) {
  if (!node) return null;
  if (node.maxItems === 0) return [];
  const kinds = (node.prefixItems ?? []).map((item) => findProperty(item, "pass_kind")?.const).filter(Boolean);
  return kinds.length ? kinds : null;
}
function branchPattern(branch) {
  const constant = (name) => findProperty(branch, name)?.const ?? null;
  return {
    state: constant("attempt_state"),
    invocations: constant("process_invocations"),
    passes: passKinds(findProperty(branch, "passes")),
    proof: presence(findProperty(branch, "evaluator_execution_start_proof_digest")),
    launch: presence(findProperty(branch, "evaluator_execution_launch_receipt_digest")),
    handoff: presence(findProperty(branch, "protected_descriptor_handoff_receipt_digest")),
    receipt: presence(findProperty(branch, "execution_receipt_digest")),
    outcome: constant("outcome"),
  };
}
function patternMatches(testCase, pattern) {
  return Object.entries(pattern).every(([key, value]) => value === null || canonical(value) === canonical(testCase[key]));
}
const branchPatterns = Object.fromEntries(Object.keys(corpus.branch_inventory).map((name) => [
  name, schema.$defs[name].oneOf.map(branchPattern),
]));
for (const testCase of corpus.prefix_branch_cases) {
  for (const [definition, patterns] of Object.entries(branchPatterns)) {
    assert.equal(patterns.filter((pattern) => patternMatches(testCase, pattern)).length, 1, `${definition}:${testCase.name}`);
  }
}
const impossible = [
  { ...corpus.prefix_branch_cases[0], launch: true },
  { ...corpus.prefix_branch_cases[3], receipt: true },
  { ...corpus.prefix_branch_cases[7], passes: ["primary"] },
];
for (const testCase of impossible) {
  for (const definition of ["executionAttempt", "verdict"]) {
    assert.equal(branchPatterns[definition].filter((pattern) => patternMatches(testCase, pattern)).length, 0);
  }
}
const closureProjection = [0, 1, 2, 3, 4, 5, 5, 6];
for (let index = 0; index < 8; index += 1) {
  const choices = { executionAttempt: index, verdict: index, protectedAccessClosureSubject: closureProjection[index], verdictApprovalSubject: closureProjection[index] };
  for (const definition of ["executionAttempt", "verdict"]) {
    const fixture = dedupeInstance(buildInstance(schema.$defs[definition], schema, choices, definition));
    assert.equal(validate(fixture, schema.$defs[definition]).length, 0, `full fixture ${definition}:${index}`);
    assert.equal(schema.$defs[definition].oneOf.filter((branch) => validate(fixture, branch).length === 0).length, 1);
    assert.equal(validate(fixture.protected_access_closure.subject, schema.$defs.protectedAccessClosureSubject).length, 0);
    if (definition === "verdict") assert.equal(validate(fixture.verdict_approval_subject, schema.$defs.verdictApprovalSubject).length, 0);
  }
}
assert.deepEqual(pointer(schema, "#/oneOf/0"), schema.oneOf[0]);
for (const testCase of corpus.cases) {
  const selected = testCase.definition ? schema.$defs[testCase.definition] : testCase.inline_schema;
  const schemaValid = validate(testCase.instance, selected).length === 0;
  const invariantValid = testCase.definition !== "path" || Buffer.byteLength(testCase.instance, "utf8") <= 1024;
  assert.equal(schemaValid && invariantValid, testCase.valid, testCase.name);
}

console.log(JSON.stringify({
  ok: true,
  schema_sha256: expectedSchemaHash,
  definitions: 69,
  reachable_definitions: 68,
  references: 1115,
  root_branches: 54,
  corpus_cases: corpus.cases.length,
}));
