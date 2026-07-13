---
summary: "Accepts an immutable semantic release supply chain and one named-canary adoption protocol with owner-issued authority, deterministic ROCS verification, and fail-closed production gates."
read_when:
  - "Implementing Decision:53 semantic release contracts."
  - "Implementing the first bounded production semantic consumer."
  - "Reviewing semantic publication, activation, evidence, or rollback authority."
type: "adr"
status: "accepted"
---
# ADR — Semantic Release and Single-Canary Adoption Protocol v0

## Decision

Accept the target architecture from AK decision `53` and corrected semantic-release revision v13:

1. The semantic supply chain is `authored → released → desired → adopted → used`; those states are immutable and non-interchangeable.
2. Semantic identity is a closed `semantic-release-coordinate.v0`, separate from executable trust, consumer intent, materialization, activation, generation, delivery, and evidence linkage.
3. The semantic owner alone owns namespace policy, owner sets and predicates, compatibility/lifecycle decisions, trust roots and revocation, release approval, publication, withdrawal, and publication revocation.
4. ROCS owns deterministic compilation, complete-tree verification, projection, materialization, bounded receipts/errors, and offline protocol validation. ROCS cannot self-approve semantic meaning or consumer consent.
5. Agent Kernel alone owns canonical decision, task, and evidence lineage. It does not store ontology bytes or issue semantic-owner or consumer-owner facts.
6. The consumer owner alone owns intent, acceptance, activation, deactivation, and rollback for its repository. Pi may attest delivery but cannot authorize adoption or claim influence.
7. Authority enters deterministic verification through owner-specific, locally pinned acquisition capabilities and owner-store read receipts. The collator is transport-only. Historical artifact integrity and current authorization are separate predicates.
8. Publication, activation, rollback, and evidence use append-only state machines with canonical heads, exact predecessor/CAS relations, immutable history, typed recovery, and fail-closed revocation/currentness.
9. Protocol v0 is bounded to exactly `softwareco/pi-canary-consumer` identity revision `3` and one operator-named canary. Any second consumer, rename, broader canary, default, startup, or fleet posture requires a new protocol and decision.
10. `live_acquisition_implemented=false` remains mandatory until separately authorized implementation and validation establish the live capability boundary.

## Accepted normative artifacts

Primary:

- `docs/project/semantic-release-capsule-and-consumer-adoption-protocol-v0.md`
- `docs/project/semantic-release-v0/protocol.schema.json`
- `docs/project/semantic-release-v0/invariants.md`
- `docs/project/semantic-release-v0/golden-fixtures.json`
- `docs/project/semantic-release-v0/differential-fixtures.json`
- `docs/project/semantic-release-v0/differential-fixtures-shard-000.json`
- `docs/project/semantic-release-v0/differential-fixtures-shard-001.json`
- `docs/project/semantic-release-v0/differential-fixtures-shard-002.json`
- `docs/project/semantic-release-revision-v13.md`

Conflict adjudication:

- `docs/project/semantic-release-many-of-the-greats-conflict-resolution-v8.md`
- `docs/project/semantic-release-many-of-the-greats-conflict-resolution-v9.md`

Controlling review closure:

- `docs/project/semantic-release-rereview13-final-synthesis.md`

Accepted machine-evidence inventory:

- 54 closed protocol types;
- 122 golden object preimages and 2 raw preimages;
- 25 rules, 19 authority-bearing, and 352 role mappings;
- 150 authority edges;
- 390 differential cases and 10 raw lexical cases;
- three authenticated, sub-16-MiB shards;
- aggregate differential digest `a364e8c3d964641adf5d445d9bc7782a35fb2cc38c0d8223e176292508496767`.

## Authority split

