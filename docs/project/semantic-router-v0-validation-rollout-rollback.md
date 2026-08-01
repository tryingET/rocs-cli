---
summary: "Falsification, rollout, and rollback contract for semantic-router-v0."
read_when:
  - "Planning implementation or evidence for semantic-router-v0."
type: "validation_rollout_rollback"
status: "proposed"
---
# Semantic router v0 validation, rollout, and rollback

## Evidence rule

Decision 98 B0 is sealed historical evidence. Its corpus, prompts, labels, row scores, failures, aliases, and floors may not be used for:

- policy authoring;
- feature or clause selection;
- threshold selection;
- regression acceptance;
- release gating;
- fresh evidence claims.

B0 may be used only to state the already-established failure class: deterministic lexical candidate generation can over-route. The router must never be executed against B0 as a fresh acceptance test.

## Validation phases

### V0 — Contract and compatibility

Before semantic evaluation:

- new schemas validate and reject unknown fields;
- canonical digests and orderings pass Python and independent Node golden verification;
- malformed requests, policies, witnesses, joint routes, and results fail closed;
- existing discovery source behavior, schemas, generated assets, golden fixtures, differential fixtures, capabilities, and direct CLI output remain unchanged;
- no network, provider, model, embedding, or ambient environment input exists;
- repository full gate passes.

### V1 — Visible development set D

D is visible to implementers and may be used for clause authoring and defect correction.

Minimum:

- 360 semantic cases, 30 per stratum;
- corpus distinct from B0 with no B0 concept ID or document hash;
- at least 60 concepts;
- no concept supplies more than five applicable cases;
- explicit policy identity and digest.

Strata:

Applicable:

1. exact label or declared alias;
2. independently authored paraphrase;
3. explicit joint-route intent;
4. near-neighbor concepts requiring discriminating evidence;
5. sparse/noisy Unicode and benign typo input;
6. indirect task language with reviewed support.

Null/adversarial:

7. clearly out of domain;
8. lexical collision/polysemy;
9. in-domain language with no owned concept;
10. negated, quoted, or metalinguistic mention;
11. high-overlap boilerplate and decoy terms;
12. irreducible ambiguity or conflicting intent.

D results support implementation only. They confer no release claim.

### V2 — Sealed acceptance set U

U is owned by an independent custodian and remains inaccessible to implementers until policy, runtime, evaluator, metrics, floors, and stop rules are immutable.

Minimum:

- 600 semantic cases, 50 per D stratum;
- same corpus-diversity rules as D;
- no B0 or D query, target ID, document hash, or prompt-template derivative;
- two independent annotators and one adjudicator;
- no router output observed before labels freeze.

Required labels:

- expected action: `route | abstain | error`;
- required selected IDs;
- acceptable selected IDs;
- forbidden selected IDs;
- ambiguity or exclusion rationale.

Dataset readiness:

- Cohen's kappa for expected action `>= 0.80`;
- mean set Jaccard for applicable labels `>= 0.80`;
- every disagreement adjudicated before locking.

Failure of annotation readiness is indeterminate, not a router failure.

### V3 — Sealed operational challenge set O

At least 96 cases, 12 per class:

1. malformed and unknown schemas;
2. empty, punctuation-only, and byte-limit boundaries;
3. identity, digest, algorithm, and policy mismatches;
4. unavailable, incompatible, exhausted, and timeout states;
5. symlink, alias, root escape, and duplicate-ID inputs;
6. controlled snapshot and concurrency changes;
7. output collision and private-temp cleanup failures;
8. locale, enumeration, cache-state, and repeat metamorphics.

Controlled fault injection is evaluated behavior. Uncontrolled environment drift is indeterminate.

## Anti-leakage

Before U locks, reject:

- exact byte or NFKC-casefold query overlap with B0 or D;
- identical token multisets;
- B0 target IDs and corpus document hashes;
- prompt-template transformations of B0 cases.

Token-set Jaccard above `0.80` or character-five-gram Jaccard above `0.85` requires independent adjudication. Custodians attest that labels were created without router outputs. U row details remain sealed until the verdict is fixed.

