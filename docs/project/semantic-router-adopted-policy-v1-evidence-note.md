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
8. Digest self-consistency does not authenticate a currentness receipt. A trusted issuer, closed approval artifacts, single-use challenge, authoritative store/channel, and monotonic checkpoint are required.
9. Dataset custody is not a repository name: it requires an owner-issued policy and authenticated, mutually exclusive participant roles.

## B0 exposure

The controller and Decision 103 design authors have confirmed B0 exposure. They may design protocol mechanics and interpret the published aggregate failure, but may not author U/O data or perform blind acceptance adjudication.

Every later participant records `confirmed | possible | disproven` exposure with date and evidence. U/O custodians, authors, annotators, adjudicators, evaluator operator, and independent verdict reviewer must be `disproven` before receiving their roles. A closed manifest denies reuse across policy, D, U, O, evaluator, fixtures, floors, templates, aliases, regressions, and execution coordinates. Any exposure retires the affected acceptance set.

## Evidence classes

| Evidence | What it proves | What it does not prove |
|---|---|---|
| policy/provenance digest | exact bytes | owner approval or quality |
| semantic-owner review | reviewed meaning at a coordinate | publication currentness |
| offline D result | visible development behavior | acceptance |
| sealed U/O verdict | frozen-coordinate acceptance result | publication or activation |
| publication event | owner-issued lifecycle transition | current head unless freshly observed |
| issuer-attested challenged read receipt | authenticated current checkpoint/head under a bounded single-use capture | consumer adoption or future currentness |
| consumer adoption event | consumer intent | Pi delivery or influence |
| Pi receipt | bounded runtime observation | semantic authority or benefit |
| AK linkage | lineage | source-owner fact issuance |

## Publication audit readback

At Decision 103 opening, local ROCS `main` was a strict descendant of the locally cached `origin/main`: `0` commits only on the tracking ref and `218` only on local `main`. Local connectivity verification passed. Direct remote read failed because `192.168.161.10:8929` was unavailable. No fetch or push occurred. This is a local audit, not remote publication proof.

## Unresolved owner actions

- Softwareco ontology owner must accept exact policy source and publication-log paths before implementation.
- DSPx must issue the closed custody policy, principal/role acceptance, and store controls before data creation.
- A trusted acquisition issuer/channel/checkpoint and caller challenge store must be implemented before any live currentness claim.
- An independent recovery owner is required before any later live activation.
- No exact consumer is selected by Decision 103.

These are deliberate later gates, not facts inferred by this packet.
