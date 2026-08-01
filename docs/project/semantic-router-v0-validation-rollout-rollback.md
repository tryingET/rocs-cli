---
summary: "Falsification, rollout, and rollback contract for semantic-router-v0."
read_when:
  - "Planning implementation or evidence for semantic-router-v0."
type: "validation_rollout_rollback"
status: "proposed"
---
# Semantic router v0 validation, rollout, and rollback

## B0 contamination truth

Decision 98 B0 is immutable contaminated historical evidence, not unseen or sealed data. Its prompts, corpus, labels, scores, report, and failure rows are repository-readable.

This design wave deliberately consulted:

- B0 preregistration commit, lock, corpus, dataset, evaluator, and report;
- aggregate metrics and failed gates;
- row IDs and scores including N02, N04, N05, P03, P04, P06, and A06;
- the conclusion that score/margin admission is falsified on B0.

Exposure for the controller and exploration/review agents in tasks 4452/Decision 102 is `confirmed`. Future implementers, policy authors, dataset authors, annotators, adjudicators, and custodians must record `confirmed | possible | disproven` B0 exposure with evidence and date before participation.

B0 is permanently prohibited as:

- policy or clause source;
- feature, threshold, alias, or fixture source;
- development, regression, or release dataset;
- fresh router execution evidence;
- metric or floor estimator.

Any B0-derived policy content or acceptance coordinate invalidates the policy and requires replacement data, policy, and preregistration.

## Clause provenance

Every policy alternative carries exactly one record in the closed `semantic-routing-provenance.v0` manifest. The policy and request bind its digest. Records bind alternatives by `(clause_id, group_id, kind, canonical_value)` and contain:

- exact clause/group/alternative coordinate;
- exact semantic-owner repository, revision, source path, and source-text digest;
- author and creation time;
- owner review reference;
- B0 exposure declaration;
- D source case IDs, if development-derived;
- contamination scan receipt.

The provenance schema, digest preimage, canonical order, policy-authority equality, and omission/extra-record rules are normative in the protocol bundle. An independent contamination reviewer accepts the manifest before policy freeze. Renamed concepts, copied documents, translated scenarios, and semantic paraphrases of B0 are prohibited even when deterministic lexical overlap is low.

## Validation phases

### V0 — Contract and compatibility

Before any semantic dataset execution:

- every new object validates against the separate route schema and invariants;
- Python and independent Node verification agree on schema, canonical bytes, digests, ordering, matching, state matrices, and errors;
- malformed and non-canonical requests, policies, witnesses, joint routes, results, and nested discovery objects fail closed;
- every protected discovery-v0 file and payload in the RFC remains byte-identical;
- direct discovery output remains byte-compatible on a frozen compatibility corpus;
- no network, provider, model, embedding, environment file, or cache dependence exists;
- repository full gate passes.

V0 uses only conspicuously synthetic policy and corpus fixtures. It makes no real-domain routing claim.

V1–V3 specify mandatory evidence for a future adopted-policy protocol. Decision 102 does not authorize those stages, and v0 results carry no adoption authority for them.

### V1 — Visible development set D

D contains exactly 360 semantic rows: 30 in each of 12 strata, with 180 applicable and 180 null/adversarial rows.

Applicable strata:

1. exact label or declared alias;
2. independent paraphrase;
3. explicit joint-route intent;
4. near-neighbor concepts requiring discriminating evidence;
5. sparse/noisy Unicode and benign typo input;
6. indirect task language with reviewed support.

Null/adversarial strata:

7. clearly out of domain;
8. lexical collision/polysemy;
9. in-domain language with no owned concept;
10. negated, quoted, or metalinguistic mention;
11. high-overlap boilerplate and decoy terms;
12. irreducible ambiguity or conflicting intent.

Policy authors may inspect D and tune clauses from D under semantic-owner review. D results confer no acceptance or release claim.

### V2 — Untouched acceptance set U

U contains exactly 600 semantic rows: 50 per D stratum, with 300 applicable and 300 null/adversarial rows.

The semantic owner freezes the complete eligible corpus, concept inventory, meanings, and source coordinates before D policy work. Independent custodians construct and seal U before D rows, scenarios, templates, or outputs are disclosed to policy authors. U authors derive prompts independently from ontology source material while blind to D rows/templates, routing clauses, and router output. D authors are separate from U authors and custodians.

Applicable U rows are split in every applicable stratum:

- 25 query-holdout rows over concepts seen as D targets;
- 25 concept-holdout rows over concepts never used as D targets.

Policy authors may know the frozen concept inventory and semantic-owner source documents but never U prompts, labels, target assignment, or row output. The policy must cover owner meaning rather than U wording.

No concept supplies more than five applicable U rows. Author/template-family caps and seen/held-out allocations are locked before annotation.

### V3 — Untouched operational set O

O contains exactly 96 rows: 12 in each class:

1. malformed and unknown schemas;
2. empty, punctuation-only, and byte-limit boundaries;
3. identity, digest, algorithm, and policy mismatches;
4. unavailable, incompatible, exhausted, and timeout states;
5. symlink, alias, root escape, and duplicate-ID inputs;
6. controlled snapshot and concurrency changes;
7. output collision and private-temp cleanup failures;
8. locale, enumeration, cache-state, and repeat metamorphics.

Every O row freezes its fault-injection mechanism, expected action or error kind, expected safe envelope, filesystem invariants, cleanup state, and mutation allowance.

U and O are independently custodied by DSPx/Oracle or another named empirical owner. Their prompts, labels, and row outputs remain inaccessible to implementers and policy authors until the immutable verdict is fixed. Any exposure permanently retires the affected set and requires a replacement set and new preregistration.

## Dataset roles and independence

- Semantic owner: freezes ontology sampling frame and confirms adjudicated meaning without changing locked rows.
- Policy authors: use D only; no U/O access.
- U/O custodian: owns sampling, locking, execution input, and report publication; does not author policy.
- Two annotators: independent of implementation and policy authorship, blind to clauses and router outputs.
- Adjudicator: independent of implementation/policy, resolves every disagreement while blind to output.
- Implementers: receive only D and aggregate U/O verdict after execution.

Every row records unique ID, stratum/class, author/template family, semantic-owner source coordinates, expected action, allowed selected sets, rationale, and provenance.

## Anti-overlap procedure

Apply to B0, D, U, policy alternatives/exclusions/aliases, source examples, and prompt templates.

Compare:

1. exact UTF-8 bytes;
2. NFKC → full casefold → whitespace collapse;
3. exact normalized token sequence;
4. exact normalized token multiset;
5. token-set Jaccard;
6. normalized character-five-gram Jaccard;
7. manual semantic/template derivation.

Tokenization uses the frozen route tokenizer. Token-set Jaccard is `|A∩B| / |A∪B|`; two empty sets count as exact overlap. Five-gram Jaccard uses normalized Unicode code-point five-gram sets; strings shorter than five use the complete normalized string as one gram, and two empty strings count as exact overlap.

Reject automatically on exact bytes, normalized equality, token-sequence equality, token-multiset equality, known template derivation, B0 document-copy lineage, or B0 semantic scenario reuse. U also rejects every D scenario, translation, semantic paraphrase, and template derivation regardless of lexical similarity. Token Jaccard `>0.80` or five-gram Jaccard `>0.85` requires independent documented adjudication before lock.

Run the same duplicate/derivative checks within U. Record every comparison, adjudication, and waiver in a digest-bound contamination manifest.

## Annotation

U expected actions are fixed by stratum:

- strata 1–6: `route`;
- strata 7–12: `abstain`;
- no well-formed U row expects `error`.

O may expect `route | abstain | error`, fixed per row.

Custodians assign provisional strata but hide stratum and expected action from annotators. Annotators independently label action and allowed selected sets from semantic-owner sources. If adjudication contradicts a stratum's fixed action, dataset construction is indeterminate and the row is retired and replaced before lock; the stratum is not silently relabeled.

A routed row contains one or more exact `allowed_selected_sets`. A route is correct only when the actual selected set exactly equals one allowed set. Unlisted or forbidden selected IDs make the route incorrect. Abstain and error rows require an empty selected set.

For the two pre-adjudication U annotations:

- compute expected-action Cohen's kappa over all rows;
- require `kappa >= 0.80`;
- if expected agreement `p_e = 1`, readiness is indeterminate;
- for every row where either annotator chooses route, treat the other annotator's abstention as an empty set and compute set Jaccard;
- require mean set Jaccard `>= 0.80`;
- require raw expected-action agreement `>= 90%` independently in every stratum and seen/held-out subset;
- require mean routed-set Jaccard `>= 0.80` independently in every applicable stratum and seen/held-out subset;
- adjudicate every disagreement before lock without rewriting pre-adjudication metrics.

## Actual-action classification

Each row produces exactly one actual action:

- `route`: valid result state `single | multi` with non-empty selected set;
- `abstain`: valid no-selection result, including explicit ambiguity;
- `error`: valid operational error envelope, absent result, or structurally invalid result.

A malformed attributable result is also an automatic gate failure. Build the exact expected/actual confusion matrix.

Rules:

- an expected abstention returned as error is not a safe abstention;
- an expected route returned as error is not coverage;
- a null route is a false route regardless of selected IDs;
- an applicable abstention is a coverage miss;
- an applicable wrong selected set is a coverage miss and an imprecise route;
- an expected O error returned as route or abstain fails;
- no unexpected errors are allowed on well-formed U rows.

## Metrics and floors

These proposals are not B0-derived estimates. They freeze before U/O observation.

Let U contain 300 applicable rows `R` and 300 expected-abstain rows `A`. Let `q_i = 1` only when row `i` routes and its selected set exactly equals one allowed set.

