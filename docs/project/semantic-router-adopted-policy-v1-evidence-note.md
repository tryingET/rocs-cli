---
summary: "Evidence and authority map for Decision 103 adopted routing-policy protocol."
read_when:
  - "Checking the evidence boundary or owner split for Decision 103."
type: "evidence_note"
status: "proposed"
decision_id: 103
---
# Evidence note — adopted semantic-routing policy v1

## Accepted inputs

- Decision 102 ADR: [`../adr/2026-08-01-abstaining-semantic-router-v0.md`](../adr/2026-08-01-abstaining-semantic-router-v0.md).
- Decision 102 validation contract: [`semantic-router-v0-validation-rollout-rollback.md`](semantic-router-v0-validation-rollout-rollback.md).
- Decision 102 KES candidate: [`../learnings/semantic-router-abstention-and-proof-boundaries.md`](../learnings/semantic-router-abstention-and-proof-boundaries.md).
- Decision 53 ADR: [`../adr/2026-07-13-semantic-release-and-single-canary-adoption.md`](../adr/2026-07-13-semantic-release-and-single-canary-adoption.md).
- Decision 53 owner-identity gate: [`semantic-release-owner-identity-gate.md`](semantic-release-owner-identity-gate.md).
- Softwareco ontology owner surface: `/home/tryinget/ai-society/softwareco/ontology`.
- Independent empirical owner candidate: `/home/tryinget/ai-society/softwareco/owned/dspx`.

## Facts established

1. Decision 102 route mechanics are offline, deterministic, abstaining, and digest-addressed, but development-only.
2. B0 validly failed null rejection and is permanently contaminated for future policy and evaluation use.
3. Decision 53 established the reusable state separation `authored → released → desired → adopted → used` and owner-specific authority.
4. Decision 53 live publication/canary gates remain blocked; its exact absent consumer, adapter, canary, and recovery identities cannot be substituted for Decision 103.
5. `softwareco/ontology` owns the Softwareco company overlay. `core/ontology-kernel` owns holding-shared concepts.
6. ROCS may verify owner-issued facts but cannot publish meaning, adopt for a consumer, or activate a runtime.
7. Tracked Softwareco ontology identifiers use canonical `co.software.*` form; lexical prefix never replaces exact frozen-inventory membership.
8. Digest self-consistency does not authenticate a currentness receipt or owner/custodian/reviewer approval. A trusted issuer, separate non-circular authority credentials carrying canonical raw-32-byte Ed25519 keys (including a distinct caller-pinned consumption credential), non-circular signed approval subjects and attestation bodies, separate caller verification request with exact authority/credential/trust/key pins, three closed domain-digested acquisition-channel/single-use-store/consumption-signing-key coordinates, authenticated single-use challenge consumption, and a monotonic checkpoint chain are required. The capture signature must cover descriptor-anchored no-follow capture, closed-environment, no-network, and stable-final-recheck assertions.
9. Dataset custody is not a repository name: it requires an owner-issued policy with exact source/license/consent evidence and complete deletion controls plus authenticated, mutually exclusive participant roles including implementer and two annotators.
10. The canonical B0 preregistration commit is `286773ee6a88b9fd2276f8008898c57ff9a073b9`; a deny-coordinate that does not resolve to this retained commit is invalid.
11. The digest-bound Decision 102 policy/provenance bytes—not a parallel ID list—must prove `softwareco/ontology` ownership and inventory-bounded concept, joint-route, and selected IDs.
12. ADR executability review `dispatch-1785629031503` rejected packet r5 because its candidate-contamination-attempt digest graph was cyclic and its P3 preregistration required a not-yet-frozen P4 candidate plus not-yet-observed P5 verdict values. Revision r6 must preserve that rejection and replace it with an explicit topological digest schedule and executable P3 custody → P4 candidate → P5 preregistration → P6 execution/verdict → P7 publication sequence.
13. R6 precommit review `dispatch-1785629514394` found a residual preregistration-acceptance cycle. R6 therefore replaced the ambiguous acceptance digest with a candidate-free P3 custody-readiness receipt and kept outcome approvals after P6 observation. Final r6 review then found that the new P3 readiness and P5 execution-contamination assertions were unsigned and that the published schedule placed policy/provenance before P3 despite P4 owning those bytes. Revision r7 makes both pre-execution owner facts non-circular signed subjects under independent caller pins and moves policy/provenance production exclusively after verified P3 readiness. R7 precommit phase review then found a reservation-order cycle; r7 resolves it by acquiring the non-executing expiring reservation before envelope construction while withholding every U/O read and process start until the signed attestation, caller pins, preregistration, and exact reservation joins validate.
14. Final r7 review found that the reservation executor was not joined to the frozen evaluator-operator role, the two caller-request preimages became opaque in final verification, and the P3 access-history freeze could not both withhold and later grant evaluator access. Revision r8 binds the reservation executor byte-exactly to the evaluator operator, nests both complete request objects in a downstream verification bundle carried through preregistration/verdict/currentness, and separates P3 base eligibility from one post-validation custodian-signed protected-access activation whose history appends exactly one evaluator grant.
15. Final r8 review found that equality to an evaluator coordinate did not prove the actual process starter possessed that authority key, the base history reserved no mandatory activation/closure capacity, the signed activation omitted the activated-history/time identity, and an expiring grant had no terminal revoke. Revision r9 requires a caller-pinned evaluator challenge and evaluator-signed start proof, caps P3/P5/P6 histories at 254/255/256 events, signs the exact grant history/time, makes access independently expire, and requires a custodian-signed terminal revoke/closure before any verdict.
16. R9 precommit review found that a detached evaluator proof remained raceable as a bearer artifact, its requested observed-start time was temporally impossible, pre-start expiry and interrupted attempts lacked truthful protocol shapes, P3 did not expose its base-history preimage, and late or wrongly signed closure could still reach publication. R9 therefore uses a prospective evaluator authorization over an authenticated channel plus a pinned custodian-gateway receipt for atomic zero-to-one reservation consumption and observed launch, carries the P3 base history, represents no-start/interrupted/completed attempts explicitly, permits nullable no-start closure coordinates, pins the exact closure signer, and makes expired/late closure indeterminate and non-publishable.
17. A second r9 review found the channel binding still opaque, gateway post-spawn signing left a crash gap, protected descriptor opening was unproved, attempt prefix variants were underconstrained, and chronology/resource text conflicted. R9 now defines a closed exporter-based evaluator/gateway channel coordinate, crash-safe signed reservation consumption before spawn, atomic signed first-descriptor handoff before row read, exact no-start/interrupted/completed prefix variants, strict chronology, and conditional attempt limits.
18. Fresh exact-r9 reviews `dispatch-1785647681550`, `dispatch-1785647681551`, and `dispatch-1785647681552` rejected aggregate `41ecfcffe6947cb432e5a6045e07f544dd1bb0c585bdc9051addc5cf0813638e`: normative no-start/interrupted branches contradicted their schema; the published schedule placed channel consumers before the channel and request before its expected subject; verdict/approval branches did not preserve exact prefixes; pre-spawn authorization did not prove timely observed spawn; and transferred descriptors could survive expiry/closure. Revision r10 preserves crash-safe pre-spawn authorization while making the eight truthful prefixes exact end-to-end, orders channel → challenge → unsigned subject → request → signature, binds custodian-observed spawn against every deadline, forbids raw descriptor transfer in favor of per-read gateway-mediated revocable handles, and requires handle closure plus process termination/reaping before verdict.

