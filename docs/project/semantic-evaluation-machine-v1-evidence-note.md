---
summary: "Exact producer evidence and authority gaps controlling Decision 106."
read_when:
  - "Checking the evidence behind Decision 106 constructibility review."
type: "evidence_note"
status: "proposed"
decision_id: 106
---
# Evidence note — Decision 106 semantic-evaluation machine

## Canonical workflow evidence

- Decision `104`: accepted owner-bounded architecture; AK outcome `accepted`. Its accepted ADR exists in Git object `e319240d7de8d43f234c53558977248050507056:docs/adr/2026-08-03-owner-bounded-semantic-evaluation.md`, outside current `main`. The controlling split remains: semantic owner = meaning; DSPx = mediated execution evidence; ROCS = deterministic evaluation under accepted meaning; Decision 53 = publication/currentness; AK = lineage.
- Decision `105`: AK outcome `accepted`; DSPx execution-custody implementation accepted at commit `cc6c80678482e0ff46cd4252f4bd5cebfe78bab1`, tree `ab35a0844aa3892eff76100038ebb693da44e832`.
- Task `4614`: `done`, outcome `accepted_and_canonical`; exact projection-byte acceptance commit `1dfbfa138dffee810896d939e8344ae8feb00537`, tree `b7add87a3e9e437b6a69c937ce996a22146cf76e`.
- Decision `106`: repo-scoped, `review_pending`, with no predecessor review artifacts before task `4618`.
- Decision `107`: remains `review_pending` with no artifacts or linked tasks. Decision 106 work grants it no authority.

The Decision 105 owner subsequently reported that implementation and byte acceptance are complete but final Decision 105 lifecycle closure is not explicitly recorded. This Decision 106 review treats task `4614` as an accepted producer-byte prerequisite only.

## Independently reproduced bytes

From DSPx `origin/main` at `1dfbfa138dffee810896d939e8344ae8feb00537`:

| Artifact | Observed identity |
|---|---|
| Exact JSON projection preimage | `1810` bytes; SHA-256 `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206` |
| Projection schema | `8227` bytes; SHA-256 `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532` |
| Verification manifest | SHA-256 `895088932e697e4b181c1e3280cc234f4b489011f488a6310289ff3498a671b5` |

The exact projection parses as JSON with all fifteen required top-level members. It is an `original` attempt with observed `return`. All nine `non_authority` members are `false`.

## What the projection proves

For the one accepted fixture, exact whole-object hashing proves byte identity with the accepted record. Schema validation can prove closed structural conformance. DSPx evidence records local validation, durable start, direct return observation, local sealing, and fixed nonclaims under its accepted threat model.

It does not prove:

- raw input, evaluation-request, output, failure, policy, candidate, receipt, manifest, or trace preimages;
- a right for ROCS to acquire any missing preimage;
- semantic-owner policy identity, meaning, provenance, approval, or currentness;
- a semantic verdict or that an observed return is a pass;
- executed provider/model identity, external effects, publication, promotion, governance, or Decision 53 compatibility;
- generic producer acceptance for arbitrary schema-valid projections.

## Substitution evidence

The generic Decision 105 schema validates field shape and cross-field null/outcome relations. It does not include the task `4614` acceptance identity, implementation commit/tree, projection whole-object hash, terminal seal, verification-manifest preimage, owner signature, or authenticated acquisition receipt. Another object can satisfy the schema while carrying arbitrary well-formed digests.

The accepted fixture is therefore usable only under exact byte identity. General projection eligibility requires a later accepted producer-authentication contract; schema conformance alone is not eligibility.

## Excluded negative evidence

- Decision 98 B0 is a frozen valid failure and is not a Decision 106 input, fixture, tuning source, or retry target.
- Rejected Decision 103 R2 and the rejected 271 KB Decision 104 global-machine packet remain immutable negative evidence.
- A digest, signature, receipt, passing test, Git commit, or AK record binds facts within its contract; none supplies missing semantic policy or raw subject bytes.
