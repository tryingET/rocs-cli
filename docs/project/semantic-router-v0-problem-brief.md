---
summary: "Problem boundary for an abstaining semantic router after the frozen Decision 98 B0 failure."
read_when:
  - "Designing or reviewing semantic-router-v0."
type: "problem_brief"
status: "draft"
---
# Semantic router v0 problem brief

## Decision question

Should ROCS add a separately versioned deterministic semantic router that evaluates ontology-owned admission and concept-support policy while preserving `rocs-lexical-v0` unchanged as diagnostic candidate generation?

## Triggering evidence

Decision 98 B0 is immutable historical evidence:

- preregistration commit: `286773ee6a88b9fd2276f8008898c57ff9a073b9`;
- lock SHA-256: `32205d30e6bdbe78c1de9c4df7068528b5ff6ff1757cba7ea1e67494d6fe0dd2`;
- report commit: `0a9d9eed00c4c2875d6a7dd870b8978032c95875`;
- report SHA-256: `a136f0eec0a72e068af058ec8521f8095ba48ad11714644e9e87a921096d67ba`.

The frozen run passed deterministic repeat, timeout, latency, overall recall@3, and every applicable-stratum recall floor. It failed:

- MRR: `0.8458333333333334 < 0.85`;
- null rejection: `0.10 < 0.90`.

Nine of ten null prompts returned candidates. High lexical scores did not establish applicability: null N02 scored `1000`, N05 `850`, and N04 `800`. Legitimate queries could be weak or absent: P04 had no relevant concept among candidates topping at `150`, while A06 returned none. A global score or margin threshold therefore cannot separate applicability from non-applicability on the observed data.

The report remains failed evidence. It is not a development set, tuning set, regression target, or fresh acceptance gate.

## Category error

The current path conflates three distinct decisions:

1. **Admission:** whether the query has reviewed support inside a governed semantic domain.
2. **Candidate generation:** which concepts have lexical evidence.
3. **Adjudication:** whether supported concepts are complete, conflicting, ambiguous, or safe to route.

`rocs-lexical-v0` performs candidate generation and retrieval classification. Its accepted protocol explicitly says candidates do not certify semantic relevance. Treating non-empty candidates as applicability violated that boundary.

## Required outcome

The target architecture must:

- abstain when explicit domain support is absent;
- preserve operational errors as errors rather than abstentions;
- preserve the existing discovery protocol, digests, golden fixtures, and direct CLI behavior byte-for-byte;
- keep lexical candidates available as diagnostics without allowing scores or margins to authorize routing;
- require positive, ontology-owned concept support before selection;
- expose conflicts and ambiguity without deterministic tie-breaking masquerading as confidence;
- keep consumer prompt projection separate from ROCS semantic evaluation;
- remain offline-first, deterministic, bounded, and digest-addressed;
- remain development-only until a new uncontaminated holdout passes and downstream activation is separately authorized.

## Non-goals

Semantic-router-v0 does not:

- tune, modify, or rerun Decision 98 B0;
- change `rocs-lexical-v0` weights, threshold, result schema, or retrieval states;
- introduce embeddings, providers, models, network access, or probabilistic inference;
- claim universal out-of-domain truth;
- automatically inject prompt context;
- author ontology meaning inside ROCS;
- activate a production consumer or close Decision 98 KES learning.

## Authority split

- The exact ontology/semantic owner authors, reviews, publishes, and withdraws concrete routing clauses and exclusions.
- ROCS owns policy-language mechanics, validation, deterministic interpretation, and receipts—not policy approval.
- The exact consumer owner owns adoption intent, suppression policy, activation, deactivation, and rollback.
- Pi, where used, owns bounded invocation, timeout, rendering, and delivery/suppression/failure attestation.
- AK owns decision, task, evidence, lineage, and coordination records only.
- DSPx/Oracle or another named independent empirical owner controls sealed acceptance analysis.

## Success condition

A successful repair is not a higher null-rejection score on B0. It is a separately versioned architecture whose contracts make admission, candidate evidence, adjudication, errors, and consumer projection independently testable—and whose acceptance evidence comes from a new sealed corpus and holdout that never informed its design.
