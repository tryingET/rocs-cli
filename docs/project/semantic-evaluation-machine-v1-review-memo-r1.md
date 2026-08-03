---
summary: "Decision 106 r1 exact-byte strict-review memo."
read_when:
  - "Checking the Decision 106 r1 lane record."
type: "review_memo"
status: "complete"
decision_id: 106
review_outcome: "reject_current_direction"
---
# Decision 106 r1 — review memo

## Reviewed identity

- Commit: `c53a16a14562e1ed69ba4f49c171e35b62a2956f`
- Tree: `bb3f3b67fd58a5408ff78eae45fdbdf02e5bdf1f`
- Four-file aggregate: `541729d1904bdc424daa66f7fbb438b157bf9123566daabbebdf0b9ba71dbda4`

| Reviewed path | Bytes | SHA-256 |
|---|---:|---|
| `docs/project/semantic-evaluation-machine-v1-evidence-note.md` | 4230 | `6d96a95d3eda5f01425d2609491531a871d9bc0cce123d667d8b38e9b8b30255` |
| `docs/project/semantic-evaluation-machine-v1-problem-brief.md` | 3861 | `f525a0d47926d0b7a53cccf2bd0cca8226561c9fdbb818d22908ce0866f4070b` |
| `docs/project/semantic-evaluation-machine-v1-review-set-plan.md` | 5218 | `4c7b66f69e7cfd4c59f461fb3635b833e64c309d25637110f551da2274cb862a` |
| `docs/project/semantic-evaluation-machine-v1-rfc.md` | 8884 | `d8898083b4ef7e942bbe09609c7898b2e733b2d0ca0bce0275fd112ca13ebb68` |

Every lane independently reproduced the pinned DSPx projection as `1810` bytes / SHA-256 `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206` and schema as `8227` bytes / SHA-256 `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532`.

## Required lane results

| Lane | Artifact | Receipt | Blockers | Material improvements | Outcome |
|---|---|---|---:|---:|---|
| ROCS constructibility | `semantic-evaluation-machine-v1-review-lane-rocs-r1.md` | `dispatch-1785751414341` | 0 | 0 | `reject_current_direction` |
| Semantic-owner boundary | `semantic-evaluation-machine-v1-review-lane-semantic-owner-r1.md` | `dispatch-1785751414341-1` | 0 | 0 | `reject_current_direction` |
| DSPx producer contract | `semantic-evaluation-machine-v1-review-lane-dspx-producer-r1.md` | `dispatch-1785751414351` | 0 | 0 | `reject_current_direction` |
| Governance/security | `semantic-evaluation-machine-v1-review-lane-governance-security-r1.md` | `dispatch-1785751414353` | 0 | 0 | `reject_current_direction` |

The lanes agree that the missing policy, subject, typed joins, and access rights are blockers to constructing a semantic machine, not defects in the rejection packet. Identity and schema conformance cannot become semantic verdicts. Decision 107 remains blocked.

## Track outcome

`reject_current_direction`

## Legal next move

Produce the controlling synthesis. If it confirms complete convergence, record no ADR and use the terminal rejected workflow described by the RFC.
