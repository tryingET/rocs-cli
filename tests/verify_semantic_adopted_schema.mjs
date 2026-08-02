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
    assert(current && typeof current === "object" && !Array.isArray(current) && Object.hasOwn(current, token));
    current = current[token];
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
  const match = /^(\d{4})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])T([01]\d|2[0-3]):[0-5]\d:[0-5]\d(?:\.\d+)?(?:Z|[+-][0-2]\d:[0-5]\d)$/.exec(value);
  if (!match) return false;
  const normalized = value.endsWith("Z") ? value : value.replace(/([+-]\d\d):(\d\d)$/, "$1$2");
  const parsed = new Date(normalized);
  if (Number.isNaN(parsed.getTime())) return false;
  const [year, month, day] = match.slice(1, 4).map(Number);
  return parsed.getUTCFullYear() === year && parsed.getUTCMonth() + 1 === month && parsed.getUTCDate() === day;
}

function validate(instance, selected, root = schema) {
  if (selected === true) return [];
  if (selected === false || !selected || typeof selected !== "object" || Array.isArray(selected)) return ["schema"];
  const issues = [];
  if (selected.$ref) issues.push(...validate(instance, pointer(root, selected.$ref), root));
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
    if (instance.length < (selected.minLength ?? 0)) issues.push("minLength");
    if (selected.maxLength !== undefined && instance.length > selected.maxLength) issues.push("maxLength");
    if (selected.pattern && !(new RegExp(selected.pattern, "u")).test(instance)) issues.push("pattern");
    if (selected.format === "date-time" && !validDateTime(instance)) issues.push("format");
  } else if (Number.isSafeInteger(instance)) {
    if (selected.minimum !== undefined && instance < selected.minimum) issues.push("minimum");
    if (selected.maximum !== undefined && instance > selected.maximum) issues.push("maximum");
  }
  return issues;
}

for (const [definition, expected] of Object.entries(corpus.branch_inventory)) {
  const branches = schema.$defs[definition].oneOf;
  assert.equal(branches.length, expected);
  assert.equal(new Set(branches.map(canonical)).size, expected, `${definition} duplicate branch`);
}
for (const testCase of corpus.cases) {
  const selected = testCase.definition ? schema.$defs[testCase.definition] : testCase.inline_schema;
  assert.equal(validate(testCase.instance, selected).length === 0, testCase.valid, testCase.name);
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
