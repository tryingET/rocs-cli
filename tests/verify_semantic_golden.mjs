#!/usr/bin/env node
// Independent Node verifier for the operator-authorized semantic golden repair.
// It imports no ROCS/Python producer code and uses only Node standard modules.
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const root = new URL("../docs/project/semantic-discovery-v0/", import.meta.url);
const golden = JSON.parse(readFileSync(new URL("golden-fixtures.json", root), "utf8"));
const differential = JSON.parse(readFileSync(new URL("differential-fixtures.json", root), "utf8"));

function jcs(value) {
  if (value === null || typeof value === "boolean" || typeof value === "string") return JSON.stringify(value);
  if (typeof value === "number") {
    if (!Number.isSafeInteger(value)) throw new Error("non-integer or unsafe JCS number");
    return String(value);
  }
  if (Array.isArray(value)) return `[${value.map(jcs).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${jcs(value[key])}`).join(",")}}`;
}

const domains = {
  caller_request: "rocs.caller-request.v0",
  corpus_snapshot: "rocs.corpus-snapshot.v0",
  tool_identity: "rocs.tool-identity.v0",
  effective_execution: "rocs.effective-execution.v0",
  result: "rocs.discovery-result.v0",
  pack: "rocs.pack.v0",
  document: "rocs.document.v0",
};
const digestFields = {
  corpus_snapshot: "corpus_snapshot_digest",
  tool_identity: "digest",
  effective_execution: "effective_execution_digest",
  result: "result_digest",
  pack: "pack_digest",
};
function hash(domain, bytes) {
  return `sha256:${createHash("sha256").update(domain, "ascii").update(Buffer.from([0])).update(bytes).digest("hex")}`;
}
function objectDigest(kind, value) {
  const copy = structuredClone(value);
  if (digestFields[kind]) delete copy[digestFields[kind]];
  return hash(domains[kind], Buffer.from(jcs(copy), "utf8"));
}

const valid = golden.valid;
const objects = {
  caller_request: valid.request,
  corpus_snapshot: valid.corpus_snapshot,
  tool_identity: valid.tool_identity,
  effective_execution: valid.effective_execution,
  result: valid.result,
  pack: valid.pack,
};
const digestNames = {
  caller_request: "caller_request_digest",
  corpus_snapshot: "corpus_snapshot_digest",
  tool_identity: "tool_identity_digest",
  effective_execution: "effective_execution_digest",
  result: "result_digest",
  pack: "pack_digest",
};
for (const [kind, value] of Object.entries(objects)) {
  const actual = objectDigest(kind, value);
  const expected = golden.digests[digestNames[kind]];
  if (actual !== expected) throw new Error(`${kind} digest mismatch: ${actual} != ${expected}`);
  const preimage = structuredClone(value);
  if (digestFields[kind]) delete preimage[digestFields[kind]];
  const bytes = Buffer.from(jcs(preimage), "utf8");
  const fixture = differential.canonical_preimages[kind];
  if (bytes.length !== fixture.byte_length || bytes.toString("hex") !== fixture.jcs_utf8_hex) {
    throw new Error(`${kind} canonical preimage mismatch`);
  }
}

const document = valid.pack.documents[0];
if (hash(domains.document, Buffer.from(document.text, "utf8")) !== document.document_digest) {
  throw new Error("document digest mismatch");
}

function bracketValues(text, field) {
  const match = text.match(new RegExp(`^\\s*${field}: \\[([^\\]]*)\\]$`, "m"));
  if (!match) return [];
  return match[1].split(",").map((item) => item.trim()).filter(Boolean);
}
function scalar(text, field) {
  const match = text.match(new RegExp(`^\\s*${field}: (.+)$`, "m"));
  if (!match) throw new Error(`missing ${field}`);
  return match[1].trim();
}
function normalize(value) {
  return value.normalize("NFKC").toLowerCase().trim().replace(/\s+/gu, " ");
}
function tokens(value) {
  return [...new Set(normalize(value).match(/[\p{L}\p{N}]+/gu) ?? [])];
}

const query = normalize(valid.request.query);
const queryTokens = tokens(valid.request.query);
const fields = {
  id: [scalar(document.text, "id")],
  label: bracketValues(document.text, "labels"),
  synonym: bracketValues(document.text, "synonyms"),
  description: [scalar(document.text, "description")],
  relation: [],
  example: bracketValues(document.text, "examples"),
  anti_example: bracketValues(document.text, "anti_examples"),
};
const weights = {
  id: [500, 1000], label: [400, 800], synonym: [350, 700],
  description: [100, 200], relation: [80, 160], example: [50, 100],
};
let score = 0;
const evidence = [];
for (const family of ["id", "label", "synonym", "description", "relation", "example"]) {
  const values = fields[family].map(normalize);
  if (values.includes(query)) {
    score += weights[family][1];
    evidence.push({ field: family, rule: "phrase_exact", query_term: query });
  }
  for (const token of queryTokens) {
    if (values.some((value) => tokens(value).includes(token))) {
      score += weights[family][0];
      evidence.push({ field: family, rule: "token_exact", query_term: token });
    }
  }
}
const anti = fields.anti_example.map(normalize);
if (anti.includes(query)) {
  score -= 400;
  evidence.push({ field: "anti_example", rule: "anti_phrase", query_term: query });
}
for (const token of queryTokens) {
  if (anti.some((value) => tokens(value).includes(token))) {
    score -= 200;
    evidence.push({ field: "anti_example", rule: "anti_token", query_term: token });
  }
}
score = Math.max(0, Math.min(0xffffffff, score));
const candidate = valid.result.candidates[0];
if (score !== 1150 || candidate.score !== score || jcs(candidate.evidence) !== jcs(evidence)) {
  throw new Error(`independent scoring mismatch: score=${score} evidence=${jcs(evidence)}`);
}
console.log(JSON.stringify({
  verifier: "independent-node-stdlib",
  score,
  evidence_items: evidence.length,
  result_preimage_bytes: differential.canonical_preimages.result.byte_length,
  result_digest: valid.result.result_digest,
  digests_verified: 6,
  preimages_verified: 6,
}));
