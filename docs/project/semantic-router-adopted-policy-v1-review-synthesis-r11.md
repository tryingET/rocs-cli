---
summary: "Controlling Decision 103 synthesis: exact adopted semantic-routing policy v1 r11 is ready for ADR; all implementation and live effects remain deferred."
read_when:
  - "Determining the legal next move for Decision 103 after r11 convergence."
type: "review_synthesis"
status: "accepted"
decision_id: 103
review_outcome: "ready_for_adr"
---
# Decision 103 review synthesis — r11

## Controlling input

This synthesis supersedes the retired r5 synthesis and the blocked r9 status. It controls only the exact packet accepted in [`semantic-router-adopted-policy-v1-review-memo-r11.md`](semantic-router-adopted-policy-v1-review-memo-r11.md):

- commit `94f2d273c5f2ce27959978b82a37a3b2a8088867`;
- tree `fb2588f0623d92b80b46fd4b0f937e346cd32f83`;
- aggregate `20e8df2547bb4816325c7546a3c0a43b0283c6e0589d123e71b809baa7bfe438`;
- manifest SHA-256 `05b39534733a81a2eb806d9c183033d7a0396e11d93c68f6a5f613fb80448fc5`.

| Required concern | Final reviewer lineage | Outcome |
|---|---|---|
| semantic authority and publication boundary | `dispatch-1785648963446` | accept |
| protocol/security and execution lifecycle | `dispatch-1785647681550` | accept |
| empirical custody and terminal access | `dispatch-1785647681551` | accept |
| constructibility, digest DAG, and phase ordering | `dispatch-1785647681552` | accept |

Unresolved blocking findings: none. Superseding packet revision required: no. Every earlier rejection remains non-authorizing history.

## Synthesis

The exact r11 packet is coherent for ADR consideration because it:

1. selects only frozen-inventory `co.software.*` IDs owned by `softwareco/ontology` without copying core ownership;
2. separates candidate freeze, independent custody/verdict, semantic-owner publication, future consumer adoption, and runtime use;
3. preserves an acyclic executable order from P3 custody readiness through P7 currentness, including channel → challenge → unsigned start subject → caller request → evaluator signature;
4. authenticates the actual evaluator/gateway path, consumes the single reservation before spawn, records timely custodian-observed spawn, transfers only gateway-mediated revocable handles, and requires process reaping plus handle closure and terminal revoke before verdict;
5. gives exact schema shapes to eight complete/interrupted/no-start attempt/verdict branches while using seven unique closure/approval projections where pass count is intentionally projected through the bound execution attempt;
6. makes currentness depend on caller-pinned trust, authenticated single-use challenge consumption, and monotonic owner checkpoints rather than proof-nested or mutable-latest authority;
7. permanently excludes Decision 98 B0 from every future policy, data, evaluator, fixture, regression, floor, template, alias, and execution coordinate;
8. keeps live issuers, keys, owner storage, real policy, D/U/O, empirical execution, publication, consumer adoption, Pi/runtime delivery, providers/models, prompt projection, and automatic preflight outside this acceptance.

## Decision recommendation

`ready_for_adr`

A new ADR may accept only this exact protocol and authority split. It must retain the previous ADR draft as rejected history and must not claim any implementation or live capability exists.

## Legal next sequence after an accepted ADR

```text
P1 ROCS offline verifier
→ P2 synthetic semantic-owner storage mechanics
→ P3 fresh custody readiness and sealed D/U/O coordinates
→ P4 visible-D policy authoring and candidate freeze
→ P5 one-shot reservation/preregistration/activation
→ P6 one immutable protected evaluation and independent verdict
→ P7 owner publication/currentness
→ later exact-consumer shadow decision
→ later prompt-projection canary
→ automatic preflight last
```

No phase is implied by its predecessor. Each requires an owner-scoped task, exact predecessor identity, independent review, rollback proof, and the packet's stop conditions.
