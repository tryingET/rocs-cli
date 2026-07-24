---
summary: "Converged RFC for pi-ontology-workflows delivery identity, host-resolved application evidence, and a non-authoritative isolated integration proof."
read_when:
  - "Reviewing the Decision 53 successor protocol or Pi host delivery witness."
system4d:
  container: "Cross-repo successor RFC for ROCS, pi-ontology-workflows, and Pi host."
  compass: "Make identity, host observation, owner authorization, and delivery authority independently executable."
  engine: "Content-addressed artifacts -> host application witness -> typed redemption -> owner-current delivery validation or isolated integration proof."
  fog: "Digest cycles, forgeable transcripts, replayed authorization, or fixture authority can create a coherent false claim."
type: "rfc"
status: "in_review"
rfc_revision: "semantic-pi-delivery-v1-r16"
---

# RFC — Semantic Pi delivery receipt v1

## Decision requested

Accept a successor to the Pi-delivery seam of Decision 53 that:

1. preserves v0 history;
2. uses the accepted `pi-extensions` / `pi-ontology-workflows` identity;
3. defines a closed v1 delivery receipt plus host witness, redemption, and attestation-resolution contracts;
4. keeps actual `delivered` validation blocked until the complete unchanged Decision 53 authority graph and a new independently owned host-attestation fact are current;
5. permits one separately authorized, non-authoritative real-host integration proof that cannot validate as semantic delivery.

No code is authorized before a successor ADR and post-ADR execution membrane.

## Inputs

- problem brief and evidence note in this review set;
- immutable r1 and r2 review/synthesis artifacts;
- Decision 53 v0 ADR and packet;
- Pi-owner identity artifact at commit `63d1e9f5c271007b48c45818d1f419a228de1561`;
- AK task `4108`, evidence `5030` and `5031`.

## Goals and non-goals

Goals are exact multi-axis identity, authenticated component release provenance, host-derived registration, sealed immutable staging, post-application host observation, durable replay resistance, deterministic independent validation, byte-preserved v0 history, default-off behavior, and one supervised integration proof.

Non-goals are provider transmission, model use/influence, semantic publication, consumer adoption/activation, automatic recovery, a production consumer/canary, live acquisition, defaults/startup/fleet behavior, or protection after compromise of the exact reviewed host/component/controller/finalizer artifacts. Durable objects still have closed recovery identities; restart never manufactures redemption or proof.

## Trust statement

Pi extensions execute in the host process. A public JSON digest is integrity, not issuance authentication. V1 claims:

- live runtime anti-confusion from a host-private opaque witness brand and host-owned one-use redemption map;
- deterministic consistency of persisted witness/redemption/transcript bytes;
- controller-observed execution only when AK evidence binds the exact command/process/output.

V1 does **not** claim that a self-digested persisted transcript alone proves execution. Registrar authority derives only from a host-private capability created for the exact sealed manifest entry; serialized identity is never registrar authority. Component release provenance is accepted only through current component-owner control, acquisition-pin, and canonical-read evidence. Production `delivered` additionally requires a signed statement and current `pi.host-attestation-resolution.v1` from a semantic-owner-appointed, control-disjoint host-attestation owner. No such owner/root exists today; no production receipt can validate until separately established. The appointment, independence, signature, acquisition, revocation, and resolver shapes are fixed here so provisioning cannot change v1 semantics.

## Fixed identities

```json
{
  "governance_owner_role": "pi-owner",
  "repository_identity": {
    "repository_id": "pi-extensions",
    "canonical_source_locator": "git+https://github.com/tryingET/pi-extensions.git",
    "workspace_projection": "local://softwareco/owned/pi-extensions",
    "identity_revision": 1
  },
  "component_identity": {
    "component_id": "pi-ontology-workflows",
    "repository_path": "packages/pi-ontology-workflows",
    "identity_revision": 1
  },
  "package_identity": {
    "kind": "repository_package",
    "package_id": "pi-extensions:packages/pi-ontology-workflows",
    "repository_path": "packages/pi-ontology-workflows",
    "package_manifest_path": "packages/pi-ontology-workflows/package.json",
    "identity_revision": 1
  },
  "protocol_issuer": {
    "kind": "pi_extension_component",
    "id": "pi-ontology-workflows",
    "role": "semantic_pi_delivery_attestor"
  }
}
```

`pi-owner` is governance only. Repository, component, package, host, loaded snapshot, execution instance, and attempt are separate. Any `pi-adapter` value in v1 is `issuer_scope_violation`; no alias or conversion exists.

`controller_identity` is the closed object `{kind:"pi_host_internal_controller",governance_owner_role:"pi-host-owner",repository_identity:{repository_id:"pi-mono",canonical_source_locator:"git+https://github.com/tryingET/pi-mono.git",identity_revision:1},component_identity:{component_id:"pi-coding-agent-host-integration-controller",repository_path:"packages/coding-agent",identity_revision:1}}`. The request, controller transcript, host-owner release provenance, and integration-proof issuer equal it byte-for-byte; ledger writer is exclusively the distinct finalizer identity. Aliases or caller-supplied identity reject. `finalizer_identity` is the analogous closed object with kind `pi_host_integration_finalizer` and component `{component_id:"pi-coding-agent-host-integration-finalizer",repository_path:"packages/coding-agent",identity_revision:1}`; it is distinct from controller identity. `pi.host-integration-release-provenance.v1` is exactly `{schema,issuer,host_commit,host_runtime_manifest_digest,controller_identity,controller_commit,controller_executable_digest,finalizer_identity,finalizer_commit,finalizer_executable_digest,canonical_ledger_identity,host_integration_release_provenance_digest}`. Issuer is exactly `{kind:"repository_owner",role:"pi-host-owner",repository_id:"pi-mono"}`. Production authority requires current host-owner control/pin/read evidence. For isolated integration only, the current signed host-owner approval plus its authenticated read receipt may authenticate this exact accepted artifact; it grants no delivery authority.

