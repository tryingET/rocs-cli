---
summary: "RFC for an additive deterministic abstaining semantic router over unchanged ROCS lexical evidence."
read_when:
  - "Reviewing the semantic-router-v0 architecture decision."
type: "rfc"
status: "proposed"
---
# RFC — Deterministic abstaining semantic router v0

## Status

Proposed for strict multi-lane review. No implementation or activation is authorized by this draft.

## Decision

Add a development-only `semantic-route` operation with new request, policy, result, invariant, and digest domains. The router evaluates ontology-owner-authored symbolic routing policy and preserves `rocs-lexical-v0` unchanged as diagnostic candidate evidence.

## Invariants

1. Existing semantic discovery source, schema, generated embedding, golden fixtures, differential fixtures, digests, CLI output, and tests remain behavior-compatible.
2. Router admission and selection require explicit positive policy evidence.
3. Lexical score, margin, candidate count, and retrieval classification never authorize routing.
4. No positive domain support means abstention, not an operational error and not a universal claim that the query is objectively out of domain.
5. Operational failures remain errors and never become abstentions.
6. Router policy meaning is authored by ontology/semantic owners. ROCS owns validation and deterministic interpretation only.
7. Consumers may suppress a route but may not override abstention, manufacture selected IDs, or rerank silently.
8. B0 is historical diagnosis only and is never executed against the router as acceptance evidence.
9. No provider, model, embedding, network, or automatic prompt projection exists in v0.

## Ownership

| Concern | Owner |
|---|---|
| Policy schema and deterministic interpreter | ROCS |
| Concrete domain, concept, joint-route, and exclusion clauses | Ontology/semantic owner |
| Adopted corpus-policy coordinate | Semantic-release owner |
| Invocation, timeout, validation, and operator projection | Consumer/Pi |
| Decision, task, evidence, rollout, rollback | AK/governance |
| Independent empirical analysis | DSPx/Oracle |

A policy file is data supplied to ROCS. Its presence does not transfer authority to ROCS to invent ontology meaning.

## Protocol family

New schemas:

- `semantic-route-request.v0`;
- `semantic-routing-policy.v0`;
- `semantic-route-effective-execution.v0`;
- `semantic-route-result.v0`.

New digest domains:

- `routing_policy`;
- `route_caller_request`;
- `route_effective_execution`;
- `route_result`.

New algorithm:

- router: `rocs-symbolic-router-v0`;
- diagnostic candidate algorithm: exactly `rocs-lexical-v0`.

Existing discovery capabilities remain unchanged. Router capabilities use a separate command and payload.

## Request

The closed request contains:

- schema;
- query;
- identity selector;
- profile;
- router algorithm;
- candidate algorithm;
- exact router and inherited discovery limits.

Development CLI shape:

```text
rocs route \
  --repo <corpus-root> \
  --routing-policy <exact-local-file> \
  --request-json - \
  --tool-kind development_runtime \
  --tool-manifest-digest sha256:<digest> \
  --json --no-index-cache --no-env-file
```

The policy file must be a regular non-symlink file beneath an explicitly supplied local root or an adopted release coordinate. V0 performs no remote resolution.

## Routing policy

The policy is a closed canonical object:

```json
{
  "schema": "semantic-routing-policy.v0",
  "policy_id": "core.review",
  "unicode_data": "15.0.0",
  "normalization": "nfkc-casefold-ws-v0",
  "domain": {
    "domain_id": "core",
    "admit_any": [],
    "exclude_any": []
  },
  "concepts": [],
  "joint_routes": [],
  "routing_policy_digest": "sha256:..."
}
```

### Clause grammar

A clause is a conjunction of named groups. A group is a disjunction of exact alternatives:

```json
{
  "clause_id": "core.validation.support.1",
  "all_of": [
    {
      "group_id": "operation",
      "any_of": [
        {"kind": "token", "value": "validate"},
        {"kind": "phrase", "value": "structurally sound"}
      ]
    },
    {
      "group_id": "object",
      "any_of": [
        {"kind": "token", "value": "ontology"},
        {"kind": "phrase", "value": "controlled concept files"}
      ]
    }
  ]
}
```

- `token` matches one exact normalized query token.
- `phrase` matches one exact contiguous normalized token sequence.
- A group matches when any alternative matches.
- A clause matches when every group matches.
- `*_any` matches when any contained clause matches.
- Clause and group IDs are globally unique inside the policy.
- Alternatives are duplicate-free after normalization.
- Empty domain `exclude_any` is allowed.
- Domain `admit_any` and every concept `support_any` are non-empty.
- No stemming, inferred synonym, regular expression, ambient stopword list, floating-point weight, embedding, or learned component exists.

### Concept policy

Each concept entry contains:

- exact `ont_id` present in the captured corpus;
- non-empty `support_any`;
- optional `exclude_any`.

Existing ontology `anti_examples` do not become router exclusions automatically. A routing exclusion requires a distinct clause ID, owner review, and new policy digest.

### Joint routes

Multi-concept selection is explicit rather than inferred from overlapping support:

```json
{
  "joint_route_id": "core.prompt-retention-plus-transmission.1",
  "ont_ids": ["core.PromptRetention", "core.ProviderTransmission"],
  "support_any": [],
  "exclude_any": []
}
```

- `ont_ids` contains two to eight unique corpus concept IDs sorted by UTF-8 bytes.
- A joint route matches only when its own positive clause matches, no joint exclusion matches, every selected concept has positive support, and none has concept exclusion.
- Multiple matching joint routes are ambiguous and abstain.
- Multiple supported concepts without exactly one matching joint route are ambiguous and abstain.

