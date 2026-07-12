---
summary: "Fresh decision:52 review plan over machine-readable semantic discovery and prepared-runtime schemas."
read_when: ["Running the decision:52 machine-schema review."]
type: "review_set_plan"
decision_id: 52
reviewed_artifact: "docs/project/semantic-discovery-protocol-v0.md"
---
# Machine-Schema Review Set — Decision 52

## Exact inputs

```text
primary RFC and protocol artifacts: e871dc4
Pi companion and prepared-runtime schema: 3ed543eb
operator authorization: pending commit containing this plan
prior controlling closure: semantic-preflight-fifth-review-synthesis-v4.md@fc9aa42
```

Required reviewed files:

- `semantic-discovery-protocol-v0.md`
- `semantic-discovery-v0/protocol.schema.json`
- `semantic-discovery-v0/invariants.md`
- `semantic-discovery-v0/golden-fixtures.json`
- Pi `semantic-preflight-adapter-v0.md`
- Pi `semantic-preflight-v0/prepared-runtime.schema.json`

## Lanes

1. Python/ROCS producer and JSON-Schema review.
2. TypeScript/Pi independent verifier and fixture review.
3. Lifecycle synthesis checks exact inputs and may emit only `ready_for_adr`, `revise_rfc`, or `reject_current_direction`.

Any structural contradiction, invalid golden fixture, divergent digest, or missing cross-field invariant forces `revise_rfc`. Review only.
