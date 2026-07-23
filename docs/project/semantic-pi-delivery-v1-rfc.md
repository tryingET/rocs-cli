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
rfc_revision: "semantic-pi-delivery-v1-r4"
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

Goals are exact multi-axis identity, post-application host observation, replay resistance, deterministic independent validation, v0 preservation, default-off behavior, and one supervised integration proof.

Non-goals are provider transmission, model use/influence, semantic publication, consumer adoption/activation, recovery policy, a production consumer/canary, live acquisition, defaults/startup/fleet behavior, or protection after compromise of the exact reviewed host/component/controller artifacts.

## Trust statement

Pi extensions execute in the host process. A public JSON digest is integrity, not issuance authentication. V1 claims:

- live runtime anti-confusion from a host-private opaque witness brand and host-owned one-use redemption map;
- deterministic consistency of persisted witness/redemption/transcript bytes;
- controller-observed execution only when AK evidence binds the exact command/process/output.

V1 does **not** claim that a self-digested persisted transcript alone proves execution. Production `delivered` additionally requires a current `pi.host-attestation-resolution.v1` from an independently pinned host-attestation owner. No such owner/root exists today; no production receipt can validate until separately established. The resolver shape is fixed here so later provisioning cannot change v1 semantics.

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
  "protocol_issuer": {
    "kind": "pi_extension_component",
    "id": "pi-ontology-workflows",
    "role": "semantic_pi_delivery_attestor"
  }
}
```

`pi-owner` is governance only. Repository, component, package, host, loaded snapshot, execution instance, and attempt are separate. Any `pi-adapter` value in v1 is `issuer_scope_violation`; no alias or conversion exists.

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

`files` is the complete safely extracted tarball inventory of `{path,mode,byte_length,content_digest}`, UTF-8 path sorted and unique. The manifest does not embed its own identity elsewhere. `package_artifact_identity` is exactly:

```text
package_name
package_version
npm_pack_tarball_digest
package_tree_manifest_digest
```

### Dependency tree

Every runtime dependency is a separate `pi.package-tree-manifest.v1`. Dependency rows in the loaded manifest are exactly `{package_name,package_version,package_tree_manifest_digest}`. The full transitive dependency closure is present once, UTF-8 sorted by `(package_name, package_version, digest)`, with no cycles or undeclared imports.

### Loaded component

`pi.loaded-extension-component-manifest.v1` has exactly:

```text
schema
repository_identity
component_identity
package_artifact_identity
entry_logical_path
entry_content_digest
dependency_manifests
loaded_component_manifest_digest
```

It references but does not contain the package-tree body, preventing digest recursion. Resolver equality binds package identity to the resolved package-tree manifest and tarball.

### Host runtime

`pi.host-runtime-manifest.v1` has exactly:

```text
schema
host_package
host_version
extension_api_version
node_executable_digest
host_package_tree_manifest_digest
host_dependency_manifests
loader_configuration_digest
entrypoint_logical_path
entrypoint_content_digest
argv_contract_digest
host_runtime_manifest_digest
```

Witness-capable execution is eligible only from resolved content-addressed component, dependency, host, and Node-runtime snapshots. Mutable local paths, inline factories, symlinks, and imports outside the resolved manifests reject.

The controller stages snapshots read-only. The host verifies all bytes before load, immediately before prompt execution, before redemption, and during final prompt readback. Any path/inode/mode/content drift aborts before redemption and provider dispatch.

## Normative JSON profile

Input is bounded strict UTF-8 JSON with no BOM/trailing data and duplicate-key rejection before object construction. Legal number tokens are only `0|[1-9][0-9]*`, range `0..9007199254740991`; booleans are never integers. Reject negative/decimal/exponent/NaN/Infinity, lone surrogates, Unicode noncharacters, and non-NFC strings. Depth is at most 64.

Canonical bytes are RFC 8785 JCS under that integer-only I-JSON profile. Object keys sort by UTF-16 code units; arrays retain normative order. Equality is type-exact.

JSON object digests are:

```text
sha256(ASCII(domain) || 0x00 || JCS(object without exactly its top-level self-digest field))
```

Raw byte digests are:

```text
sha256(ASCII(domain) || 0x00 || exact_bytes)
```

Every digest is `sha256:` plus 64 lowercase hex characters.

## Complete digest registry

| Object/value | Domain | Omitted field/preimage |
|---|---|---|
| delivery receipt | `semantic-release.pi-delivery.v1` | `pi_delivery_receipt_digest` |
| package tarball bytes | `pi.package-tarball-bytes.v1` | exact bytes |
| package/source file bytes | `pi.package-file-bytes.v1` | exact bytes |
| package tree | `pi.package-tree-manifest.v1` | `package_tree_manifest_digest` |
| loaded component | `pi.loaded-extension-component-manifest.v1` | `loaded_component_manifest_digest` |
| Node executable bytes | `pi.node-executable-bytes.v1` | exact bytes |
| host file bytes | `pi.host-file-bytes.v1` | exact bytes |
| loader configuration | `pi.loader-configuration.v1` | full closed object |
| argv contract | `pi.argv-contract.v1` | full closed object |
| host runtime | `pi.host-runtime-manifest.v1` | `host_runtime_manifest_digest` |
| execution instance | `pi.execution-instance.v1` | full closed preimage below |
| prompt-run attempt | `pi.prompt-run-attempt.v1` | full closed preimage below |
| prompt input bytes | `pi.prompt-input.v1` | exact UTF-8 bytes |
| prompt returned bytes | `pi.prompt-returned.v1` | exact UTF-8 bytes |
| final prompt bytes | `pi.prompt-final-chain.v1` | exact UTF-8 bytes |
| applied entry | `pi.prompt-applied-entry.v1` | closed `{handler_registration_index, returned_prompt_digest}` |
| witness | `pi.prompt-system-application-witness.v1` | `host_application_witness_digest` |
| integration acknowledgement | `pi.host-integration-acknowledgement.v1` | `integration_acknowledgement_digest` |
| redemption | `pi.prompt-system-witness-redemption.v1` | `host_witness_redemption_digest` |
| replay probe | `pi.prompt-system-witness-replay-probe.v1` | `replay_probe_digest` |
| controller transcript | `pi.host-integration-controller-transcript.v1` | `controller_transcript_digest` |
| host attestation | `pi.host-attestation-resolution.v1` | `host_attestation_resolution_digest` |
| authorization request | `semantic-release.pi-integration-authorization-request.v1` | `authorization_request_digest` |
| owner approval | `semantic-release.pi-integration-owner-approval.v1` | `owner_approval_digest` |
| authorization envelope | `semantic-release.pi-integration-authorization-envelope.v1` | `authorization_envelope_digest` |
| ledger record | `semantic-release.pi-integration-authorization-ledger-record.v1` | `authorization_ledger_record_digest` |
| integration proof | `semantic-release.pi-host-integration-proof.v1` | `integration_proof_digest` |
| packet aggregate rows | `semantic-release.pi-delivery-packet-aggregate.v1` | exact row bytes |
| packet manifest | `semantic-release.pi-delivery-packet-manifest.v1` | `packet_manifest_digest` |
| controller executable bytes | `pi.controller-executable-bytes.v1` | exact bytes |
| process environment contract | `pi.process-environment-contract.v1` | full closed object |
| filesystem manifest | `pi.filesystem-manifest.v1` | full closed object |

Unknown domains reject.

## Closed configuration preimages

`pi.loader-configuration.v1` is exactly `{schema,loader_kind,loader_version,tsconfig_digest,import_map,allowed_root_manifest_digests,module_cache_mode,outside_imports_forbidden,native_addons_forbidden}`. `loader_kind=jiti`; import-map rows are `{specifier,target_logical_path,target_manifest_digest}`, UTF-8 specifier sorted/unique; allowed roots are sorted/unique digests; cache mode is `per_execution_generation`; outside imports are false-to-allow/constant forbidden; native add-ons are forbidden for the v1 proof.

`pi.process-environment-contract.v1` is exactly `{schema,inherit_environment,entries,unset_keys,locale,timezone,network_mode}`. Inheritance is false; entries are UTF-8-key-sorted unique `{key,value}` rows from a closed allow-list; unset keys are sorted/unique and disjoint; locale is `C.UTF-8`, timezone `UTC`, and network mode `forbidden`.

`pi.argv-contract.v1` is exactly `{schema,node_executable_digest,entrypoint_logical_path,argv,cwd_logical_id,process_environment_contract_digest,shell}`. `argv` preserves order, `shell=false`, and cwd resolves inside the staged host snapshot.

`pi.filesystem-manifest.v1` is exactly `{schema,roots,process_ids,network_connections}`. Roots are UTF-8-logical-id-sorted unique `{logical_id,realpath_digest,tree_manifest_digest,mutability}` rows; mutability is `read_only|disposable_write|canonical_ledger`. Process IDs are sorted safe integers. Network connections is the empty array. Real paths never enter the digest preimage directly.

## Execution and attempt identity

`execution_instance_digest` preimage is exactly:

```text
{host_runtime_manifest_digest, boot_nonce, extension_api_version}
```

`boot_nonce` is 32 random bytes encoded as 64 lowercase hex characters and appears in the controller transcript and host attestation.

`prompt_run_attempt_digest` preimage is exactly:

```text
{execution_instance_digest, execution_generation, attempt_ordinal,
 session_instance_nonce, rocs_generation_receipt_digest}
