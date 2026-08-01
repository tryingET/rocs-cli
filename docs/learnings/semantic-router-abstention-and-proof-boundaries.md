---
summary: "Decision 102 learning: semantic retrieval, domain admission, selection, and proof must remain separate, with abstention as the default under missing or conflicting support."
read_when:
  - "Designing semantic retrieval, routing, preflight, or context-selection systems."
  - "Turning a failed relevance experiment into a new retrieval architecture."
type: "learning"
status: "candidate"
---
# Learning — Abstaining Semantic Routing and Proof Boundaries

## Context

Decision 102 followed the valid frozen failure of Decision 98 B0. Deterministic lexical discovery retained useful recall, repeatability, and latency, but null rejection was `0.10`. High-scoring null prompts overlapped low-scoring applicable prompts, falsifying a global score threshold as the primary repair. The accepted implementation preserves lexical discovery unchanged and adds a separate development-only symbolic router.

Durable evidence:

- accepted architecture: [`../adr/2026-08-01-abstaining-semantic-router-v0.md`](../adr/2026-08-01-abstaining-semantic-router-v0.md);
- normative invariants: [`../project/semantic-router-v0/invariants.md`](../project/semantic-router-v0/invariants.md);
- implementation plan: [`../project/semantic-router-v0-implementation-plan.md`](../project/semantic-router-v0-implementation-plan.md);
- frozen B0 report: [`../project/decision98-b0-semantic-relevance-report.json`](../project/decision98-b0-semantic-relevance-report.json);
- implementation tasks `4464`, `4465`, `4469`, `4476`, corrective task `4478`, S4 task `4477`, and canonical promotion task `4481`;
- final verified implementation head `a016ac144ba01f1210efbfe94dc4f45eb3278358` (tree `a6dd7ecbc43effbd41e7fd62ca371f7351a561d4`).

## Durable pattern

A semantic preflight system must separate four contracts:

1. **domain admission** decides whether the policy has jurisdiction;
2. **candidate generation** provides diagnostic candidates without selecting authority;
3. **semantic adjudication** requires explicit positive policy support and applies exclusions;
4. **proof and lineage** bind the request, policy, provenance, corpus, tool, nested retrieval, and result.

Missing support, support/exclusion conflict, unresolved multiplicity, absent exact joint policy, or operational uncertainty must emit no semantic selection. Resource exhaustion, invalid inputs, changed snapshots, and runtime incompatibility are errors—not successful abstentions.

## What the failed experiment established

- Nearest-match retrieval is not open-set admission. Sparse and dense systems both produce a nearest neighbor unless abstention is designed separately.
- Similarity magnitude cannot establish ontology jurisdiction when null and applicable score distributions overlap.
- A valid preregistered failure should terminate its hypothesis. Repair requires a fresh architecture and fresh evaluation contract, not threshold tuning or mechanical retry.
- Retrieval relevance, provider delivery, model input, behavioral influence, and production benefit remain different evidence dimensions.

## Implementation lessons

### Preserve the useful primitive

`rocs-lexical-v0` remained unchanged and executes exactly once per successful route. Lexical scores are nested diagnostic evidence and never influence symbolic selection. This preserved deterministic discovery compatibility while preventing candidate generation from acquiring admission authority.

### Make evidence schedules exact

Policy alternatives have one provenance record each. Matching emits one canonical witness per group, every matched clause required by the schedule, and no extra evidence. Multi-concept selection requires an owner-authored joint route whose ontology-ID set exactly equals the supported set.

### Bind bytes, not convenient paths

Policy and provenance capture retains no-follow descriptors, rechecks identities and bytes, and reads source blobs only from a closed local Git object database. Git alternates, replace refs, common directories, shallow/partial/promisor state, network protocols, and ambient configuration fail closed.

Directory identity checks must distinguish path replacement from unrelated directory churn. Device, inode, and mode detect directory replacement. Corrective task `4478` stabilized anchored rechecks under shared `TMPDIR` churn.

### Pin semantic runtimes explicitly

Unicode normalization, full casefold, and Letter/Number classification are protocol behavior. The independent Node verifier therefore carries pinned Unicode-15 tables instead of trusting a newer ambient Node Unicode runtime. Runtime or schema incompatibility is a distinct safe error.

### Prove rollback outside the implementation

The accepted reverse-rollback rehearsal copied the compatibility verifier outside the candidate, recorded its digest, reverted the corrective and S3→S0 commits, and reached the exact implementation-base tree. A failed ambient-TMPDIR attempt was retained by digest before the passing rehearsal.

## Dogfood result and boundary

Synthetic development-only CLI dogfood passed on canonical `main`:

- routing state `multi`;
- selected concepts `synthetic.Alpha` and `synthetic.Beta`;
- the canonical dogfood reproduced the S4 route result digest;
- S4 recorded the nested discovery digest;
- automatic semantic preflight remained disabled.

The dogfood proves only the bounded synthetic development CLI path at the verified implementation identity. Separately, the accepted reverse-rollback rehearsal proves restoration to the exact implementation-base tree. Neither proves real ontology policy quality, publication or adoption, consumer/Pi integration, provider transmission, model input, behavioral benefit, or production readiness.

## Reuse rule

For future semantic preflight work:

```text
frozen failure evidence
-> fresh architecture and hypothesis
-> explicit domain admission
-> deterministic candidate generation
-> evidence-aware adjudication
-> abstention on uncertainty
-> exact lineage and safe operational errors
-> synthetic dogfood
-> external reverse rollback proof
```

Never repair open-set failure by silently increasing a similarity threshold, swapping in another nearest-neighbor mechanism, or treating a candidate as an authorized selection.

## Activation boundary

This is candidate KES guidance. It does not create real routing policy, adopted publication semantics, automatic preflight activation, consumer consent, provider/model authority, or permission to rerun Decision 98 B0.
