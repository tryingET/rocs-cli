---
summary: "Decisions 106 and 107 learning: digests and lifecycle outcomes are not semantic operands, and adapters require accepted source facts before mappings."
read_when:
  - "Designing semantic evaluation over digest-bearing evidence."
  - "Proposing an adapter between owner-bounded protocols."
  - "Distinguishing structural conformance, governance outcomes, and domain verdicts."
type: "learning"
status: "candidate"
source_decisions: [106, 107]
---
# Learning — Source Facts Before Semantic Evaluation and Adapters

## Context

Decision 105 accepted exact digest-only execution-custody evidence. Decision 106 then tested whether ROCS could derive a deterministic semantic verdict from that projection. Strict review rejected the direction because the accepted inputs contained no semantic-owner policy, policy-selected subject preimages, typed joins, acquisition authority, verdict vocabulary, precedence, or conformance vectors.

Decision 107 tested whether a non-authoritative adapter could connect such evaluation to the accepted Decision 53 semantic-release and consumer-adoption protocol. Strict review also rejected that direction: Decision 106 exposed no accepted semantic-result interface, and an adapter cannot transform a source fact that does not exist.

The controlling evidence is:

- Decision 106 artifact 874, [`../project/semantic-evaluation-machine-v1-review-synthesis-r2.md`](../project/semantic-evaluation-machine-v1-review-synthesis-r2.md);
- Decision 107 artifact 879, [`../project/semantic-evaluation-decision53-compatibility-v1-review-synthesis-r2.md`](../project/semantic-evaluation-decision53-compatibility-v1-review-synthesis-r2.md);
- the accepted Decision 53 owner-partition learning, [`semantic-release-authority-graphs-and-contextual-dominance.md`](semantic-release-authority-graphs-and-contextual-dominance.md).

Both rejected decisions use final `unblocked/rejected` only to mean linked-task reevaluation completed. Neither accepted architecture, an ADR, implementation, or activation.

## Durable distinctions

Keep these predicates separate:

| Predicate | Maximum truthful claim |
|---|---|
| Digest equality | These exact bytes match an identity. |
| Schema conformance | A value has the declared structural shape. |
| Custody evidence | An accepted owner recorded specified execution or transport facts. |
| Read capability | A named owner permits a named subject to acquire exact bytes under constraints. |
| Semantic policy | A semantic owner defines predicates, subjects, vocabulary, precedence, and scope. |
| Current authorization | Independent owner state says the policy or action remains usable now. |
| Governance outcome | A proposal was accepted, rejected, revised, or superseded. |
| Domain verdict | An accepted policy was evaluated over authorized subjects and produced a typed result. |
| Adapter result | An existing typed source fact was mapped without strengthening its authority. |

None of these implies a later row by itself.

A digest is not a preimage, predicate, read right, owner approval, currentness observation, or semantic verdict. A governance rejection is not a domain-level `not_evaluable` result. Calling an adapter `non-authoritative` limits its maximum claim but does not remove its need for authoritative source inputs.

## Constructibility rule

Before proposing a semantic evaluator, require a closed inventory:

```text
semantic-owner policy and current approval
-> policy-selected subject contract
-> exact subject bytes or accepted owner-local evaluation posture
-> capability/read receipts for every non-public subject
-> typed joins to producer/custody evidence
-> closed verdict and abstention vocabulary
-> positive and negative conformance vectors
-> independent deterministic or owner-bounded verification
```

If any edge is missing, the evaluator is unconstructible. Identity or schema validation may still be useful, but it must retain identity/shape vocabulary and must not be renamed semantic evaluation.

### Private-subject fork

A future decision must explicitly choose one of two authority models:

1. **Capability-bounded ROCS reproduction** — the owner grants ROCS exact policy and subject bytes under reviewable read capabilities; ROCS may then claim deterministic derivation within the accepted contract.
2. **Owner-local semantic evaluation** — protected subjects remain in owner custody; the owner issues a typed result and currentness evidence. ROCS may verify the receipt and closed joins but must not claim independently reproduced semantics unless an accepted proof mechanism establishes that stronger fact.

These models are not interchangeable. The second preserves data locality but carries a different maximum verification claim. Either requires a new decision; neither is retroactive evidence for Decision 106.

## Adapter-ordering rule

Build adapters only in this order:

```text
accepted source decision
-> exact source schema, issuer, vocabulary, currentness, and nonclaims
-> named destination owner and accepted destination predicates
-> closed authority-preserving mapping
-> failure, stale, revoked, malformed, and abstention behavior
-> named consumer need
-> independent conformance vectors
-> adapter decision
```

An adapter may reduce or preserve a source claim. It may not strengthen the claim, supply a missing source value, translate AK lifecycle state into a domain verdict, or issue destination-owner facts.

If the source interface is absent, leave the adapter absent. A permanent placeholder or constant `not_evaluable` runtime usually creates a misleading compatibility surface rather than useful fail-closed behavior.

A custody/wire checker is a distinct capability. It may report exact identity and structural conformance only, and it needs its own consumer, decision, vocabulary, and explicit semantic nonclaims.

## Contextual dominance

When a future path becomes constructible:

- the semantic owner dominates meaning, subject selection, verdict vocabulary, precedence, approval, and currentness;
- the subject owner dominates disclosure and capability grants;
- DSPx dominates only execution effects and custody facts it mediates;
- ROCS dominates deterministic canonicalization, validation, joins, and derivation under accepted contracts;
- Decision 53 owners retain publication, currentness, consumer adoption, activation, and rollback boundaries;
- AK dominates task, decision, artifact, evidence, and lineage state without issuing domain facts;
- adapters preserve typed boundaries and never become shadow authorities.

## Anti-patterns

### Hash-to-semantics promotion

Inferring an unobserved property of a preimage from its digest or treating digest-role labels as semantic predicates.

### Schema-to-acceptance promotion

Treating a structurally valid object as owner-authenticated, current, eligible, compatible, or semantically correct.

### Lifecycle-to-domain promotion

Translating `rejected`, `blocked`, or `unblocked` decision state into a runtime semantic result.

### Placeholder interface capture

Publishing a generic or constant-unavailability interface before the source vocabulary and owner contract exist, then letting downstream coupling make the placeholder permanent.

### Adapter authority laundering

Using a supposedly non-authoritative mapping to issue semantic-owner, publication, currentness, compatibility, consumer, or activation facts.

### Retroactive evidence

Using future owner inputs to rewrite a previously rejected decision. New facts require a new decision and preserve the rejection as historical evidence.

## Operational consequence

Missing owner inputs are a stop condition, not an invitation to implement scaffolding. Continue independent ready work while the semantic path remains absent. Reopen the capability only through a new owner proposal that satisfies the constructibility and ordering rules.

## Activation boundary

This document is candidate KES guidance. Attaching it to Decisions 106 and 107 records learning closure only. It does not create ontology meaning, a Prompt Vault procedure, ROCS runtime policy, semantic-owner approval, read capability, evaluator or adapter implementation, Decision 53 publication/adoption/activation authority, production authorization, or evidence that any live semantic evaluation occurred.
