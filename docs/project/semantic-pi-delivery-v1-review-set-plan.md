---
summary: "Exact-byte multi-lane review plan for the Decision 82 semantic Pi delivery v1 r24 RFC."
read_when:
  - "Running or synthesizing review of the Decision 82 semantic Pi delivery v1 r24 RFC."
system4d:
  container: "Review topology and closure contract for the Decision 82 r24 successor."
  compass: "Make every authority owner and host seam challenge the same immutable RFC bytes."
  engine: "Freeze commit/digests -> independent lanes -> controlling synthesis -> legal next move."
  fog: "Prior identity reviews or partial lane agreement may be mistaken for v1 ADR readiness."
type: "review_set_plan"
status: "active"
---

# Review set plan — semantic Pi delivery v1 r24

## Reviewed set

The review controller freezes one Git commit containing exactly:

- `docs/project/semantic-pi-delivery-v1-problem-brief.md`;
- `docs/project/semantic-pi-delivery-v1-evidence-note.md`;
- `docs/project/semantic-pi-delivery-v1-rfc.md`;
- `docs/project/semantic-pi-delivery-v1-runtime-contracts.md`;
- `docs/project/semantic-pi-delivery-v1-authority-contracts.md`;
- `docs/project/semantic-pi-delivery-v1-validation-contracts.md`;
- `docs/project/semantic-pi-delivery-v1-machine-contract.md`;
- `docs/project/semantic-pi-delivery-v1-seccomp-policy.json`;
- `docs/project/semantic-pi-delivery-v1-wasm-grammar.json`;
- `docs/project/semantic-pi-delivery-v1-wasm-validation-algorithm.md`;
- `docs/project/semantic-pi-delivery-v1-durable-store.sql`;
- `docs/project/semantic-pi-delivery-v1-integration-ledger.sql`;
- `docs/project/semantic-pi-delivery-v1-production-replay.sql`;
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

## R24 correction focus

Every lane must independently compare the r24 Complete digest registry with frozen r23 and prove that all 193 rows retain their first three logical cells exactly and each has exactly one explicit fourth-cell enum value. Review must reproduce 43 `exact_bytes`, 144 `jcs_object` split into 134 backticked self-digest rows plus 10 `full closed object` rows, and exactly six `jcs_preimage` projections: the two full closed preimages, applied entry, logical realpath identity, filesystem tree, and signed authority statement. It must also reproduce 193 rows across 191 domains, the three reviewed object names sharing `semantic-release.pi-packet-file-bytes.v1`, and generated sorting/uniqueness by `(domain,object_name)` rather than domain alone.

The ROCS and semantic-owner lanes must prove that the fourth cell only classifies existing byte, full-object, self-omitting-object, and bespoke-JCS preimages. The machine compiler must copy that cell directly, emit only `exact_bytes|jcs_object|jcs_preimage`, enforce the exact relational combinations and counts, and obtain byte-identical complete inventories from independent Python and Node implementations without prose, suffix, schema, object-name, or domain-name inference. Validation must reject a missing, unknown, null, extra, count-drifting, self-field-inconsistent, or row-inconsistent value and must recompute the preimage selected by the explicit reviewed row.

Every lane must additionally prove that r24 leaves the three pinned Unicode input hashes, comment preprocessing order, six exact non-emitting `UnicodeData.txt` `Cs` rows, scalar-only decomposition/casefold/exclusion/output semantics, and six source-compiler obligations unchanged. Fixture semantics and counts remain exactly 112 mandatory protocol cases, 115 mandatory-plus-boundary Python/Node protocol cases, 25 Pi-host cases, and 127 rule-coverage rows; revision-bearing packet, profile, and valid-case IDs advance consistently to r24, while Decision-bearing policy, ledger-anchor, and task/scope bindings advance to Decision 82, without changing routes or outcomes.

Decision 71/r21/task 4230/evidence 5325 and Decision 80/r23/failed task 4250/evidence 5404 must remain immutable non-authorizing predecessor history. Decision 82 supersession is conditional on a future accepted ADR, and every r24 packet/runtime/appointment/task/scope/reevaluation/ledger authority binding must name Decision 82. Any inferred classification, altered preimage algorithm, first-three-cell drift, inventory/count mismatch, Unicode or fixture semantic drift, stale active Decision-80 binding, packet-generation shortcut, missing predecessor lineage, or claimed implementation/live authority forces `revise_rfc`.

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

Pi-owner reviews `dispatch-1784658092396`, `dispatch-1784658106914`, and `dispatch-1784658320675` establish the owner identity artifact only. They are evidence inputs, not v1 RFC review lanes. Decision-80 r22/r23 lane outputs, controlling syntheses, and the accepted r23 ADR remain immutable predecessor review history; none is a Decision-82 r24 lane result or synthesis.

## Stop conditions

Stop without synthesis if:

- reviewed bytes or commit drift;
- a required lane is missing;
- a reviewer claims implementation/live authority;
- a reviewer substitutes passing tests or fixtures for owner facts;
- the host seam cannot support post-application witnessing;
- any proposal edits v0 or Decision-71/Decision-80 predecessor history, infers a preimage kind, mutates a preimage algorithm, or aliases `pi-adapter`.
