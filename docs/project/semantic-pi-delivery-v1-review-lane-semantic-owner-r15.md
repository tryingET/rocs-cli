---
summary: "Semantic-owner exact-byte review of semantic Pi delivery v1 RFC r15."
read_when: ["Tracing Decision 71 r15 review findings."]
type: "review_lane"
status: "complete"
review_outcome: "revise_rfc"
---
# Semantic-owner lane — r15

Reviewed commit `9aaaecd050261ba2cebb08d0e0469f89f46bfdbf`, aggregate `e6719438d2922f9c281f4fb12efeca310dfaab21ed2937034a27e4c639ff60a6`. `dispatch-1784866291337-1` independently reproduced the aggregate.

## Findings

Blocker:

- The future host-attestation owner appointment, independence/disjointness, revocation, and `self_certification` rules are not closed. A host/component-controlled verifier could satisfy the generic shape and acquire a new trust edge without preserving semantic-owner authority.

Material improvement:

- Define `use_observed` precisely as provider/model use or rename it; host prompt application must not conflict with an ambiguous false value.

Non-blocking confirmations: the surrounding Decision 53 graph is intended to remain byte-equal except for the Pi seam; fixtures and integration proofs acquire no meaning/publication authority; missing consumer, consent, named canary, recovery, live-acquisition, and host-attestation facts remain live blockers.

## Outcome and legal next move

`revise_rfc`. Close attestation-owner appointment/independence/revocation/self-certification and exact use semantics, then freeze and rerun every lane.

This lane grants no implementation, dogfood, publication, adoption, activation, live, production, synthesis, or ADR-drafting authority.
