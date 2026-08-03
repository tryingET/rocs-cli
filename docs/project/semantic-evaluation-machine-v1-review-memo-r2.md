---
summary: "Decision 106 r2 exact-byte strict-review memo."
read_when: ["Checking Decision 106 r2 review convergence."]
type: "review_memo"
status: "complete"
decision_id: 106
review_outcome: "reject_current_direction"
---
# Decision 106 r2 — review memo

## Reviewed identity

- Commit: `fe6f71170db43c5d3015a653d192bdb72363434d`
- Tree: `aa123aa67ed523e40ec7e108e96ebf7114072e29`
- Aggregate: `41c2cc2f311828927e4fcc15914b48e70ab16a78aafbee525c575692bf2c8944`

| Reviewed path | Bytes | SHA-256 |
|---|---:|---|
| `docs/project/semantic-evaluation-machine-v1-evidence-note.md` | 4230 | `6d96a95d3eda5f01425d2609491531a871d9bc0cce123d667d8b38e9b8b30255` |
| `docs/project/semantic-evaluation-machine-v1-problem-brief.md` | 3861 | `f525a0d47926d0b7a53cccf2bd0cca8226561c9fdbb818d22908ce0866f4070b` |
| `docs/project/semantic-evaluation-machine-v1-review-set-plan.md` | 5734 | `f354eed71f313694b9d61180617504a2f24748762b27a479d2ce52a3508839fd` |
| `docs/project/semantic-evaluation-machine-v1-rfc.md` | 9959 | `c9c684ea3d1cd022e1f5acd64ae21bf0878d47c9261237093de29cab86a6bd7f` |

Every lane independently reproduced the D105 projection as `1810` bytes / `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206` and schema as `8227` bytes / `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532`.

## Required lanes

| Lane | Artifact | Receipt | Blockers | Material improvements | Outcome |
|---|---|---|---:|---:|---|
| ROCS | `semantic-evaluation-machine-v1-review-lane-rocs-r2.md` | `dispatch-1785752124841` | 0 | 0 | `reject_current_direction` |
| Semantic owner | `semantic-evaluation-machine-v1-review-lane-semantic-owner-r2.md` | `dispatch-1785752124842` | 0 | 0 | `reject_current_direction` |
| DSPx producer | `semantic-evaluation-machine-v1-review-lane-dspx-producer-r2.md` | `dispatch-1785752124843` | 0 | 0 | `reject_current_direction` |
| Governance/security | `semantic-evaluation-machine-v1-review-lane-governance-security-r2.md` | `dispatch-1785752124844` | 0 | 0 | `reject_current_direction` |

All lanes agree both the substantive rejection and the current AK path: `review_pending -> decision_pending -> tasks_reevaluation_pending(outcome=rejected) -> unblocked(outcome=rejected)`, no ADR. Final `unblocked/rejected` records completed reevaluation only.

## Track outcome

`reject_current_direction`

## Legal next move

Produce the controlling r2 synthesis. Only that synthesis can replace the historical r1 closure and authorize the reviewed rejection workflow.
