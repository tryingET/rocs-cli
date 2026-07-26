---
summary: "Strict multi-lane exact-byte review plan for Decision 85 semantic Pi insertion evidence v1."
read_when:
  - "Running Decision 85 review lanes or synthesis."
type: "review_set_plan"
status: "active"
---
# Review set plan — semantic Pi insertion evidence v1

## Frozen set

Freeze one commit containing exactly:

1. `docs/project/semantic-pi-insertion-evidence-v1-problem-brief.md`;
2. `docs/project/semantic-pi-insertion-evidence-v1-evidence-note.md`;
3. `docs/project/semantic-pi-insertion-evidence-v1-rfc.md`;
4. `docs/project/semantic-pi-insertion-evidence-v1-review-set-plan.md`;
5. `docs/project/semantic-pi-insertion-evidence-v1-vectors.json`.

For each path compute exact byte length and ordinary SHA-256. Sort ASCII rows `path<TAB>length<TAB>sha256<LF>` by unsigned UTF-8 path and SHA-256 the concatenation. Any byte change invalidates all lane results.

## Closure mode

`multi_lane_requires_synthesis`. All lanes review the same commit and aggregate. A timeout, missing lane, byte mismatch, or material finding yields no legal convergence.

## Required lanes

| Lane | Question |
|---|---|
| ROCS protocol | Are all six schemas, eight digest domains, sequencing rules, sixteen exact cases, and thirteen exact host fixtures closed and independently implementable without a registry or inference? |
| Pi host owner | Can the host issue the private witness only after assignment/readback and keep dispatch guarded until record creation? |
| Pi component owner | Can `pi-ontology-workflows` acknowledge the witness without acquiring host, semantic, provider, or production authority? |
| Governance/security | Are replay, reentry, identity substitution, reload, failure, and no-overclaim boundaries complete? |
| Scope/debt | Did the redesign actually remove the failed 155-schema production/recovery surface rather than hide or defer required insertion semantics? |

## Mandatory checks

Every lane must confirm:

- repository/component/package identity and no `pi-adapter` alias;
- no active use of Decision 71/80/82/84 implementation tasks or packet bytes;
- no generic resolver, edge registry, SQL store, recovery actor, seccomp, Wasm, consumer, production, or semantic-release overlay;
- at most seven schemas including any later packaging manifest;
- exact host order: prepare -> apply -> assign -> readback -> witness -> applied acknowledgement -> record -> dispatch eligibility;
- private brand cannot be reconstructed from JSON/digest;
- generation/attempt/index and one-use replay closure;
- record claim is insertion only and both provider/model booleans are false at record time;
- persisted bytes are unauthenticated audit data, not public owner evidence;
- exact sixteen protocol cases and thirteen host fixtures from the reviewed vector source, with no claim of continuity from the rejected 112/3/25/127 inventory;
- no implementation, dogfood, publication, activation, live, or production authority.

Reviewers must verify nonempty retained NFC contribution bytes, combined-size closure, non-NFC concatenation rejection, apply-operation-derived offsets for repeated identical occurrences, immutable registration identity, stale ExtensionAPI rejection, detached callback rejection, mutex-linearized abort/deadline/reload, complete six-entrypoint frame/guard matrix, recursive prompt/continuation/completion poisoning, optional post-commit persistence, and reload between assignment and acknowledgement. A schema means one named top-level protocol object; inline rows do not count.

## Verdicts

Each lane returns exactly `ready_for_adr`, `revise_rfc`, or `reject_current_direction`, with blockers/material findings/notes, exact commit and aggregate, and legal next move. Any blocker or material architecture question forces `revise_rfc`.

The controlling synthesis may return `ready_for_adr` only with five valid `ready_for_adr` lanes, zero blockers, zero unresolved material findings, exact-byte agreement, and explicit confirmation that implementation remains post-ADR and default-off.

## Predecessor preservation

Decision 53 v0, Decisions 71/80/82/84, failed tasks `4230`/`4250`/`4278`/`4298`, evidence `5325`/`5404`/`5446`/`5492`, their ADRs/reviews, and all frozen sources remain immutable non-authorizing history. No lane may call their downstream tasks reusable.
