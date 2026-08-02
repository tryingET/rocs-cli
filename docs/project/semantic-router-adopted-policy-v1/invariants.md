---
summary: "Normative invariants for Softwareco routing-policy release, verdict, publication, and currentness objects."
read_when:
  - "Implementing or independently validating Decision 103 protocol objects."
type: "specification"
status: "proposed"
decision_id: 103
---
# Adopted semantic-routing policy v1 invariants

## 1. Scope

These invariants govern protocol objects defined by `protocol.schema.json`. They do not authorize policy authoring, evaluation, publication, acquisition, consumer adoption, or runtime use.

The first policy owner is exactly:

```text
owner_company = softwareco
owner_repository_id = softwareco/ontology
jurisdiction = softwareco-owned ontology IDs only
```

Core ontology references remain dependencies. No core-owned ontology ID may appear in `selectable_ontology_ids` in v1.

## 2. Canonical data

All protocol objects are UTF-8 I-JSON with duplicate keys rejected, integer values only where the schema declares integers, and no byte-order mark. Canonical bytes use RFC 8785 JCS. Every digest string is lowercase `sha256:` plus 64 hexadecimal digits.

Arrays declared `sorted-set` below are duplicate-free and sorted by UTF-8 bytes of their JCS scalar or tuple key. Validators reject rather than repair non-canonical input.

### 2.1 Canonical Softwareco inventory source

The bytes named by `ontologyInventory.inventory_source_path` are exactly the RFC 8785 JCS canonical UTF-8 encoding of one closed I-JSON object with exactly these two members and no others:

```json
{"ontology_ids":["co.software.example"],"schema":"softwareco-ontology-inventory-source.v1"}
```

`schema` is exactly `softwareco-ontology-inventory-source.v1`. `ontology_ids` is nonempty, duplicate-free, and sorted by the unsigned UTF-8 bytes of each complete canonical ID; every member matches canonical `co.software.*` form. The displayed member order follows JCS UTF-16 property ordering and is normative through the exact canonical bytes. Validators reject floats anywhere, duplicate object keys, duplicate IDs, extra keys, invalid UTF-8, a BOM, noncanonical escapes/whitespace/member order/ID order, any `core.*` or other non-Softwareco ID, and an empty inventory; they never parse and repair a noncanonical source.

`inventory_source_digest` is `sha256:` followed by lowercase raw SHA-256 of those exact source bytes, with no domain prefix and no omitted member. `inventory_extractor_algorithm` is exactly `rocs-softwareco-ontology-inventory-source-v1`; it validates the source above and emits `ontology_ids` unchanged. This raw source digest is not one of the sixty-one domain-separated protocol-object digests.

## 3. Digest domains

For canonical object bytes `J` excluding the object's own digest member:

```text
candidate_digest = SHA256("rocs-semantic-policy-candidate-v1\0" || J)
verdict_digest = SHA256("rocs-semantic-policy-verdict-v1\0" || J)
publication_event_digest = SHA256("rocs-semantic-policy-publication-event-v1\0" || J)
publication_history_digest = SHA256("rocs-semantic-policy-publication-history-v1\0" || J)
owner_head_digest = SHA256("rocs-semantic-policy-owner-head-v1\0" || J)
read_receipt_digest = SHA256("rocs-semantic-policy-owner-read-receipt-v1\0" || J)
currentness_proof_digest = SHA256("rocs-semantic-policy-currentness-v1\0" || J)
custody_policy_digest = SHA256("rocs-semantic-policy-custody-policy-v1\0" || J)
contamination_manifest_digest = SHA256("rocs-semantic-policy-contamination-v1\0" || J)
preregistration_digest = SHA256("rocs-semantic-policy-preregistration-v1\0" || J)
execution_attempt_digest = SHA256("rocs-semantic-policy-execution-attempt-v1\0" || J)
approval_artifact_digest = SHA256("rocs-semantic-policy-approval-artifact-v1\0" || J)
issuer_trust_digest = SHA256("rocs-semantic-policy-issuer-trust-v1\0" || J)
caller_challenge_digest = SHA256("rocs-semantic-policy-caller-challenge-v1\0" || J)
owner_checkpoint_digest = SHA256("rocs-semantic-policy-owner-checkpoint-v1\0" || J)
policy_semantic_binding_digest = SHA256("rocs-semantic-policy-binding-v1\0" || J)
attempt_envelope_digest = SHA256("rocs-semantic-policy-attempt-envelope-v1\0" || J)
issuer_attestation_digest = SHA256("rocs-semantic-policy-issuer-attestation-v1\0" || J)
challenge_consumption_digest = SHA256("rocs-semantic-policy-challenge-consumption-v1\0" || J)
verification_request_digest = SHA256("rocs-semantic-policy-verification-request-v1\0" || J)
ontology_inventory_digest = SHA256("rocs-semantic-policy-ontology-inventory-v1\0" || J)
policy_binding_receipt_digest = SHA256("rocs-semantic-policy-binding-receipt-v1\0" || J)
receipt_attestation_body_digest = SHA256("rocs-semantic-policy-receipt-body-v1\0" || J)
challenge_consumption_body_digest = SHA256("rocs-semantic-policy-consumption-body-v1\0" || J)
b0_exposure_evidence_digest = SHA256("rocs-semantic-policy-b0-exposure-v1\0" || J)
access_history_event_digest = SHA256("rocs-semantic-policy-access-event-v1\0" || J)
access_history_digest = SHA256("rocs-semantic-policy-access-history-v1\0" || J)
role_separation_receipt_digest = SHA256("rocs-semantic-policy-role-separation-v1\0" || J)
process_reservation_digest = SHA256("rocs-semantic-policy-process-reservation-v1\0" || J)
rollback_plan_digest = SHA256("rocs-semantic-policy-evaluation-rollback-v1\0" || J)
policy_concept_ids_digest = SHA256("rocs-semantic-policy-concept-ids-v1\0" || J)
joint_route_sets_digest = SHA256("rocs-semantic-policy-joint-sets-v1\0" || J)
capability_coordinate_digest = SHA256("rocs-semantic-policy-capability-coordinate-v1\0" || J)
clock_coordinate_digest = SHA256("rocs-semantic-policy-clock-coordinate-v1\0" || J)
approval_attestation_body_digest = SHA256("rocs-semantic-policy-approval-body-v1\0" || J)
verdict_approval_subject_digest = SHA256("rocs-semantic-policy-verdict-approval-subject-v1\0" || J)
publication_approval_subject_digest = SHA256("rocs-semantic-policy-publication-approval-subject-v1\0" || J)
authority_credential_digest = SHA256("rocs-semantic-policy-authority-credential-v1\0" || J)
channel_coordinate_digest = SHA256("rocs-semantic-policy-acquisition-channel-coordinate-v1\0" || J)
consumption_store_coordinate_digest = SHA256("rocs-semantic-policy-consumption-store-coordinate-v1\0" || J)
consumption_signing_key_coordinate_digest = SHA256("rocs-semantic-policy-consumption-signing-key-coordinate-v1\0" || J)
execution_contamination_digest = SHA256("rocs-semantic-policy-execution-contamination-v1\0" || J)
custody_readiness_digest = SHA256("rocs-semantic-policy-custody-readiness-v1\0" || J)
custody_readiness_subject_digest = SHA256("rocs-semantic-policy-custody-readiness-subject-v1\0" || J)
execution_contamination_subject_digest = SHA256("rocs-semantic-policy-execution-contamination-subject-v1\0" || J)
custody_readiness_verification_request_digest = SHA256("rocs-semantic-policy-custody-readiness-verification-request-v1\0" || J)
execution_contamination_verification_request_digest = SHA256("rocs-semantic-policy-execution-contamination-verification-request-v1\0" || J)
preexecution_verification_bundle_digest = SHA256("rocs-semantic-policy-preexecution-verification-bundle-v1\0" || J)
protected_access_activation_subject_digest = SHA256("rocs-semantic-policy-protected-access-activation-subject-v1\0" || J)
protected_access_activation_digest = SHA256("rocs-semantic-policy-protected-access-activation-v1\0" || J)
evaluator_invocation_challenge_digest = SHA256("rocs-semantic-policy-evaluator-invocation-challenge-v1\0" || J)
evaluator_execution_start_subject_digest = SHA256("rocs-semantic-policy-evaluator-execution-start-subject-v1\0" || J)
evaluator_execution_start_proof_digest = SHA256("rocs-semantic-policy-evaluator-execution-start-proof-v1\0" || J)
evaluator_execution_start_verification_request_digest = SHA256("rocs-semantic-policy-evaluator-execution-start-verification-request-v1\0" || J)
evaluator_execution_launch_subject_digest = SHA256("rocs-semantic-policy-evaluator-execution-launch-subject-v1\0" || J)
evaluator_execution_launch_receipt_digest = SHA256("rocs-semantic-policy-evaluator-execution-launch-receipt-v1\0" || J)
evaluator_authenticated_channel_coordinate_digest = SHA256("rocs-semantic-policy-evaluator-authenticated-channel-coordinate-v1\0" || J)
protected_descriptor_handoff_subject_digest = SHA256("rocs-semantic-policy-protected-descriptor-handoff-subject-v1\0" || J)
protected_descriptor_handoff_receipt_digest = SHA256("rocs-semantic-policy-protected-descriptor-handoff-receipt-v1\0" || J)
protected_access_closure_subject_digest = SHA256("rocs-semantic-policy-protected-access-closure-subject-v1\0" || J)
protected_access_closure_digest = SHA256("rocs-semantic-policy-protected-access-closure-v1\0" || J)
```

