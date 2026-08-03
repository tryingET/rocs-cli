---
summary: "Decision 107 RFC requesting rejection because no accepted semantic result exists for a Decision 53 adapter."
read_when:
  - "Reviewing Decision 107 or any proposed semantic-evaluation compatibility adapter."
type: "rfc"
status: "in_review"
decision_id: 107
rfc_revision: "semantic-evaluation-decision53-compatibility-v1-r1"
---
# RFC — Decision 107 semantic-evaluation compatibility boundary r1

## Decision requested

Return **`reject_current_direction`** for a non-authoritative semantic-evaluation adapter to Decision 53 over the currently accepted inputs.

Decision 106 rejected the only proposed upstream semantic machine and exposes no accepted result interface. An adapter cannot transform a result that does not exist. Creating a placeholder interface, permanent `not_evaluable` result, or semantic-looking status from Decision 105 identity/schema facts would contradict the accepted authority boundary.

This RFC requests explicit rejection closure, not an ADR. Future work must use a new decision after a semantic owner supplies and obtains acceptance for a real semantic-evaluation contract.

## Reviewed prerequisites

Decision 107 r1 reviews:

- Decision 53 accepted semantic release and consumer adoption protocol;
- Decision 53 legal closure artifact 447 and accepted ADR;
- Decision 105's exact accepted digest-only projection and schema identities;
- Decision 106's controlling `reject_current_direction` synthesis, artifact 874;
- Decision 106 frozen commit `fe6f71170db43c5d3015a653d192bdb72363434d`, tree `aa123aa67ed523e40ec7e108e96ebf7114072e29`, and aggregate `41c2cc2f311828927e4fcc15914b48e70ab16a78aafbee525c575692bf2c8944`;
- task 4626 as documentation-only Decision 107 adjudication authority.

No prerequisite supplies an accepted semantic-evaluation result.

## Fixed authority partition

1. The semantic owner defines semantic policy, subject selection, verdict vocabulary, precedence, approval, and currentness.
2. ROCS may deterministically verify or derive results only under accepted owner contracts and authorized subjects. It may not invent the missing source fact.
3. Decision 53 remains the owner protocol for semantic release publication/currentness, consumer adoption, activation, and rollback boundaries.
4. A non-authoritative adapter may translate accepted typed facts but may not issue or strengthen semantic, publication, currentness, compatibility, adoption, or activation authority.
5. AK records decision, task, evidence, and artifact lineage. AK state does not create domain facts.
6. DSPx may attest mediated execution and analyze outcomes but does not issue semantic meaning or Decision 53 adoption authority.

## Adapter constructibility test

A Decision 53 semantic-evaluation adapter is constructible only if all of the following already exist:

1. **Accepted source interface** — exact semantic-evaluation result schema, issuer, identity, verdict vocabulary, nonclaims, and accepted decision/ADR.
2. **Authority/currentness contract** — owner identity, approval, revocation/currentness observations, action-time predicate, and independent local pin.
3. **Typed subject joins** — exact relation among policy, evaluated subjects, producer evidence, and semantic result.
4. **Decision 53 mapping** — closed mapping from source outcomes to existing Decision 53 predicates that neither weakens nor issues owner facts.
5. **Failure and abstention semantics** — explicit handling for unavailable, indeterminate, stale, revoked, malformed, and out-of-scope inputs without relabeling them as compatibility verdicts.
6. **Independent conformance** — positive and negative vectors reproducible by independent implementations.
7. **Consumer need** — a named owner request for the mapping rather than speculative interface growth.

Current inputs satisfy none of items 1–7. Decision 106's rejection is not an accepted source interface.

## Exact insufficiency findings

### No source value

Decision 106 returns an architectural lifecycle outcome, not a runtime semantic-evaluation result. `reject_current_direction` says the proposed machine is unconstructible. It is not a semantic verdict about any Decision 105 subject.

### Structural facts are not semantic facts

Exact-byte equality and schema conformance remain useful custody facts. They cannot become `compatible`, `incompatible`, `current`, `adoptable`, or any other Decision 53 predicate without accepted semantic-owner meaning and subjects.

### Constant unavailability is not an interface

A permanent `not_evaluable` runtime or adapter would expose no accepted semantic capability, create misleading integration surface, and invite downstream code to treat a missing prerequisite as a stable result contract. Decision 106 expressly rejected that direction.

### Non-authoritative does not mean authority-free

Even a non-authoritative adapter must have authoritative source facts and a reviewed mapping. The adjective limits its maximum claim; it does not permit it to manufacture inputs or Decision 53 conclusions.

### Future evidence is not retroactive

A future semantic-owner proposal may establish a new accepted machine or owner-local result contract. That evidence cannot reopen or silently revise Decisions 106 or 107. A later adapter needs a fresh decision citing both rejections.

## Considered directions

### A. Adapt Decision 105 projection fields directly

Rejected. The projection is digest-only, lacks semantic operands and policy, and carries explicit semantic and authority nonclaims.

### B. Adapt Decision 106's rejection as `not_evaluable`

Rejected. Decision 106's outcome is architecture governance, not a domain result. Translating it would collapse lifecycle state into semantic output.

### C. Define a generic adapter contract now and fill the source later

Rejected. The absent source vocabulary, owner, currentness, and mapping determine the adapter's type. Designing around placeholders would freeze speculative authority assumptions.

### D. Create an exact-byte custody/wire-conformance adapter

Rejected as Decision 107. Such a checker could lawfully report only identity and shape facts, but it is a different capability. It requires a concrete consumer, explicit nonclaims, and a new owner-scoped decision.

### E. Reject the current direction and wait for an accepted source interface

Selected. This preserves every accepted Decision 53 and Decision 105 fact while keeping Decision 106's rejection truthful.

## Review outcome and legal next move

The requested controlling outcome is:

```text
reject_current_direction
```

If strict review agrees:

1. preserve the exact r1 packet and all lane results as immutable rejection evidence;
2. record no Decision 107 ADR;
3. advance Decision 107 from `review_pending` to `decision_pending` without an outcome;
4. advance to `tasks_reevaluation_pending` with `outcome=rejected` and the controlling synthesis as evidence;
5. reevaluate task 4626 as `still_valid`, record its required evidence, and complete it as successful adjudication;
6. advance Decision 107 to `unblocked`, retaining `outcome=rejected` and null ADR;
7. leave Decisions 53, 105, and 106 unchanged.

For this rejected decision, final `unblocked/rejected` means linked-task reevaluation is complete. It grants no accepted architecture or execution authority.

If any lane identifies an already accepted source interface or a material packet defect, it must return `revise_rfc`. `ready_for_adr` is lawful only if all constructibility inputs already exist and the mapping is proven authority-preserving.

## Future reopening boundary

A future adapter proposal requires:

1. a new accepted semantic-owner evaluation decision and exact source interface;
2. explicit subject custody/acquisition posture;
3. closed currentness and authority proof graph;
4. a Decision 53 owner mapping and named consumer;
5. independent conformance vectors;
6. a new decision and task citing Decisions 106 and 107 as non-retroactive rejection history.

## Non-authorization

This RFC authorizes no code, machine schema, fixtures, ADR, ontology or DSPx mutation, data acquisition, provider/model/network use, publication, adoption, activation, dogfood, production, or push.
