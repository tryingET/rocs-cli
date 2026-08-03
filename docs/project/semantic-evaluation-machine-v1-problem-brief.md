---
summary: "Decision 106 problem brief: the accepted Decision 105 projection is immutable execution evidence but does not contain the policy or subject bytes required for semantic evaluation."
read_when:
  - "Reviewing whether Decision 106 can construct a ROCS semantic-evaluation machine."
type: "problem_brief"
status: "proposed"
decision_id: 106
---
# Problem brief — Decision 106 semantic-evaluation constructibility

## Trigger

Decision 104 accepted an owner-bounded architecture: the semantic owner retains immutable policy meaning, DSPx owns only effects it mediates, ROCS owns deterministic evaluation under accepted meaning, Decision 53 retains publication/currentness, and AK retains lineage. The accepted Decision 104 ADR is preserved at Git commit `e319240d7de8d43f234c53558977248050507056`; it is not present on the current `main` tree and is cited by immutable commit identity rather than an absent working-tree path.

Decision 105 then accepted and implemented a DSPx-local execution-custody primitive. AK task `4614` accepted one exact synthetic projection at DSPx commit `1dfbfa138dffee810896d939e8344ae8feb00537`:

- projection length: `1810` bytes;
- projection SHA-256: `43cb523b3787726956f331ea0917fd55757cf317a13815cd6f0f97c8b9eb7206`;
- projection-schema SHA-256: `d42569781d23c625627d92a9f37ea9c26211c92c403b0dcdb45b0360c386c532`.

The byte gate is accepted and sufficient to initiate a separate Decision 106 owner review. It is not Decision 106 authority, and the Decision 105 owner has reported that final lifecycle closure is not yet explicitly attached. Decision 106 therefore may rely only on the exact accepted byte gate, not on a claim that Decision 105 is fully closed.

## Contradiction

The projection is execution evidence, not a semantic subject:

- `input_coordinate.disclosure_posture` is exactly `digest_only_no_raw_access_right`;
- the evaluation request, input, return/failure, candidate, receipt, manifest, and trace are represented by digests rather than their preimages;
- every `non_authority` field is exactly `false`, including `semantic_meaning` and `deterministic_verdict`;
- no semantic-owner policy artifact, policy identity, predicate set, verdict vocabulary, precedence, or currentness proof is present;
- the generic schema proves shape only and carries no authenticated owner acceptance or attempt-eligibility proof.

ROCS can reproduce the accepted fixture identity and parse its shape. It cannot inspect or evaluate bytes it does not have, turn a digest into its preimage, choose semantic predicates for another owner, or infer that an observed return is a semantic pass.

## Required outcome

Decision 106 must decide whether a truthful deterministic semantic-evaluation interface is constructible from the accepted inputs. Review must not force an ADR merely because a prerequisite fixture exists.

A constructible interface would require, at minimum:

1. immutable semantic-owner policy bytes with owner identity, scope, policy digest, canonicalization, closed predicates, verdict vocabulary, and precedence;
2. the exact authorized subject preimages that policy evaluates;
3. typed digest-domain and canonicalization rules joining each preimage to the Decision 105 projection;
4. owner-granted acquisition/read authority for those preimages;
5. authenticated producer eligibility beyond generic JSON Schema shape;
6. generated positive/negative vectors that independently reproduce the same verdict.

None of those semantic inputs is supplied by the accepted Decision 105 projection-byte gate.

## Non-goals

This slice does not implement a conformance checker, evaluation runtime, CLI, policy language, ontology change, DSPx change, Decision 53 adapter, Decision 107 artifact, publication/currentness path, provider/model execution, network access, dogfood, activation, or production behavior.
