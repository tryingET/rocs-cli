---
summary: "Revised RFC for a real pi-ontology-workflows delivery issuer, independently resolved Pi host application witness, and default-off semantic Pi delivery receipt v1."
read_when:
  - "Reviewing the Decision 53 successor protocol or Pi host delivery witness."
system4d:
  container: "Cross-repo successor RFC for ROCS, pi-ontology-workflows, and Pi host."
  compass: "Attest only what the component and host can independently observe, with every identity and authority axis explicit."
  engine: "Closed v1 packet -> immutable staged artifacts -> host post-application witness -> host redemption -> component receipt or non-authoritative integration proof."
  fog: "Identity substitution, pre-application callbacks, forgeable self-digests, replay, or test authorization can manufacture a false delivered claim."
type: "rfc"
status: "in_review"
rfc_revision: "semantic-pi-delivery-v1-r2"
---

# RFC — Semantic Pi delivery receipt v1

## Decision requested

Accept a versioned successor to the Pi-delivery seam of Decision 53. Preserve v0 as history, replace its fictional `pi-adapter` identity with the accepted `pi-ontology-workflows` component identity, and require independently resolved Pi-host post-application evidence before a v1 `delivered` receipt can validate.

Accept separately that an isolated host-integration proof may exercise the host/component seam without sealing a semantic delivery receipt while current consumer/activation/recovery facts remain unavailable. The proof is validation evidence only and cannot enter the Decision 53 delivery authority graph.

This RFC authorizes no code until a successor ADR and post-ADR execution membrane are complete.

## Inputs

- [`semantic-pi-delivery-v1-problem-brief.md`](semantic-pi-delivery-v1-problem-brief.md)
- [`semantic-pi-delivery-v1-evidence-note.md`](semantic-pi-delivery-v1-evidence-note.md)
- immutable r1 review and synthesis artifacts;
- accepted Decision 53 v0 ADR and packet;
- Pi-owner identity artifact at exact commit `63d1e9f5c271007b48c45818d1f419a228de1561`;
- AK task `4108`, evidence `5030` and `5031`.

## Goals

1. Bind the real repository, component, and package without creating or aliasing `pi-adapter`.
2. Keep component attestation, host observation, owner authorization, and external validation separate.
3. Permit `delivered` only after successful host application, host-side single-use redemption, and complete unchanged Decision 53 authority-graph validation.
4. Bind exact component package, loaded component snapshot, host executable, runtime generation, prompt-run attempt, ROCS generation, and application contribution.
5. Preserve default-off and live-gate boundaries.
6. Keep Python and Node validation independent and all generated/embedded artifacts reproducible.

## Non-goals

- final provider transmission, provider acceptance, model reading, interpretation, influence, or correctness;
- semantic publication, consumer intent/acceptance/adoption/activation, or rollback policy;
- naming a production consumer or canary;
- appointing a recovery controller;
- live acquisition, startup enforcement, defaults, or fleet rollout;
- cryptographic protection after compromise of the exact trusted host or component artifacts.

## Threat and trust boundary

Pi extensions currently execute arbitrary code in the Pi host process. An unkeyed JSON self-digest cannot prove host issuance, and same-process code isolation is not a security boundary against a compromised trusted artifact.

V1 therefore makes two explicit claims:

1. **Runtime anti-confusion:** the exact trusted host implementation issues an opaque branded witness object after application and accepts it once through a host-owned redemption API. Caller JSON, copied fields, or a recomputed digest cannot redeem in that live runtime.
2. **Independent evidence:** an external validator accepts a persisted witness only together with a host redemption receipt and a controller transcript bound to the exact host executable, component snapshot, process launch, and output bytes. This proves behavior of the reviewed exact artifacts under supervised execution; it is not nonrepudiation against compromise of those artifacts.

Production acceptance additionally requires a separately approved host attestation root or isolation boundary. None exists today, so v1 `delivered` sealing remains unreachable while `live_acquisition_implemented=false`.

## Identity model

