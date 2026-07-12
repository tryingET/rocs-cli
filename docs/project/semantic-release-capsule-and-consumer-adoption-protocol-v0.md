---
summary: "Cross-owner RFC for immutable semantic release coordinates, consumer desired state, adoption receipts, use evidence, compatibility, and rollback."
read_when:
  - "Defining production semantic identity for ROCS consumers."
  - "Reviewing the production dependency of decision:52."
type: "rfc"
status: "proposed"
---

# RFC — Semantic Release Capsule and Consumer Adoption Protocol v0

## Status

This is a proposal-stage cross-owner RFC opened to give decision `52` a concrete production dependency. It authorizes no semantic release, AK mutation beyond its own decision record, consumer adoption, implementation task, rollout, or default change.

## Problem

A wrapper, mutable `dist/`, manifest version, ROCS version, CI gate, or vendored runtime does not prove which governed semantic generation a consumer desired, adopted, used, or can roll back to.

The missing supply chain is:

```text
authored -> released -> desired -> adopted -> used -> rolled back when required
```

## Decision requested

Approve a target architecture with four separate facts:

1. an immutable **semantic release capsule** issued under semantic-owner approval;
2. a consumer-owned **semantic dependency intent** selecting an exact release coordinate and rollback target;
3. a ROCS-emitted **semantic adoption receipt** proving exact local materialization and verification;
4. a **semantic use receipt** referencing the exact release, discovery result, and bounded pack when semantics materially influenced work.

## Owner split

| Fact | Owner |
|---|---|
| Ontology meaning, compatibility policy, release approval | `core/ontology-kernel` and semantic owners |
| Deterministic compilation, packaging, verification, discovery, adoption/use receipt emission | `core/rocs-cli` |
| Desired state, rollout decision, task/decision lineage, evidence references | AK plus consumer owner |
| Prompt/session delivery | Pi adapter |
| Empirical behavior analysis | DSPx/Oracle |

AK references semantic-owner and ROCS facts; it does not become ontology storage. ROCS observes and verifies desired state; it does not choose it.

## Reserved production coordinate

The single production term is:

```text
semantic_release_coordinate
```

Illustrative shape:

```text
ai-society.core@X.Y.Z+sha256:<capsule-digest>
```

The capsule digest identifies semantic release content only. ROCS executable/tool trust is a separate independently pinned coordinate. Consumer adoption intent is a third separate fact.

## Capsule content

A `semantic-release-capsule.v0` must bind:

- semantic namespace and semantic version;
- source revision and complete source digest;
- semantic-owner approval decision/reference;
- compilation contract and required ROCS protocol versions;
- compiled records and discovery index;
- compatibility report against the prior accepted release;
- deprecation/removal facts;
- whole-capsule digest;
- rollback predecessor coordinate.

A capsule is immutable and content addressed. Signing infrastructure is deferred; v0 trust may use an owner-approved pinned digest distributed through an accepted local process.

## Consumer intent

A `semantic-dependency-intent.v0` declares:

- consumer identity;
- exact desired semantic release coordinate;
- compatible protocol range;
- rollout posture: canary, explicit-search default, automatic-preflight default, or fleet;
- exact rollback coordinate or explicit no-prior-generation fallback;
- owner decision reference;
- independently pinned ROCS runtime/tool coordinate.

Intent is not adoption proof.

## Adoption receipt

A `semantic-adoption-receipt.v0` records:

- intent digest;
- capsule coordinate/digest;
- ROCS tool coordinate/digest;
- exact materialized file manifest and digest;
- verification and compatibility outcomes;
- consumer repository identity;
- timestamp as audit metadata, excluded from semantic identity;
- prior generation and rollback readiness;
- receipt digest.

ROCS emits the fact; AK may reference it as evidence.

## Use receipt

A `semantic-use-receipt.v0` records:

- adopted release coordinate;
- discovery request/result and effective-execution digests;
- selected exact ontology IDs, if any;
- bound pack digests, if any;
- task/session evidence references without making session logs canonical;
- outcome: `matched`, `ambiguous`, `no_match`, `not_applicable`, or `unavailable`;
- receipt digest.

A use receipt proves which semantic inputs were exposed, not that the model interpreted them correctly.

## Compatibility and rollback

Compatibility classification is semantic-owner policy, compiled and verified deterministically by ROCS. Required states are:

```text
compatible | conditionally_compatible | breaking | unknown
```

Rollback has two independent axes:

- semantic release N -> prior accepted coordinate, or disable-to-current behavior when no prior adopted generation exists;
- ROCS/Pi package/runtime -> prior independently pinned generation.

Neither rollback may rewrite historical receipts.

## Discovery relationship

Decision `52` may accept development-only discovery architecture independently. Production `semantic_release_coordinate` support remains rejected until this decision reaches ADR acceptance and post-ADR planning.

## Options considered

- **Mutable latest semantic state:** rejected; no replay or rollback identity.
- **Tool version as semantic identity:** rejected; merges executable and meaning.
- **AK stores ontology bytes:** rejected; owner drift.
- **One capsule plus separate intent/receipts:** proposed; joins owners without merging them.

## Non-goals

- online registry;
- automatic upgrades;
- universal enforcement;
- signing/key infrastructure;
- embeddings or model reranking;
- fleet rollout before one producer/consumer rollback slice;
- semantic content changes such as `core.AgentExperience`.

## Required proof before defaults

One minimum vertical slice must prove:

1. one ontology-kernel release capsule;
2. one consumer intent pinning it;
3. deterministic materialization and adoption receipt;
4. task-language discovery and bound pack;
5. use receipt;
6. semantic rollback and independent runtime rollback.

One slice authorizes a canary only. Search, automatic preflight, startup orientation, and fleet defaults require separate accepted gates and evidence.

## Candidate lifecycle after ADR

```text
schema fixtures -> producer capsule -> consumer intent -> adoption -> discovery/use -> rollback -> evidence -> later default decisions
```

This is candidate sequencing, not an implementation plan or authorization.
