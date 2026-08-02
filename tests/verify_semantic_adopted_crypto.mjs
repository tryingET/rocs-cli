#!/usr/bin/env node
import assert from "node:assert/strict";
import crypto from "node:crypto";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const fixtures = path.join(root, "tests/fixtures/semantic-adopted-policy-v1");
const vectorsPath = path.join(fixtures, "cryptographic-vectors.json");
const provenancePath = path.join(fixtures, "fixture-provenance.json");
const generatorPath = path.join(root, "tests/generate_semantic_adopted_fixtures.py");
const invariantsPath = path.join(root, "docs/project/semantic-router-adopted-policy-v1/invariants.md");
const hash = (bytes) => crypto.createHash("sha256").update(bytes).digest("hex");
const payload = JSON.parse(fs.readFileSync(vectorsPath, "utf8"));
const provenance = JSON.parse(fs.readFileSync(provenancePath, "utf8"));
const invariants = fs.readFileSync(invariantsPath, "utf8");
const domains = [...invariants.matchAll(/^([a-z0-9_]+)_digest = SHA256\("([^"]+)\\0" \|\| J\)$/gm)];
assert.equal(domains.length, 61);
assert.equal(new Set(domains.map((match) => match[1])).size, 61);
assert.equal(new Set(domains.map((match) => match[2])).size, 61);
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
assert.equal(provenance.conspicuously_synthetic, true);
assert.equal(provenance.decision98_b0_material_present, false);
assert.equal(provenance.private_key_serialized, false);
assert.equal(provenance.secret_material_serialized, false);
const publicFiles = Buffer.concat([fs.readFileSync(vectorsPath), fs.readFileSync(provenancePath)]);
assert(!publicFiles.includes(Buffer.from("BEGIN PRIVATE KEY")));
assert(!publicFiles.includes(Buffer.from("private_key_base64")));
console.log(JSON.stringify({ ok: true, domains: 61, vectors: payload.vectors.length, fixture_sha256: provenance.fixture_sha256 }));