| Concern | Owner |
|---|---|
| Ontology meaning, namespace lifecycle, compatibility, trust, release approval, publication | semantic owner / ontology owner |
| Deterministic build, complete-tree verification, materialization, receipts, protocol validation | ROCS |
| Canonical decisions, tasks, evidence, revocation and supersession lineage | Agent Kernel |
| Repository intent, acceptance, activation, deactivation, rollback | consumer owner |
| Prompt-run delivery/suppression/failure attestation | Pi |
| Recovery execution under an accepted owner request | independently pinned recovery controller |
| Empirical outcome analysis | DSPx/Oracle |

Joining facts across these owners does not transfer issuance authority.

## Consequences

### Positive

- Semantic versions permanently bind one immutable capsule and complete source/payload/archive/projection identity.
- Compatibility, SemVer, lifecycle, tombstones, approval thresholds, trust rotation/revocation, and publication recovery are executable contracts rather than prose assertions.
- Python and Node independently validate the same closed corpus without network or shared implementation imports.
- Owner-issued facts, canonical currentness, deterministic derivation, and terminal trust pins remain distinct and auditable.
- Materialization, activation, ROCS generation, Pi delivery, AK linkage, and empirical evidence cannot be conflated.
- Rollback supports semantic, runtime, disable, combined, partial-failure, and idempotent recovery paths with immutable typed history.
- Transport is no-follow, bounded, hash-complete, sharded, deadline-limited, depth-limited, and offline.

### Costs

- V0 deliberately supports only one named canary and rejects broader adoption.
- Live owner-capability acquisition, signing/key distribution, and crash-safe implementations require substantial owner-specific work.
- Complete proof bundles and differential fixtures are large and require deterministic sharding.
- Every authority expansion requires explicit protocol and decision work rather than configuration drift.

## Implementation obligations

Before implementation begins, Decision `53` must carry accepted post-ADR:

- implementation plan;
- validation/rollout/rollback plan;
- owner-scoped fan-out and tasks linked as `post_adr_execution`;
- reevaluation of concrete production dependencies.

Implementation must preserve:

- `live_acquisition_implemented=false` until the separately reviewed activation gate;
- owner-specific capability/read boundaries and AK-exclusive task authority;
- exact Python/Node schema, digest, manifest, registry, source-audit, shard, and mutation-descriptor agreement;
- no network, ambient wrapper, model, or mutable `dist/` authority;
- no publication, materialization, activation, delivery, or rollback claim without its complete current authority graph;
- the one-consumer, one-operator-named-canary v0 boundary;
- receipt/history roots outside replaceable semantic and runtime roots;
- deterministic bounded resource, deadline, no-follow, and process effects.

## Deferred gates

This ADR does **not** authorize:

- live owner capability provisioning or authenticated owner-store reads;
- semantic release publication;
- consumer materialization or activation;
- a canary identity or consumer consent;
- explicit-search, automatic-preflight, startup, default, or fleet behavior;
- signing/key infrastructure;
- production crash-recovery claims;
- task creation or implementation fan-out;
- ontology mutation.

Those require separately authorized implementation, validation, owner consent, evidence, and authoritative AK unblocking.

## Rejected alternatives

- mutable `latest` semantic state;
- tool/package version as semantic identity;
- ROCS, AK, Pi, or a consumer self-approving semantic release;
- one receipt combining intent, bytes, activation, generation, delivery, and influence;
- caller-issued cross-owner snapshot facts;
- generic context values or generator defaults as canonical authority;
- rollback assertions without locally available, independently usable targets;
- treating one successful canary as a default or fleet gate;
- unbounded or network-dependent fixture validation.

## Rollback and supersession

Before implementation, rollback is semantic: supersede this ADR and retain current production behavior.

During implementation, any owner-boundary, currentness, determinism, resource-limit, crash-safety, or rollback failure stops before activation and preserves/restores prior state under the accepted transaction protocol.

After a future named-canary activation, rollback is owned by the consumer owner and must use the predeclared semantic/runtime/disable target under the independent recovery controller. Publication withdrawal or revocation remains separately owned by the semantic owner.

This ADR can be expanded only by a later accepted decision and superseding ADR; protocol v0 itself cannot be widened in place.