No digest is interchangeable with Decision 102 route, discovery, policy, provenance, or result digests.

### 3.1 Acyclic dependency schedule

Producers and validators must follow this topological order; no edge may point to a later row:

```text
closed canonical inventory source bytes/path/raw digest/extractor at real commit/tree I + extracted closed inventory coordinate/digest + custody policy + frozen role/access history + sealed D/U/O coordinates
→ P3 custody-readiness subject signing that I-bound source path/raw digest/extractor/extracted IDs/snapshot/coordinate digest + custodian signature/credential + independent caller verification request
→ P4 D disclosure + Decision 102 policy/provenance from strict-ancestor source revisions + descendant candidate snapshot C retaining every exact source byte and byte-identical canonical inventory source at the same path + candidate contamination manifest (10 pre-attempt surfaces)
→ candidate
→ P5 custodian process reservation (non-executing, expires unused on later validation failure)
→ attempt envelope (binds candidate + reservation)
→ execution-contamination subject + custodian/reviewer signatures/credentials + independent caller verification request
→ preexecution verification bundle (nests both caller-request preimages)
→ preregistration (binds candidate, envelope, both contamination objects, the complete request bundle, custody, roles, datasets, evaluator, floors)
→ signed protected-access activation (binds validated preregistration, a base history of at most 254 events, exact evaluator operator, U/O seals, reservation, the activated-history digest, and one time-equal appended grant event)
→ closed evaluator-authenticated-channel coordinate jointly bound by evaluator and custodian-gateway identities
→ caller-supplied evaluator invocation challenge over that channel
→ unsigned prospective execution-start subject
→ evaluator-start verification request pinning the channel, challenge, subject, authorities, credentials, trust roots, and keys
→ evaluator-signed prospective execution-start authorization over that exact subject
→ crash-safe custodian launch-gateway authorization receipt proving same-channel presentation plus atomic zero-to-one reservation consumption before spawn
→ optional custodian handoff receipt atomically recording the first gateway-mediated revocable U/O handle after spawn and before row read; raw OS descriptors never transfer
→ nullable P6 raw execution receipt: null for no-start, null or present for zero-pass interruption, present for one-pass interruption, and present for two-pass completion
→ mandatory custodian-signed protected-access closure (activated history plus one terminal revoke, authorization inactive no later than expiry)
→ closed execution-attempt object and metrics
→ verdict approval subject and post-execution custodian/reviewer approvals
→ verdict
→ P7 publication event/history/head/checkpoint/currentness
```

The candidate never binds the execution-contamination attestation, preregistration, envelope, attempt, or verdict. The candidate contamination manifest never contains `candidate_digest` or `attempt_envelope_digest`. The downstream execution-contamination attestation is bound only by preregistration, the post-execution approval subject, and verdict. Validators construct a dependency graph from the normative equality schedule and reject a back edge or cycle before digest computation.

## 4. Candidate release

A candidate release binds exactly:

- owner company and repository ID;
- owner Git commit and tree;
- root-relative policy and provenance paths;
- Decision 102 policy and provenance digests;
- route protocol/schema/algorithm coordinates;
- frozen ontology snapshot digest;
- exact root-relative Softwareco inventory path and inventory digest at that snapshot;
- sorted Softwareco-owned selectable IDs using their canonical `co.software.*` identifiers;
- independent candidate-contamination-manifest digest covering exactly the ten pre-attempt surfaces;
- candidate digest.