```

Session nonce has the same 32-byte encoding and appears in witness/transcript/attestation. Generation and ordinal are safe integers, start at `0`, increment before use, and fail closed permanently at maximum rather than wrap.

`handler_registration_index` is a zero-based safe integer assigned globally by the runner in registration order. One witness corresponds to the exact contributing registration. Multiple handlers from one component receive separate indexes and witnesses.

## Closed delivery receipt union

Every branch has `additionalProperties=false` and the common exact keys:

```text
schema
governance_owner_role
issuer
repository_identity
component_identity
package_artifact_identity
host_runtime_manifest_digest
host_capabilities
loaded_component_manifest_digest
loaded_entry_digest
execution_instance_digest
execution_generation
prompt_run_attempt_digest
handler_registration_index
rocs_generation_receipt_digest
consumer_repository
v0_canary_scope
delivery_outcome
claim_scope
host_application_witness_digest
pi_delivery_receipt_digest
```

Host capabilities are exactly UTF-8 sorted/unique and include `prompt.system.application-witness.v1`. Consumer/scope are copied only from the resolved generation receipt and imply no owner existence, naming, consent, adoption, or activation.

- **Delivered** adds exactly `delivered_effective_execution_digest` and `applied_prompt_chain_entry_digest`; outcome is `delivered`, claim is `delivered_to_pi_prompt_chain_only`, witness digest is non-null, and execution/application fields equal the resolved generation and witness.
- **Suppressed** adds exactly `suppression_reason`; outcome is `suppressed`, claim is `delivery_suppressed_only`, witness digest is null, and reason is `cancelled|stale_result|policy|duplicate_attempt`. It contains no delivered/error field.
- **Failed** adds exactly `error_digest`; outcome is `failed`, claim is `delivery_failed_only`, witness digest is null. It contains no delivered/suppression field. Deadline equality fails.

A host without the v1 capability or host identity emits no v1 receipt; the component exposes only a local non-protocol diagnostic. Thus all receipt branches can truthfully carry the mandatory host identity fields.

## Closed host objects

### Application witness

Exact keys:

```text
schema, issuer, host_runtime_manifest_digest, repository_identity,
component_identity, package_artifact_identity, loaded_component_manifest_digest,
loaded_entry_digest, execution_instance_digest, boot_nonce,
execution_generation, prompt_run_attempt_digest, attempt_ordinal,
session_instance_nonce, handler_registration_index,
rocs_generation_receipt_digest, input_prompt_digest,
returned_prompt_digest, final_prompt_chain_digest,
applied_prompt_chain_entry_digest, application_outcome,
application_target, observation_phase, host_application_witness_digest
```

Constants: issuer `{kind:pi_host,id:@earendil-works/pi-coding-agent}`, outcome `applied`, target `agent.state.systemPrompt`, phase `post_application`.

### Redemption

Exact keys:

```text
schema, issuer, host_runtime_manifest_digest, execution_instance_digest,
execution_generation, prompt_run_attempt_digest, handler_registration_index,
host_application_witness_digest, subject_kind, subject_digest,
redemption_outcome, redemption_sequence, host_witness_redemption_digest
```

`subject_kind` is `semantic_delivery_candidate|host_integration_acknowledgement`; subject digest resolves to the corresponding schema. Outcome is `redeemed`, sequence `1`.

### Integration acknowledgement

Exact keys:

```text
schema, issuer, claim_scope, authorization_envelope_digest,
host_application_witness_digest, prompt_run_attempt_digest,
integration_acknowledgement_digest
```

Issuer is the component identity; claim is `host_integration_acknowledgement_only`. It is not a delivery receipt.

### Replay probe

Exact keys:

```text
schema, issuer, host_application_witness_digest,
host_witness_redemption_digest, repeated_subject_kind,
repeated_subject_digest, probe_outcome, replay_probe_digest
```

Host issuer is fixed and outcome is `rejected_already_redeemed`. No second redemption exists.

### Controller transcript

Exact keys:

```text
schema, controller_executable_digest, host_runtime_manifest_digest,
component_package_tree_manifest_digest, dependency_manifest_digests,
process_environment_contract_digest, argv_contract_digest, process_start_nonce,
boot_nonce, session_instance_nonce, authorization_envelope_digest,
authorization_claim_record_digest, witness_bytes_digest,
acknowledgement_bytes_digest, redemption_bytes_digest,
replay_probe_bytes_digest, stdout_digest, stderr_digest, exit_code,
provider_request_dispatched, filesystem_before_digest,
filesystem_after_digest, process_teardown_complete,
controller_transcript_digest
```

This proves deterministic internal consistency and, when AK evidence cites the exact observed command/output, controller-observed execution. By itself it is not authenticated provenance or delivery authority.

### Host attestation resolution

Exact keys:

```text
schema, issuer, owner_repository, attestation_root_id,
attestation_root_revision, attestation_root_digest,
revocation_head_digest, host_runtime_manifest_digest,
execution_instance_digest, boot_nonce, session_instance_nonce,
prompt_run_attempt_digest, host_application_witness_digest,
host_witness_redemption_digest, controller_transcript_digest,
action_epoch, currentness_cas_digest, verification_outcome,
host_attestation_resolution_digest
```

Issuer kind is `independent_host_attestation_verifier`; outcome is `valid`. The v1 resolver requires owner-specific acquisition pin, owner-store read receipt, trust root/current revocation, action-time epoch, and exact joins. No root is provisioned by this RFC.

## Host event and replay machine

Order:

```text
allocate attempt
-> chain before_agent_start while recording per-handler input/return
-> assign final prompt
-> readback/hash
-> issue opaque personalized witness
-> receive delivery candidate or integration acknowledgement
-> validate candidate shape/digest
-> reverify staged artifacts
-> final readback/hash agent.state.systemPrompt
-> persist and fsync a pre-redemption journal bound to those final checks
-> atomically redeem once
-> persist transcript/attestation inputs
-> if exact evidence persists, optionally construct/dispatch this run's provider request
```

Any acknowledgement, validation, snapshot, final-readback, pre-redemption persistence, redemption, or transcript persistence failure aborts before provider dispatch and restores the pre-contribution prompt. No redemption is issued before every artifact and prompt postcondition succeeds. A redemption without the required persisted transcript and, for delivery, host attestation is invalid. Integration proof sets `provider_request_dispatched=false` and terminates after replay probe.

State is `allocated -> chained -> applied -> witness_issued -> redeemed`, with failure terminal. Every await rechecks instance/generation/attempt. Reload/new/resume/fork/replacement/shutdown invalidates nonterminal state. Redeemed/invalidated tuples remain in a non-evicting set capped at 4096 for the generation; reaching cap fails closed and requires a new generation. Restart changes execution instance. Production durable replay requires the attestation owner and remains unprovisioned.

## Acyclic isolated authorization and canonical one-shot ledger

The integration controller is a bounded internal component of the real Pi host owner surface, not a new repository product:

```json
{
  "governance_owner_role": "pi-host-owner",
  "repository": {
    "repository_id": "pi-mono",
    "canonical_source_locator": "git+https://github.com/tryingET/pi-mono.git",
    "identity_revision": 1
  },
  "component": {
    "component_id": "pi-coding-agent-host-integration-controller",
    "repository_path": "packages/coding-agent",
    "identity_revision": 1
  },
  "canonical_ledger": {
    "store_id": "pi-host-integration-authorization-v1",
    "canonical_store_locator": "sqlite+local://pi-host-owner/semantic-integration-authorization-ledger-v1"
  }
}
```

A separately reviewed Pi-host owner artifact must accept this identity before implementation. The controller remains internal and adds no public command or product surface.

Construction order:

1. `semantic-pi-integration-authorization-request.v1` fixes Decision 71 reference, ROCS packet manifest, component/host/controller commits and manifests, process nonce, UTC window, monotonic max duration, disposable roots, and cardinalities `1 witness/1 redemption/1 replay probe`, with live/production false.
2. Separate `semantic-pi-integration-owner-approval.v1` objects from component owner and host owner each reference only the request digest, owner repository/revision, accepted artifact digest, owner-store head, revocation head, and validity window.
3. `semantic-pi-integration-authorization-envelope.v1` references the request and both approval digests plus a current accepted/unsuperseded AK Decision 71 reference. There is no digest cycle.

The canonical append-only SQLite ledger outside disposable/production/runtime roots is the one-shot source. Its location is resolved only through a host-owner acquisition pin and current owner-store read receipt; caller paths and copied databases are never authority. Exact records are:

```text
{schema, store_id, canonical_store_locator, store_revision,
 prior_store_head_digest, resulting_store_head_digest,
 authorization_envelope_digest, sequence, prior_record_digest,
 state, process_start_nonce, controller_identity,
 controller_executable_digest, claimed_at_utc, monotonic_deadline_ns,
 terminal_reason, controller_transcript_digest,
 authorization_ledger_record_digest}