## B0 exposure

The controller and Decision 103 design authors have confirmed B0 exposure. They may design protocol mechanics and interpret the published aggregate failure, but may not author U/O data or perform blind acceptance adjudication.

Every later participant records `confirmed | possible | disproven` exposure with date and evidence. U/O custodians, authors, annotators, adjudicators, evaluator operator, and independent verdict reviewer must be `disproven` before receiving their roles. A ten-row candidate-contamination manifest denies reuse across policy, D, U, O, evaluator, fixtures, floors, templates, aliases, and regressions without depending on candidate/envelope identity. A separate downstream execution-contamination attestation covers the attempt-envelope coordinate after candidate freeze. Together they cover all eleven surfaces without a digest cycle. Any exposure retires the affected acceptance set.

## Evidence classes

| Evidence | What it proves | What it does not prove |
|---|---|---|
| policy/provenance digest | exact bytes | owner approval or quality |
| semantic-owner review | reviewed meaning at a coordinate | publication currentness |
| offline D result | visible development behavior | acceptance |
| sealed U/O verdict | frozen-coordinate acceptance result | publication or activation |
| publication event | owner-issued lifecycle transition | current head unless freshly observed |
| Ed25519 issuer-attested challenged read plus authenticated consumption receipt | authenticated current checkpoint/head under a bounded single-use capture and separate caller request | consumer adoption or future currentness |
| consumer adoption event | consumer intent | Pi delivery or influence |
| Pi receipt | bounded runtime observation | semantic authority or benefit |
| AK linkage | lineage | source-owner fact issuance |

## Publication audit readback

At Decision 103 opening, local ROCS `main` was a strict descendant of the locally cached `origin/main`: `0` commits only on the tracking ref and `218` only on local `main`. Local connectivity verification passed. Direct remote read failed because `192.168.161.10:8929` was unavailable. No fetch or push occurred. This is a local audit, not remote publication proof.

## Unresolved owner actions

- Softwareco ontology owner must accept exact policy source and publication-log paths before implementation.
- DSPx must issue the closed custody policy, principal/role acceptance, and store controls before data creation.
- A trusted acquisition issuer/key distribution/channel/checkpoint chain, caller verification-request boundary, exact consumption credential/key distribution, and authenticated single-use challenge store must be implemented before any live currentness claim.
- An independent recovery owner is required before any later live activation.
- No exact consumer is selected by Decision 103.

These are deliberate later gates, not facts inferred by this packet.
