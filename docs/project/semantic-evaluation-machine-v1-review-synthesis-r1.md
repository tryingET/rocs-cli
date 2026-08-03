---
summary: "Controlling Decision 106 r1 synthesis rejecting an unconstructible projection-only semantic machine."
read_when:
  - "Determining the legal next move for Decision 106."
type: "review_synthesis"
status: "complete"
decision_id: 106
review_outcome: "reject_current_direction"
---
# Decision 106 r1 — controlling synthesis

## Exact review identity

All four required lanes reviewed commit `c53a16a14562e1ed69ba4f49c171e35b62a2956f`, tree `bb3f3b67fd58a5408ff78eae45fdbdf02e5bdf1f`, and aggregate `541729d1904bdc424daa66f7fbb438b157bf9123566daabbebdf0b9ba71dbda4`.

Each lane independently reproduced the accepted DSPx projection at `1810` bytes / SHA-256 `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206` and projection schema at `8227` bytes / SHA-256 `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532` from commit `1dfbfa138dffee810896d939e8344ae8feb00537`.

## Inputs

- ROCS constructibility: `semantic-evaluation-machine-v1-review-lane-rocs-r1.md` / `dispatch-1785751414341` / `reject_current_direction`.
- Semantic-owner boundary: `semantic-evaluation-machine-v1-review-lane-semantic-owner-r1.md` / `dispatch-1785751414341-1` / `reject_current_direction`.
- DSPx producer contract: `semantic-evaluation-machine-v1-review-lane-dspx-producer-r1.md` / `dispatch-1785751414351` / `reject_current_direction`.
- Governance/security: `semantic-evaluation-machine-v1-review-lane-governance-security-r1.md` / `dispatch-1785751414353` / `reject_current_direction`.

All four results are valid, exact-byte aligned, and contain zero packet blockers, zero material improvements, and zero architecture-shaping disagreements.

## Synthesis

The accepted Decision 105 projection is truthful digest-only execution evidence. It supplies neither semantic-owner policy bytes nor policy-selected subject preimages, typed preimage joins, acquisition authority, verdict vocabulary, or semantic precedence. Its explicit non-authority values deny semantic meaning and deterministic verdict authority. Generic schema conformance also cannot authenticate producer eligibility.

ROCS can verify the one accepted fixture's identity and structural shape. It cannot execute a semantic predicate over absent bytes, reverse a digest, invent another owner's meaning, or promote an observed return into a semantic pass. A conformance-only or constant `not_evaluable` runtime would create a misleading interface rather than a Decision 106 semantic machine.

The packet correctly preserves the Decision 104 owner split, the Decision 105 nonclaims and incomplete-final-closure caveat, Decision 53 publication/currentness authority, and Decision 107's blocked state.

## Controlling outcome

`reject_current_direction`

## Legal next move

1. Preserve the frozen RFC, lane artifacts, memo, and this synthesis as immutable rejection evidence.
2. Attach the problem brief, evidence note, review-set plan, review memo, and this controlling synthesis to Decision 106.
3. Record no ADR.
4. Transition Decision 106 to terminal state `superseded` with outcome `rejected` and this synthesis as evidence.
5. Complete task `4618` as reviewed owner-boundary adjudication.
6. Keep Decision 107 blocked; this outcome exposes no accepted interface.

Any future semantic machine requires a new decision and task after the semantic owner supplies exact policy bytes, authorized subject preimages, typed joins, and acquisition evidence. This synthesis grants no implementation, data access, ontology mutation, Decision 107, provider/model/network, publication, activation, or production authority.