The candidate uses two distinct Git coordinates. The nested closed canonical inventory object identifies the real P3 inventory-source commit/tree **I** and binds `inventory_source_path`, the raw `inventory_source_digest`, the fixed `inventory_extractor_algorithm`, extracted `ontology_ids`, `ontology_snapshot_digest`, and its domain-separated `inventory_digest`; candidate `owner_git_commit` / `owner_git_tree` identify the later descendant snapshot **C**. I must be a strict ancestor of C, and both commit and tree pairs must differ: candidate owner commit/tree equality with nested inventory owner commit/tree is invalid. Candidate `ontology_inventory_path` equals nested `inventory_source_path`. Candidate `ontology_snapshot_digest`, `ontology_inventory_digest`, and `selectable_ontology_ids` equal the P3 I-bound inventory coordinate, with `selectable_ontology_ids` exactly equal to the nested inventory’s extracted `ontology_ids`. Resolving `inventory_source_path` at C must yield bytes exactly equal to the digest-bound canonical source bytes at I; re-extraction at both commits must emit that same ID array. Every selectable ID must be a member of that exact frozen inventory object. The `co.software.*` lexical form is necessary but never sufficient authority. Prefix inference, an absent inventory member, a `core.*` ID, or a relabeled/copied core meaning is invalid.

The candidate's `policy_semantic_binding` is computed by parsing the exact digest-bound Decision 102 policy and provenance bytes. Both embedded owner repositories must equal `softwareco/ontology`; every executable concept ID and every member of every joint-route ID set must be in both `selectable_ontology_ids` and the frozen inventory; the binding inventory digest must equal the candidate inventory digest. Every provenance record's `source_owner_repo`, not merely the manifest-level owner, must equal `softwareco/ontology`. The closed binding receipt names the fixed `rocs-adopted-policy-binding-v1` extractor, exact policy/provenance/inventory digests, parsed owners, and concept/joint-set digests. That extractor first validates the exact Decision 102 v0 policy/provenance objects, then emits `policy_concept_ids` as the UTF-8-byte-sorted JCS array of `concepts[].ont_id`; it emits each `joint_routes[].ont_ids` as a UTF-8-byte-sorted JCS array and sorts those arrays by their complete JCS bytes. The two output digests use the explicit domains above over those complete JCS arrays. Its fields equal the candidate and semantic-binding fields; its receipt and binding digests validate under separate domains. A later route result is valid under this coordinate only when every `selected_ont_id` belongs to that same set.

P4 constructs Decision 102 policy and provenance from declared policy-authority and provenance-source revisions that are each real strict ancestors of C. C must contain the exact digest-bound policy and provenance bytes, exact copies at the named paths of every provenance source byte resolved from those declared revisions, and the exact canonical inventory source bytes from I at the candidate `ontology_inventory_path`, which equals nested `inventory_source_path`. Each retained source copy must be digest-equal to its named strict-ancestor blob; a same-as-C or non-ancestor source revision, missing or changed retained byte, changed/noncanonical inventory source, source path/digest/extractor/extracted-ID mismatch, or any attempt to serialize a nested inventory containing C’s own hash into C is invalid. Validators derive these relations from the local Git object graph and blobs; caller assertions cannot establish ancestry or byte equality. A candidate is immutable. Correcting any byte creates a new candidate ID and digest.

Candidate paths are canonical root-relative POSIX paths: no absolute path, empty segment, `.`, `..`, backslash, NUL, symlink traversal, or alias. Later capture inherits Decision 102's descriptor and Git object-database safety requirements.

## 5. Evaluation custody, preregistration, and verdict

A closed custody policy is issued by the named custodian and binds its authenticated principal coordinate, exact source coordinates and license/consent authority artifacts, privacy class, the complete mandatory prohibited-content set, ACLs, audit log, retention periods by artifact class, backup controls, all retention/withdrawal/privacy-exposure deletion triggers and verification, exposure retirement, and incident-response reference. Dataset creation cannot begin until that policy is approved and digest-fixed.

P3 ends with one closed `semantic-routing-policy-custody-readiness.v1` receipt. It nests the exact base-access-history preimage capped at 254 events plus its digest, so the independent caller can verify the two-event activation/closure reserve before D disclosure. Its separately domain-digested subject binds the authenticated custodian authority, custody policy, role separation, that access history, the nested I-owned inventory including source path/raw digest/extractor/extracted IDs/snapshot/coordinate digest, sealed D digest, U/O seals, the pre-disclosure seal assertion, and issuance time while excluding the approval and outer receipt digest. The receipt nests the exact custodian credential and an Ed25519 `custody_readiness` approval whose signed subject equals that subject digest. Credential/authority identity, validity, non-revocation, trust root, raw-32 public key, approval body, purpose, and signature must verify. A separate caller-supplied `semantic-routing-policy-custody-readiness-verification-request.v1`, never nested authority, pins that complete base-history preimage/digest and the complete expected custodian authority/credential, approval digest, trust root, public key, subject, and receipt. The subject authority, credential identity, approval issuer, request authority, custody-policy authority, and preregistration `custodian_authority` must be byte-equal to the exact frozen `custodian` role-assignment authority coordinate; matching only principal or role text is invalid. It contains no candidate, policy/provenance, envelope, preregistration, execution, metrics, outcome, or verdict field. P4 cannot disclose D or author policy until this signed receipt and independent request validate; ROCS, a policy author, or the controller cannot synthesize the custodian fact.

A closed **candidate contamination manifest** names the immutable Decision 98 deny coordinates exactly: preregistration commit `286773ee6a88b9fd2276f8008898c57ff9a073b9`, failed-run commit, lock digest, prompt-set digest, and report digest. Its coverage is the exact ordered bijection acceptance dataset, aliases, D, evaluator, fixtures, floors, O, policy, regression inputs, and templates—exactly ten pre-attempt surfaces. Each row's `source_digest` equals the actual policy, D/U/O seal, evaluator, fixtures, floors, templates, aliases, or regression-input coordinate. It contains neither `candidate_digest` nor `attempt_envelope_digest`, so the candidate can bind this manifest without a back edge.

