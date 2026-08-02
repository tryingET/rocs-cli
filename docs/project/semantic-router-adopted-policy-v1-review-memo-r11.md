---
summary: "Decision 103 strict review memo for exact adopted semantic-routing policy v1 packet revision r11."
read_when:
  - "Checking Decision 103 pre-ADR review closure after the rejected r5 ADR and r6-r10 corrections."
type: "review_memo"
status: "accepted"
decision_id: 103
review_outcome: "ready_for_adr"
---
# Decision 103 review memo — adopted semantic-routing policy v1 r11

## Reviewed identity

- packet commit: `94f2d273c5f2ce27959978b82a37a3b2a8088867`
- packet tree: `fb2588f0623d92b80b46fd4b0f937e346cd32f83`
- packet aggregate: `20e8df2547bb4816325c7546a3c0a43b0283c6e0589d123e71b809baa7bfe438`
- packet-manifest SHA-256: `05b39534733a81a2eb806d9c183033d7a0396e11d93c68f6a5f613fb80448fc5`

Any normative packet byte change retires this review.

## Final lane outcomes

| Required lane | Reviewer lineage | Outcome |
|---|---|---|
| semantic authority and publication boundary | `dispatch-1785648963446` | accept |
| protocol/security and execution lifecycle | `dispatch-1785647681550` | accept |
| empirical custody and terminal access | `dispatch-1785647681551` | accept |
| constructibility, digest DAG, and phase ordering | `dispatch-1785647681552` | accept |

All reviewers named the exact r11 commit and aggregate. Each independently recomputed the seven manifest entries and aggregate. The protocol reviewers also confirmed eight distinct full attempt/verdict branches, seven unique closure/approval projections, 1,115 resolving local schema references, and an acyclic 69-definition `$ref` graph.

These are static packet reviews. They do not establish live issuers, keys, owner stores, custodian acceptance, real policy, D/U/O, evaluator implementation, empirical verdict, publication, consumer consent, Pi/runtime delivery, provider/model behavior, prompt projection, or automatic preflight.

## Rejected and superseded history

- r1-r4 were rejected during initial strict review.
- r5's former review closure was retired when ADR executability review `dispatch-1785629031503` found a digest cycle and impossible phase ordering.
- r6-r8 corrected those defects but were rejected for unsigned authority facts, phase conflicts, executor binding, access activation, and closure gaps.
- exact r9 was rejected by `dispatch-1785647681550`, `dispatch-1785647681551`, and `dispatch-1785647681552` for contradictory attempt branches, incorrect channel/start ordering, incomplete prefix preservation, unproved timely spawn, and durable descriptor capability.
- exact r10 was rejected by the same lineages because duplicate interrupted closure/approval alternatives made two branches invalid under JSON Schema `oneOf`.
- r11 removed only that final duplicate-projection defect and all four required review concerns accepted the exact successor.

Rejected commits, aggregates, reports, the retained rejected ADR draft, and the r9 blocked-status marker remain historical evidence and convey no approval.

## Boundary conclusion

The accepted packet keeps authority separate:

- `softwareco/ontology` alone owns the first Softwareco policy meaning and publication;
- `core/ontology-kernel` remains upstream meaning authority for core IDs and is not copied or relabelled;
- ROCS verifies closed offline protocol objects but issues no semantic, custodian, consumer, or runtime authority;
- a future explicitly accepted DSPx custodian owns raw U/O and controlled execution;
- AK links decision/task/evidence records but stores no policy or protected U/O bytes;
- a later exact consumer owns adoption, suppression, activation, and rollback;
- Pi/runtime, providers/models, prompt projection, and automatic preflight require later explicit decisions.

Decision 98 B0 remains frozen failed evidence and is prohibited as policy, data, evaluator, fixtures, regressions, floors, templates, aliases, or execution input.

## Outcome

`ready_for_adr`

The only legal next move is a new ADR over this exact r11 packet identity. No implementation or live action is authorized by this memo.