## Acyclic artifact model

### Package tree

`pi.package-tree-manifest.v1` has exactly:

```text
schema
package_name
package_version
source_commit
npm_pack_tarball_digest
files
package_tree_manifest_digest
```

`files` is the complete safely extracted tarball inventory of `{path,mode,byte_length,content_digest}`, UTF-8 path sorted and unique. `source_commit` is exactly 40 lowercase hexadecimal characters. The manifest does not embed its own identity elsewhere. Root `package_artifact_identity` is exactly:

```text
package_identity
package_name
package_version
source_commit
npm_pack_tarball_digest
package_tree_manifest_digest
```

Its `package_identity` equals the fixed identity; all remaining values equal the resolved root manifest. Dependencies never carry or reuse the fixed package identity. `pi.component-release-provenance.v1` is exactly `{schema,issuer,repository_identity,component_identity,package_identity,accepted_identity_artifact_digest,source_commit,package_artifact_identity,entry_logical_path,entry_content_digest,dependency_manifest_digests,module_import_closure_manifest_digest,issued_at_utc,component_release_provenance_digest}`. Issuer is `{kind:"repository_owner",role:"pi-owner",repository_id:"pi-extensions"}`. Production authority requires its digest as the subject of current component-owner control, acquisition-pin, canonical-store read, and revocation evidence. For isolated integration only, the current signed component-owner approval plus authenticated read receipt may authenticate this exact accepted artifact; it grants no delivery authority. Every package/source/entry/dependency field must equal the loaded manifests; a self-digested provenance object is `self_certification`.

### Dependency tree

Every runtime dependency is a separate `pi.package-tree-manifest.v1`. Dependency rows in the loaded manifest are exactly `{package_name,package_version,package_tree_manifest_digest}`. The full transitive dependency closure is present once, UTF-8 sorted by `(package_name, package_version, digest)`, with no cycles or undeclared imports.

### Loaded component

`pi.loaded-extension-component-manifest.v1` has exactly:

```text
schema
repository_identity
component_identity
package_identity
package_artifact_identity
component_release_provenance_digest
entry_logical_path
entry_content_digest
dependency_manifests
loaded_component_manifest_digest
```

It references but does not contain package-tree or provenance bodies, preventing digest recursion. Resolver equality requires fixed repository/component/package identities, the provenance-selected root manifest/tarball/source commit, an entry path resolving exactly one root file row with the same content digest, and dependency rows resolving every and only non-root manifest in the deterministic import closure.

## Normative contract annexes

This core RFC and the following three annexes are one indivisible normative r16 review object:

- `semantic-pi-delivery-v1-runtime-contracts.md` — host runtime, sealed staging, maps, digest registry, deterministic loading, registrar, attempt, and receipt preimages;
- `semantic-pi-delivery-v1-authority-contracts.md` — receipt/witness semantics, durable replay, signed attestation, integration authorization, finalizer, canonical ledger, and proof;
- `semantic-pi-delivery-v1-validation-contracts.md` — unchanged-v0 overlay, closed resolver, packet, independent validators, mandatory vectors, limits, and embedding.

No annex is optional, informative, or lower precedence. Definitions occur once across the four files. A missing annex, review-byte mismatch, undefined cross-reference, or contradiction rejects r16. The review-set manifest covers every file.

## Public surface and cross-repo sequence

V1 adds no user-facing tool, command, prompt, flag, default, startup hook, or general package export. Reconcile the package vision, foundation, stable-core ADR, and accepted identity artifact before code.

After ADR:

1. ROCS packet/validators/overlay/embedding;
2. Pi host ADR and content-addressed host API implementation;
3. component v1 validation, v0 rejection, and constructor-authority removal;
4. owner request/approvals/envelope and one-shot ledger task;
5. supervised real Pi integration proof plus rejected replay probe;
6. no delivered receipt until later owner facts and host-attestation root are provisioned and reviewed.

## Stop and rollback matrix

Stop before provider/live mutation on owner/AK currentness drift, duplicate claim, clock rollback, root overlap after realpath, artifact/version skew, post-witness prompt drift, persistence failure, resource/deadline failure, surviving process, or teardown mismatch.

Rollback is owner-specific:

- ROCS: revert v1-only modules/packet entrypoint; preserve v0 history and keep successor delivery disabled.
- Pi host: remove witness event only after component v1 path is disabled; preserve receipts/transcripts.
- component: disable v1 integration path without re-enabling v0 receipt acceptance or constructor authority.
- ledger: never delete history; mark outstanding claim failed and reject reuse.

No rollback restores `pi-adapter`, v0 successor acceptance, test flags, or a false delivered claim.

## Live boundary

This decision may authorize implementation and one isolated host-integration D2E after post-ADR tasks and joint one-shot authorization. It does not authorize a v1 `delivered` receipt, production semantic-release D2E, publication, adoption, activation, or recovery. Those require the missing consumer/consent/canary/recovery facts, live acquisition, and an independently owned host-attestation root/current receipt.

## Open questions

None. Missing production owner/root instances are explicit future gate facts, not protocol-shape questions.

## Requested review outcome

Run a fresh exact-byte five-lane review. Only complete synthesis with zero material findings and `ready_for_adr` permits ADR drafting.