After candidate freeze and attempt-envelope construction, a separate `semantic-routing-policy-execution-contamination-attestation.v1` uses an acyclic subject binding authenticated custodian and independent-review authorities, candidate digest, candidate-contamination-manifest digest, attempt-envelope digest, evaluator digest, `source_digest == attempt_envelope_digest`, deterministic overlap receipt, independent derivation review, `no_reuse`, and issuance time while excluding approvals and outer attestation digest. It nests exact authority credentials and separate Ed25519 approvals with stage-specific purposes `execution_contamination_custodian` and `execution_contamination_independent_review`; both sign that exact subject. A separate caller-supplied `semantic-routing-policy-execution-contamination-verification-request.v1` pins both authorities, credentials, approvals, trust roots, public keys, subject, and attestation. The subject authorities, credential identities, approval issuers, request authorities, and preregistration `custodian_authority` / `independent_review_authority` must respectively be byte-equal to the exact frozen `custodian` and `independent_reviewer` role-assignment authority coordinates; all repository, commit, tree, credential, principal, and role fields participate in equality. Its domain-digested identity flows only downstream into preregistration, verdict approval subject, and verdict. P5 acquires the custodian-issued single-invocation reservation before constructing the envelope; acquiring that lock is non-executing and grants no permission to read sealed rows. The reservation is nested into the envelope and thereby authenticated by the later custodian/reviewer execution-contamination signatures. P6 cannot start the reserved process until the attestation, both nested caller-request preimages, preregistration, reservation identity/expiry, every join, and the downstream signed protected-access activation validate; validation failure leaves the reservation unused to expire or be released under its predeclared cleanup rule. Together the ten-row candidate manifest and one authenticated execution attestation cover the same eleven prohibited B0-reuse surfaces without a digest cycle. An unsigned assertion, unrelated clean digest, duplicate surface, opaque or incomplete coverage, authority/pin mismatch, or backward dependency is invalid.

After candidate freeze, a preregistration binds the exact candidate digest, custody and candidate-contamination digests, nested signed P3 custody-readiness receipt/digest, nested signed execution-contamination attestation/digest, and a closed preexecution-verification bundle that nests both complete independent caller-request preimages and their digests, plus explicit frozen `custodian_authority` and `independent_review_authority` coordinates, frozen inventory and dataset seals, evaluator, floors, one-attempt envelope, and authenticated role assignments. The readiness subject's custody/role/access/inventory/D/U/O fields equal preregistration fields; the execution-contamination subject joins candidate/manifest/envelope/evaluator exactly. Both independently supplied requests validate before protected-access activation; their complete canonical objects remain reachable through preregistration → verdict → currentness proof, and each object digest equals its legacy preregistration digest field. An opaque request digest without the matching preimage is invalid. Preregistration has no approval over future execution outcome or `custodian_acceptance_digest`; the P3/P5 approvals authorize only their exact pre-execution subjects. Any later approval over execution outcome belongs only to the post-execution verdict-approval subject. Every role assignment binds principal/repository/commit/tree/artifact coordinates, exact role, access rights, timestamp, and a nested independently assessed B0 exposure-evidence object whose principal/result/evidence digest equal the assignment. U/O authors, annotators, adjudicator, custodian, evaluator operator, and independent verdict reviewer must be B0 exposure `disproven`; policy and D authors may be exposed but may never receive sealed U/O access.

Role separation is mechanical. The preregistration contains exactly one semantic owner, policy author, D author, U author, O author, adjudicator, custodian, independent reviewer, evaluator operator, and implementer plus exactly two annotators, in the canonical role order. All twelve principal IDs are pairwise distinct, including semantic owner, custodian, D/U/O authors, evaluator, adjudicator, reviewer, implementer, and both annotators. Every authority coordinate's `authority_role` equals its assignment role. The nested role-separation receipt binds the canonical matrix, participant-array digest, these pairwise-distinct and role-equality results, absence of access conflict, and exact access-history digest. The D author differs from policy authors, custodian, evaluator operator, and U/O authors; the custodian differs from the independent reviewer; policy author differs from U author, O author, annotators, adjudicator, custodian, evaluator operator, implementer, and independent reviewer; U/O authors differ from implementers and policy authors; annotators differ from each other, authors, policy authors, evaluator operator, implementer, and adjudicator; the adjudicator differs from all authors/annotators/policy authors/implementers; no principal receives both policy bytes and sealed U/O rows before verdict fixation. Repository difference alone is insufficient. A nested append-only access history records every assignment/grant/revocation with sequence and predecessor digests; its principals, roles, current grants, and digest must reconcile exactly with the twelve assignments, custody ACL, and role-separation receipt. No opaque current-access claim substitutes for history.

P3 freezes a **base** access history and eligibility policy with at most 254 events, reserving one slot for activation and one for mandatory closure. It does not grant the evaluator operator sealed U/O read or process-start authority. After every P5 signature, caller-request preimage, preregistration, reservation, and equality join validates, the custodian alone may issue one `semantic-routing-policy-protected-access-activation.v1`. Its non-circular signed subject binds the preregistration digest, P3 base-history digest, exact frozen custodian and evaluator-operator authorities, U/O seals, reservation, the exact grant-access array (`sealed_acceptance_rows`, `sealed_operational_rows`, `evaluator_bytes`), three exact action permissions (`read_sealed_acceptance`, `read_sealed_operational`, `start_reserved_evaluator_process`), the complete activated-history digest, exact appended grant-event digest, and a bounded issuance/expiry interval. The activation nests the base history byte-identically and an activated history of at most 255 events that is exactly the base sequence plus one terminal `grant` for the frozen evaluator operator. The grant predecessor equals the prior terminal event, its access equals `grant_access`, and `grant.occurred_at == subject.issued_at`; changing or backdating history invalidates the custodian signature. The subject custodian, approval issuer/credential/authority, preregistration custodian, and custodian coordinate pinned by the nested P3 caller request are byte-identical; the approval uses purpose `protected_access_activation`. The reservation executor equals the frozen evaluator-operator assignment byte-for-byte. P6 rejects a missing, expired, reordered, capacity-exhausted, extra-event, differently authorized, or self-issued activation.

Activation is not a bearer credential. Before process start, the caller supplies one closed `semantic-routing-policy-evaluator-authenticated-channel-coordinate.v1`. It names the exact evaluator and custodian-gateway authorities, channel ID, allowlisted mutual-TLS or Unix-peercred-plus-Ed25519 exporter algorithm/context/digest, establishment and expiry times, and a domain-separated coordinate digest. The caller then constructs, in order, a fresh invocation challenge over that channel, the unsigned prospective start subject, and an independent verification request that nests and pins the complete channel and challenge, the expected subject digest, both endpoint credentials/raw Ed25519 keys/trust roots, and approval purpose before any signature or launch exists. The evaluator signs the non-circular start authorization with purpose `evaluator_execution_start`; it binds preregistration, envelope, reservation, activation, challenge, complete channel coordinate, process-start ID, and `authorized_start_not_after`.

