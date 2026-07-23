---
summary: "Pi host-owner review of semantic Pi delivery v1 RFC revision r2."
read_when: ["Revising or synthesizing decision 71 RFC review r2."]
type: "review_memo"
status: "complete"
review_outcome: "revise_rfc"
---
# Pi host-owner review — r2

Reviewed commit `82bf27ce39d87a840d2e486a40ecdda46ab9a1b7`; aggregate `a2a0ba9cb53812e8c93319fe0f349cb7dd6e9f6bfece7acef22f365cc5544882`; exact-byte check passed. Dispatch `dispatch-1784832221100-1`. Outcome: `revise_rfc`.

Blockers: persisted controller evidence remains unauthenticated and must be described only as supervised controller-observed evidence or gain an authentic provenance mechanism; integration acknowledgement/redemption/replay schemas are missing; closed schemas have null/digest contradictions; package/host artifact digests remain ambiguous; handler index, contribution preimage, and ROCS request binding are not exact.

Material: fail closed before provider dispatch on acknowledgement/redemption/post-check failure; use a non-evicting replay set; define integer exhaustion.

Legal next move: revise and rerun all lanes. No authority granted.
