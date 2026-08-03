---
summary: "Exact-byte four-lane strict review plan for Decision 106 r1 constructibility adjudication."
read_when:
  - "Running or synthesizing Decision 106 review."
type: "review_set_plan"
status: "active"
decision_id: 106
review_mode: "strict_convergence"
review_closure_mode: "multi_lane_requires_synthesis"
---
# Review set plan — Decision 106 r1

## Reviewed set

The reviewed set consists exactly of these four paths from one frozen Git commit:

1. `docs/project/semantic-evaluation-machine-v1-problem-brief.md`;
2. `docs/project/semantic-evaluation-machine-v1-evidence-note.md`;
3. `docs/project/semantic-evaluation-machine-v1-rfc.md`;
4. `docs/project/semantic-evaluation-machine-v1-review-set-plan.md`.

For each path, compute SHA-256 over exact bytes and serialize:

```text
path<TAB>byte_length<TAB>sha256<LF>
```

Sort rows by unsigned UTF-8 path bytes, concatenate with no header or extra bytes, and compute ordinary SHA-256 over the resulting manifest bytes. Every lane must cite the same commit, tree, per-file identities, and aggregate. Any reviewed-byte change invalidates all lane outputs.

The external prerequisite is immutable and excluded from this repository aggregate. Its source repository is `/home/tryinget/ai-society/softwareco/owned/dspx`, pinned at commit `1dfbfa138dffee810896d939e8344ae8feb00537`. The acceptance record path at that commit is `docs/project/semantic-evaluation-execution-custody-v1-projection-byte-acceptance.md`; the projection-schema path is `docs/project/semantic-evaluation-execution-custody-v1-projection.schema.json`. Every lane uses `git show <commit>:<path>`, extracts the first `json` fenced body from the acceptance record with no fence or surrounding newline, and independently reproduces exact projection length `1810`, projection SHA-256 `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206`, and schema SHA-256 `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532`. Mutable branch names and working-tree bytes are not review inputs.

## Closure mode

`multi_lane_requires_synthesis`. Lane verdicts are immutable inputs. Only the latest complete synthesis supplies the Decision 106 outcome.

## Required lanes

| Lane | Controlling question | Required checks |
|---|---|---|
| ROCS constructibility | Can ROCS execute a semantic predicate from existing exact inputs? | accepted bytes, canonicalization, available operands, deterministic derivation, failure classification, no conformance/verdict conflation |
| Semantic-owner boundary | Is policy meaning and subject selection supplied by its owner? | policy bytes/identity/provenance, subject preimages, acquisition rights, verdict vocabulary/precedence, no ROCS invention |
| DSPx producer contract | Does the RFC preserve Decision 105 evidence and nonclaims exactly? | digest-only disclosure, return/failure meaning, eligibility, replay, generic schema versus exact fixture, incomplete lifecycle-closure caveat |
| Governance/security | Does any result escalate authority or enable substitution? | whole-object and field-role substitution, Decision 53/107 boundary, AK non-authority, no publication/currentness/activation |

## Lane protocol

Each lane must:

1. inspect the frozen files from the cited commit rather than mutable working-tree assumptions;
2. independently reproduce the external projection length/hash and schema hash;
3. classify each finding as blocker, material improvement, or note;
4. state whether any currently accepted artifact supplies semantic policy bytes, subject preimages, typed digest joins, and acquisition authority;
5. state one explicit outcome: `ready_for_adr`, `revise_rfc`, or `reject_current_direction`;
6. state the legal next move;
7. grant no implementation, Decision 107, data access, publication, activation, or live authority.

A reviewer timeout, transport failure, missing hash reproduction, scope mismatch, or invented owner fact yields no verdict.

## Synthesis rule

Strict convergence applies; there is no vote or threshold.

`reject_current_direction` requires:

- all four valid lane outputs exist against identical bytes;
- zero lane proposes a constructible semantic machine from currently accepted exact inputs;
- zero unresolved blocker or material wording defect in the rejection packet;
- exact agreement that conformance cannot be relabeled as semantic verdict;
- exact agreement that future owner-supplied policy/subject contracts require a new decision;
- explicit confirmation that Decision 107 remains blocked.

Any material packet defect forces `revise_rfc`. Any architecture-shaping disagreement prevents synthesis. `ready_for_adr` requires a constructible current machine and therefore cannot be inferred from prerequisite acceptance alone.

## Stop conditions

Stop without synthesis if:

- reviewed bytes drift;
- any required lane is missing;
- external hashes do not reproduce;
- a reviewer treats schema validity, a digest, a return, a receipt, a test, Git, or AK state as semantic truth;
- a reviewer invents policy meaning, raw-data access, producer eligibility, publication/currentness, or Decision 107 authority;
- final Decision 105 lifecycle closure is claimed without canonical owner evidence.
