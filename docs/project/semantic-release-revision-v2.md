---
summary: "Decision 53 revision v2 blocker map and dual-language machine-packet evidence."
read_when:
  - "Rereviewing Decision 53 after semantic-release-rereview-synthesis-v1."
type: "revision_note"
status: "proposed_for_fresh_review"
decision: "53"
rfc_revision: "semantic-release-revision-v2"
review_basis: "semantic-release-rereview-synthesis-v1"
---

# Decision 53 — Semantic Release Revision v2

## 1. Posture

Revision v2 addresses the finite eleven-blocker set in [`semantic-release-rereview-synthesis-v1.md`](semantic-release-rereview-synthesis-v1.md). It submits a revised RFC and machine packet for fresh strict review. It does **not** declare `ready_for_adr`, accept an ADR, authorize implementation, issue a semantic release, approve publication, consent for a consumer, activate a canary/default/fleet gate, mutate ontology, or unblock Decision 53 in AK.

The controlling legal state remains proposal/review pending until an authorized reviewer closes it. Fixtures and validator passes are contract evidence only.

## 2. Finding map

| # | Synthesis blocker | Revision-v2 closure surface | Positive fixtures | Negative/adversarial fixtures |
|---:|---|---|---|---|
| 1 | Closed owner policy/set/trust-root/rotation/revocation and threshold semantics | Closed `semantic-owner-policy`, `owner-set`, `approval-predicate`, `trust-root`, `trust-rotation`, and `trust-revocation` schemas; invariants §3 recomputes distinct active-owner threshold/unanimity and fail-closed rotation/revocation | `owner_policy`, `owner_set`, `approval_predicate`, `trust_root`, `trust_rotation`, `trust_revocation`; `threshold_two_of_three_accepts`, `valid_old_to_new_root_rotation` | `threshold_insufficient_rejected`, `revoked_owner_vote_rejected`, `rotation_not_bound_to_current_root`, `revoked_rotation_root_rejected` |
| 2 | Executable compatibility, conditions, overrides, deprecation/removal/tombstones, SemVer/lifecycle | Closed policy rule table, typed condition operators/operands, report, override, deprecation, removal, and tombstone objects; invariants §4 defines execution and exact version relation | `compatibility_policy`, compatible/conditional reports, override, deprecation/removal/tombstone records; minor/major/condition/lifecycle acceptance cases | patch-for-minor, minor-for-major, missing/false condition, early removal, tombstone reuse, and attempted identifier-reuse override |
| 3 | Publication transaction/journal/marker and status transition with stale CAS, replay, fork, withdrawal/revocation, recovery | Closed publication transaction, journal, commit-marker, publication, and discriminated status-transition schemas; invariants §5 fixes linearization and legal transitions | Fresh CAS, idempotent replay, committed withdrawal/revocation, recovery before/after linearization | Stale CAS, divergent fork, illegal status self-transition, committed-without-linearization |
| 4 | Exact capsule payload → consumer projection and capsule archive linkage | `semantic-payload-projection.v0` binds total exact path/mode/length/content projection; `semantic-capsule-archive-linkage.v0` binds complete archive, payload root, metadata, format; capsule/build/materialization link both | Payload, archive, consumer manifests; projection/archive records; exact projection acceptance | Consumer tree outside projection and archive-link drift return `projection_mismatch` |
| 5 | Axis-discriminated rollback, retain/revalidation/disable/combined/partial/failure/history heads | Closed semantic/runtime/no-prior/combined target union; typed active state, stages, and history heads; invariants §8 | Semantic retains runtime, runtime retains semantic with revalidation, no-prior disable, combined partial failure, failed unchanged state/head | Missing runtime revalidation, disable leaving semantics active, partial without failed stage, failed rollback changing typed history |
| 6 | Generation only from current activated/unrevoked/unsuperseded activation | Generation invariant §7.1 checks activation state and current head before generation | `generation_from_current_activation_accepts` | Revoked, superseded, and non-head activation cases return `activation_not_current` |
| 7 | `digest_mismatch` and real calendar-valid UTC outside annotation-only format | Error enum/precedence includes `digest_mismatch`; both validators independently recompute embedded digests; Python `strptime` round-trip and Node UTC component round-trip enforce Gregorian validity | Golden digest recomputation; `calendar_valid_utc_accepts` | Intentionally wrong capsule digest; impossible `2026-02-30T12:00:00Z` |
| 8 | Canonical AK decision identity/revision/state/ADR/scope/revocation and activation bindings | Closed `semantic-ak-decision-reference.v0` binds AK repository/runtime identity, decision revision/lifecycle, ADR, scope/revocation, target/evidence/rollback/stop; owner approval, intent, acceptance, activation and rollback bind its digest | Owner and consumer canonical AK references; exact activation binding | Rejected decision and changed stop-condition binding fail closed |
| 9 | Pi delivered/suppressed/failed variants and optional generation-only Pi receipt | Pi schema is a closed discriminated `oneOf`; AK linkage makes Pi digest nullable only while retaining generation link | All three Pi variants and both delivered/generation-only AK linkage | Delivered missing prompt, suppressed leaking prompt claim, failed missing error are schema-invalid |
| 10 | Split AK coordination from consumer-owner fan-out and name first non-authorizing consumer candidate | RFC §14 has separate AK coordination and consumer-owner lanes; names `softwareco/pi-canary-consumer` as one operator-named canary candidate with future scoped task contract | Owner-bound canonical task/decision/evidence linkage and consumer identity fixtures | RFC explicitly says candidate creates no task, consent, canary, default, or authority; self-certification remains fail-closed |
| 11 | Independent-language verification | `validate_fixtures.mjs` uses Node crypto and its own JCS/schema/link/rule implementation; it imports no Python and starts no Python subprocess. Python validator remains stdlib-only. | Both recompute all 58 golden object preimages/links and 35 accepted transition cases | Both reject 39 expected adversarial cases, including digest/date/transaction/authority/rollback attacks |

