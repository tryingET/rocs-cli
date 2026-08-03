---
summary: "Decision 106 RFC rejecting semantic-verdict derivation from the digest-only Decision 105 projection."
read_when:
  - "Reviewing the Decision 106 ROCS evaluation boundary."
type: "rfc"
status: "in_review"
decision_id: 106
rfc_revision: "semantic-evaluation-machine-v1-r1"
---
# RFC — Decision 106 deterministic semantic-evaluation boundary r1

## Decision requested

Return **`reject_current_direction`** for a Decision 106 semantic-evaluation machine over the currently accepted Decision 105 projection interface.

The exact producer fixture is accepted and structurally verifiable, but it is intentionally digest-only and non-semantic. No semantic-owner policy bytes, subject preimages, typed preimage contract, or acquisition authority exist. Calling projection identity or schema conformance a semantic verdict would be an authority and evidence error.

This RFC requests an explicit terminal rejection rather than an ADR for a fake machine. A future semantic owner may initiate a new decision after supplying independently reviewable policy meaning and authorized subject bytes. That future work must not reopen task `4618` or silently revise this rejection into implementation authority.

## Inputs reviewed

Decision 106 r1 reviews exactly these prerequisite identities:

- Decision 104 accepted owner partition, AK decision `104`, accepted ADR Git object `e319240d7de8d43f234c53558977248050507056`;
- Decision 105 accepted projection-byte gate, task `4614`;
- DSPx acceptance commit `1dfbfa138dffee810896d939e8344ae8feb00537`, tree `b7add87a3e9e437b6a69c937ce996a22146cf76e`;
- exact projection: `1810` bytes, SHA-256 `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206`;
- exact schema: `8227` bytes, SHA-256 `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532`.

The producer-byte gate authorizes no ROCS consumption by itself. Task `4618` is the separate ROCS-owner decision-support authorization. The Decision 105 lifecycle is not represented here as fully closed; only its exact accepted implementation and byte gate are used.

## Fixed authority partition

1. The semantic owner exclusively defines policy meaning, policy identity, subject selection, verdict vocabulary, and semantic precedence.
2. DSPx attests only execution effects it mediates and the exact digest-only projection it accepted.
3. ROCS may canonicalize accepted contract inputs, validate evidence, and execute deterministic derivation under semantic-owner-defined meaning. ROCS may not invent missing meaning or evidence.
4. Decision 53 remains the sole publication/currentness/adoption/rollback owner.
5. AK records task, decision, artifact, and evidence lineage; AK state does not create domain authority.

## Constructibility test

A deterministic semantic evaluator is constructible only if all of the following exact inputs exist:

1. **Producer envelope** — authenticated accepted-producer identity, exact projection bytes, projection-schema identity, terminal eligibility evidence, and typed digest roles.
2. **Policy envelope** — semantic-owner identity, policy ID/revision/digest, exact canonical policy bytes, scope, closed predicates, verdict vocabulary, precedence, and owner approval/currentness posture.
3. **Subject envelope** — every exact preimage selected by the policy, its schema/canonicalization, typed digest domain, and a byte-for-byte join to the producer projection.
4. **Acquisition envelope** — owner-granted read authority and receipt for each non-public preimage; a digest or local path is not a read right.
5. **Conformance vectors** — complete positive/negative vectors generated from the accepted producer, policy, and subject contracts and reproducible by independent implementations.

The current interface satisfies none of items 2–5 and satisfies item 1 only for one exact synthetic fixture by whole-object hash. Therefore no semantic predicate can be executed.

## Exact insufficiency findings

### Digest-only subject

The projection carries opaque digests for the evaluation request, normalized input, return/failure evidence, candidate, receipt, manifest, and trace. It contains no corresponding preimages. SHA-256 is not reversible, and equality to a digest cannot establish an unobserved property of its preimage.

`input_coordinate.disclosure_posture="digest_only_no_raw_access_right"` explicitly denies any implied access right. ROCS cannot obtain private bytes merely because their digest appears in a projection.

### No semantic policy

No accepted input names the semantic owner, policy bytes, policy scope, predicate set, verdict meanings, or precedence. ROCS defining those values would collapse deterministic execution into unauthorized policy authorship.

### Explicit non-authority

The projection fixes `semantic_meaning=false` and `deterministic_verdict=false`, along with false publication, currentness, promotion, governance, AK-mutation, external-authority, and executed-identity claims. Those are mandatory nonclaims, not dormant capabilities.

### Structural substitution

The JSON Schema accepts the closed projection shape; it does not authenticate Decision 105 owner acceptance or eligibility. Arbitrary lowercase 64-hex values can occupy role-distinct digest fields while remaining schema-valid. Schema success is therefore `projection_shape_conformant`, never `producer_accepted`, `eligible`, or a semantic pass.

### Eligibility not generically exposed

Decision 105 eligibility depends on an atomic terminal `closed` outcome with reason `observed_return|observed_failure`. The generic projection omits the terminal state/reason preimages and owner-authenticated seal. The one fixture is eligible only because task `4614` accepted its exact whole bytes and external record. That cannot be generalized by inference.

### Replay is not reproduction

The schema can enforce only original/replay null structure. It does not authenticate a replay source receipt or prove equivalent policy, input, candidate, or effects. A replay cannot rehabilitate an indeterminate original or become semantic truth by lineage syntax.

## Considered directions

### A. Derive a verdict from projection fields

Rejected. The projection contains no semantic operands or policy. `outcome_kind="return"` means only that DSPx observed a direct return; it is not a semantic pass.

### B. Rename structural conformance as semantic evaluation

Rejected. An exact-byte/schema checker can be useful, but it yields identity and shape facts only. Labeling that result a semantic verdict launders authority.

### C. Let ROCS define a generic predicate AST and infer subjects

Rejected. This invents semantic-owner meaning and subject selection. It also cannot acquire the missing preimages or prove typed digest domains.

### D. Accept a permanent `not_evaluable` machine

Rejected as a Decision 106 semantic machine. A constant failure classifier would be deterministic but would expose no accepted evaluation interface for Decision 107 and would create misleading implementation surface. The review artifacts themselves can record the missing prerequisites without introducing a runtime.

### E. Reject the current direction and require a fresh owner proposal

Selected. It is the smallest truthful result. It preserves the accepted producer evidence while preventing a structurally valid digest bundle from being promoted into semantic truth.

## Review outcome and legal next move

The requested controlling outcome is:

```text
reject_current_direction
```

If strict review agrees, the legal next move is:

1. preserve this RFC and all lane results as immutable rejection evidence;
2. record no Decision 106 ADR;
3. transition Decision 106 to terminal `superseded` with outcome `rejected` and this controlling synthesis as evidence;
4. complete task `4618` as reviewed owner-boundary adjudication;
5. keep Decision 107 blocked because Decision 106 exposes no accepted output interface.

If any lane finds a constructible existing input or a material wording defect, it must return `revise_rfc` rather than forcing rejection or ADR readiness. `ready_for_adr` is lawful only if exact existing inputs support a real semantic machine; this RFC identifies none.

## Future reopening boundary

A future proposal must use a new decision and task after the semantic owner provides exact policy and authorized subject contracts. It must cite this rejection, preserve Decision 105's nonclaims, and rerun strict producer/semantic/ROCS/governance review. It cannot treat future owner inputs as retroactive evidence for Decision 106 r1.

## Non-authorization

This RFC authorizes no code, machine JSON, vectors, ontology mutation, DSPx mutation, Decision 107 adapter, provider/model/network use, data acquisition, dogfood, publication, adoption, activation, or production. No ADR is requested for the rejected direction.