The pinned custodian launch gateway accepts that proof only on the live channel whose exporter recomputes to the signed coordinate. In one crash-safe pre-spawn transaction it verifies the evaluator signature, consumes the reservation from zero to one, records the launch authorization, and signs `semantic-routing-policy-evaluator-execution-launch-receipt.v1` with purpose `evaluator_execution_launch`; only then may it spawn. The launch subject binds proof/request, both authorities, complete channel coordinate, reservation, process ID, consumption counts, sealed U/O digests, `protected_descriptors_opened=false`, authorization time, and spawn deadline. Thus gateway failure after the transaction still leaves an authoritative receipt; failure before it leaves the reservation unconsumed.

Spawn alone receives no sealed U/O descriptor. At first protected handoff, the same gateway atomically records and signs `semantic-routing-policy-protected-descriptor-handoff-receipt.v1` with purpose `protected_descriptor_handoff` while issuing only a gateway-mediated revocable handle—never a raw OS descriptor or durable capability. Every protected read remains gateway-authorized under that live handle. Its subject binds start proof, launch receipt/request, endpoint authorities, complete channel, reservation/process, U/O seals, handoff counts `0 → 1`, observed handoff time, handle expiry, `direct_os_descriptor_transfer=false`, and `per_read_gateway_authorization_required=true`. A process crash before handoff is interrupted with no protected access; a completed attempt requires this receipt. Detached proof replay, another channel, consumption race, gateway crash window, direct descriptor transfer, or row read before signed handoff is invalid. Proof, request, launch, and handoff receipts remain reachable through attempt → verdict → currentness.

Protected access is valid only for the exact reservation/process, through the custodian gateway, and only before the earliest of activation, channel, challenge, evaluator-authorization, gateway-spawn, reservation, and handle deadlines. Immediately after the raw execution receipt is fixed—or on pre-start failure, abort, indeterminate termination, or expiry—the exact frozen custodian must sign one `semantic-routing-policy-protected-access-closure.v1` with purpose `protected_access_closure`. Its acyclic subject binds custodian authority, activation and activated-history digests, reservation, exact process invocation count, custodian-observed spawn and termination/reaping times, closure state, activation expiry, gateway-mediated handle closure state/time, the complete terminal-history digest, and appended revoke-event digest. For `attempt_state == not_started`, process invocations are zero, spawn/termination times are null, proof/request and crash-safe launch authorization retain exactly the lawful prefix that exists, descriptor handoff is null, descriptor state is `never_handed_off`, and closure reason is `aborted | expired`. For `interrupted`, proof/request/launch authorization are non-null and one process invocation has a signed custodian-observed `process_spawned_at` plus `process_terminated_at` with `process_termination_state=terminated_and_reaped`. With zero completed passes, handoff and raw receipt may both be null; if a handoff exists its gateway-mediated handle must be revoked/closed even when the raw receipt is null; a non-null raw receipt requires that handoff. Retaining one completed primary pass requires both handoff and raw receipt. For `completed`, proof/request/launch/handoff/raw receipt are all non-null, exactly two ordered passes exist, the process is terminated/reaped, and the handle is revoked/closed. The terminal history is exactly activated history plus one final `revoke` for the same evaluator and access; its predecessor is the grant and `revoke.occurred_at == subject.closed_at`. Timestamp order is strict: grant/activation issuance ≤ launch authorization ≤ custodian-observed spawn ≤ any handoff ≤ any raw receipt fixation ≤ handle close/process termination ≤ closure/revoke time. Spawn must be no later than every signed reservation/challenge/channel/authorization/gateway deadline; handle expiry is no later than activation expiry. Completion/failure/abort/indeterminate closure occurs no later than expiry; the gateway rejects every read after handle expiry or closure even if evaluator cleanup is delayed. An `expired` or otherwise late closure forces verdict outcome `indeterminate` and can never publish. Closure credential/issuer/trust/key equal the frozen preregistration custodian and final caller pins. The closed attempt, verdict subject, verdict, and currentness proof bind identical proof/request/launch/handoff/receipt/closure prefixes. A missing closure, un-reaped started process, unclosed handed-off handle, direct descriptor transfer, terminal grant, late publishable closure, wrong signer/principal/process, or history above 256 events is invalid.

One immutable preregistered attempt envelope binds exact argv, the closed seven-name environment object (`HOME`, `LANG`, `LC_ALL`, `PATH`, `PYTHONHASHSEED`, `TMPDIR`, `TZ`), runtime/evaluator/candidate and U/O seals, working-directory class, one nested custodian-issued process reservation whose `executor_authority` is byte-identical to the frozen `evaluator_operator` role assignment and whose lock/store/time bounds validate, fixed pass order, zero retries/reruns/repairs, and a nested rollback plan with owner, preimage/final-state, cleanup, and verification coordinates. Envelope reservation/rollback digest fields equal the nested objects; duplicate or ambient environment names are impossible. It reserves at most one process invocation. A truthful attempt state is exact: `not_started` has zero invocations/passes and a mandatory closure; proof/request may be absent, present without gateway authorization, or present with the crash-safe pre-spawn launch receipt, while handoff/raw receipt remain null and outcome is `indeterminate`. `interrupted` has one invocation, mandatory proof/request/launch, zero or one completed primary pass, mandatory closure, and outcome `indeterminate`; its zero-pass prefix is exactly one of no handoff/no raw receipt, handoff/no raw receipt, or handoff/raw receipt, while a retained primary pass requires both. `completed` has one invocation and exactly two ordered internal passes—`primary`, then `immediate_repeat`—over identical coordinates with handoff/raw receipt/closure. Completed pass input-coordinate, row-receipt, and result-byte digests satisfy the determinism oracle. Retry, selective rerun, an extra pass, same-candidate repair, or a second invocation is forbidden. Every nullable prefix coordinate is one of these eight end-to-end attempt/verdict branches and is byte-equal across attempt, closure, verdict subject, and verdict: absent facts are null everywhere; present proof/request/launch/handoff/receipt objects are nested and their digests match everywhere. Closure and approval-subject schemas have seven unique prefix projections because the zero-pass-with-receipt and one-pass interrupted branches intentionally share the same digest projection and are disambiguated by the nested execution-attempt branch and its digest; duplicate alternatives are forbidden under `oneOf`. A completed verdict cannot nest a not-started/interrupted attempt or closure, and a non-completed attempt cannot escalate above `indeterminate`.