Any premature access to U prompts, labels, or row output invalidates U. A replacement set and new preregistration are required.

## Metrics and proposed acceptance floors

These floors are design proposals, not B0-derived estimates. They may change only before any U/O observation.

### Semantic safety

| Gate | Floor |
|---|---:|
| Overall null false-route rate | `<= 3/300` and one-sided 95% Wilson upper bound `<= 2.5%` |
| Negated/metalinguistic false routes | `0/50` |
| Irreducible-ambiguity false routes | `0/50` |
| Selective route precision | point `>= 97%` and one-sided 95% Wilson lower bound `>= 94%` |
| Error/unavailable/exhausted converted to route or abstain | `0` |

### Utility and anti-trivial-abstention

| Gate | Floor |
|---|---:|
| Correct-route coverage over applicable cases | `>= 80%` |
| Each applicable stratum correct-route coverage | `>= 70%` |
| Exact label/alias positive control | `>= 49/50` |
| End-to-end complete recall@3 with abstentions scored zero | `>= 80%` |
| End-to-end MRR with abstentions scored zero | `>= 0.80` |
| Selected-ID precision on routed applicable cases | `>= 97%` |

### Determinism and operation

| Gate | Floor |
|---|---:|
| Byte-identical immediate repeat | `1.00` |
| Timeout rate | `0.00` |
| Policy/corpus/runtime mutation | `0` |
| Invalid result accepted | `0` |
| Cold p95 | preregistered from D before U |
| Warm p95 | preregistered from D before U |

All mandatory strata and operational classes must pass. No averaging may conceal a failed safety class.

## Evaluation identity

The U/O preregistration freezes:

- source and evaluator commits and trees;
- exact runtime, interpreter, dependency, base-Python, and native-library identities;
- schema and generated-asset digests;
- corpus and policy digests;
- D/U/O dataset digests;
- limits, metrics, floors, confidence method, and report path;
- exact output and transient mutation boundaries;
- exact one-shot command and rollback procedure.

The evaluator runs once. A failed semantic report is retained. An indeterminate effect is never mechanically retried.

## Decision rule

- **Pass:** every semantic, utility, determinism, compatibility, and operational gate passes; independent review accepts the immutable report.
- **Fail:** a well-formed report fails any numerical gate; retain it and stop without same-task policy or dataset changes.
- **Indeterminate:** identity drift, leakage, annotation unreadiness, uncontrolled timeout, mutation, collision, cleanup failure, malformed output, or restoration uncertainty; stop and require a fresh authorized task.

Provider/model benefit work and consumer activation remain blocked even after a router pass until separately authorized.

## Rollout

1. Land development-only protocol/interpreter and compatibility tests.
2. Author D policy and fixtures through ontology-owner review.
3. Freeze and execute U/O under a fresh task.
4. If accepted, create an adopted semantic-release coordinate.
5. Run a no-injection consumer shadow that records route/abstain receipts only.
6. Review shadow evidence.
7. Open a separate decision for any Pi prompt projection.

No stage is implied by the previous stage.

## Rollback

Development rollback:

- remove or revert the additive router commit;
- existing discovery remains unchanged and available;
- no migration or data rewrite is required.

Shadow rollback:

- disable router invocation;
- delete only private transient state created by the shadow task;
- preserve immutable receipts and failed reports;
- verify normal Pi settings, executable, launcher, cache, and discovery behavior remain unchanged.

Adopted-coordinate rollback, if ever authorized:

- restore the previous semantic-release coordinate;
- retain the failed coordinate and evidence;
- do not rewrite or delete policy history.

## Stop conditions

Stop immediately on:

- any existing discovery fixture or byte output change;
- policy ownership ambiguity;
- B0-derived policy content;
- leaked U/O content;
- route selection without positive policy support;
- error converted to abstention;
- consumer override of abstention;
- unexpected network, provider, model, or normal Pi mutation;
- restoration uncertainty.
