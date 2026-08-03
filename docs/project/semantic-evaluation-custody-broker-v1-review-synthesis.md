---
summary: "Controlling Decision 104 synthesis accepting only the owner-boundary architecture for ADR consideration."
read_when:
  - "Determining the legal next move after Decision 104 strict review."
type: "review_synthesis"
status: "accepted"
decision_id: 104
review_outcome: "ready_for_adr"
---
# Decision 104 controlling review synthesis

## Controlling input

This synthesis controls only the exact identity recorded in [`semantic-evaluation-custody-broker-v1-review-memo.md`](semantic-evaluation-custody-broker-v1-review-memo.md):

- commit `a7c291c780be4981ed14f16c8e3ed79f501b9a8f`;
- tree `e8d24279bffb73488bb5bf1b3d4b2ea46f278c59`;
- four document hashes listed in the review memo.

The rejected 271 KB packet at `e43eb045179ba95638e690a9574fdc80fd26de7f` and the non-converged first compact review at `c47535da074fa5d119fcbb1215dcb92096317993` remain non-authorizing evidence.

## Synthesis

The exact packet is coherent for ADR consideration because it makes authority local to the component that can truthfully exercise it:

1. the semantic owner alone owns immutable policy meaning and intent;
2. DSPx may own bounded execution episodes and evidence only for effects it actually mediates;
3. ROCS owns deterministic evaluation under owner-defined meaning, without acquiring runtime, semantic-owner, or publication authority;
4. Decision 53 continues to own publication, currentness, adoption, use, and rollback;
5. AK records task, decision, and evidence lineage but creates none of those domain authorities;
6. executable state machines may be canonical inside an owner boundary but may not become one cross-owner global authority;
7. immutable evidence contracts and hostile interface traces replace duplicated private state at integration boundaries.

This is contextual dominance rather than a fake universal synthesis: state-machine rigor dominates within owner-local state; enforcement discipline dominates at real effect boundaries; information hiding dominates between owners; evolutionary sequencing dominates the successor decisions.

## Successor separation

- Decision 105 must obtain DSPx owner acceptance for the exact effect inventory, local machine, crash/replay behavior, and receipts.
- Decision 106 must obtain ROCS owner acceptance for evaluation inputs, canonicalization, deterministic derivation, failure classification, and vectors while preserving owner-defined meaning.
- Decision 107 may ask only whether a verdict reference can enter Decision 53 without becoming publication/currentness authority. It must not presuppose Decisions 105 or 106.

No successor is accepted by this synthesis.

## Decision recommendation

`ready_for_adr`

A superseding ADR may accept only this authority partition and successor split. It must preserve Decision 103 and rejected R2 history, keep Decision 98 B0 frozen, and state that no implementation or live capability exists.

## Legal next sequence

```text
Decision 104 superseding boundary ADR
→ owner review of Decision 105
→ owner review of Decision 106
→ Decision 107 only after its assumed inputs are accepted
→ separate post-ADR implementation tasks, if any
```

No arrow authorizes its successor. Real policy, datasets, processes, providers/models, network, Pi integration, publication, adoption, automatic preflight, and dogfood remain blocked.
