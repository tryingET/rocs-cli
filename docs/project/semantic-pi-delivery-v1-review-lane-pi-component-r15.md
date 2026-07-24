---
summary: "Pi component-owner exact-byte review of semantic Pi delivery v1 RFC r15."
read_when: ["Tracing Decision 71 r15 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# Pi component-owner lane — r15

Reviewed commit `9aaaecd050261ba2cebb08d0e0469f89f46bfdbf`, aggregate `e6719438d2922f9c281f4fb12efeca310dfaab21ed2937034a27e4c639ff60a6`. `dispatch-1784866291336` independently reproduced the aggregate.

## Findings

Blockers:

1. Package and issuer provenance are not closed: the fixed identity omits canonical package identity and production lacks a current component-owner package acquisition/release fact, allowing coherent package substitution.
2. Contributor registration is not host-derived from the exact manifest-confined loaded entry; another extension could self-assert the canonical repository/component tuple and receive a genuine witness.

Material improvement:

- Resolve the contradiction between immutable v0 history/runtime wording and required removal of active `isolatedDogfood` constructor authority. Historical artifacts remain immutable, but active successor runtime must permanently reject every non-host-witness delivered path.

Non-blocking confirmations: `pi-ontology-workflows` is the correct conceptual issuer; no `pi-adapter` alias or extraction is lawful; the paired API is compact; integration evidence remains distinct from delivery.

## Outcome and legal next move

`revise_rfc`. Close package provenance, host-derived registrar binding, exact cross-object equalities, and active constructor-authority removal; then freeze and rerun all five lanes.

This lane grants no implementation, dogfood, publication, adoption, activation, live, ADR-acceptance, or provider-dispatch authority.
