---
summary: "Controlling strict-convergence synthesis for Decision 102 semantic-router-v0."
read_when:
  - "Determining Decision 102's legal next move."
type: "review_synthesis"
status: "accepted"
review_outcome: "ready_for_adr"
---
# Semantic router v0 review synthesis r1

## Inputs

- exact final packet commit `52454f5dd86582290db642b73acc6c5cab8e9e1d`;
- packet aggregate `417ee5c7148573f80b841a0ae0d22f12ab8152c020c765f9a2a32976a001ba53`;
- review-set plan `docs/project/semantic-router-v0-review-set-plan.md`;
- final review memo `docs/project/semantic-router-v0-review-memo-r1.md`;
- Lane A `dispatch-1785603595275` — accept;
- Lane B `dispatch-1785603595275-1` — accept;
- Lane C `dispatch-1785603595276` — accept.

## Controlling synthesis

The B0 failure does not justify score tuning or replacing lexical discovery with another similarity engine. It justifies separating policy admission and adjudication from candidate evidence.

The accepted architecture is additive:

1. preserve `semantic-discovery-result.v0` and `rocs-lexical-v0` as protected deterministic evidence;
2. add separate route request, policy, provenance, effective-execution, result, capability, error, and digest contracts;
3. evaluate exact owner-provenanced symbolic clauses;
4. select one concept or an explicit joint route only from positive policy support;
5. abstain without selection on absent support, conflict, or unresolved multiplicity;
6. nest and digest the complete unchanged lexical result;
7. authorize only ROCS development mechanics and synthetic fixtures.

Authority remains explicit:

- the protocol cannot infer synthetic meaning;
- v0 results are development evidence only;
- Decision 102 does not authorize non-synthetic policy execution, publication, empirical U/O work, consumer shadowing, Pi integration, or prompt projection;
- every later effect requires a separate owner-reviewed protocol, task, and gate.

The validation design prevents the failed B0 set from becoming a hidden tuning set and prevents both route-everything and abstain-everything strategies from satisfying future acceptance.

## Resolved tensions

- **ROCS versus ontology authority:** ROCS owns mechanics; semantic owners own meaning and publication.
- **Lexical evidence versus routing judgment:** the lexical result is nested evidence, never admission authority.
- **Synthetic process scope versus runtime semantics:** synthetic-only is an AK/Decision authorization boundary, not a schema claim.
- **Multi-concept inference versus governed meaning:** only explicit joint routes may select multiple concepts.
- **Development implementation versus activation:** accepted ADR authority stops at synthetic ROCS development.

## Remaining work deliberately deferred

- adopted-policy/publication/currentness protocol;
- non-synthetic ontology policy;
- D/U/O datasets and one-shot evaluation;
- semantic-owner publication;
- consumer shadow;
- Pi prompt projection;
- provider/model benefit claims.

These are not implementation gaps inside the bounded v0 decision. They are separately owned future decisions.

## Legal next move

`ready_for_adr`

Record an ADR that authorizes only the bounded ROCS development implementation defined by the exact final packet. Implementation must not begin before that ADR is accepted and Decision 102 advances lawfully.