## 3. Machine packet changes

The revision-v2 packet contains:

- `protocol.schema.json`: generated closed Draft 2020-12 union for 37 protocol types;
- `invariants.md`: normative cross-object rules, operation state machines, precedence, retention, and legal membrane;
- `golden-fixtures.json`: 58 canonical objects, two raw preimages, and 23 exact digest-link assertions;
- `differential-fixtures.json`: 74 positive/negative cases (35 accepted transitions and 39 expected rejections);
- `schema_builder.py`: deterministic closed-schema builder;
- `generate_fixtures.py`: deterministic schema and fixture regeneration;
- `validate_fixtures.py`: stdlib-only Python schema/JCS/digest/link/adversarial validator;
- `validate_fixtures.mjs`: independent Node schema/JCS/digest/link/adversarial verifier.

The generator may share Python digest primitives with the Python validator because generation is not independent evidence. Independence is supplied by the Node verifier, whose domain table, JCS, SHA-256, schema walker, UTC parser, SemVer/lifecycle logic, CAS/recovery machine, projection checks, authority checks, and rollback checks are separately implemented.

## 4. Determinism and validation commands

From the repository root:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 docs/project/semantic-release-v0/generate_fixtures.py
PYTHONDONTWRITEBYTECODE=1 python3 docs/project/semantic-release-v0/validate_fixtures.py
node docs/project/semantic-release-v0/validate_fixtures.mjs

# Determinism: snapshot generated artifacts, regenerate, compare byte-for-byte.
tmp="$(mktemp -d)"
cp docs/project/semantic-release-v0/{protocol.schema.json,golden-fixtures.json,differential-fixtures.json} "$tmp"/
PYTHONDONTWRITEBYTECODE=1 python3 docs/project/semantic-release-v0/generate_fixtures.py
cmp "$tmp/protocol.schema.json" docs/project/semantic-release-v0/protocol.schema.json
cmp "$tmp/golden-fixtures.json" docs/project/semantic-release-v0/golden-fixtures.json
cmp "$tmp/differential-fixtures.json" docs/project/semantic-release-v0/differential-fixtures.json
rm -rf "$tmp"

node ~/ai-society/core/agent-scripts/scripts/docs-list.mjs --docs . --strict
git diff --check
```

Expected validator summary for this revision:

```text
schema: Draft 2020-12, 37 protocol types, all object shapes closed
golden: 58 object preimages and 2 raw preimages independently recomputed
chain: 23 exact digest links verified
differential: 74 cases (35 accepted transitions, 39 expected rejections)
result: PASS
```

## 5. Owner-boundary and coverage limits

- The packet defines protocol facts; it does not create owner facts. Semantic-owner policy/approval/publication remain on the semantic-owner surface. Consumer intent/acceptance/activation remain with each consumer owner. ROCS builds/verifies/generates only. AK links canonical authority records without storing semantic bytes. Pi records delivery outcome only. Empirical influence remains outside this protocol.
- The named consumer is a candidate for later planning only. No mutation to that repository, AK task, acceptance, activation, or rollout occurred.
- v0 remains unsigned local trust rooted in an independently provisioned owner-controlled pin. It does not defend a host where both verifier and root store are compromised.
- The packet specifies filesystem transaction requirements but does not demonstrate platform implementation or crash testing. Those require a separately authorized post-ADR implementation/validation plan.
- No source, tests, lockfile, ontology, runtime, or external owner surface is changed by this docs-only revision.

## 6. Requested rereview outcome

Reviewers are asked to evaluate whether the eleven finite blockers are contractually closed by revision v2. Until that review returns an authorized closure and the later Decision-53 membrane steps occur, the only lawful outcome is continued non-implementation.