This prevents shared words from being misrepresented as complete multi-intent.

## Normalization and matching

Use the existing semantic protocol normalization boundary:

1. Unicode NFKC;
2. full casefold;
3. whitespace collapse;
4. Unicode letter/number tokenization.

Matching records canonical witnesses. When an alternative occurs multiple times, choose by:

1. lowest start-token index;
2. lowest end-token index;
3. `token` before `phrase` only when spans are identical;
4. UTF-8 byte order of normalized value.

Policy arrays and result arrays use closed deterministic orderings. The policy digest covers the canonical object with `routing_policy_digest` omitted.

## Evaluation algorithm

1. Capture and validate corpus and policy identities without following symlink escapes.
2. Validate request, limits, algorithms, tool identity, and digests.
3. Normalize and tokenize the query once.
4. Evaluate all domain positive and exclusion clauses.
5. If domain support and exclusion both match, abstain with conflict.
6. If exclusion alone matches, abstain with explicit exclusion.
7. If no positive domain support matches, abstain with no support.
8. Otherwise admit and evaluate all concept clauses.
9. Mark each concept supported, conflicted, or unsupported.
10. Any concept conflict relevant to a potential selection forces abstention.
11. If exactly one concept is supported, select it unless a conflicting joint route matches.
12. If multiple concepts are supported, select only when exactly one explicit joint route matches the exact selected set and no exclusion matches.
13. Otherwise abstain as ambiguous or unsupported.
14. Run unchanged lexical discovery for diagnostic candidates and retain its result digest or exact nested reference.
15. Add symbolically supported concepts absent from the lexical top-K as diagnostics with lexical score `0`.
16. Canonicalize, validate invariants, enforce result byte limit, and digest the result.

No numeric score influences steps 4–13.

## Closed reason taxonomy

Admission:

- `domain_support`;
- `no_domain_support`;
- `explicit_domain_exclusion`;
- `domain_support_exclusion_conflict`.

Routing:

- `admission_abstained`;
- `single_supported_concept`;
- `explicit_joint_route`;
- `no_concept_support`;
- `multiple_supported_without_joint_route`;
- `multiple_joint_routes`;
- `concept_support_exclusion_conflict`;
- `joint_route_exclusion`.

Operational errors retain existing safe categories and separate error envelopes.

## Result

The closed result contains:

- request, corpus, policy, tool, lexical-result, and effective-execution identities;
- algorithm identities;
- admission state, reason, clause IDs, and witnesses;
- routing state, reason, selected/supported/conflicted concept IDs;
- joint-route identity when used;
- deterministic evidence entries;
- diagnostic candidates and truncation;
- result digest.

States:

- admission: `admitted | abstained`;
- routing: `not_evaluated | single | multi | ambiguous | abstained`.

`selected_ont_ids` is non-empty only for `single` or `multi`. An abstained or ambiguous result never selects a concept.

## Resource limits

V0 hard maxima:

| Resource | Maximum |
|---|---:|
| Query bytes | `16,384` |
| Policy bytes | `4,194,304` |
| Concepts | `5,000` |
| Total clauses | `20,000` |
| Groups per clause | `16` |
| Alternatives per group | `32` |
| Normalized alternative bytes | `256` |
| Joint routes | `5,000` |
| Concepts per joint route | `8` |
| Evidence entries | `10,000` |
| Diagnostic candidates | `12` |
| Result bytes | `262,144` |
| Parser depth | `32` |
| Collection items | `20,000` |

Limit exhaustion is `resource_exhausted`, never abstention.

## Security and determinism

- No network or environment file.
- No index cache in acceptance evaluation.
- Closed environment and exact runtime identity.
- No symlink policy or corpus inputs.
- Byte/mtime or stronger inventory checks before and after capture.
- Unknown fields, duplicate IDs, duplicate normalized alternatives, invalid order, digest mismatch, and unsupported Unicode coordinates fail closed.
- Hostile clause text and evidence remain JSON data and never become control instructions.
- Errors expose safe bounded messages only.

## Compatibility

The implementation must prove that all existing discovery golden fixtures and direct CLI bytes remain unchanged. Router support is additive:

- new source modules;
- new schema and generated embedding;
- new golden and differential fixtures;
- new CLI command and contract entry;
- new tests and independent verifier.

No existing discovery digest domain, capability payload, result schema, or algorithm vocabulary changes.

## Rollout boundary

V0 is development-only. It cannot be adopted or projected into Pi until:

1. implementation and compatibility gates pass;
2. a new uncontaminated visible-development corpus is used for authoring;
3. a sealed acceptance corpus and operational challenge set pass every preregistered gate;
4. independent review accepts the report;
5. a separate consumer adoption decision authorizes projection.

## Alternatives rejected

- score/margin threshold tuning;
- in-place discovery protocol changes;
- dense retrieval as an admission substitute;
- consumer-specific hidden heuristics;
- converting errors into abstention;
- using B0 as a regression acceptance target.

## Open review gates

Strict review must resolve:

- whether separate policy files are the correct development coordinate;
- whether explicit joint routes are sufficient and non-explosive;
- whether the resource maxima are defensible;
- whether a nested lexical result or digest reference best preserves lineage;
- whether ROCS interpretation of owner-authored clauses preserves the accepted source-owner boundary.