V1 separates and independently compares:

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
  "package_artifact_identity": {
    "package_name": "@tryinget/pi-ontology-workflows",
    "package_version": "<semver>",
    "npm_pack_tarball_digest": "<digest>",
    "package_tree_manifest_digest": "<digest>"
  },
  "protocol_issuer": {
    "kind": "pi_extension_component",
    "id": "pi-ontology-workflows",
    "role": "semantic_pi_delivery_attestor"
  },
  "host_artifact_identity": {
    "host_package": "@earendil-works/pi-coding-agent",
    "host_version": "<semver>",
    "extension_api_version": "1.0.0",
    "host_executable_digest": "<digest>"
  }
}
```

`pi-owner` is a governance role, not a Git owner or receipt issuer. Canonical source provenance and local projection are distinct. Host is not component issuer. Package name is not component ID. Any `pi-adapter` value in a v1 identity axis is `issuer_scope_violation`; no alias exists.

## Immutable package and load contract

The component owner produces an `npm pack` tarball from an exact clean commit. `npm_pack_tarball_digest` uses raw SHA-256 bytes under `semantic-release.pi-package-tarball.v1`. A deterministic safe extractor creates a disposable snapshot with no symlinks, hard links, devices, sockets, traversal, or extra files.

`pi.loaded-extension-component-manifest.v1` is a closed object containing:

```text
schema
repository_identity
component_identity
package_artifact_identity
package_root_logical_id
entry_logical_path
files[] = {path, mode, byte_length, raw_sha256}
dependency_manifests[] = {package_name, version, manifest_digest}
package_json_raw_sha256
entry_raw_sha256
loaded_component_manifest_digest
```

Files are the complete extracted tarball inventory, UTF-8 path sorted and unique. Dependencies used by the extension are separately content-addressed immutable snapshots and included by manifest; imports outside the component/dependency snapshots reject. Inline factories and mutable direct local-path loading are ineligible for v1 witnessing.

The host loads only from these read-only snapshots, verifies every file before load, verifies entry and manifest again immediately before prompt execution and after witness redemption, and rejects inode/content/mode drift. This is the normative package-to-loaded-artifact join:

```text
receipt.package_artifact_identity
= witness.package_artifact_identity
= loaded_manifest.package_artifact_identity

receipt.loaded_component_manifest_digest
= witness.loaded_component_manifest_digest
= digest(resolved loaded manifest)
```

## Closed component receipt union

All objects use `additionalProperties=false`. Common fields in all three branches, in this exact order-independent key set, are:

```text
schema
governance_owner_role
issuer
repository_identity
component_identity
package_artifact_identity
host_artifact_identity
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

Constants:

- `schema=semantic-pi-delivery-receipt.v1`;
- governance/issuer/repository/component constants equal the identity model;
- capabilities are exactly UTF-8 sorted and unique and include `prompt.system.application-witness.v1`;
- package/host values are non-empty and digest-bound;
- all digest fields are lowercase `sha256:` digests;
- generation and handler index are safe integers;
- consumer/scope are copied only from a fully resolved valid ROCS generation receipt and attest byte binding only—not owner existence, naming, consent, adoption, or activation.

### Delivered exact extension fields

Delivered adds exactly:

```text
delivered_effective_execution_digest
applied_prompt_chain_entry_digest
```

and requires:

- `delivery_outcome=delivered`;
- `claim_scope=delivered_to_pi_prompt_chain_only`;
- non-null witness digest;
- delivered execution equals `generation.effective_execution_digest`;
- applied entry equals `witness.applied_prompt_chain_entry_digest`;
- every common identity/attempt/generation value equals the resolved generation, loaded manifest, host witness, host redemption, and authority context.

### Suppressed exact extension field

Suppressed adds exactly `suppression_reason`, requires a null witness digest, and uses:

```text
claim_scope=delivery_suppressed_only
suppression_reason ∈ cancelled | stale_result | policy | incompatible_host |
  host_witness_unavailable | application_not_acknowledged | duplicate_attempt
```

It contains no delivered or error field. Identity and attempt fields remain mandatory so duplicate/stale outcomes are attributable.

### Failed exact extension field

Failed adds exactly `error_digest`, requires a null witness digest, and uses `claim_scope=delivery_failed_only`. It contains no delivered or suppression field. Deadline equality is failure.

## Closed host objects and API

### Application witness

`pi.prompt-system-application-witness.v1` has exactly:

```text
schema
issuer
host_artifact_identity
repository_identity
component_identity
package_artifact_identity
loaded_component_manifest_digest
loaded_entry_digest
execution_instance_digest
execution_generation
prompt_run_attempt_digest
handler_registration_index
rocs_generation_receipt_digest
input_prompt_digest
returned_prompt_digest
final_prompt_chain_digest
applied_prompt_chain_entry_digest
application_outcome
application_target
observation_phase
host_application_witness_digest
```

Constants are:

```text
issuer = {kind: pi_host, id: @earendil-works/pi-coding-agent}
application_outcome = applied
application_target = agent.state.systemPrompt
observation_phase = post_application
```

The witness binds the selected component and exact ROCS generation request supplied to that component. Prompt digests use raw UTF-8 bytes with domain-specific prefixes. `applied_prompt_chain_entry_digest` identifies the component's exact returned contribution and its position, not the whole final prompt.

### Redemption receipt

`pi.prompt-system-witness-redemption.v1` has exactly:

```text
schema
issuer
host_artifact_identity
execution_instance_digest
execution_generation
prompt_run_attempt_digest
handler_registration_index
host_application_witness_digest
component_receipt_digest
redemption_outcome
redemption_sequence
host_witness_redemption_digest
```

`redemption_outcome=redeemed`; sequence is `1`. It is emitted only after the component returns a schema-valid candidate receipt referencing the opaque witness. A second redemption returns no receipt and drives `suppressed/duplicate_attempt` through a separate probe result.

### Controller transcript

`pi.host-integration-controller-transcript.v1` binds exact controller executable digest, host executable digest, process argv/environment allow-list digest, staged package/dependency manifests, process start nonce, witness bytes, redemption bytes, exit status, filesystem before/after manifest, and transcript digest. It is required for independent isolated-proof validation and is not semantic authority.

### Event sequence

The host API adds `prompt_system_applied` as a personalized opt-in event. Exact order:

```text
before_agent_start chain
-> assign final chain to agent.state.systemPrompt
-> read back and hash exact value
-> emit opaque branded prompt_system_applied witness to the contributing component
-> component returns candidate receipt or integration acknowledgement
-> host atomically redeems once and records receipt digest
-> construct or dispatch this agent run's next provider request
```

The host tracks each handler contribution rather than only the final string. Generic preflight success, command handling, intercepted input, queued input, prepared bytes, and callback return cannot issue a witness.

## Generation, attempt, and replay machine

At process boot the trusted host creates a 256-bit random boot nonce. `execution_instance_digest` hashes host executable digest, boot nonce, and extension API version. Generation starts at `0` and increments before every new/reloaded/replaced extension runtime. Attempt ordinal starts at `0` per generation and increments before invoking the first `before_agent_start` handler for one direct non-queued prompt. `prompt_run_attempt_digest` hashes execution instance, generation, ordinal, session-instance nonce, and bound ROCS request digest.

The host state machine is:

```text
allocated -> chained -> applied -> witness_issued -> redeemed
                                 \-> failed
```

Transitions are atomic in the host event loop. Every await rechecks instance/generation/attempt currentness. Reload, replacement, new/resume/fork boundary, or shutdown invalidates nonterminal state. Within a process/generation, redeemed and invalidated tuples remain in a bounded 4096-entry LRU until generation disposal; overflow fails closed before issuing another witness. Restart creates a new execution instance, so tuples cannot collide. Production replay durability remains separately gated; no production delivered receipt is issued until an approved durable host ledger exists.

One witness is evidence that may be redeemed at most once; it authorizes nothing. Component code cannot create a redeemable opaque brand or host map entry through the public API. Compromise of the exact trusted host/component artifacts remains outside the claim.

## Digest registry

All JSON digests use:

```text
sha256(ASCII(domain) || 0x00 || JCS(object without its top-level self-digest))
```

Raw prompt/file/tarball bytes use the same construction without JCS. Domains are:

