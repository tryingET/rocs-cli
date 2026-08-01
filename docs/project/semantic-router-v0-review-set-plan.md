---
summary: "Strict multi-lane review plan for semantic-router-v0."
read_when:
  - "Reviewing the semantic-router-v0 design packet."
type: "review_set_plan"
status: "proposed"
---
# Semantic router v0 review-set plan

## Reviewed packet

Review the exact aggregate of:

- `docs/project/semantic-router-v0-problem-brief.md`;
- `docs/project/semantic-router-v0-exploration.md`;
- `docs/project/semantic-router-v0-rfc.md`;
- `docs/project/semantic-router-v0-validation-rollout-rollback.md`;
- `docs/project/semantic-router-v0/protocol.schema.json`;
- `docs/project/semantic-router-v0/invariants.md`;
- this review-set plan.

`docs/project/semantic-router-v0/packet-manifest.json` is the derived identity envelope and is not itself in the aggregate.

The manifest lists each reviewed path in UTF-8 byte order with canonical decimal byte length and lowercase SHA-256. The aggregate preimage is the concatenation of UTF-8 rows:

```text
path<TAB>canonical_decimal_byte_length<TAB>lowercase_sha256<LF>
```

There is no header or trailing data after the final LF. Ordinary SHA-256 of that preimage is `packet_aggregate_sha256`. The review commit, inventory, per-file identities, and aggregate must be recorded before reviews begin. Any packet mutation invalidates prior verdicts.

## Closure mode

`multi_lane_requires_synthesis`

All required lanes must return an explicit verdict. A controlling synthesis must cite every lane, resolve or preserve each blocker, and state one legal next move:

- `ready_for_adr`;
- `revise_and_rereview`;
- `reject`.

No implementation begins from lane reviews alone.

## Required lanes

### Lane A — Semantic authority and owner boundary

Questions:

- Does ontology-owner-authored policy preserve source-owner authority?
- Does ROCS interpret rather than invent meaning?
- Is `no_policy_domain_support` scoped to the exact policy coordinate rather than universal truth?
- Are anti-examples and routing exclusions lawfully distinct?
- Does consumer projection preserve rather than override router evidence?
- Is a separate development policy file an acceptable coordinate?

Blockers include hidden meaning authored in code, ROCS claiming consumer desired state, or consumer heuristics silently overriding abstention.

### Lane B — Protocol, security, and compatibility

Questions:

- Are new schemas and digest domains additive?
- Can existing discovery remain byte-compatible?
- Are errors, admission, retrieval, routing, and projection structurally distinct?
- Are clause matching, joint routes, ordering, witnesses, limits, and safe errors deterministic?
- Are symlink, resource, snapshot, collision, and hostile-data boundaries complete?
- Is lexical lineage retained without allowing scores to authorize routes?

Blockers include in-place mutation of discovery v0, ambiguous canonicalization, unbounded resources, or operational failure represented as abstention.

### Lane C — Empirical falsification and anti-leakage

Questions:

- Is B0 truthfully treated as contaminated historical evidence with auditable exposure and clause provenance?
- Are D/U/O independent and sufficiently adversarial?
- Do safety gates prevent trivial routing while utility gates prevent trivial abstention?
- Are annotation and leakage rules independently auditable?
- Are pass, fail, and indeterminate outcomes complete?
- Does the plan block provider/model and consumer activation claims?

Blockers include B0-derived clauses, implementer access to sealed U/O, missing null confidence bounds, or acceptance from aggregate metrics that hide a failed stratum.

## Cross-lane mandatory issues

Every lane must address:

1. Verify the selected explicit owner-authored joint-route design; inferred independent-evidence heuristics are excluded.
2. Verify the selected complete nested unchanged discovery result; digest-only lineage is excluded.
3. Verify cumulative resource and matching-work maxima against the complete schema/invariants.
4. Verify that an accepted ADR authorizes only ROCS development mechanics with conspicuously synthetic fixtures before any concrete policy exists.
5. Verify cross-repo Decision 102 scope while preserving separate owner-local tasks and gates for every later effect.

## Verdict vocabulary

- `accept`: no unresolved blocker; packet may enter synthesis.
- `accept_with_conditions`: only conditions mechanically checkable before ADR.
- `revise`: at least one blocker requires packet mutation and full rereview.
- `reject`: the architecture is unsound within the stated constraints.

## Synthesis rule

The synthesis may not average verdicts. It must:

- enumerate all blockers by lane;
- identify exact packet corrections or owner deferrals;
- distinguish design acceptance from implementation authorization;
- choose one protocol boundary;
- choose one owner split;
- choose one validation lineage;
- preserve unresolved cross-repo activation work as blocked.

`ready_for_adr` requires all blocker corrections to be present in one immutable final packet and every required lane to accept that exact aggregate.