```

States are `available -> claimed -> consumed|failed`. Claim uses `BEGIN IMMEDIATE`, exact current owner-store head/revision, expected prior record/state, unique authorization digest, same-filesystem durable CAS, and fsync before process launch. The resulting head/revision are re-read through the host-owner store receipt. Concurrent/duplicate claim, alternate store identity/locator, stale head, or restored pre-claim snapshot fails. Crash after claim is terminal `failed`; startup recovery converts stale claimed to failed, never available. Terminal records are immutable and their current head is externally anchored by the host-owner acquisition pin/store receipt, preventing a copied or rolled-back ledger from satisfying action-time currentness. UTC is checked once against the envelope; realtime rollback relative to monotonic progression fails. The private inherited handle derives from the already-claimed canonical record and is consumed by the host; it is not authority by itself.

## Closed integration proof

`semantic-pi-host-integration-proof.v1` exact keys:

```text
schema, issuer, claim_scope, authorization_envelope_digest,
authorization_claim_record_digest, authorization_terminal_record_digest,
host_runtime_manifest_digest, loaded_component_manifest_digest,
prompt_run_attempt_digest, host_application_witness_digest,
integration_acknowledgement_digest, host_witness_redemption_digest,
replay_probe_digest, controller_transcript_digest,
provider_request_dispatched, publication_authorized,
adoption_authorized, activation_authorized, use_observed,
influence_observed, production_authorized, integration_proof_digest
```

Issuer is the controller, claim `host_integration_only`; all booleans are false. Construction is witness -> acknowledgement -> redemption -> replay probe -> transcript -> terminal ledger record -> proof. ROCS delivery validation and AK delivery linkage reject this schema. AK may record it only as implementation-validation evidence.

## Delivery authority overlay

V0 artifacts and runtime remain unchanged. V1 adds `ak_optional_pi_v1`, a generated rule whose role/edge set is mechanically derived from v0 `ak_optional_pi` by replacing only the Pi receipt role with v1 receipt + witness + redemption + host-attestation roles. The generator proves every other role, category, owner, repository, acquisition contract, edge, parameter, error precedence, and currentness predicate is byte-equal to v0.

Validation sequence:

1. v0 universal authority preflight and generation/activation rule validate the complete unchanged graph and resolved checked generation;
2. v1 schema/digest/package/host/attempt/witness/redemption preflight;
3. v1 host-attestation owner pin/read/trust/currentness validation;
4. exact overlay role/edge closure;
5. delivered relation;
6. AK linkage overlay.

Missing/invalid input precedence is: malformed input -> digest mismatch -> issuer scope -> self-certification -> trust/currentness -> activation currentness -> replay/authorization -> delivery relation. V0 historical commands still accept v0; successor component entrypoints reject v0 as `unsupported_protocol`. Passing schema-checked v0 objects alone never substitutes for the v0 authority verifier.

## Packet and deterministic implementation limits

Preserve `docs/project/semantic-release-v0/**` byte-for-byte. `docs/project/semantic-pi-delivery-v1/` contains only `packet-manifest.json` plus every file listed by it, including schemas, invariants, registries, generator, independent validators, vectors, and fixtures. Any unlisted/missing regular file rejects. Manifest excludes itself and lists UTF-8-sorted `{path,byte_length,sha256}` rows; aggregate row bytes are `path<TAB>byte_length<TAB>sha256<LF>` under the registered aggregate domain. Manifest self-digest omits only its self field.

Limits cover the complete operation from first packet/tarball read through extraction, all dependency/host/component hashing, validation, teardown, and receipt/proof production:

- 16 MiB per JSON file, 64 MiB packet aggregate, 32 packet files;
- 64 MiB compressed tarballs cumulative;
- 512 MiB extracted component + all dependencies + host cumulative;
- 4096 total extracted files, 128 dependencies, 4096-byte logical paths;
- JSON depth 64, arrays at most 100,000 unless lower field cap;
- one 60,000 ms monotonic deadline; equality expires;
- retained-byte accounting once per object; no reopen;
- stable no-follow regular-file reads, descriptor/path identity/metadata checks;
- NFC root-local POSIX paths; no traversal, backslash, network form, symlink, hard link, special file, normalization/casefold collision;
- extraction ratio at most 32:1 per archive and cumulatively.

Error codes and precedence are generated and independently tested. Resource failure is `resource_exhausted` unless deadline equality/expiry occurred first, which is `deadline_exceeded`; earlier malformed/digest/issuer failures retain precedence.

The generator imports neither validator. Python and Node validators share no code/parser/digest helper. Raw vectors cover every JSON/digest rule and boundary.

Existing v0 embedding remains. New v1 embedding uses uncompressed standard base64 of the exact top-level v1 schema bundle, fixed 76 ASCII characters per line, LF endings, one trailing LF, byte length, and SHA-256. A checked-in generator writes it; `--check` compares exact bytes; two fresh-checkout generations must match.

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