### Safety

| Gate | Floor |
|---|---:|
| False routes on A | `0/300` |
| One-sided 95% Wilson upper bound for false-route rate | `<= 1.0%` |
| Successful abstention on A | `300/300` |
| False routes in every null stratum 7–12 | `0/50` and Wilson upper `<= 5.2%` |
| Unexpected errors on well-formed U | `0/600` |
| Correct routes / all actual routes | point `>= 97%`, Wilson lower `>= 94%` |
| Expected O error returned as route or abstain | `0` |

Use one-sided 95% Wilson without continuity correction and `z = 1.6448536269514722`. For successes `x` of `n`, `p=x/n`, denominator `d=1+z^2/n`, center `(p+z^2/(2n))/d`, radius `z*sqrt(p*(1-p)/n+z^2/(4n^2))/d`, lower `max(0,center-radius)`, and upper `min(1,center+radius)`. `n=0` is indeterminate. Use binary64 in the written evaluation order, compare full-precision values, and report 12 decimal places without gating on rounded values. Every Wilson gate names its exact numerator and denominator above.

### Utility and anti-trivial-abstention

| Gate | Floor |
|---|---:|
| Correct-route coverage `sum(q_i)/300` | `>= 80%` |
| Each applicable stratum `sum(q_i)/50` | `>= 70%` |
| Exact-label/alias correct routes | `>= 49/50` |
| Query-holdout correct-route coverage | `>= 80%` |
| Concept-holdout correct-route coverage | `>= 70%` |
| Exact selected-set precision on routed applicable rows | `>= 97%` |

Lexical MRR and recall are diagnostic only. Router selection is an unordered exact set; no MRR gate is defined. Abstention cannot pass utility gates.

### Determinism and operation

| Gate | Floor |
|---|---:|
| Byte-identical immediate repeat | `1.00` |
| Uncontrolled timeout rate | `0.00` |
| Policy/corpus/runtime mutation | `0` |
| Invalid result accepted | `0` |
| Every O class exact oracle | `12/12` |
| Cold/warm p95 | frozen from D before U/O |

Every mandatory stratum, seen/held-out subset, and O class passes independently.

## Identity and one-shot execution

The preregistration freezes source/evaluator commits and trees, runtime and native identities, schema/generated-asset digests, corpus/policy/provenance/D/U/O/contamination-manifest digests, limits, metrics, floors, Wilson method, report path, mutation boundaries, exact command, and rollback procedure.

U/O execution occurs once. Row output remains sealed until the report verdict is immutable.

## Outcome classification

Apply this mutually exclusive precedence:

1. **Indeterminate first:** any loss of evidence integrity or execution validity—annotation unreadiness, leakage, unauthorized exposure, identity drift, evaluator inability to classify output, malformed/incomplete report, uncontrolled environment timeout, uncontrolled mutation, collision, cleanup failure, restoration uncertainty, or independent review unable to accept evidence integrity. Stop without mechanical retry; no gate verdict is computed from invalid evidence.
2. **Semantic/operational fail second:** only when evidence is valid and the report is complete, failure of any numerical, semantic, utility, compatibility, protected-discovery, determinism, or controlled-O gate, including unexpected U error, route without support, error converted to abstention, or independent review that accepts evidence integrity but rejects the pass verdict. Retain the report and stop without same-task changes.
3. **Pass last:** only when evidence is valid, the report is complete, every mandatory gate passes, and independent review accepts both evidence integrity and the pass verdict.

Controlled O timeout/collision/cleanup injections are scored under step 2 against their frozen oracle. Uncontrolled occurrences are step-1 indeterminate. Every stop condition and review disposition maps through this precedence exactly once.

## Rollout

1. Accepted ADR may authorize only ROCS protocol/interpreter implementation with synthetic fixtures.
2. Separate architecture work defines an adopted-policy/publication protocol; Decision 102 does not authorize non-synthetic execution, and v0 results carry no adoption authority.
3. Separate semantic-owner task authors and reviews policy using D under that future protocol.
4. Separate empirical-owner task freezes and executes U/O.
5. Separate semantic-owner gate publishes an adopted coordinate with currentness/withdrawal proof.
6. Separate consumer-owner decision may authorize a no-injection shadow.
7. Separate consumer-owner decision and owner gate may authorize any prompt projection.

No stage is implied by the prior stage.

## Rollback

ROCS development rollback reverts the additive router commit. Existing discovery remains unchanged; no migration or data rewrite exists.

Any later owner-local rollback is owned by that consumer or semantic owner, preserves immutable receipts and failed reports, restores the previous adopted coordinate or disables invocation, and does not rewrite policy history.

## Stop conditions

Stop on any protected discovery change, policy authority ambiguity, B0-derived clause, U/O exposure, route without positive policy support, error converted to abstention, consumer override, unexpected network/provider/model/Pi mutation, or restoration uncertainty.
