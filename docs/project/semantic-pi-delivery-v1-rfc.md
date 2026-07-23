---
summary: "RFC for a real pi-ontology-workflows delivery issuer, independent Pi host application witness, and default-off semantic Pi delivery receipt v1."
read_when:
  - "Reviewing the Decision 53 successor protocol or Pi host delivery witness."
system4d:
  container: "Cross-repo successor RFC for ROCS, pi-ontology-workflows, and Pi host."
  compass: "Attest only what the component and host can independently observe, with every identity axis explicit."
  engine: "Closed v1 packet -> component validation -> host post-application witness -> one sealed component receipt."
  fog: "Identity substitution, pre-application callbacks, replay, or test flags can manufacture a false delivered claim."
type: "rfc"
status: "in_review"
rfc_revision: "semantic-pi-delivery-v1-r1"
---

# RFC — Semantic Pi delivery receipt v1

## Decision requested

Accept a versioned successor to the Pi-delivery portion of Decision 53. Preserve v0 as history, replace its fictional `pi-adapter` identity with the accepted `pi-ontology-workflows` component identity, and make `delivered` depend on an independently issued Pi-host post-application witness.

This RFC changes no semantic-owner, consumer-owner, AK, ROCS, or recovery authority. It authorizes no code until a successor ADR and post-ADR execution membrane are complete.

## Inputs

- [`semantic-pi-delivery-v1-problem-brief.md`](semantic-pi-delivery-v1-problem-brief.md)
- [`semantic-pi-delivery-v1-evidence-note.md`](semantic-pi-delivery-v1-evidence-note.md)
- accepted Decision 53 v0 ADR and packet;
- Pi-owner identity artifact at exact commit `63d1e9f5c271007b48c45818d1f419a228de1561`;
- AK task `4108`, evidence `5030` and `5031`.

## Goals

1. Bind the real repository/component/package identity without creating or aliasing `pi-adapter`.
2. Keep component attestation and host observation independently issued and falsifiable.
3. Permit `delivered` only after successful host application of the completed prompt chain.
4. Bind one receipt to one current generation, one prompt-run attempt, one application witness, and one ROCS generation.
5. Preserve default-off and live-gate boundaries.
6. Keep Python and Node validation independent and generated artifacts reproducible.

## Non-goals

- final provider transmission, provider acceptance, model reading, interpretation, influence, or correctness;
- semantic publication, consumer intent/acceptance/adoption/activation, or rollback policy;
- naming a production consumer or canary;
- appointing a recovery controller;
- live acquisition, startup enforcement, defaults, or fleet rollout.

## Identity model