A verdict nests and binds the exact custody policy, preregistration, candidate contamination manifest, downstream execution-contamination attestation, attempt envelope, signed protected-access activation, evaluator-signed execution-start proof and caller verification request, custodian launch-gateway receipt, mandatory signed protected-access closure, and execution attempt plus evaluator commit/tree/tool digest, D/U/O dataset digests, execution receipt digest, metrics digest, outcome, and exact authority coordinates and closed signed approval artifacts for both custodian approval and independent verdict review. Every nested digest equals the corresponding verdict field. Candidate inventory and candidate-contamination digests equal preregistration, candidate contamination coverage, and verdict values. The execution-contamination attestation digest equals preregistration, verdict, and verdict-approval-subject fields; its candidate, candidate-contamination, envelope, evaluator, and source joins validate exactly. Verdict D/U/O/evaluator/floor/execution coordinates equal preregistration, coverage objects, attempt envelope, execution attempt, and receipt coordinates. The attempt envelope nested by verdict is byte-identical to the preregistration envelope and its digest equals preregistration and execution-attempt fields. The protected-access activation, evaluator execution-start proof/request, gateway launch receipt, and protected-access closure nested by both execution attempt and verdict are byte-identical; their digests equal the execution-attempt, verdict, and verdict-approval-subject fields. Activation subject/history/executor/seal/reservation, evaluator credential/challenge/channel/deadline/proof-of-possession, gateway authority/key/channel/zero-to-one crash-safe pre-spawn authorization, descriptor-handoff authority/channel/U/O seals/zero-to-one transfer, and closure signer/state/terminal-revoke/receipt/expiry joins validate exactly. Each authority coordinate binds authenticated principal ID, role, repository ID, Git commit/tree, and the digest of a separate authority credential; it never contains or identifies the enclosing verdict approval. The verdict `custodian_authority` and `independent_review_authority`, verdict-approval-subject authorities, authority credentials, approval issuers, and external verification-request authority pins must respectively be byte-equal to `preregistration.custodian_authority` and `preregistration.independent_review_authority`, and therefore to the exact frozen role-assignment coordinates; different commit, tree, credential, repository, principal, or role bytes are invalid even when signatures otherwise verify. The custodian is exactly `softwareco/owned/dspx` unless a pre-data reviewed packet revision names another owner. Custodian and independent-review principals must differ from each other, the policy owner, policy authors, and evaluator operator; a self-issued approval is invalid.

The verdict also nests one non-circular `verdict_approval_subject`. Its separately domain-digested body binds verdict ID, candidate, evaluator, preregistration, D/U/O, candidate contamination, execution-contamination attestation, custody, attempt envelope, execution attempt/receipt, metrics, exact outcome, both authority coordinates, and issuance time, but excludes both approvals and `verdict_digest`. Custodian and independent-review approval artifacts must each bind that exact subject digest. Each approval nests a separately domain-digested attestation body mirroring issuer, subject, purpose, validity, non-revocation, trust root, and Ed25519 public key; every mirrored outer/body field must be byte-equal. The issuer coordinate's `authority_credential_digest` equals a separately supplied, caller-pinned credential object—not the enclosing approval digest. That credential repeats the coordinate identity fields, binds its validity and trust root, and carries canonical base64 of exactly 32 raw Ed25519 public-key bytes. Its credential digest uses the separate domain above; `public_key_digest` is SHA-256 of those decoded 32 bytes. Credential and coordinate identity fields, trust root, key digest, validity, and non-revocation must all agree with the approval and external request. The signature input is UTF-8 bytes `rocs-semantic-policy-approval-signature-v1\0` followed by the raw 32 bytes decoded from the body digest's lowercase hexadecimal suffix. Signing JCS, ASCII digest text, or any other representation is invalid. The approval artifact itself may then be included in the verdict without a digest cycle. Changing outcome, metrics, authority, or any evidence coordinate invalidates both signatures; an approval cannot be replayed across verdicts.

`outcome` is exactly `pass | fail | indeterminate`. Precedence is:

1. evidence-integrity or execution-validity defect → `indeterminate`;
2. otherwise any semantic, utility, operational, compatibility, or review gate failure → `fail`;
3. otherwise every frozen gate and independent review passes → `pass`.

`not_started` and `interrupted` attempts, an `expired` closure, or any closure after activation expiry force `indeterminate`. Only a `completed` attempt with two valid passes and a timely `completed` closure may be `pass | fail` under the frozen metric gates. A null execution receipt is valid for `not_started` and for the exact zero-pass interrupted branches; it can never publish.

Only `pass` may be referenced by a `publish` event. A later discovery of leakage or integrity loss requires an owner `revoke` event; the old verdict is not rewritten.

Raw U/O prompts, labels, and row outputs are not protocol members and must not enter ROCS, Git, Pi, session summaries, or AK. Only digests, role/custody receipts, and aggregate verdicts may cross the custodian boundary.

## 6. Publication event chain

An owner publication history is one closed `semantic-routing-policy-publication-history.v1` object encoded as RFC 8785 JCS. It contains `owner`, a non-empty `events` array in ascending sequence order, and `history_digest`. The history digest uses its separate domain over the object without `history_digest`; no JSONL, concatenated-record, mutable-index, or filesystem enumeration is normative.

Every event binds:

- owner and namespace;
- monotonically increasing positive `sequence`;
- `previous_event_digest` (`null` only at sequence 1);
- action `publish | withdraw | revoke`;
- candidate and verdict digests;
- the exact semantic-owner authority coordinate;
- a non-circular, separately domain-digested publication-approval subject that binds owner, semantic-owner authority, sequence, predecessor, action, candidate, verdict, reason, and issuance time while excluding owner approval and event digest;
- a closed signed owner approval artifact whose authenticated issuer, subject digest, purpose, validity, trust root/key, signature, and non-revocation state match that exact subject and action;
- reason code;
- issued-at UTC instant;
- event digest.

For sequence `n > 1`, `previous_event_digest` equals the digest of sequence `n-1`. The candidate digest is stable across a withdrawal/revocation event targeting that publication. `publish` requires a pass verdict. `withdraw` is a reversible lifecycle choice only through a new publish event. `revoke` marks the target unsafe; republishing the same candidate digest is forbidden. A `publish` event may use at most sequence 9,999, reserving sequence 10,000 for a terminal `withdraw` or `revoke`; owner storage must also preflight byte capacity for that reserved event before accepting a publish.

There is no mutable `latest` release. The only mutable owner-store pointer is an authenticated compare-and-swap checkpoint on one owner-issued authoritative ref. Each checkpoint names the exact head, complete history, owner commit/tree, monotonically increasing checkpoint sequence, and predecessor checkpoint digest. History is authoritative only when every supplied event verifies, the history digest verifies, and the authenticated current checkpoint matches that same complete history and terminal event.

