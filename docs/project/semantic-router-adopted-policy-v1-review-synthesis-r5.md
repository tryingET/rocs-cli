---
summary: "Controlling Decision 103 synthesis: adopted semantic-routing policy v1 r5 is ready for ADR, with all execution and activation effects deferred."
read_when:
  - "Determining the legal next move for Decision 103."
type: "review_synthesis"
status: "accepted"
decision_id: 103
review_outcome: "ready_for_adr"
---
# Decision 103 review synthesis — r5

## Controlling input

This synthesis controls only the exact packet accepted in [`semantic-router-adopted-policy-v1-review-memo-r5.md`](semantic-router-adopted-policy-v1-review-memo-r5.md):

- commit `415e73d2f4128041911a76414a4d407ad20e0c31`;
- tree `01b6200b1ef6533b84dd93df81f385e4d8454f15`;
- aggregate `198b0203511650abd72f33962096f9b5004932de5163804849b60a057c814f0b`;
- manifest SHA-256 `22beb1a62e625e02ef1b98da62b871782b8585c4cc47a1faf45feeb2805981df`.

All three required lanes accepted that identity:

| Required lane | Final reviewer lineage | Outcome |
|---|---|---|
| semantic authority and publication boundary | `dispatch-1785623427853` | accept |
| protocol, cryptography, currentness, and resource safety | `dispatch-1785623427853-1` | accept |
| empirical independence, custody, contamination, and one-shot evaluation | `dispatch-1785623427854` | accept |

Unresolved minority findings: none. Superseding packet revision required: no. Earlier rejected revisions remain non-authorizing history.

## Synthesis

The protocol is coherent for ADR consideration because it:

1. selects exactly Softwareco-owned IDs from a frozen `softwareco/ontology` inventory without copying core ownership;
2. separates candidate freeze, independent verdict, semantic-owner publication, future consumer adoption, and runtime use;
3. binds policy/provenance, inventory, custody, contamination, preregistration, execution, approvals, publication history, currentness, and external verification through closed digest and equality schedules;
4. makes currentness depend on authenticated caller-pinned trust, single-use challenge consumption, and monotonic owner checkpoints rather than mutable `latest` state;
5. preserves fresh D/U/O custody and one-attempt evaluation while permanently excluding Decision 98 B0 from all future policy/evaluation coordinates;
6. keeps provider/model work, Pi integration, prompt projection, activation, and automatic preflight outside Decision 103.

## Decision recommendation

`ready_for_adr`

The ADR may accept the protocol and its authority split. It must not claim that any live issuer, key distribution, owner store, real policy, D/U/O set, evaluator, publication, consumer, recovery controller, or Pi path exists.

## Legal next sequence after an accepted ADR

A separately reviewed implementation plan must preserve the staged gates:

```text
P1 ROCS offline verifier
→ P2 synthetic semantic-owner storage mechanics
→ P3 fresh custody/preregistration
→ P4 visible D policy authoring
→ P5 one-shot U/O verdict
→ P6 owner publication
→ later exact-consumer shadow decision
→ later prompt-projection canary
→ automatic preflight last
```

No phase is implied by the preceding phase. Each requires owner-scoped tasks, predecessor evidence, independent review, and rollback proof.
