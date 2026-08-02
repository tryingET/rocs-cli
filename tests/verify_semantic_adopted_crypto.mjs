#!/usr/bin/env node
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import zlib from "node:zlib";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const fixtures = path.join(root, "tests/fixtures/semantic-adopted-policy-v1");
const vectorsPath = path.join(fixtures, "cryptographic-vectors.json");
const provenancePath = path.join(fixtures, "fixture-provenance.json");
const generatorPath = path.join(root, "tests/generate_semantic_adopted_fixtures.py");
const invariantsPath = path.join(root, "docs/project/semantic-router-adopted-policy-v1/invariants.md");
const assetPath = path.join(root, "src/rocs_cli/_bootstrap_assets/semantic-router-adopted-policy-v1.schema.zlib");
const hash = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const payload = JSON.parse(fs.readFileSync(vectorsPath, "utf8"));
const provenance = JSON.parse(fs.readFileSync(provenancePath, "utf8"));
const invariants = fs.readFileSync(invariantsPath, "utf8");
const domainRows = [...invariants.matchAll(/^([a-z0-9_]+)_digest = SHA256\("([^"]+)\\0" \|\| J\)$/gm)];
const domains = Object.fromEntries(domainRows.map((match) => [match[1], match[2]]));
assert.equal(domainRows.length, 61);
assert.equal(new Set(Object.keys(domains)).size, 61);
assert.equal(new Set(Object.values(domains)).size, 61);
const canonical = (value) => {
  if (value === null || typeof value === "boolean" || typeof value === "number" || typeof value === "string") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${value.map(canonical).join(",")}]`;
  return `{${Object.keys(value).sort().map((key) => `${JSON.stringify(key)}:${canonical(value[key])}`).join(",")}}`;
};
const domainDigest = (name, value) => `sha256:${hash(Buffer.concat([
  Buffer.from(domains[name], "ascii"), Buffer.from([0]), Buffer.from(canonical(value)),
]))}`;
assert.equal(domainDigest(payload.body_domain, payload.body), payload.body_digest);
const prefixes = {
  approval: Buffer.from("rocs-semantic-policy-approval-signature-v1\0"),
  receipt: Buffer.from("rocs-semantic-policy-receipt-signature-v1\0"),
  consumption: Buffer.from("rocs-semantic-policy-consumption-signature-v1\0"),
};
function canonicalBase64(value, bytes) {
  assert.equal(typeof value, "string");
  assert.match(value, /^[A-Za-z0-9+/]*={0,2}$/);
  const raw = Buffer.from(value, "base64");
  assert.equal(raw.length, bytes);
  assert.equal(raw.toString("base64"), value);
  return raw;
}
function digestBytes(value) {
  assert.match(value, /^sha256:[0-9a-f]{64}$/);
  return Buffer.from(value.slice(7), "hex");
}
function verify(vector) {
  try {
    assert.equal(vector.purpose, vector.expected_purpose);
    assert.equal(canonical(vector.issuer), canonical(vector.expected_issuer));
    assert.equal(vector.trust_root_digest, vector.expected_trust_root_digest);
    digestBytes(vector.trust_root_digest);
    assert.equal(vector.revoked, false);
    assert(new Date(vector.valid_from) <= new Date(vector.trusted_now));
    assert(new Date(vector.trusted_now) <= new Date(vector.valid_until));
    const rawKey = canonicalBase64(vector.public_key_base64, 32);
    const signature = canonicalBase64(vector.signature_base64, 64);
    const der = Buffer.concat([Buffer.from("302a300506032b6570032100", "hex"), rawKey]);
    const key = crypto.createPublicKey({ key: der, format: "der", type: "spki" });
    const message = Buffer.concat([prefixes[vector.purpose], digestBytes(vector.body_digest)]);
    return crypto.verify(null, message, key, signature);
  } catch {
    return false;
  }
}
for (const vector of payload.vectors) assert.equal(verify(vector), vector.valid, vector.name);
const publicKey = canonicalBase64(payload.vectors[0].public_key_base64, 32);
assert.equal(`sha256:${hash(publicKey)}`, payload.public_key_digest);
assert.equal(hash(fs.readFileSync(vectorsPath)), provenance.fixture_sha256);
assert.equal(hash(fs.readFileSync(generatorPath)), provenance.generator_sha256);
const committedGenerator = execFileSync("git", ["show", `${provenance.generator_commit}:tests/generate_semantic_adopted_fixtures.py`], { cwd: root });
assert.equal(hash(committedGenerator), provenance.generator_sha256);
const schema = JSON.parse(zlib.inflateSync(fs.readFileSync(assetPath)));
const fields = ["b0_preregistration_commit", "b0_failure_commit", "b0_preregistration_lock_digest", "b0_prompt_set_digest", "b0_report_digest"];
const coordinates = fields.map((field) => schema.$defs.contaminationManifest.properties[field].const).sort();
assert.equal(hash(Buffer.from(coordinates.join("\n"))), provenance.b0_coordinate_set_sha256);
assert.deepEqual(provenance.b0_coordinate_hits, []);
assert.equal(provenance.private_material_scan, "raw-hex-base64-v1:pass");
assert.equal(provenance.private_key_serialized, false);
assert.equal(provenance.secret_material_serialized, false);
assert.equal(provenance.dependency_review.version, "46.0.5");
assert.equal(provenance.dependency_review.scope, "offline-caller-pinned-ed25519-verify-only");
assert.equal(provenance.dependency_review.network_calls, false);
assert.equal(provenance.dependency_review.signing_api_exposed_by_rocs, false);
assert.equal(provenance.dependency_review.lock_sha256, hash(fs.readFileSync(path.join(root, "uv.lock"))));
const publicFiles = Buffer.concat([fs.readFileSync(vectorsPath), fs.readFileSync(provenancePath)]);
assert(!publicFiles.includes(Buffer.from("BEGIN PRIVATE KEY")));
assert(!publicFiles.includes(Buffer.from("private_key_base64")));
console.log(JSON.stringify({ ok: true, domains: 61, vectors: payload.vectors.length, fixture_sha256: provenance.fixture_sha256 }));