V1 separates the following axes and compares each independently:

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
    "package_distribution_digest": "sha256:<64 lowercase hex>"
  },
  "protocol_issuer": {
    "kind": "pi_extension_component",
    "id": "pi-ontology-workflows",
    "role": "semantic_pi_delivery_attestor"
  }
}
```

`pi-owner` is a governance role, not a Git owner or receipt issuer. Canonical source provenance and local workspace projection are distinct. The Pi host is not the receipt issuer. The package name is not the component ID.

Any `pi-adapter` value in a v1 identity axis is `issuer_scope_violation`. No compatibility alias exists.

## Component receipt

Introduce the closed discriminated union `semantic-pi-delivery-receipt.v1`.

### Common fields

```json
{
  "schema": "semantic-pi-delivery-receipt.v1",
  "governance_owner_role": "pi-owner",
  "issuer": {
    "kind": "pi_extension_component",
    "id": "pi-ontology-workflows",
    "role": "semantic_pi_delivery_attestor"
  },
  "repository_identity": "<exact identity above>",
  "component_identity": "<exact identity above>",
  "package_artifact_identity": "<versioned package identity above>",
  "host_identity": {
    "host_package": "@earendil-works/pi-coding-agent",
    "host_version": "<semver>",
    "extension_api_version": "1.0.0"
  },
  "host_capabilities": [
    "prompt.system.application-witness.v1",
    "prompt.system.chain.v1",
    "session.lifecycle.reason.v1",
    "session.shutdown.v1",
    "ui.confirm.timeout.v1",
    "ui.mode.v1"
  ],
  "loaded_component_identity": {
    "availability": "host_witnessed | unavailable",
    "loaded_component_manifest_digest": "<digest-or-null>",
    "loaded_entry_digest": "<digest-or-null>"
  },
  "execution_identity": {
    "availability": "host_witnessed | unavailable",
    "execution_generation": "<safe-integer-or-null>",
    "execution_instance_digest": "<digest-or-null>"
  },
  "prompt_run_attempt_digest": "<digest>",
  "rocs_generation_receipt_digest": "<digest>",
  "consumer_repository": "<unchanged closed Decision 53 consumer identity>",
  "v0_canary_scope": "<unchanged closed Decision 53 canary scope>",
  "delivery_outcome": "delivered | suppressed | failed",
  "claim_scope": "<outcome constant>",
  "host_application_witness_digest": "<digest-or-null>",
  "pi_delivery_receipt_digest": "<digest>"
}
```

The legacy field name `v0_canary_scope` remains only because the surrounding Decision 53 consumer protocol is still v0. It does not make the delivery receipt v0 and grants no canary authority.

Capabilities are exact, UTF-8 sorted, unique, and host-issued. Static host context may populate host identity and capabilities, but not loaded or execution identity and not the witness.

### Delivered

`delivered` requires:

- `claim_scope=delivered_to_pi_prompt_chain_only`;
- both availability values `host_witnessed` with non-null fields;
- non-null `host_application_witness_digest` resolving to one valid `pi.prompt-system-application-witness.v1`;
- `delivered_effective_execution_digest` equal to the ROCS generation receipt;
- `applied_prompt_chain_entry_digest` equal to the host witness;
- no suppression or error field.

The claim ends at successful installation into Pi's prompt chain. It does not claim provider transmission.

### Suppressed

`suppressed` requires `claim_scope=delivery_suppressed_only`, null witness digest, no delivered/error fields, and exactly one reason:

```text
cancelled
stale_result
policy
incompatible_host
host_witness_unavailable
application_not_acknowledged
duplicate_attempt
```

Loaded and execution identity may be either completely host-witnessed or completely unavailable. Partial availability is malformed.

### Failed

`failed` requires `claim_scope=delivery_failed_only`, null witness digest, one `error_digest`, and no delivered/suppression fields. Deadline equality is failure, not delivery.

## Host-owned application witness

Pi host introduces capability `prompt.system.application-witness.v1` and the closed host-owned object `pi.prompt-system-application-witness.v1`.

Minimum fields:

```json
{
  "schema": "pi.prompt-system-application-witness.v1",
  "issuer": {
    "kind": "pi_host",
    "id": "@earendil-works/pi-coding-agent"
  },
  "host_identity": "<exact component-receipt host identity>",
  "loaded_component_manifest_digest": "<digest>",
  "loaded_entry_digest": "<digest>",
  "execution_generation": "<safe integer>",
  "execution_instance_digest": "<digest>",
  "prompt_run_attempt_digest": "<digest>",
  "handler_registration_index": "<safe integer>",
  "input_prompt_digest": "<digest>",
  "returned_prompt_digest": "<digest>",
  "final_prompt_chain_digest": "<digest>",
  "applied_prompt_chain_entry_digest": "<digest>",
  "application_outcome": "applied",
  "application_target": "agent.state.systemPrompt",
  "observation_phase": "post_application",
  "host_application_witness_digest": "<digest>"
}
```

The Pi-host owner must define the exact loaded-component manifest algorithm in its host ADR before implementation. The algorithm must hash the complete approved extension artifact used for the run, not merely trust a package path, component declaration, or callback. The host independently reads and binds the entry bytes, rejects mutable/replaced material across load and application, and issues a fresh generation after reload/replacement.

The witness is emitted only after the host:

1. chains every `before_agent_start` result;
2. assigns the final chain to `agent.state.systemPrompt`;
3. reads the assigned value back and verifies its digest;
4. binds the personalized extension contribution and final chain;
5. freezes the witness before delivery to the extension.

It is emitted before provider execution and therefore never claims provider transmission. Command handling, intercepted input, queued streaming input, callback success, or generic preflight success cannot issue it.

## Digest contracts

Component receipt:

```text
sha256(ASCII("semantic-release.pi-delivery.v1") || 0x00 || JCS(receipt without pi_delivery_receipt_digest))
```

Host witness:

```text
sha256(ASCII("pi.prompt-system-application-witness.v1") || 0x00 || JCS(witness without host_application_witness_digest))
```

All nested identity and null-availability fields remain in the preimage. JSON follows Decision 53's I-JSON/JCS restrictions, duplicate-key rejection, Unicode rules, safe-integer range, byte/depth caps, and exact type equality.

## State and replay invariants

1. One host witness authorizes at most one component receipt digest.
2. One `(execution_generation, prompt_run_attempt_digest, handler_registration_index)` tuple is single-use.
3. The component records the tuple before sealing success; a second attempt is `suppressed/duplicate_attempt`.
4. Cancellation, stale activation head, stale generation, reload, replacement, shutdown, incompatible capabilities, missing witness, failed assignment, readback mismatch, deadline equality, or witness digest mismatch cannot yield `delivered`.
5. Host, loaded artifact, execution, attempt, generation receipt, consumer, scope, and effective-execution values agree byte-for-byte across resolved objects.
6. Component code cannot mint, accept from caller input, or reconstruct a host witness.
7. The host cannot issue the component receipt.
8. V0 delivery receipts are rejected by the successor runtime after v1 lands but remain readable in historical fixtures and evidence.

## Default-off and authorization

- `SEMANTIC_RELEASE_DELIVERY_DEFAULT_ENABLED=false` remains a compile-time/runtime invariant.
- `live_acquisition_implemented=false` remains mandatory.
- Remove `isolatedDogfood` as a constructor authority flag; do not replace it with an environment variable, startup hook, ordinary command, or fixture token.
- An isolated proof requires a separate one-shot Pi-owner authorization artifact bound to exact ROCS, component, package, host, and witness commits/digests; one attempt; expiry; disposable roots; and explicit non-authorizations.
- A valid isolated proof produces no publication, adoption, activation, use, influence, or production fact.

## Generated packet and validator ownership

Preserve `docs/project/semantic-release-v0/**` unchanged. Add a versioned successor packet under `docs/project/semantic-pi-delivery-v1/` containing:

- closed receipt and host-witness reference schemas;
- normative invariants;
- golden and differential fixtures;
- packet manifest with per-file byte length/SHA-256 and aggregate digest;
- deterministic generator and source audit.

Generated files change only through the packet generator. Python and Node validators remain independent and share no implementation imports.

The current runtime embedding in `src/rocs_cli/semantic_release_schema.py` has no checked-in regeneration command. V1 acceptance requires a deterministic generator command that writes the embedded bytes, byte length, and SHA-256 from the generated normative schema and a clean-check mode proving byte equality. Manual base85 editing is forbidden.

## Compatibility and supersession

- V0 packet, fixtures, ADR, receipts, and evidence are preserved as history.
- V1 changes only the Pi delivery identity/evidence seam and references unchanged surrounding Decision 53 v0 objects where required.
- No v0-to-v1 issuer alias or receipt conversion exists.
- Runtime delivery validation accepts v1 only after the implementation lands.
- The accepted v0 default-off implementation remains rollback history, not a production fallback.

## Cross-repo implementation shape after ADR

1. **ROCS:** generate/validate the v1 packet; add independent Python/Node conformance; document and automate runtime schema embedding.
2. **Pi host:** accept a dedicated host ADR; implement loaded-artifact identity, generation/attempt tracking, post-application witness event, immutability, replay resistance, and tests.
3. **pi-ontology-workflows:** reconcile product docs and the accepted identity artifact; replace v0 delivery runtime with v1; remove constructor authority; validate host witness; remain default-off.
4. **Dogfood:** after all exact commits pass review, issue a separate one-shot authorization and run one isolated real-host attempt plus a duplicate suppression attempt.

## Validation requirements

- exact schema/digest parity across Python and Node;
- deterministic regeneration twice with byte-identical output;
- identity-axis substitution attacks;
- host/component issuer substitution attacks;
- callback-return, prepared-byte, path, manifest, static-capability, and fixture-authority attacks;
- cancellation, stale generation, deadline equality, reload/replacement, failed assignment/readback, missing witness, replay, and duplicate attempts;
- proof that defaults/live acquisition/publication/adoption/activation/use/influence remain absent;
- sanitized isolated install and a real Pi host proof after separate authorization.

## Live D2E boundary

The successor can enable a full isolated delivery D2E only. Production/live D2E remains blocked until independently retrieved owner artifacts establish a real consumer, consent, one operator-named canary, and an independent recovery controller. Those facts require a later gate and are not implementation details of this RFC.

## Alternatives rejected

- create a standalone `pi-adapter` repository;
- silently alias `pi-adapter` to the package;
- use Pi host identity as receipt issuer;
- treat `before_agent_start` return, prepared bytes, static capabilities, or preflight success as application proof;
- keep `isolatedDogfood` as authority;
- edit accepted v0 in place;
- let one receipt imply delivery, provider transmission, adoption, and influence.

## Rollback

Before implementation, supersede or reject this proposal with no runtime effect. After implementation, revert only owner-scoped default-off commits and restore v0 code as historical disabled behavior while retaining v1 decision, packets, reviews, receipts, and failed-attempt evidence. No rollback may re-authorize the fictional identity or a false delivered claim.

## Open questions

None are allowed to affect ADR legality. The Pi-host owner ADR must pin the loaded-component manifest algorithm before its implementation task can be unblocked; that is a post-ADR owner-specific design obligation, not permission to weaken the witness fields or claim.

## Requested review outcome

Run exact-byte multi-lane review. Any unresolved material issue yields `revise_rfc`. Only a controlling synthesis with all required lanes and `ready_for_adr` permits ADR drafting.
