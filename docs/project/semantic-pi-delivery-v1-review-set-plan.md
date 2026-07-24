---
summary: "Exact-byte multi-lane review plan for the semantic Pi delivery v1 RFC."
read_when:
  - "Running or synthesizing review of the semantic Pi delivery v1 RFC."
system4d:
  container: "Review topology and closure contract for the Decision 53 successor."
  compass: "Make every authority owner and host seam challenge the same immutable RFC bytes."
  engine: "Freeze commit/digests -> independent lanes -> controlling synthesis -> legal next move."
  fog: "Prior identity reviews or partial lane agreement may be mistaken for v1 ADR readiness."
type: "review_set_plan"
status: "active"
---

# Review set plan — semantic Pi delivery v1

## Reviewed set

The review controller freezes one Git commit containing exactly:

- `docs/project/semantic-pi-delivery-v1-problem-brief.md`;
- `docs/project/semantic-pi-delivery-v1-evidence-note.md`;
- `docs/project/semantic-pi-delivery-v1-rfc.md`;
- `docs/project/semantic-pi-delivery-v1-runtime-contracts.md`;
- `docs/project/semantic-pi-delivery-v1-authority-contracts.md`;
- `docs/project/semantic-pi-delivery-v1-validation-contracts.md`;
- `docs/project/semantic-pi-delivery-v1-review-set-plan.md`.

The controller records commit SHA, per-file SHA-256, byte lengths, and an aggregate SHA-256. For each reviewed path, compute SHA-256 over its exact file bytes and serialize one ASCII row exactly as `path<TAB>byte_length<TAB>sha256<LF>`, where `path` is the repository-relative POSIX path shown above, byte length is canonical unsigned decimal with no leading zero except `0`, and `sha256` is 64 lowercase hexadecimal characters without a prefix. Sort complete rows by the unsigned UTF-8 bytes of `path`, concatenate them with no header or extra bytes, and compute ordinary SHA-256 over that concatenation; the aggregate is 64 lowercase hexadecimal characters without a prefix. Any byte change invalidates every review and requires a new set.

## Closure mode

`multi_lane_requires_synthesis`.

Track verdicts are inputs. Only the latest complete synthesis supplies the decision-level outcome. Reviewer failure, timeout, missing output, or scope mismatch produces no verdict.

## Required lanes

| Lane | Owner question | Required checks |
|---|---|---|
| Pi component owner | Is `pi-ontology-workflows` the correct product/component issuer? | multi-axis identity, package boundary, no adapter extraction/alias, compact surface, constructor-authority removal |
| Pi host owner | Can the host truthfully issue the proposed witness? | exact post-application seam, loaded artifact provenance, generation/attempt identity, immutability, replay, no provider-transmission overclaim |
| ROCS protocol | Is v1 deterministic and independently executable? | closed schema, JCS/digest domain, generators, fixtures, Python/Node independence, embedding reproducibility, v0 preservation |
| Semantic owner | Does the successor preserve semantic-owner authority? | no publication/meaning/trust transfer, unchanged surrounding release graph, no fixture authority |
| Governance/security/operations | Are legality and failure boundaries complete? | exact owner split, anti-substitution, default-off, one-shot dogfood authorization, live blockers, rollback and stop conditions |

No consumer-owner or recovery-owner verdict may be fabricated while those owner products do not exist. Their absence remains a live-gate blocker.

## Review prompt

Each lane must:

1. cite exact reviewed commit and manifest aggregate;
2. classify every finding as blocker, material improvement, or non-blocking note;
3. challenge coherent identity substitution, witness forgery, replay, and authority escalation;
4. state one explicit outcome: `ready_for_adr`, `revise_rfc`, or `reject_current_direction`;
5. state the legal next move;
6. grant no implementation, dogfood, publication, adoption, activation, or live authority.

Use strict convergence. Any blocker, material architecture question, cross-lane contradiction, or unowned required fact forces `revise_rfc`.

## Synthesis rule

The designated ROCS decision controller synthesizes only after all five valid lane results exist. `ready_for_adr` requires:

- zero blockers;
- zero unresolved material improvements;
- zero architecture-shaping open questions;
- zero cross-lane contradictions;
- exact reviewed-byte agreement;
- explicit confirmation that implementation remains post-ADR gated and live D2E remains blocked.

The synthesis cites every lane result and emits one outcome plus legal next move. It does not average or outvote owner-boundary objections.

## Prior review exclusion

Pi-owner reviews `dispatch-1784658092396`, `dispatch-1784658106914`, and `dispatch-1784658320675` establish the owner identity artifact only. They are evidence inputs, not v1 RFC review lanes.

## Stop conditions

Stop without synthesis if:

- reviewed bytes or commit drift;
- a required lane is missing;
- a reviewer claims implementation/live authority;
- a reviewer substitutes passing tests or fixtures for owner facts;
- the host seam cannot support post-application witnessing;
- any proposal edits v0 history or aliases `pi-adapter`.
