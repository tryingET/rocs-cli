---
summary: "Decision:52 rereview plan after machine-schema fixture expansion."
read_when: ["Running the decision:52 machine-schema rereview."]
type: "review_set_plan"
decision_id: 52
reviewed_artifact: "docs/project/semantic-discovery-protocol-v0.md"
---
# Machine-Schema Rereview Set — Decision 52

```text
primary protocol and differential fixtures: e5b42db
Pi companion and prepared-runtime fixtures: 628dce83
prior machine-schema review inputs: e871dc4 / 3ed543eb
prior peer runs: scoutpeer-mrhrfkgx-ab12b8e3 / scoutpeer-mrhrfkha-2de8eb1f
```

The rereview is limited to closure of the two machine-schema review lanes:

1. Python/ROCS scoring, schema, invariant, JCS, digest, and negative-fixture validation.
2. TypeScript/Pi independent fixture-only verification with no Python imports or producer calls.
3. Controlling lifecycle synthesis.

Any invalid golden, conflicting order, missing pointer/invariant expectation, or divergent digest returns `revise_rfc`. Review only.
