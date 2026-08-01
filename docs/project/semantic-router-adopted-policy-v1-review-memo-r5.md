---
summary: "Decision 103 strict three-lane review memo for adopted semantic-routing policy v1 packet revision r5."
read_when:
  - "Checking Decision 103 pre-ADR review closure."
type: "review_memo"
status: "accepted"
decision_id: 103
review_outcome: "ready_for_adr"
---
# Decision 103 review memo — adopted semantic-routing policy v1 r5

## Reviewed identity

- packet commit: `415e73d2f4128041911a76414a4d407ad20e0c31`
- packet tree: `01b6200b1ef6533b84dd93df81f385e4d8454f15`
- packet aggregate: `198b0203511650abd72f33962096f9b5004932de5163804849b60a057c814f0b`
- packet-manifest SHA-256: `22beb1a62e625e02ef1b98da62b871782b8585c4cc47a1faf45feeb2805981df`

Any packet byte change retires this review.

## Final lane outcomes

| Lane | Reviewer lineage | Outcome |
|---|---|---|
| semantic authority and publication boundary | `dispatch-1785623427853` | accept |
| protocol, cryptography, currentness, and resource safety | `dispatch-1785623427853-1` | accept |
| empirical independence, custody, contamination, and one-shot evaluation | `dispatch-1785623427854` | accept |

All final reviewers inspected revision r5. Their acceptance is static protocol review only; it does not establish live issuers, keys, stores, policy, datasets, evaluation, publication, consumer consent, Pi behavior, provider/model delivery, or automatic preflight.

## Rejected revisions retained

Strict review rejected r1 through r4 before convergence. Corrected blockers included:

- canonical `co.software.*` owner inventory and executable-policy membership;
- exact Decision 98 B0 deny coordinates and closed contamination coverage;
- role independence, custody policy, data-source authority, and one immutable attempt with two internal passes;
- authenticated non-redatable currentness, monotonic anti-rollback checkpoints, explicit graph joins, and coherent resource reserves;
- acyclic verdict/publication approval subjects and externally pinned authority credentials;
- a caller-pinned consumption credential plus canonical acquisition-channel, challenge-store, and signing-key coordinate domains.

Rejected packet aggregates remain historical evidence and convey no approval.

## Boundary conclusion

The final packet keeps authority separate:

- `softwareco/ontology` owns Softwareco meaning, policy clauses, publication, withdrawal, and revocation;
- ROCS verifies deterministic protocol objects but cannot issue semantic authority;
- a future accepted DSPx/custodian owner controls sealed U/O and verdict execution;
- AK links decisions, tasks, and evidence but stores neither policy nor protected U/O bytes;
- a future exact consumer owns adoption, suppression, activation, and rollback;
- Pi/runtime delivery and provider/model evidence require later explicit decisions.

Decision 98 B0 remains frozen failed evidence and is prohibited as policy, data, evaluator, regression, floor, or execution input.

## Outcome

`ready_for_adr`

The legal next move is an ADR over the exact reviewed r5 identity. No implementation, real policy, dataset authoring, publication, shadow integration, prompt projection, or automatic preflight is authorized by this memo.
