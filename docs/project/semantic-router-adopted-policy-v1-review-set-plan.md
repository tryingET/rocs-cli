---
summary: "Strict three-lane review plan for Decision 103 adopted routing-policy protocol."
read_when:
  - "Opening or synthesizing Decision 103 review."
type: "review_set_plan"
status: "proposed"
decision_id: 103
---
# Review-set plan — adopted semantic-routing policy v1

## Reviewed packet

Review exactly the paths listed and hashed by [`semantic-router-adopted-policy-v1/packet-manifest.json`](semantic-router-adopted-policy-v1/packet-manifest.json). Any byte change retires all reviews against the prior aggregate.

## Closure mode

Decision 103 uses `multi_lane_requires_synthesis`. All three lanes are mandatory. Each lane returns `accept | revise | reject` with evidence. A designated synthesis cites all final lane reviews and alone may recommend `ready_for_adr`.

## Lane A — semantic authority and publication

Reviewer must be independent of packet authorship and assess:

- `softwareco/ontology` is the only first-policy semantic owner;
- P3 semantic inventory authority has complete preimages: the signed subject requires and nests the I-bound `concept_inventory` plus its equal digest; the independent caller request requires and nests a byte-identical `expected_concept_inventory` plus a digest equal to the subject field, receipt-nested subject field, and object; explicit local I repository/source bytes prove path, raw digest, extractor, commit/tree, extracted IDs, snapshot, and coordinate before D disclosure;
- canonical `co.software.*` identifiers are accepted only when emitted from that exact P3 I-bound source by the fixed extractor; the source is closed JCS-canonical UTF-8 I-JSON with only the fixed schema and a nonempty unique UTF-8-byte-sorted ID array, and floats, duplicate keys/IDs, extra keys, noncanonical bytes/order, core IDs, and empty inventory reject; candidate snapshot C is a strict descendant with a byte-identical canonical inventory source and unequal candidate/nested-inventory commit/tree pairs; and the parsed digest-bound Decision 102 policy/provenance manifest and every provenance-record source owner, concept IDs, joint-route IDs, and later selected IDs all remain bound to it; prefix inference and core relabeling fail;
- core-owned meaning is not copied, relabeled, or selected by convenience;
- owner publication, withdrawal, and revocation remain owner-issued;
- ROCS and AK do not acquire semantic authority;
- publication and consumer adoption remain separate;
- later owner paths and approval remain explicit gates.

Reject on ambiguous namespace ownership, mutable-latest semantics, inferred approval, or publication without withdrawal/currentness handling.

## Lane B — protocol, security, and rollback

Reviewer assesses:

- closed JSON shapes, canonical I-JSON and digest domains, including raw SHA-256 (not a domain digest) over exact canonical inventory source bytes;
- append-only event chain, authenticated monotonic checkpoint, authoritative ref, and reserved terminal-event capacity;
- no-follow, local-only, bounded acquisition expectations with closed issuer/approval/channel/store trust;
- acquisition channel, single-use challenge store, and consumption signing key use three closed canonical coordinate objects and separate digest domains; every approval subject equals its complete coordinate digest rather than an identifier or implementation-selected projection;
- fresh single-use caller challenge/action binding, separate caller verification request, approved Ed25519 key/signature with non-circular attestation body, and authenticated challenge-consumption body/receipt whose issuer trust, complete credential with raw public-key bytes, store, key, and digest are externally pinned without an ambient registry;
- unidirectional checkpoint→head commitment plus a contiguous monotonic checkpoint chain from the caller pin;
- explicit phase-aligned topological digest order and exact equality joins across P3 canonical inventory source commit/tree I plus signed subject inventory object/equal digest and caller-pinned byte-identical expected object/equal digest, all validated from explicit local I repo/source bytes, plus readiness/base access, P4 policy/provenance from strict-ancestor revisions and descendant snapshot C retaining every exact named source byte plus the byte-identical canonical inventory source at the equal candidate/nested path with C != I, candidate contamination, candidate, reservation/exact evaluator operator, envelope, signed downstream execution-contamination attestation, both complete independent verification-request preimages and their bundle, preregistration, signed protected-access activation/one time-equal appended grant with event reserve, caller-pinned closed evaluator+gateway channel/exporter, challenge, unsigned prospective subject, verification request, evaluator signature, crash-safe gateway-signed zero-to-one reservation consumption before spawn, atomic signed gateway-mediated revocable-handle handoff, one of eight exact complete/interrupted/no-start prefixes, mandatory custodian-observed timely spawn/process reaping/handle closure plus signed terminal revoke, post-execution verdict approvals/verdict, publication approvals/event, history, head, checkpoint, receipt, commit/tree, and proof; no object binds a digest produced later in that order;
- the external request pins exact custodian, reviewer, and semantic-owner authority coordinates, separate non-circular authority credentials, signed approval digests, trust roots, and canonical raw-32-byte Ed25519 public keys; repository strings or self-digests cannot issue authority;
- the signed receipt body authenticates descriptor-anchored no-follow capture, closed-environment, no-network, and stable-final-recheck guarantees as well as identity, challenge, checkpoint, and time;
- stale H1 replay after H2, forked, absent, withdrawn, revoked, or mismatched heads fail closed;
- rollback disables invocation or returns to a separately current prior release without rewriting history;
- no network, live signing/key provisioning, provider/model, or live capability is implied.

