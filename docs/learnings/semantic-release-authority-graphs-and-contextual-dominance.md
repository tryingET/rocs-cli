---
summary: "Decision 53 learning: authority-bearing protocols need closed proof graphs, contextual owner dominance, and separate historical-integrity/current-authorization predicates."
read_when:
  - "Designing a cross-owner protocol, release process, or adoption gate."
  - "Resolving conflicts between semantic, execution, consumer, evidence, and recovery authorities."
type: "learning"
status: "candidate"
---
# Learning — Closed Authority Graphs and Contextual Dominance

## Context

Decision 53 evolved the semantic supply chain from a plausible release/adoption document into a closed executable authority protocol. The work links:

- the accepted ADR: [`../adr/2026-07-13-semantic-release-and-single-canary-adoption.md`](../adr/2026-07-13-semantic-release-and-single-canary-adoption.md);
- corrected machine revision: [`../project/semantic-release-revision-v13.md`](../project/semantic-release-revision-v13.md);
- final strict synthesis: [`../project/semantic-release-rereview13-final-synthesis.md`](../project/semantic-release-rereview13-final-synthesis.md);
- implementation plan: [`../project/semantic-release-implementation-plan.md`](../project/semantic-release-implementation-plan.md);
- rollout/rollback plan: [`../project/semantic-release-validation-rollout-rollback.md`](../project/semantic-release-validation-rollout-rollback.md).

## Durable pattern

When one operation joins facts from multiple owners, do not seek one globally dominant authority. Use **contextual dominance**:

1. each fact is issued only by its owning surface;
2. deterministic tooling verifies shape, derivation, joins, and currentness without acquiring issuance authority;
3. every authority-bearing rule has a closed proof graph from subject claim to independent owner observation and terminal local pin;
4. historical artifact integrity and current authorization are distinct predicates;
5. task/evidence lineage, semantic meaning, consumer consent, delivery, recovery execution, and empirical influence remain separate even when one operation needs all of them.

For semantic release this means:

- semantic owner dominates meaning, trust, compatibility, lifecycle, approval, and publication;
- ROCS dominates deterministic verification and bounded effects;
- AK dominates task, decision, and evidence lineage;
- consumer owner dominates intent, acceptance, activation, deactivation, and rollback policy;
- Pi dominates only delivery attestations;
- an independently pinned controller executes accepted recovery requests;
- DSPx/Oracle may analyze outcomes but cannot authorize them.

## Anti-patterns discovered

### Self-asserted canonical state

A subject cannot prove its own current authorization by repeating a claimed store head, approval, task state, or activation pointer. Currentness must be compared with an independent owner-store observation bound to a local terminal pin.

### Integrity-authority collapse

A valid digest proves bytes, not current permission. Signed or immutable history can remain authentic after revocation, withdrawal, supersession, or head movement.

### Tool-authority collapse

A compiler or validator may prove deterministic derivation but cannot approve semantic meaning or consumer intent. CI success, wrappers, package versions, vendored presence, and mutable `dist/` are facts or adapters—not adoption authority.

### Lifecycle collapse

`authored`, `released`, `desired`, `adopted`, and `used` are not aliases. Publication does not imply adoption; delivery does not imply use; use does not prove influence.

### Generic rollback ownership

Rollback combines policy selection and technical execution. The affected owner selects an accepted rollback policy; an independently pinned controller executes it. Neither role should silently absorb the other.

### Fixture-to-production inference

Closed schemas and differential fixtures establish declared conformance. They do not prove live capability distribution, authenticated reads, race behavior, crash safety, owner consent, publication, or canary operation.

## Method that worked

The Many-of-the-Greats conflict-resolution pass was useful only when subordinated to strict evidence:

- use competing architectural lenses to expose hidden conflicts;
- select the strongest principle per context rather than averaging authorities;
- translate the selected principle into closed schemas, invariants, exact joins, and adversarial fixtures;
- rerun independent owner, deterministic-tooling, and governance reviews;
- never let the adjudication override an unresolved strict blocker.

This converted abstract tensions—simplicity versus proof completeness, owner autonomy versus end-to-end verification, recovery speed versus separation of powers—into testable contracts.

## Reuse rule

For any new cross-owner authority protocol, require an inventory shaped like:

```text
rule
-> claimed subject
-> owner-issued observation
-> canonical owner head/currentness
-> capability/read receipt
-> immutable local terminal pin
-> exact join and action-time predicate
```

If any authority-bearing edge is caller-issued, generic, self-asserted, unresolved, or merely prose, the operation must fail closed.

## Activation boundary

This learning is candidate guidance, not ontology or runtime policy. Promotion through AK knowledge/KES may make it a reusable precedent, but it must not mutate ROCS contracts, Prompt Vault procedures, ontology semantics, consumer defaults, or production authorization by convenience.