Concurrent fork, sequence gap, predecessor mismatch, missing event, duplicate sequence, checkpoint fork/regression, a history longer than the checkpoint, or insufficient reserved append bytes is `invalid_owner_history`. An old otherwise-valid publish head H1 is not current after authenticated checkpoint H2 records withdrawal or revocation.

## 7. Owner head, trust bundle, challenge, and local read receipt

An owner head binds owner, namespace, terminal sequence/digest, owner repository commit/tree, publication-history path/digest, owner-store ID, authoritative ref, monotonic checkpoint sequence, and head digest. It never embeds a checkpoint digest: the authenticated checkpoint commits the head digest unidirectionally, avoiding a digest cycle. Its `publication_history_digest` equals the nested history object's digest and its checkpoint sequence equals the authenticated owner checkpoint.

The capability coordinate digest is over the JCS object `{capability_id, capability_git_commit, capability_git_tree, capability_approval_digest}` projected from the read receipt. The clock coordinate digest is over `{clock_source_id, clock_source_approval_digest, clock_uncertainty_ms}`. The acquisition-channel coordinate is the closed object `{schema, owner_store_id, authoritative_ref, trusted_channel_id, channel_coordinate_digest}`; the digest domain above covers its JCS bytes without the digest member. The challenge-consumption-store coordinate is the closed object `{schema, single_use_store_id, store_issuer, store_coordinate_digest}`. The consumption-signing-key coordinate is the closed object `{schema, signing_key_id, issuer, authority_credential_digest, public_key_digest, key_coordinate_digest}`. Their approval subjects must equal those exact three coordinate digests; no hash of an identifier, partial tuple, ambient registry lookup, or implementation-selected projection is valid.

Approval artifacts are closed signed objects, not opaque references. Each binds authenticated issuer coordinate, subject digest, purpose, validity interval, non-revocation state, trust-root digest, approved Ed25519 public-key digest, a non-circular attestation-body digest, signature, and artifact digest. An issuer-trust bundle binds the expected issuer, trust root, exact acquisition-capability, clock-source, the three closed coordinates above, issuer-signing-key, consumption-signing-key, and single-use-store approval objects; each approval subject equals its corresponding canonical coordinate digest. It also nests a distinct consumption-signing authority credential carrying canonical base64 for exactly 32 raw Ed25519 public-key bytes. The credential identity equals the consumption-signing-key coordinate's issuer; its credential/key digests equal that coordinate and the signed consumption body.

Before every read, the caller creates a fresh, single-use challenge binding candidate digest, intended action, owner-store ID, authoritative ref, prior/minimum checkpoint, issuance/expiry, and challenge digest. The acquisition capability must echo that exact challenge in its issuer-attested receipt. Reuse across candidate, action, store, checkpoint, or expiry is invalid.

A bounded read receipt binds:

- the complete issuer-trust bundle, approved Ed25519 signing-key coordinate, a closed receipt-attestation-body object, and authenticated issuer attestation over that separately domain-separated body digest (the body excludes both attestation and receipt digests, so no signature/digest cycle exists);
- the exact fresh caller challenge and its intended action;
- caller-pinned acquisition capability ID, Git commit/tree, and closed approval artifact;
- exact owner repository, owner-store, authoritative-ref, and trusted-channel identities;
- authenticated monotonic owner checkpoint and predecessor relation;
- no-follow local capture identity;
- observed commit/tree and exact head/history bytes and digests;
- UTC `capture_started_at` and `capture_finished_at`, exact clock-source approval, and bounded uncertainty;
- owner coordinate and exact captured publication-history byte count;
- descriptor-anchored no-follow capture, closed environment, no-network assertion, and stable final recheck, all mirrored inside the signed attestation body;
- the separate read-receipt digest.

Ed25519 signature inputs are exact: the read attestation signs UTF-8 bytes `rocs-semantic-policy-receipt-signature-v1\0` followed by the raw 32 bytes decoded from the lowercase hexadecimal suffix of `attestation_body_digest`; the consumption receipt signs `rocs-semantic-policy-consumption-signature-v1\0` followed by the raw 32 bytes of its body digest under the exact public-key bytes from the caller-pinned consumption credential. Signing JCS bytes, the ASCII `sha256:...` string, or any other representation is invalid. A digest alone does not authenticate a redated receipt. A verifier accepts only an issuer-attested receipt whose Ed25519 signature verifies under the exact 32-byte public key from the caller-pinned issuer credential and whose public-key digest, trust root, closed approvals, challenge, receipt-attestation digest, channel/store identity, checkpoint, and issuer coordinate exactly equal a separate `semantic-routing-policy-verification-request.v1` supplied by the caller as an independent API input. Values nested in the proof never become caller pins. Recomputing timestamps or receipt bytes without a new trusted signature fails. `capture_finished_at` must be no earlier than `capture_started_at`; challenge expiry, replay, clock rollback, excessive uncertainty, or an untrusted source fails closed.

The single-use challenge store emits a separately Ed25519-authenticated consumption receipt with a closed, separately domain-digested signing body binding issuer, challenge, read attestation, zero prior consumption, one resulting consumption, store, consumed time, the exact consumption-store/signing-key coordinate digests, the consumption-credential digest, and approved public-key digest. The external verification request pins the consumption receipt, issuer trust, all three closed coordinate objects and digests, the full consumption credential, its raw public-key bytes/key digest, and every relevant approval. The verifier obtains no key bytes or coordinate meaning from an ambient registry or caller-substituted unpinned object. Decision 103 defines these shapes, not a live acquisition capability or trust root. Until a later owner task implements and independently verifies the issuer, key distribution, channel, monotonic checkpoint chain, single-use challenge store, and acquisition capability, currentness cannot pass.

## 8. Action-time currentness proof

A currentness proof binds candidate, pass verdict, the complete publication history, owner head, a contiguous authenticated checkpoint chain from the caller's pinned predecessor through the current checkpoint, caller challenge, issuer-trust bundle, read receipt, and authenticated challenge-consumption receipt. The verifier also requires a separate caller-supplied verification request; it is not nested authority. `observed_at` must byte-equal the receipt's `capture_finished_at`; it is not an independently chosen timestamp. It is valid only when:

1. all schemas and all sixty-one digest domains and the acyclic dependency schedule validate;
2. candidate digest equals verdict candidate, envelope/attempt candidate, publication-event candidate, challenge/request candidate, and proof candidate; candidate inventory and semantic-binding objects, receipts, Decision 102 parsed owner/source-owner fields, concept/joint sets, and later selected IDs satisfy Section 4;
3. verdict digest equals the terminal event verdict; verdict candidate/inventory/contamination/custody/preregistration/envelope/protected-access-activation/attempt/receipt fields equal their nested object digests; both preexecution caller-request preimages and their bundle/digests validate through the nested preregistration; the protected-access subject, custodian signature, P3-carried base-history preimage, base/activated/terminal histories, event-capacity reserve, evaluator-operator/reservation equality, U/O seals, signed evaluator challenge/proof/request, authenticated channel and gateway launch receipt, atomic reservation consumption, exact process identity, expiry, sole appended grant event, and mandatory appended revoke/closure validate; the verdict approval subject equals every subject-bound field and verifies under its own domain; and the closed custodian/reviewer approval bodies, signatures, trust roots, keys, subjects, purposes, issuers, validity, and non-revocation equal the external request pins;
4. owner/repository/namespace values equal candidate, every event, history, head, checkpoint, receipt, trust bundle, and proof;
5. candidate owner commit/tree identify C and equal the snapshot from which policy, provenance, every retained named provenance-source byte, and the canonical inventory-source bytes are verified; candidate `ontology_inventory_path` equals nested `inventory_source_path`; nested inventory owner commit/tree identify strict-ancestor I and differ from C; the P3 source path/raw digest/extractor/extracted IDs/snapshot/coordinate digest, candidate snapshot/inventory digests and selectable IDs, and byte-identical canonical I→C inventory source satisfy Sections 2.1 and 4; every declared policy-authority/provenance-source revision is a strict ancestor of C and its named blob is retained digest-equal in C; head/checkpoint/receipt observed commit/tree equal each other and the authenticated authoritative-ref observation;
6. every event and complete history digest verify; history digest equals head, checkpoint, receipt, and proof history values;
7. terminal event sequence/digest equals history terminal and head terminal; current checkpoint commits that head; checkpoint sequence/digest equals receipt and the external verification request and is not below caller minimum;
8. every checkpoint-chain predecessor is contiguous and digest-valid from the external request's caller-pinned prior checkpoint to the current checkpoint, and the authenticated capability proves it read the current owner-store ref rather than caller-supplied old bytes;
9. terminal action is `publish` and no later withdrawal/revocation exists under the authenticated current checkpoint;
10. issuer trust, signing/consumption keys and all approval subjects/purposes/validity/non-revocation, challenge, intended action, receipt-attestation digest, consumption receipt/trust/store/key digests, channel/store identity, and both Ed25519 signatures equal and verify against the external caller verification request; channel, single-use-store, and consumption-signing-key approvals bind the three explicit coordinate-domain digests; the request separately pins those complete owner-acquisition coordinates plus the complete evaluator authenticated-channel coordinate, launch-gateway receipt, and descriptor-handoff receipt, the complete consumption credential/raw key, exact custodian, independent-review, semantic-owner, evaluator-operator, and evaluator launch-gateway authority coordinates, authority-credential objects, approval digests, trust roots, and public keys; every event's publication subject and owner signature verify under those semantic-owner pins;
11. capture identity remained stable through final recheck;
12. proof age is positive, bounded, and measured from issuer-attested `capture_finished_at` against the trusted current clock; uncertainty is within the caller pin;
13. the authenticated consumption receipt proves the challenge was unused, unexpired, and consumed for exactly this receipt/action;
14. the consumer obtains this fresh capture immediately before its separately authorized action.

Clock uncertainty, stale cache, missing capability, owner mismatch, withdrawn/revoked terminal state, or changed snapshot is an error, never abstention.

## 9. Authority non-transfer

- Semantic owner issues candidate approval and publication events.
- DSPx or another named independent custodian issues the sealed evaluation verdict.
- ROCS validates objects and bytes.
- AK links decision/task/evidence identifiers.
- A future consumer owner independently adopts and activates.
- Pi may later attest bounded delivery.

No participant may synthesize another owner's missing fact. Joining valid facts does not transfer issuance authority.

## 10. Resource bounds

Protocol parsers enforce before trusted allocation:

| Resource | Maximum |
|---|---:|
| one non-history JSON object | 1,048,576 bytes |
| one complete publication-history object | 16,777,216 bytes |
| one currentness-proof object (complete history/checkpoint chain exception) | 33,554,432 bytes |
| publication events | 10,000; publish at most 9,999 |
| selectable IDs | 2,000 |
| path bytes | 1,024 |
| string bytes | 65,536 |
| collection items | 50,000 |
| parser depth | 32 |
| participants | 64 |
| candidate contamination coverage rows | 10 |
| downstream execution-contamination attestations | exactly 1 |
| preexecution caller-request preimages | exactly 2 |
| protected-access activations | exactly 1 |
| evaluator execution-start proofs | 0 or 1 for `not_started`; exactly 1 for `interrupted|completed` |
| evaluator launch-gateway receipts | 0 or 1 for `not_started`; exactly 1 for `interrupted|completed` |
| protected descriptor-handoff receipts | 0 for `not_started`; 0 or 1 for `interrupted`; exactly 1 for `completed` |
| protected-access closures | exactly 1 |
| base / activated / terminal access-history events | at most 254 / 255 / 256 |
| attempt process invocations | `not_started=0`; `interrupted|completed=1` |
| completed internal attempt passes | `not_started=0`; `interrupted=0..1 primary`; `completed=2 primary+immediate_repeat` |

The history and currentness-proof objects are the only 1 MiB exceptions. History remains capped at 16 MiB; a proof that nests that history and a bounded checkpoint chain is capped at 32 MiB. Before accepting any publish, the owner store reserves enough event-count and byte capacity for at least one worst-case terminal withdraw/revoke event; otherwise publish fails before mutation. Exhaustion is `resource_exhausted`. Safe errors contain only closed kind, protocol coordinate, and optional bounded numeric limit; they contain no path, query, policy text, exception, environment, or secret.

## 11. Rollback

Before consumer activation, rollback is disablement plus preservation of candidate/verdict/publication history. After a future activation, the consumer owner may return to a separately current prior candidate only with its own accepted rollback plan and independent recovery controller. Withdrawal or revocation never rewrites consumer or owner history.

## 12. Stop conditions

Stop on an unauthenticated executor, missing/late protected-access closure, terminal evaluator grant, exhausted activation/closure history reserve, ownership ambiguity, selectable ID absent from the frozen owner inventory, malformed/noncanonical/empty inventory source, inventory path/raw-digest/extractor/extracted-ID drift, B0 derivation or incomplete deny-surface coverage, missing or conflicting custody policy, participant role conflict, U/O exposure, an extra process invocation/pass/rerun, non-pass publication, mutable history, stale or self-issued currentness, owner-head fork, unbounded capture, network dependence, consumer substitution, provider/model activity, or inability to restore/disable without deleting evidence.