Reject on digest ambiguity/cycle, inventory self-hash, candidate/inventory coordinate equality, non-ancestor source authority, missing subject/request inventory preimage, inventory object/digest inequality, inventory source path/raw-digest/extractor/I-coordinate/extracted-ID mismatch or absent explicit local I repo/source bytes, malformed or noncanonical source, missing or changed descendant source bytes, repository-string or opaque-ref authority, self-issued/redatable/replayable currentness, invalid/unapproved signing key, proof-nested values masquerading as caller pins, missing challenge consumption, rollbackable/broken checkpoint chain, non-atomic head semantics, incoherent proof/history size bounds, exhausted withdraw/revoke reserve, unsafe error disclosure, or rollback that erases history.

## Lane C — empirical custody and falsification

Reviewer must be independent of policy authorship and assess:

- closed canonical B0 deny coordinates and complete no-reuse coverage: an exact ten-surface pre-attempt candidate-manifest bijection plus one downstream execution-contamination attestation, each source digest joined to its actual artifact coordinate without a candidate/envelope back edge;
- P3 inventory authority is constructible before D disclosure: the subject and independent request nest byte-identical complete inventory objects and equal object/subject/request/receipt-nested-subject digests, validated from explicit local I repository/source bytes; nested inventory at I binds exact canonical source path/raw SHA-256/fixed extractor/extracted IDs/snapshot/coordinate digest; P4 candidate path equals nested source path, C bytes equal I bytes, and extracted/nested/selectable IDs are identical;
- owner-issued custody policy established before data creation, including exact source/license/consent evidence, complete prohibited-content set, privacy/ACL/retention/backups/all deletion triggers/incidents;
- exact canonical role cardinalities, twelve pairwise-distinct authenticated principals, nested exposure evidence and append-only base/activated access histories, custodian/reviewer distinction, implementer binding, exact reservation-executor equality to the frozen evaluator operator, and mechanical D/U/O-author/annotator/adjudicator/evaluator separation;
- exact unique B0 surface bijection and canonical commit coordinates;
- executable phase timing and authority: P3 validates explicit local I repository/source bytes, freezes the canonical owner-native inventory source at real commit/tree I, and signs a subject nesting its complete object/equal digest while the caller request nests the byte-identical expected object/equal digest, seals D/U/O and roles before D disclosure, freezes only a base access history with no evaluator sealed-row/process grant, and emits a candidate-free custodian-signed readiness subject/receipt under independent caller pins; P4 alone discloses D, creates Decision 102 policy/provenance from declared strict-ancestor revisions, and freezes strict-descendant C containing exact policy/provenance bytes, digest-equal copies of every named provenance source byte, and the byte-identical I inventory source at the candidate path equal to the nested source path; candidate owner C and nested inventory owner I coordinates differ while candidate inventory and selectable values equal P3 and the extracted IDs; the same object/digest remains reachable through preregistration readiness, verdict, and currentness; P5 first acquires a non-executing expiring reservation whose executor equals the frozen evaluator operator, then signs execution contamination, nests both complete caller-request preimages in a closed bundle, preregisters the exact candidate/reservation/envelope without cyclic or post-execution fields, and only after full validation obtains a custodian-signed protected-access activation whose history is exactly the P3 base plus one evaluator grant; the P3/P5 subjects, credentials, approval issuers, request preimages, custody policy, preregistration coordinates, activation, and exact frozen custodian/reviewer/evaluator role coordinates must be byte-equal through execution, the post-execution verdict subject, credentials, approval issuers, verdict fields, and final proof; P6 constructs channel → challenge → unsigned subject → request → signature, verifies evaluator key possession and same-channel gateway identity/exporter, crash-safely consumes the reservation before spawn, permits only gateway-mediated revocable handles before protected reads, truthfully records one of eight complete/interrupted/no-start prefix branches, verifies custodian-observed spawn met every deadline, terminates/reaps every started process, closes every handed-off handle, obtains a mandatory custodian-signed terminal revoke/closure before expiry, and only then creates/signs the verdict subject; P7 alone publishes;
- inspectable preregistered attempt envelope with closed environment and nested reservation/rollback, anti-overlap, one process invocation with two fixed internal passes, and outcome precedence;
- policy quality gates prevent both false routing and trivial abstention;
- raw protected rows remain outside ROCS, Git, and AK;
- failed or indeterminate evidence is retained without mechanical retry.

Reject on reusable or incompletely covered B0 coordinates, opaque custody, role conflict, exposed acceptance data, post-observation floor changes, extra invocation/pass/retry/rerun, or execution without sealed identities.

## Synthesis checklist

Synthesis must state:

1. packet aggregate and manifest SHA-256;
2. exact review dispatch/session identifiers;
3. every lane outcome and unresolved minority finding;
4. whether protocol design may proceed to ADR;
5. that no real policy, evaluation, publication, consumer, or Pi action is authorized;
6. whether a superseding packet revision is required.

## Independence disclosure

Every reviewer records repository paths read, B0 exposure, authorship conflicts, and whether they observed any proposed D/U/O content. A reviewer with U/O access cannot review policy authorship; a policy author cannot review U/O custody or verdict correctness.