```text
semantic-release.pi-delivery.v1
semantic-release.pi-package-tarball.v1
pi.loaded-extension-component-manifest.v1
pi.host-executable.v1
pi.execution-instance.v1
pi.prompt-run-attempt.v1
pi.prompt-input.v1
pi.prompt-returned.v1
pi.prompt-final-chain.v1
pi.prompt-applied-entry.v1
pi.prompt-system-application-witness.v1
pi.prompt-system-witness-redemption.v1
pi.host-integration-controller-transcript.v1
semantic-release.pi-host-integration-authorization.v1
semantic-release.pi-host-integration-proof.v1
```

The packet registry maps every schema to exactly one domain and omitted field. Unknown domains reject.

## Unchanged Decision 53 authority graft

V1 delivered validation changes only the delivery receipt/witness seam. The following remain required and unchanged in owner meaning and currentness semantics:

- semantic owner policy, trust roots, rotations/revocations, approvals, publication and lifecycle;
- consumer intent, acceptance, activation and history;
- ROCS materialization and current generation from the current activation;
- AK canonical decision/task/evidence currentness;
- recovery identity and availability;
- owner-specific acquisition receipts and `live_acquisition_implemented=false` behavior;
- complete rejection of fixtures, validators, generators, callers, and copied objects as owner facts.

A delivered receipt validates only when the complete unchanged graph is independently resolved. V0 rejection is delivery-protocol compatibility only; it transfers no semantic compatibility authority.

## Default-off and isolated integration authorization

`SEMANTIC_RELEASE_DELIVERY_DEFAULT_ENABLED=false` and `live_acquisition_implemented=false` remain invariant. Remove `isolatedDogfood`; add no environment, startup, ordinary command, public tool, prompt, flag, default, or general package export.

A closed `semantic-pi-host-integration-authorization.v1` is jointly referenced by separate component-owner and host-owner accepted artifacts and contains exactly:

```text
schema
authorization_id
ak_decision_reference_digest
component_owner_artifact_digest
host_owner_artifact_digest
rocs_packet_manifest_digest
component_commit
package_artifact_identity
loaded_component_manifest_digest
host_commit
host_executable_digest
controller_executable_digest
process_start_nonce
not_before_utc
not_after_utc
max_witness_issuances
max_redemptions
max_replay_probes
disposable_roots
live_acquisition_implemented
production_authorized
authorization_digest
```

Cardinalities are `1`, `1`, and `1`; booleans are false. Roots are absolute disposable paths outside production roots. The controller—not the component constructor—retrieves and validates the authorization, stages exact artifacts, and launches the host with a one-use opaque handle over a private inherited channel. The host consumes the handle before witness issuance. Failure or crash consumes the authorization; no retry is implicit. The replay probe reuses the already consumed witness and is not a second application.

Because the complete current consumer/activation/recovery graph is absent, isolated execution emits only `semantic-pi-host-integration-proof.v1`, never `semantic-pi-delivery-receipt.v1`. The proof has `claim_scope=host_integration_only`, binds authorization/witness/redemption/transcript digests, asserts the replay probe was rejected, and carries explicit false fields for publication, adoption, activation, use, influence, and production authorization. ROCS delivery validation and AK delivery linkage reject this schema. AK may record it only as implementation-validation evidence.

## Packet, validators, and resources

Preserve `docs/project/semantic-release-v0/**` byte-for-byte. Add `docs/project/semantic-pi-delivery-v1/` with schema, invariants, golden/differential fixtures, digest registry, source audit, generator, and manifest.

Exact limits:

- 16 MiB per JSON file;
- 64 MiB aggregate retained bytes;
- 32 generated files maximum;
- depth 64;
- 100,000 array items unless a lower field cap applies;
- 60,000 ms one monotonic validation deadline; equality is expired;
- 4096 replay tuples per generation;
- 4096 package files, 512 MiB extracted bytes, 4096-byte logical paths.

Stable reads use no-follow open, regular-file checks, descriptor/path identity and metadata comparison, `limit+1` reads, retained-byte hashing, and no reopen. Paths are root-local NFC POSIX paths without traversal, backslash, empty segments, normalization/casefold collision, or network form. Symlinks, hard links, special files, extra/missing generated files, and snapshot mutation reject.

`packet-manifest.json` does not list itself. It lists every other generated packet file as UTF-8 path-sorted rows `{path,byte_length,sha256}`. Aggregate preimage is the UTF-8 sequence `path<TAB>byte_length<TAB>sha256<LF>` and domain `semantic-release.pi-delivery-packet-aggregate.v1`. The manifest's self-digest uses its complete rows/aggregate after omitting only `packet_manifest_digest`. Any extra or missing generated file rejects.

The generator has its own canonicalization/digest implementation and imports neither validator. Python and Node validators share no code, generated library, parser, or digest helper. Independent raw vectors cover Unicode astral-key UTF-16 ordering, escapes, duplicate keys, non-NFC/noncharacters/surrogates, booleans-as-integers, unsafe numbers, limits, and all domains.

Runtime architecture:

- existing `semantic_release_protocol.py` and embedded v0 schema remain the historical/general v0 reader;
- new `semantic_pi_delivery_v1_protocol.py` owns the v1 packet and cross-object resolver;
- successor component delivery entrypoints accept only v1; v0 receipts return `unsupported_protocol`;
- historical corpus commands continue validating v0 fixtures;
- unchanged surrounding v0 objects are resolved by the v0 runtime and passed as immutable checked objects into the v1 resolver.

Embedding generation uses uncompressed standard base64 of exact schema bytes with fixed 76-character lines, byte length, and SHA-256. A checked-in generator command writes the module; `--check` regenerates in memory and compares exact bytes. Clean-checkout double regeneration must be byte-identical. Manual editing is forbidden.

## Cross-repo sequence after ADR

1. Reconcile the Pi package vision, foundation, stable-core ADR, and accepted identity artifact; this precedes code.
2. ROCS generates and validates the v1 packet and embedding path.
3. Pi host accepts its owner ADR pinning immutable staging, API, witness/redemption, and trust limitation.
4. Pi host implements and proves the exact event/replay/transcript seam.
5. `pi-ontology-workflows` replaces v0 runtime acceptance with v1 validation, removes constructor authority, and adds no public surface.
6. Separate component-owner and host-owner artifacts issue one joint isolated authorization.
7. A supervised real Pi process emits one integration proof and one rejected replay probe.
8. Actual delivered sealing remains blocked until separately acquired live owner graph and durable host attestation/ledger approval.

## Validation requirements

- exact Python/Node schema, digest, packet, and cross-object parity;
- double deterministic generation and fresh-checkout embedding check;
- repository/component/package/host/executable/snapshot/dependency/generation/attempt substitution attacks;
- forged JSON witness versus opaque live redemption;
- cancellation, stale generation, deadline equality, reload/replacement, failed assignment/readback, missing witness, replay, LRU overflow, restart, and snapshot drift;
- authorization expiry, wrong owner artifact, wrong root, wrong process nonce, crash consumption, and retry rejection;
- proof that defaults/live acquisition/publication/adoption/activation/use/influence remain absent;
- sanitized package installation and one supervised real Pi host integration proof.

## Live D2E boundary

This successor authorizes implementation and a full isolated **host-integration** D2E after post-ADR tasks and one-shot owner authorization. It does not authorize a protocol-valid `delivered` receipt or production semantic-release D2E. Those remain blocked until a real consumer, consent, operator-named canary, independent recovery controller, live owner acquisition, and durable host attestation/ledger are separately accepted.

## Alternatives rejected

- standalone or aliased `pi-adapter`;
- Pi host as component receipt issuer;
- public self-digest as proof of host issuance;
- callback/prepared/static-context evidence as application proof;
- constructor/environment/command test authority;
- isolated fixtures as current owner facts;
- edit v0 in place;
- one receipt implying provider transmission, adoption, and influence.

## Rollback

Before implementation, supersede or reject this proposal. After implementation, revert bounded default-off owner commits while retaining v1 decisions, packet, reviews, authorization, transcripts, and failed attempts. Rollback never restores the fictional identity, constructor authority, v0 acceptance at the successor entrypoint, or a false delivered claim.

## Open questions

None. Production host attestation, durable replay state, consumer identity, canary consent, and recovery ownership are explicit later-gate prerequisites rather than unresolved v1 implementation choices.

## Requested review outcome

Run a fresh exact-byte five-lane review. Any unresolved material issue yields `revise_rfc`; only complete controlling synthesis with `ready_for_adr` permits ADR drafting.
